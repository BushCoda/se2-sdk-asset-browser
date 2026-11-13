# SPDX-License-Identifier: GPL-3.0-or-later
"""Classify SDK FBX paths independently of Blender."""
import re

MODEL_ROOTS = ("Blocks", "Armors")
PRODUCTION_FAMILIES = {
    "assembler", "fabricator", "gearforge", "o2h2generator", "oxygenfarm",
    "refinery", "smelter", "survivalkit",
}
ANIMATION = re.compile(r"(?:^|[_ .-])anim(?:ation)?s?(?:$|[_ .-]|\d)", re.I)
ALTERNATE = re.compile(r"lod\d|(?<!non)fractured|construction|collision|deformed", re.I)


def model_filters(path):
    family = path.parts[1]
    words = re.sub(r"([a-z])([A-Z])|([A-Z])([A-Z][a-z])",
                   lambda match: " ".join(part for part in match.groups() if part), family)
    category = "Armour" if path.parts[0] == "Armors" else words
    size = next((int(part) for part in path.parts[2:-1]
                 if re.fullmatch(r"[1-9][0-9]{1,4}", part)), None)
    return category, f"{size / 100:g} m" if size is not None else "Unspecified"


def classify_model(path):
    parts = path.parts
    if len(parts) < 3 or parts[0] not in MODEL_ROOTS or path.suffix.lower() != ".fbx":
        return None
    if any(ANIMATION.search(part) for part in (*parts[:-1], path.stem)):
        return None
    family = parts[1].casefold()
    if family in {"icons", "sound"}:
        return None
    production = parts[0] == "Blocks" and family in PRODUCTION_FAMILIES
    return ("PRODUCTION" if production else "MODELS", bool(ALTERNATE.search(path.as_posix())))
