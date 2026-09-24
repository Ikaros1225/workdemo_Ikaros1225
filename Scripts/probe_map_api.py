import unreal

unreal.log("MAP_API_METHODS=%s" % [x for x in dir(unreal.EditorLoadingAndSavingUtils) if "map" in x.lower() or "world" in x.lower()])
for name in ("new_blank_map", "new_map", "load_map"):
    fn = getattr(unreal.EditorLoadingAndSavingUtils, name, None)
    unreal.log("MAP_API_%s=%s" % (name, fn))
