import unreal

SOURCE = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"
DEST = "/Game/ThirdPerson/Maps/ThirdPersonMap_SaveAsNoAssetRenameProbe"
world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
if not world:
    raise RuntimeError("Could not load source map")
asset = unreal.EditorAssetLibrary.load_asset(SOURCE)
if not asset:
    raise RuntimeError("Could not load source world")
if not asset.rename("ThirdPersonMap_SaveAsNoAssetRenameProbe"):
    raise RuntimeError("Could not rename world object in memory")
unreal.log("SAVE_AS_PROBE_WORLD=%s" % asset.get_path_name())
if not unreal.EditorLoadingAndSavingUtils.save_map(world, DEST):
    raise RuntimeError("Could not save destination map")
unreal.EditorLoadingAndSavingUtils.load_map(DEST)
dest = unreal.EditorAssetLibrary.load_asset(DEST)
unreal.log("SAVE_AS_PROBE_DEST=%s" % dest.get_path_name())
unreal.log("SAVE_AS_PROBE_ACTORS=%d" % len(unreal.EditorLevelLibrary.get_all_level_actors()))
