import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1523"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

for actor in sorted(unreal.EditorLevelLibrary.get_all_level_actors(), key=lambda a: a.get_actor_label()):
    label = actor.get_actor_label()
    if not label.startswith("WB_D_MineOffice"):
        continue
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    origin, extent = actor.get_actor_bounds(False)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = comp.get_editor_property("static_mesh").get_path_name() if comp and comp.get_editor_property("static_mesh") else ""
    unreal.log("MINE_PROBE label=%s class=%s loc=(%.1f,%.1f,%.1f) rot=(%.1f,%.1f,%.1f) scale=(%.3f,%.3f,%.3f) bounds_origin=(%.1f,%.1f,%.1f) bounds_extent=(%.1f,%.1f,%.1f) mesh=%s" % (
        label, actor.get_class().get_name(), loc.x, loc.y, loc.z,
        rot.pitch, rot.yaw, rot.roll,
        scale.x, scale.y, scale.z, origin.x, origin.y, origin.z,
        extent.x, extent.y, extent.z, mesh))
