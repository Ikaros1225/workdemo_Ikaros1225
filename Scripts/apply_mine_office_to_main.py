import unreal


SOURCE = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"
DEST = "/Game/ThirdPerson/Maps/ThirdPersonMap"

world = unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
if not world:
    raise RuntimeError("Could not load source map: " + SOURCE)

# Save the loaded world directly into the existing map package. This intentionally
# avoids all asset rename APIs and therefore cannot trigger reference-replacement.
if not unreal.EditorLoadingAndSavingUtils.save_map(world, DEST):
    raise RuntimeError("Could not save main map: " + DEST)

unreal.EditorLoadingAndSavingUtils.load_map(DEST)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
unreal.log("MINE_OFFICE_MAIN_SAVE_OK source=%s dest=%s actors=%d" % (SOURCE, DEST, len(actors)))
