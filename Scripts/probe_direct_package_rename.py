import unreal

PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_DirectProbe"
ALT = "/Game/ThirdPerson/Maps/ThirdPersonMap_DirectPackageProbe"
world = unreal.EditorLoadingAndSavingUtils.load_map(PATH)
asset = unreal.EditorAssetLibrary.load_asset(PATH)
package = asset.get_outermost()
unreal.log("PACKAGE_RENAME_BEFORE package=%s asset=%s" % (package.get_name(), asset.get_path_name()))
try:
    ok = package.rename("ThirdPersonMap_DirectPackageProbe")
    unreal.log("PACKAGE_RENAME_CALL ok=%s package=%s asset=%s" % (ok, package.get_name(), asset.get_path_name()))
    unreal.log("PACKAGE_RENAME_EXISTS_ALT=%s OLD=%s" % (
        unreal.EditorAssetLibrary.does_asset_exist(ALT), unreal.EditorAssetLibrary.does_asset_exist(PATH)))
    unreal.EditorLoadingAndSavingUtils.save_map(world, ALT)
    unreal.log("PACKAGE_RENAME_SAVED alt=%s old=%s" % (
        unreal.EditorAssetLibrary.does_asset_exist(ALT), unreal.EditorAssetLibrary.does_asset_exist(PATH)))
finally:
    # No automatic rollback: this probe package is disposable and will be left
    # for inspection if the package rename succeeds.
    pass
