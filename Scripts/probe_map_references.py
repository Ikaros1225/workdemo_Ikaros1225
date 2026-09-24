import unreal
unreal.log("MAP_REF_UNREAL_FUNCS=%s" % [x for x in dir(unreal) if "object" in x.lower() or "class" in x.lower()])

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
asset = unreal.EditorAssetLibrary.load_asset(MAP_PATH)
unreal.log("MAP_REF_ASSET=%s class=%s" % (asset, asset.get_class().get_name() if asset else None))
tools = unreal.AssetToolsHelpers.get_asset_tools()
try:
    refs = tools.find_soft_references_to_object(unreal.SoftObjectPath(MAP_PATH))
    unreal.log("MAP_REF_SOFT=%s" % refs)
    for ref in refs:
        unreal.log("MAP_REF_SOFT_ITEM=%s class=%s outer=%s cdo=%s" % (
            ref.get_path_name(), ref.get_class().get_name(), ref.get_outermost().get_name(),
            ref.has_any_flags(unreal.ObjectFlags.CLASS_DEFAULT_OBJECT)))
except Exception as exc:
    unreal.log_error("MAP_REF_SOFT_ERROR=%s" % exc)
try:
    packages = unreal.EditorAssetLibrary.find_package_referencers_for_asset(MAP_PATH, True)
    unreal.log("MAP_REF_PACKAGES=%s" % packages)
except Exception as exc:
    unreal.log_error("MAP_REF_PACKAGE_ERROR=%s" % exc)

try:
    settings = unreal.get_default_object(unreal.GameMapsSettings)
    editor_map = settings.get_editor_property("editor_startup_map")
    game_map = settings.get_editor_property("game_default_map")
    unreal.log("MAP_REF_SETTINGS=%s editor=%s editor_text=%s game=%s game_text=%s" % (
        settings.get_path_name(),
        editor_map, editor_map.export_text(), game_map, game_map.export_text()))
    for property_name in ("editor_startup_map", "game_default_map"):
        settings.set_editor_property(property_name, unreal.SoftObjectPath(
            "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Work.ThirdPersonMap_MineOffice_Work"))
    editor_map = settings.get_editor_property("editor_startup_map")
    game_map = settings.get_editor_property("game_default_map")
    unreal.log("MAP_REF_SETTINGS_AFTER editor_text=%s game_text=%s" % (
        editor_map.export_text(), game_map.export_text()))
except Exception as exc:
    unreal.log_error("MAP_REF_SETTINGS_ERROR=%s" % exc)

for cls in list(unreal.ClassIterator()):
    try:
        cdo = cls.get_default_object()
        if not cdo:
            continue
        for prop in cls.get_properties():
            ptype = prop.get_class().get_name()
            if "SoftObject" in ptype or "Object" in ptype:
                try:
                    value = cdo.get_editor_property(prop.get_name())
                    text = value.export_text() if hasattr(value, "export_text") else str(value)
                    if "ThirdPersonMap" in text:
                        unreal.log("MAP_REF_CDO class=%s prop=%s type=%s value=%s" % (
                            cls.get_name(), prop.get_name(), ptype, text))
                except Exception:
                    pass
    except Exception:
        pass
