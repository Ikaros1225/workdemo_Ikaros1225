import unreal

TEMP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"
MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
BACKUP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_Original_20260924_1509"


if not unreal.EditorAssetLibrary.does_asset_exist(TEMP_PATH):
    raise RuntimeError("Validated temporary map is missing: " + TEMP_PATH)
if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    raise RuntimeError("Original map is missing: " + MAP_PATH)
if unreal.EditorAssetLibrary.does_asset_exist(BACKUP_PATH):
    raise RuntimeError("Backup map already exists; refusing to overwrite: " + BACKUP_PATH)

new_world = unreal.EditorLoadingAndSavingUtils.load_map(TEMP_PATH)
if not new_world:
    raise RuntimeError("Could not load the validated MineOffice map")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

def redirect_maps_settings_temporarily():
    # The project maps settings CDO usually points at ThirdPersonMap as the
    # startup/default map. Point it at an untouched workspace map in memory
    # after new_blank_map has finished, so AssetTools sees no CDO reference to
    # either package being moved.
    maps_settings = unreal.get_default_object(unreal.GameMapsSettings)
    safe_map = unreal.SoftObjectPath(
        "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Work.ThirdPersonMap_MineOffice_Work")
    for property_name in ("editor_startup_map", "game_default_map"):
        try:
            maps_settings.set_editor_property(property_name, safe_map)
        except Exception as exc:
            unreal.log_warning("Could not redirect maps settings temporarily (%s): %s" % (property_name, exc))
    unreal.log("MINE_OFFICE_PROMOTE maps_settings=%s/%s" % (
        maps_settings.get_editor_property("editor_startup_map").export_text(),
        maps_settings.get_editor_property("game_default_map").export_text()))

def rename_without_prompt(source_path, destination_path):
    asset = unreal.EditorAssetLibrary.load_asset(source_path)
    if not asset:
        raise RuntimeError("Could not load asset for rename: " + source_path)
    # AssetTools.rename_assets performs the package move without opening the
    # editor's source/config/text reference confirmation dialog.
    if not asset_tools.rename_assets([(asset, destination_path)]):
        raise RuntimeError("UE failed to rename asset: %s -> %s" % (source_path, destination_path))
    if not unreal.EditorAssetLibrary.does_asset_exist(destination_path):
        raise RuntimeError("Destination asset missing after rename: " + destination_path)

# Release the original map package before renaming its asset.  The command-line
# editor starts with the project's default map already loaded.
if not unreal.EditorLoadingAndSavingUtils.new_blank_map(False):
    raise RuntimeError("Could not unload the original map before promotion")

redirect_maps_settings_temporarily()

rename_without_prompt(MAP_PATH, BACKUP_PATH)
unreal.log("MINE_OFFICE_PROMOTE original map archived: " + BACKUP_PATH)

# Keep references to the main map path valid by replacing its rename redirector.
redirector = unreal.load_asset(MAP_PATH)
if redirector:
    if not unreal.EditorAssetLibrary.delete_asset(MAP_PATH):
        raise RuntimeError("UE failed to clear the original map redirector")

rename_without_prompt(TEMP_PATH, MAP_PATH)
unreal.log("MINE_OFFICE_PROMOTE new map installed: " + MAP_PATH)

check_world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not check_world:
    raise RuntimeError("Could not reload promoted map")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
by_label = {a.get_actor_label(): a for a in actors}
required = (
    "WB_D_MineOffice",
    "WB_D_MineOffice_Floor",
    "WB_D_MineOffice_Wall_Back",
    "WB_D_MineOffice_Wall_Entry_Left",
    "WB_D_MineOffice_Wall_Entry_Right",
    "WB_D_MineOffice_Wall_Entry_DoorHeader",
    "WB_D_MineOffice_Door_Leaf_Open",
    "WB_D_MineOffice_Interior_Light",
    "WB_D_MineOffice_Roof",
    "WB_D_MineYard",
    "WB_B_GasStation_Building_Light_Ground",
    "WB_B_GasStation_Building_Roof",
)
missing = [label for label in required if label not in by_label]
if missing:
    raise RuntimeError("Promoted map is missing expected actors: " + ", ".join(missing))

office = [a for a in actors if a.get_actor_label().startswith("WB_D_MineOffice")]
labels = [a.get_actor_label() for a in office]
if any("Stair" in label or "SecondFloor" in label or "UpperFloor" in label for label in labels):
    raise RuntimeError("Promoted office unexpectedly contains stairs or a second floor")

office_floor = by_label["WB_D_MineOffice_Floor"]
yard_origin, yard_extent = by_label["WB_D_MineYard"].get_actor_bounds(False)
floor_origin, floor_extent = office_floor.get_actor_bounds(False)
floor_top = floor_origin.z + floor_extent.z
yard_top = yard_origin.z + yard_extent.z
if abs(floor_top - yard_top) > 1.0:
    raise RuntimeError("Promoted MineOffice entrance is not level with MineYard")

light = by_label["WB_D_MineOffice_Interior_Light"].get_component_by_class(unreal.RectLightComponent)
intensity = float(light.get_editor_property("intensity"))
attenuation = float(light.get_editor_property("attenuation_radius"))
if not (60 <= intensity <= 120 and 600 <= attenuation <= 900):
    raise RuntimeError("Promoted MineOffice light is outside the intended range")

if not unreal.EditorLoadingAndSavingUtils.save_map(check_world, MAP_PATH):
    raise RuntimeError("Could not save promoted map after validation")
unreal.log("MINE_OFFICE_PROMOTE_OK office_actors=%d floor_top=%.1fcm yard_top=%.1fcm light=(%.0flm,%.0fcm)" % (
    len(office), floor_top, yard_top, intensity, attenuation))
