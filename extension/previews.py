# SPDX-License-Identifier: GPL-3.0-or-later
"""Manage locally cached previews without importing into the active scene."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

import bpy
import bpy.utils.previews

icons = None
job = None
failure = None


def cache(path):
    stat = path.stat()
    signature = [f"2:{path}:{stat.st_size}:{stat.st_mtime_ns}"]
    if path.suffix.lower() == ".comparm":
        from .armor import resolve_faces
        root = next(parent.parent for parent in path.parents if parent.name == "Armors")
        for source, _, _ in resolve_faces(root, path):
            signature.append(f"{source}:{source.stat().st_mtime_ns}")
    key = hashlib.sha256("\n".join(signature).encode()).hexdigest()
    return Path(bpy.utils.user_resource("DATAFILES")) / "se2_sdk_asset_browser" / "previews" / key


def load(folder):
    if not (folder / "details.json").is_file() or not (folder / "thumbnail.png").is_file():
        return None
    try:
        data = json.loads((folder / "details.json").read_text(encoding="utf-8"))
        key = folder.name
        if key not in icons:
            icons.load(key, str(folder / "thumbnail.png"), "IMAGE")
        return icons[key].icon_id, data
    except (OSError, ValueError, RuntimeError):
        return None


def poll():
    global job, failure
    process, folder, deadline = job
    if process.poll() is None:
        if time.monotonic() < deadline:
            return 0.25
        process.kill()
        failure = folder
    elif process.returncode or load(folder) is None:
        failure = folder
    job = None
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
    return None


def start(path):
    global job, failure
    if job:
        raise ValueError("A model preview is already being generated")
    folder = cache(path)
    folder.mkdir(parents=True, exist_ok=True)
    args = [bpy.app.binary_path, "-b", "--factory-startup", "--python-exit-code", "1",
            "--python", str(Path(__file__).with_name("preview_worker.py")), "--", str(path), str(folder)]
    with (folder / "preview.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    failure = None
    job = process, folder, time.monotonic() + 180
    bpy.app.timers.register(poll, first_interval=0.25, persistent=True)


def register():
    global icons
    icons = bpy.utils.previews.new()


def unregister():
    global icons, job, failure
    if bpy.app.timers.is_registered(poll):
        bpy.app.timers.unregister(poll)
    if job and job[0].poll() is None:
        job[0].kill()
    job = failure = None
    bpy.utils.previews.remove(icons)
    icons = None
