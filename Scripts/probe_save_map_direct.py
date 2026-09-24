import unreal


SOURCE = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"
DEST = "/Game/ThirdPerson/Maps/ThirdPersonMap_SaveMapDirectProbe"

world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
if not world:
    raise RuntimeError("Could not load source map")

# This deliberately does not load or rename the world asset. SaveMap writes the
# currently loaded world package directly to the destination package path.
if not unreal.EditorLoadingAndSavingUtils.save_map(world, DEST):
    raise RuntimeError("Could not save destination map")

unreal.EditorLoadingAndSavingUtils.load_map(DEST)
actors = unreal.EditorActorSubsystem().get_all_level_actors()
unreal.log("SAVE_MAP_DIRECT_DEST=%s" % DEST)
unreal.log("SAVE_MAP_DIRECT_ACTORS=%d" % len(actors))
