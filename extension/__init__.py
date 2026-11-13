# SPDX-License-Identifier: GPL-3.0-or-later
"""Search and import assets directly from an installed Space Engineers 2 Mod SDK."""
from functools import lru_cache

from pathlib import Path
import re
import time

import bpy

from .builder import Library, document
from .model_scope import MODEL_ROOTS, classify_model, metadata_value, model_filters, model_owners
from . import armor, previews

SDK_PATH = Path("steamapps/common/Space Engineers 2 - Mod SDK/GameData/Vanilla/Assets")
LAST_CLICK = None


def detect_sdk():
    import os
    roots = [Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Steam"]
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                roots.insert(0, Path(winreg.QueryValueEx(key, "SteamPath")[0]))
        except OSError:
            pass
    for root in list(roots):
        vdf = root / "steamapps/libraryfolders.vdf"
        if vdf.is_file():
            roots.extend(Path(value.replace("\\\\", "\\")) for value in
                         re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf8", errors="replace")))
    return next((root / SDK_PATH for root in roots if (root / SDK_PATH / "Blocks").is_dir()), None)


@lru_cache(maxsize=1)
def index(root):
    library = Library(root)
    models = []
    owners = model_owners(root)
    for folder in MODEL_ROOTS:
        for path in (root / folder).rglob("*"):
            relative = path.relative_to(root)
            result = classify_model(relative)
            if result and path.is_file():
                tab, stage = result
                owner = None
                if folder == "Blocks":
                    asset_id = metadata_value(path.with_suffix(".fbx.meta")).get("AssetID", "")
                    owner = owners.get(asset_id.lower())
                    if owner:
                        owner_scope = classify_model(owner.with_suffix(".fbx"))
                        if owner_scope:
                            tab = owner_scope[0]
                models.append((tab, relative.as_posix(), stage, *model_filters(relative, owner)))
    for paths in library.definitions.values():
        for path in paths:
            rel = path.relative_to(root)
            if not any("material" in part.lower() or "decal" in part.lower() for part in rel.parts[:-1]):
                continue
            kind, _ = document(path)
            if "MaterialDefinition" in kind or "DecalKind" in kind:
                relative = path.relative_to(root).as_posix()
                tab = "DECALS" if "decal" in relative.lower() or "atlas" in path.stem.lower() else "MATERIALS"
                models.append((tab, relative, False, "", ""))
    return library, sorted(models, key=lambda row: (Path(row[1]).stem.casefold(), row[1]))


def settings(context):
    return context.preferences.addons[__package__].preferences


def refresh(context):
    state = context.window_manager.se2_browser
    state.results.clear()
    state.active = 0
    state.total = 0
    state.categories.clear()
    state.sizes.clear()
    sdk = settings(context).sdk
    if not sdk:
        state.total = 0
        return
    root = Path(bpy.path.abspath(sdk)).resolve()
    if not (root / "Blocks").is_dir():
        state.total = 0
        return
    _, records = index(root)
    candidates = [record for record in records
                  if record[0] == state.tab and (state.variants or not record[2])]
    for collection, column in ((state.categories, 3), (state.sizes, 4)):
        values = {row[column] for row in candidates if row[column]}
        ordered = sorted(values, key=(lambda value: float(value[:-2]) if value.endswith(" m")
                                     else float("inf")) if column == 4 else str.casefold)
        for value in ordered:
            collection.add().name = value
    terms = state.query.casefold().split()
    count = 0
    for _, relative, _, category, size in candidates:
        if category and state.category and category != state.category:
            continue
        if size and state.size and size != state.size:
            continue
        if not all(term in relative.casefold() for term in terms):
            continue
        if count < 300:
            entry = state.results.add()
            entry.name = Path(relative).stem
            entry.relative = relative
            entry.size = size
            entry.category = category
        count += 1
    state.total = count


def update(self, context):
    refresh(context)


def change_tab(self, context):
    self.category = ""
    self.size = ""
    refresh(context)


class SE2Entry(bpy.types.PropertyGroup):
    relative: bpy.props.StringProperty()
    size: bpy.props.StringProperty()
    category: bpy.props.StringProperty()


class SE2BrowserState(bpy.types.PropertyGroup):
    results: bpy.props.CollectionProperty(type=SE2Entry)
    active: bpy.props.IntProperty()
    total: bpy.props.IntProperty()
    categories: bpy.props.CollectionProperty(type=SE2Entry)
    sizes: bpy.props.CollectionProperty(type=SE2Entry)
    category: bpy.props.StringProperty(name="Category", update=update)
    size: bpy.props.StringProperty(name="Size", update=update)
    query: bpy.props.StringProperty(name="Search SDK", update=update)
    variants: bpy.props.BoolProperty(name="Show LODs and alternate stages", update=update)
    tab: bpy.props.EnumProperty(items=[
        ("MODELS", "Blocks", ""), ("PRODUCTION", "Production", ""),
        ("MATERIALS", "Materials", ""), ("DECALS", "Decals", "")
    ], update=change_tab)


class SE2Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    sdk: bpy.props.StringProperty(name="SDK Vanilla Assets", subtype="DIR_PATH")

    def draw(self, context):
        self.layout.prop(self, "sdk")
        self.layout.operator("se2.scan_sdk")


class SE2Scan(bpy.types.Operator):
    bl_idname = "se2.scan_sdk"
    bl_label = "Find or Rescan SDK"

    def execute(self, context):
        prefs = settings(context)
        if not prefs.sdk or not (Path(bpy.path.abspath(prefs.sdk)) / "Blocks").is_dir():
            found = detect_sdk()
            if found is None:
                self.report({"ERROR"}, "Set the SDK GameData/Vanilla/Assets path in the add-on preferences")
                return {"CANCELLED"}
            prefs.sdk = str(found)
        index.cache_clear()
        armor.armor_files.cache_clear()
        refresh(context)
        return {"FINISHED"}


def import_asset(root, relative, context):
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("The selected SDK file could not be found")
    if path.suffix.lower() == ".comparm" and classify_model(path.relative_to(root)):
        try:
            collection = armor.assemble(root, path)
        except KeyError as error:
            raise ValueError(f"Missing armour recipe reference {error}") from error
        return f"Imported {collection.name} ({len(collection.objects)} mesh parts)"
    library, _ = index(root)
    if path.suffix.lower() == ".fbx":
        old = set(bpy.data.objects)
        if classify_model(path.relative_to(root)) is None:
            raise ValueError("This FBX is outside the block model library")
        bpy.ops.import_scene.fbx(filepath=str(path), use_image_search=False, use_anim=False)
        imported = set(bpy.data.objects) - old
        if not imported:
            raise ValueError("Blender did not import any objects from this FBX")
        collection = bpy.data.collections.new(path.stem)
        context.scene.collection.children.link(collection)
        materials = set()
        for obj in imported:
            for previous in list(obj.users_collection):
                previous.objects.unlink(obj)
            collection.objects.link(obj)
            materials.update(slot.material for slot in obj.material_slots if slot.material)
        collection["SDK source"] = relative
        for mat in materials:
            definition, value = library.material_definition(mat.name)
            if definition and not mat.get("SDK definition"):
                library.configure(mat, definition, value)
        return f"Imported {path.stem} ({len(imported)} objects)"
    kind, value = document(path)
    if "MaterialDefinition" in kind:
        mat = bpy.data.materials.new(path.stem)
        mat.use_fake_user = True
        library.configure(mat, path, value)
        library.mark(mat, "Materials", path)
        obj = context.active_object
        if obj and obj.type == "MESH":
            obj.data.materials.append(mat)
        return f"Imported material {mat.name}"
    raise ValueError("This decal definition describes an in-game effect. Choose an atlas or a model containing decal meshes.")


class SE2Import(bpy.types.Operator):
    bl_idname = "se2.import_sdk_asset"
    bl_label = "Import Selected Asset"
    bl_options = {"REGISTER", "UNDO"}
    row: bpy.props.IntProperty(default=-1, options={"SKIP_SAVE"})

    def invoke(self, context, event):
        global LAST_CLICK
        state = context.window_manager.se2_browser
        if self.row >= 0:
            if self.row >= len(state.results):
                return {"CANCELLED"}
            state.active = self.row
            key = state.results[self.row].relative
            now = time.monotonic()
            if not LAST_CLICK or LAST_CLICK[0] != key or now - LAST_CLICK[1] > 0.45:
                LAST_CLICK = key, now
                return {"FINISHED"}
            LAST_CLICK = None
        return self.execute(context)

    def execute(self, context):
        state = context.window_manager.se2_browser
        if state.active >= len(state.results):
            return {"CANCELLED"}
        root = Path(bpy.path.abspath(settings(context).sdk)).resolve()
        try:
            message = import_asset(root, state.results[state.active].relative, context)
        except (RuntimeError, ValueError, OSError) as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        self.report({"INFO"}, message)
        return {"FINISHED"}


class SE2Preview(bpy.types.Operator):
    bl_idname = "se2.preview_sdk_model"
    bl_label = "Generate Model Preview"

    def execute(self, context):
        state = context.window_manager.se2_browser
        if not 0 <= state.active < len(state.results):
            return {"CANCELLED"}
        root = Path(bpy.path.abspath(settings(context).sdk)).resolve()
        path = (root / state.results[state.active].relative).resolve()
        try:
            if not path.is_relative_to(root) or not classify_model(path.relative_to(root)):
                raise ValueError("Select a block or production model")
            previews.start(path)
        except (OSError, ValueError, KeyError) as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


def draw_model_details(layout, context, item):
    box = layout.box()
    box.label(text=item.name, icon="MESH_CUBE")
    source = Path(item.relative)
    box.label(text=f"{item.category} · {item.size}")
    box.label(text=str(source.parent))
    root = Path(bpy.path.abspath(settings(context).sdk))
    try:
        folder = previews.cache((root / source).resolve())
        preview = previews.load(folder)
    except (OSError, ValueError, KeyError):
        box.label(text="SDK model file unavailable", icon="ERROR")
        return
    if preview:
        icon, details = preview
        box.template_icon(icon_value=icon, scale=8)
        dimensions = " × ".join(f"{value:g}" for value in details["dimensions"])
        box.label(text=f"Mesh bounds: {dimensions} m")
        for key in ("meshes", "materials"):
            values = details[key]
            box.label(text=f"{key.title()} ({len(values)})")
            for value in values[:5]:
                box.label(text=value)
            if len(values) > 5:
                box.label(text=f"Plus {len(values) - 5} more")
    elif previews.job:
        message = "Generating preview…" if previews.job[1] == folder else "Another preview is generating"
        box.label(text=message, icon="TIME")
    else:
        if previews.failure == folder:
            box.label(text="Preview failed. See preview.log in the cache.", icon="ERROR")
        box.operator("se2.preview_sdk_model", icon="RENDER_STILL")


class SE2_UL_sdk_results(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        text = f"{item.name}  ·  {item.size}" if item.size and item.size != "Unspecified" else item.name
        button = layout.operator("se2.import_sdk_asset", text=text, emboss=False)
        button.row = index


class SE2_PT_browser(bpy.types.Panel):
    bl_label = "SE2 SDK Asset Browser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SE2 Assets"

    def draw(self, context):
        layout = self.layout
        state = context.window_manager.se2_browser
        layout.operator("se2.scan_sdk")
        layout.prop(state, "tab", expand=True)
        layout.prop(state, "query", icon="VIEWZOOM")
        if state.tab in {"MODELS", "PRODUCTION"}:
            layout.prop_search(state, "category", state, "categories")
            layout.prop_search(state, "size", state, "sizes")
            layout.prop(state, "variants")
        if not state.total:
            layout.label(text="No matching assets")
        layout.template_list("SE2_UL_sdk_results", "", state, "results", state, "active", rows=12)
        if state.total > len(state.results):
            layout.label(text=f"Showing {len(state.results)} of {state.total}. Narrow your search.")
        if state.active < len(state.results):
            layout.operator("se2.import_sdk_asset")
            if state.tab in {"MODELS", "PRODUCTION"}:
                draw_model_details(layout, context, state.results[state.active])


classes = (SE2Entry, SE2BrowserState, SE2Preferences, SE2Scan, SE2Import, SE2Preview,
           SE2_UL_sdk_results, SE2_PT_browser)


def register():
    previews.register()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.se2_browser = bpy.props.PointerProperty(type=SE2BrowserState)


def unregister():
    previews.unregister()
    del bpy.types.WindowManager.se2_browser
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    index.cache_clear()
