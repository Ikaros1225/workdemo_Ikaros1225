import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

prefixes = ("WB_B_GasStation", "WB_D_MineOffice", "MineOffice", "GasStation")
for actor in sorted(unreal.EditorLevelLibrary.get_all_level_actors(), key=lambda a: a.get_actor_label()):
    label = actor.get_actor_label()
    if not any(label.startswith(prefix) for prefix in prefixes):
        continue
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    origin, extent = actor.get_actor_bounds(False)
    mesh = ""
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        mesh_obj = comp.get_editor_property("static_mesh")
        mesh = mesh_obj.get_path_name() if mesh_obj else ""
    unreal.log("BUILDING_STATE label=%s class=%s loc=(%.1f,%.1f,%.1f) rot=(%.1f,%.1f,%.1f) scale=(%.3f,%.3f,%.3f) bounds_origin=(%.1f,%.1f,%.1f) bounds_extent=(%.1f,%.1f,%.1f) mesh=%s tags=%s" % (
        label,
        actor.get_class().get_name(),
        loc.x, loc.y, loc.z,
        rot.pitch, rot.yaw, rot.roll,
        scale.x, scale.y, scale.z,
        origin.x, origin.y, origin.z,
        extent.x, extent.y, extent.z,
        mesh,
        [str(tag) for tag in actor.tags],
    ))
