import unreal

PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"
ALT = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_DirectProbe"
world = unreal.EditorLoadingAndSavingUtils.load_map(PATH)
if not world:
    raise RuntimeError("load failed")
asset = unreal.EditorAssetLibrary.load_asset(PATH)
unreal.log("DIRECT_RENAME_BEFORE asset=%s outer=%s path=%s" % (
    asset, asset.get_outermost().get_name(), asset.get_path_name()))
package = asset.get_outermost()
try:
    ok = asset.rename("ThirdPersonMap_MineOffice_DirectProbe")
    unreal.log("DIRECT_RENAME_CALL ok=%s asset=%s outer=%s path=%s package=%s" % (
        ok, asset, asset.get_outermost().get_name(), asset.get_path_name(), package.get_name()))
    unreal.log("DIRECT_RENAME_EXISTS_ALT=%s OLD=%s" % (
        unreal.EditorAssetLibrary.does_asset_exist(ALT), unreal.EditorAssetLibrary.does_asset_exist(PATH)))
    if ok:
        unreal.EditorLoadingAndSavingUtils.save_map(asset, ALT)
        unreal.log("DIRECT_RENAME_SAVED alt_exists=%s" % unreal.EditorAssetLibrary.does_asset_exist(ALT))
finally:
    # Leave the temporary map under its original path for subsequent tests.
    current = unreal.EditorAssetLibrary.load_asset(ALT)
    if current:
        current.rename("ThirdPersonMap_MineOffice_Updated_20260924_1535")
        unreal.EditorLoadingAndSavingUtils.save_map(current, PATH)
        unreal.log("DIRECT_RENAME_ROLLBACK path=%s" % current.get_path_name())
