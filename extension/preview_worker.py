# SPDX-License-Identifier: GPL-3.0-or-later
"""Render one FBX in a separate Blender process."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def main(source, output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = Path(source)
    if path.suffix.lower() == ".comparm":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from armor import assemble
        root = next(parent.parent for parent in path.parents if parent.name == "Armors")
        assemble(root, path)
    else:
        bpy.ops.import_scene.fbx(filepath=source, use_anim=False, use_image_search=False)
    scene = bpy.context.scene
    meshes = [obj for obj in scene.objects if obj.type == "MESH" and obj.data.polygons]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    if not points:
        raise ValueError("This FBX has no visible mesh geometry")
    low, high = (Vector([fn(p[i] for p in points) for i in range(3)]) for fn in (min, max))
    center = (low + high) / 2
    span = max((high - low).length, 0.01)
    camera = bpy.data.objects.new("Preview Camera", bpy.data.cameras.new("Preview Camera"))
    scene.collection.objects.link(camera)
    camera.location = center + Vector((1, -1.5, 0.95)).normalized() * span * 2
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.15
    camera.data.clip_end = span * 5 + 10
    camera.data.clip_start = min(0.01, span / 20)
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = (0.43, 0.53, 0.64)
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    scene.render.resolution_x = scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output / "thumbnail.png")
    bpy.ops.render.render(write_still=True)
    materials = sorted({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material})
    metadata = {"meshes": sorted(obj.name for obj in meshes), "materials": materials,
                "dimensions": [round(value, 3) for value in high - low]}
    (output / "details.json").write_text(json.dumps(metadata), encoding="utf-8")


if __name__ == "__main__":
    source, directory = sys.argv[sys.argv.index("--") + 1:]
    main(source, Path(directory))
