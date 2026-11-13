# SPDX-License-Identifier: GPL-3.0-or-later
"""Classify SDK FBX paths independently of Blender."""
import re
import json

MODEL_ROOTS = ("Blocks", "Armors")
PRODUCTION_FAMILIES = {
    "assembler", "fabricator", "gearforge", "o2h2generator", "oxygenfarm",
    "refinery", "smelter", "survivalkit",
}
ANIMATION = re.compile(r"(?:^|[_ .-])anim(?:ation)?s?(?:$|[_ .-]|\d)", re.I)
ALTERNATE = re.compile(r"lod\d|(?<!non)fractured|construction|collision|deformed", re.I)
FUNCTIONS = {
    "Structure": "catwalks coverwalls deckpanel detailingblocks handrail interiorpillarsandwalls passages pillars ramp stairs truss walls",
    "Doors and Windows": "doors gate hangardoor windows",
    "Power": "batteries capacitor hydrogenengine reactor solarpanel waterturbine windturbine",
    "Cargo and Conveyors": "cargocontainers collector connectors conveyors crate pipeset tanks watertank",
    "Flight and Mobility": "cockpit controlseat flightseat gyroscopes jumpdrive landinggear parachute suspensionwheels thrusters wheels",
    "Controls and Displays": "button buttonpanels controlpanel eventcontroller lcdpanels programmableblock projector remotecontroller sensor timer",
    "Mechanical": "artificialmass gravitygenerator hinge magneticplates merge pistons rotor",
    "Lighting": "lightpanels lights neontubes",
    "Tools": "drills grinder welder",
    "Communications": "antennas camera laserantenna rss_scanner",
    "Crew and Interior": "bed cryopod kitchen lockers medicalroom seat shower sink smallclutterprops table toilet",
    "Defence": "decoy gatlingcannon gatlingturret interiorturret rocketlauncher rocketturret safezone warheads",
}
FAMILY_GROUPS = {family: group for group, families in FUNCTIONS.items() for family in families.split()}


def metadata_value(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")).get("$Value", {})
    except (OSError, ValueError):
        return {}


def model_owners(root):
    owners = {}
    for path in sorted((root / "Blocks").rglob("*_BlockModelDefinition.partialdef")):
        model = metadata_value(path).get("Manipulator", {}).get("Model")
        if isinstance(model, str):
            owners.setdefault(model.removeprefix("{G}").lower(), path.relative_to(root))
    return owners


def model_filters(path, owner=None):
    owner = owner or path
    family = owner.parts[1]
    words = re.sub(r"([a-z])([A-Z])|([A-Z])([A-Z][a-z])",
                   lambda match: " ".join(part for part in match.groups() if part), family)
    key = family.casefold()
    group = "Production" if key in PRODUCTION_FAMILIES else FAMILY_GROUPS.get(key)
    category = ("Light Armour" if path.suffix == ".comparm" else "Armour Faces") if path.parts[0] == "Armors" else (
        f"{group} / {words}" if group else words)
    size = next((int(part) for part in owner.parts[2:-1]
                 if re.fullmatch(r"[1-9][0-9]{1,4}", part)), None)
    return category, f"{size / 100:g} m" if size is not None else "Unspecified"


def classify_model(path):
    parts = path.parts
    if len(parts) >= 4 and parts[0] == "Armors" and path.suffix.lower() == ".comparm":
        return "MODELS", False
    if len(parts) < 3 or parts[0] not in MODEL_ROOTS or path.suffix.lower() != ".fbx":
        return None
    if any(ANIMATION.search(part) for part in (*parts[:-1], path.stem)):
        return None
    family = parts[1].casefold()
    if family in {"icons", "sound"}:
        return None
    production = parts[0] == "Blocks" and family in PRODUCTION_FAMILIES
    return ("PRODUCTION" if production else "MODELS",
            parts[0] == "Armors" or bool(ALTERNATE.search(path.as_posix())))
