# SPDX-License-Identifier: GPL-3.0-or-later
"""Resolve SDK composite armour into its transformed FBX faces."""
from functools import lru_cache
import json
from math import radians

import bpy
from mathutils import Euler, Matrix


def value(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))["$Value"]


@lru_cache(maxsize=1)
def armor_files(root):
    return {value(meta)["AssetID"].lower(): meta.with_suffix("")
            for pattern in ("*.armorside.meta", "*.fbx.meta")
            for meta in (root / "Armors").rglob(pattern)}


def resolve_faces(root, path):
    index = armor_files(root)
    result = []
    for face in value(path)["SideMeshes"]:
        side = value(index[face["SideMesh"].removeprefix("{G}").lower()])
        source = index[side["ModelAsset"].removeprefix("{G}").lower()]
        if not source.is_file():
            raise ValueError(f"Missing armour face {source.name}")
        result.append((source, face, side))
    if not result:
        raise ValueError("The armour recipe has no faces")
    return result


def assemble(root, path, order="XYZ"):
    faces = resolve_faces(root, path)
    context = bpy.context
    collection = bpy.data.collections.new(f"Light Armour · {path.stem}")
    context.scene.collection.children.link(collection)
    collection["SDK source"] = path.relative_to(root).as_posix()
    axes = Matrix.Rotation(radians(90), 4, "X")
    templates = {}
    created = set()
    try:
        for source, face, side in faces:
            if source not in templates:
                before = set(bpy.data.objects)
                bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False, use_image_search=False)
                imported = set(bpy.data.objects) - before
                created.update(imported)
                templates[source] = [(obj.data, obj.matrix_world.copy(), obj.name)
                                     for obj in imported if obj.type == "MESH" and obj.data.polygons]
                if not templates[source]:
                    raise ValueError(f"No mesh in armour face {source.name}")
            rotation = Euler(tuple(radians(int(face["Rotation"][axis].removeprefix("Rotate")))
                                   for axis in "XYZ"), order).to_matrix().to_4x4()
            translation = Matrix.Translation(tuple(side["Translation"][axis] for axis in "XYZ"))
            local = Euler(tuple(radians(side["Rotation"][axis]) for axis in "XYZ")).to_matrix().to_4x4()
            scale = Matrix.Scale(side["Scale"], 4)
            offset = Matrix.Translation((0, 0, face.get("PlanarOffset", 0)))
            transform = axes @ rotation @ offset @ translation @ local @ scale @ axes.inverted()
            for mesh, matrix, name in templates[source]:
                obj = bpy.data.objects.new(name, mesh)
                collection.objects.link(obj)
                obj.matrix_world = transform @ matrix
    except Exception:
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
        raise
    finally:
        for obj in created:
            bpy.data.objects.remove(obj, do_unlink=True)
    return collection
