import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

def label(actor):
    return actor.get_actor_label()

def summary(actor):
    loc = actor.get_actor_location()
    rot = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    origin, extent = actor.get_actor_bounds(False)
    parent = actor.get_attach_parent_actor()
    unreal.log(
        "ROUTE_AUDIT actor=%s class=%s loc=(%.1f,%.1f,%.1f) rot=(%.1f,%.1f,%.1f) "
        "scale=(%.3f,%.3f,%.3f) bounds_origin=(%.1f,%.1f,%.1f) "
        "bounds_extent=(%.1f,%.1f,%.1f) parent=%s tags=%s" % (
            label(actor), actor.get_class().get_name(),
            loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll,
            scale.x, scale.y, scale.z, origin.x, origin.y, origin.z,
            extent.x, extent.y, extent.z,
            label(parent) if parent else "", [str(tag) for tag in actor.tags]))
    for component in actor.get_components_by_class(unreal.PrimitiveComponent):
        mesh = ""
        try:
            mesh_obj = component.get_editor_property("static_mesh")
            mesh = mesh_obj.get_path_name() if mesh_obj else ""
        except Exception:
            pass
        try:
            collision = str(component.get_editor_property("collision_enabled"))
        except Exception:
            collision = "?"
        try:
            profile = str(component.get_editor_property("collision_profile_name"))
        except Exception:
            profile = "?"
        relative = component.get_editor_property("relative_location")
        component_scale = component.get_editor_property("relative_scale3d")
        unreal.log(
            "ROUTE_COMPONENT actor=%s name=%s type=%s mesh=%s rel=(%.1f,%.1f,%.1f) "
            "scale=(%.3f,%.3f,%.3f) collision=%s profile=%s" % (
                label(actor), component.get_name(), component.get_class().get_name(), mesh,
                relative.x, relative.y, relative.z,
                component_scale.x, component_scale.y, component_scale.z,
                collision, profile))

actors = unreal.EditorLevelLibrary.get_all_level_actors()
anchor = unreal.Vector(6500.0, -1040.0, 450.0)
unreal.log("ROUTE_AUDIT_BEGIN map=%s actors=%d" % (MAP_PATH, len(actors)))
targets = []
for actor in actors:
    name = label(actor)
    origin, extent = actor.get_actor_bounds(False)
    near_wall = max(abs(origin.x - anchor.x) - extent.x,
                    abs(origin.y - anchor.y) - extent.y) <= 1700.0
    if name.startswith("WB_B_GasStation") or "Overpass" in name or near_wall:
        targets.append(actor)
for actor in sorted(targets, key=label):
    summary(actor)
unreal.log("ROUTE_AUDIT_END selected=%d" % len(targets))
