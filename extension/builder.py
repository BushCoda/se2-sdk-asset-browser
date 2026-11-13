# SPDX-License-Identifier: GPL-3.0-or-later
"""Run in Blender background mode. All source files are read-only."""
from collections import defaultdict
import json
from pathlib import Path
import re
import uuid

import bpy

NAMESPACE = uuid.UUID("45eebce9-c10c-4d69-a15b-cc6ffb605fd3")
IMAGE_TYPES = {".png", ".dds", ".tga", ".jpg", ".jpeg", ".exr", ".tif", ".tiff"}


def document(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data.get("$Type", ""), data.get("$Value", {})
    except (ValueError, OSError, UnicodeError):
        return "", {}


class Library:
    def __init__(self, source):
        self.source = source

        self.catalogs = set()
        self.guid = None
        self.definitions = defaultdict(list)
        for path in source.rglob("*.def"):
            self.definitions[path.stem.casefold()].append(path)

    def mark(self, block, category, path):
        self.catalogs.add(category)
        block.asset_mark()
        block.asset_data.catalog_id = str(uuid.uuid5(NAMESPACE, category))
        block.asset_data.author = "Keen Software House (SDK source)"
        block.asset_data.description = path.relative_to(self.source).as_posix()
        block["SDK source"] = block.asset_data.description

    def resolve(self, ref):
        if not isinstance(ref, str):
            return None
        if self.guid is None:
            self.guid = {}
            for meta in self.source.rglob("*.meta"):
                if meta.with_suffix("").suffix.lower() not in IMAGE_TYPES | {".comptex"}:
                    continue
                _, data = document(meta)
                if data.get("AssetID"):
                    self.guid[data["AssetID"].lower()] = meta.with_suffix("")
        return self.guid.get(ref.removeprefix("{G}").lower())

    def texture(self, ref, channel=0):
        path = self.resolve(ref)
        if not path:
            return None
        if path.suffix.lower() in IMAGE_TYPES and path.is_file():
            return path
        _, data = document(path)
        sources = data.get("PresetModel", {}).get("TextureSourceModels", [])
        if channel < len(sources):
            image = self.resolve(sources[channel].get("Texture"))
            if image and image.is_file() and image.suffix.lower() in IMAGE_TYPES:
                return image
        return None

    def configure(self, mat, path, value):
        mat["SDK definition"] = path.relative_to(self.source).as_posix()
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        shader = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
        if shader is None:
            return
        connections = (
            ("ColorMetalTexture", 0, "Base Color", False),
            ("ColorMetalTexture", 3, "Metallic", True),
            ("NormalRoughnessTexture", 0, "Normal", True),
            ("NormalRoughnessTexture", 3, "Roughness", True),
        )
        for index, (key, channel, socket, noncolor) in enumerate(connections):
            image_path = self.texture(value.get(key), channel)
            if image_path is None:
                continue
            image = bpy.data.images.load(str(image_path), check_existing=True)
            if noncolor and image.colorspace_settings.name != "Non-Color":
                image = image.copy()
                image.colorspace_settings.name = "Non-Color"
            node = nodes.new("ShaderNodeTexImage")
            node.image = image
            node.label = socket
            node.location = (-660, -300 * index)
            if socket == "Normal":
                normal = nodes.new("ShaderNodeNormalMap")
                normal.location = (-350, -300 * index)
                links.new(node.outputs["Color"], normal.inputs["Color"])
                links.new(normal.outputs["Normal"], shader.inputs[socket])
            else:
                links.new(node.outputs["Color"], shader.inputs[socket])
        mat["Preview texture inputs"] = sum(n.type == "TEX_IMAGE" for n in nodes)

    def material_definition(self, name):
        name = re.sub(r"\.\d{3}$", "", name).casefold()
        for path in self.definitions.get(name, []):
            kind, value = document(path)
            if "MaterialDefinition" in kind:
                return path, value
        return None, {}
