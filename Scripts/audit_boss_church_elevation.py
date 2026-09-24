import unreal


MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"


def actor_map():
    return {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

actors = actor_map()
required = [
    "WB_E_BossArena_Floor",
    "WB_E_Church_Landmark",
    "WB_E_RaisedPlateau",
    "测试点_Boss场",
    "WB_C2_StreetFloor",
]
missing = [label for label in required if label not in actors]
if missing:
    raise RuntimeError("Missing elevation actors: " + ", ".join(missing))


def bounds_top(label):
    origin, extent = actors[label].get_actor_bounds(False)
    return origin.z + extent.z


def bounds_bottom(label):
    origin, extent = actors[label].get_actor_bounds(False)
    return origin.z - extent.z


def bounds_for_actor(actor):
    origin, extent = actor.get_actor_bounds(False)
    return (
        origin.x - extent.x,
        origin.x + extent.x,
        origin.y - extent.y,
        origin.y + extent.y,
        origin.z - extent.z,
        origin.z + extent.z,
    )


def instanced_cube_bounds(actor, transform):
    actor_location = actor.get_actor_location()
    location = transform.translation
    scale = transform.scale3d
    # /Engine/BasicShapes/Cube is a 100 cm cube, so each local half extent
    # is 50 cm before the per-instance scale is applied.
    half_x = abs(scale.x) * 50.0
    half_y = abs(scale.y) * 50.0
    half_z = abs(scale.z) * 50.0
    world_x = actor_location.x + location.x
    world_y = actor_location.y + location.y
    world_z = actor_location.z + location.z
    return (
        world_x - half_x,
        world_x + half_x,
        world_y - half_y,
        world_y + half_y,
        world_z - half_z,
        world_z + half_z,
    )


def bounds_for_instanced_cubes(actor, component):
    if component.get_instance_count() == 0:
        raise RuntimeError("Instanced component has no geometry: " + actor.get_actor_label())
    instance_bounds = [
        instanced_cube_bounds(actor, component.get_instance_transform(index, False))
        for index in range(component.get_instance_count())
    ]
    return (
        min(bounds[0] for bounds in instance_bounds),
        max(bounds[1] for bounds in instance_bounds),
        min(bounds[2] for bounds in instance_bounds),
        max(bounds[3] for bounds in instance_bounds),
        min(bounds[4] for bounds in instance_bounds),
        max(bounds[5] for bounds in instance_bounds),
    )


def overlaps_xy(first, second):
    return (
        first[0] < second[1]
        and first[1] > second[0]
        and first[2] < second[3]
        and first[3] > second[2]
    )


boss_top = bounds_top("WB_E_BossArena_Floor")
church_bottom = bounds_bottom("WB_E_Church_Landmark")
plateau_top = bounds_top("WB_E_RaisedPlateau")
c2_top = bounds_top("WB_C2_StreetFloor")
spawn_z = actors["测试点_Boss场"].get_actor_location().z

stair_actors = [
    actor for actor in actors.values()
    if actor.get_actor_label() == "WB_E_EntranceStairs"
    and "BossChurchElevation" in [str(tag) for tag in actor.tags]
]
if len(stair_actors) != 1:
    raise RuntimeError("Expected one combined stair actor, found %d" % len(stair_actors))
stairs = stair_actors[0]
stair_components = stairs.get_components_by_class(unreal.InstancedStaticMeshComponent)
if len(stair_components) != 1:
    raise RuntimeError("Expected one stair instanced mesh component, found %d" % len(stair_components))
stair_instances = stair_components[0].get_instance_count()
if stair_instances != 37:
    raise RuntimeError("Expected 37 stair instances, found %d" % stair_instances)

stair_bounds = bounds_for_instanced_cubes(stairs, stair_components[0])
first_bottom = stair_bounds[4]
last_top = stair_bounds[5]
if abs(boss_top - 1000.0) > 1.0:
    raise RuntimeError("Boss floor top is %.1f, expected 1000" % boss_top)
if abs(church_bottom - 1000.0) > 1.0:
    raise RuntimeError("Church bottom is %.1f, expected 1000" % church_bottom)
if abs(plateau_top - 1000.0) > 1.0:
    raise RuntimeError("Raised plateau top is %.1f, expected 1000" % plateau_top)
if abs(c2_top - 0.0) > 1.0:
    raise RuntimeError("C2 floor changed unexpectedly: %.1f" % c2_top)
if abs(spawn_z - 1100.0) > 1.0:
    raise RuntimeError("Boss spawn Z is %.1f, expected 1100" % spawn_z)
if abs(first_bottom - 0.0) > 1.0 or abs(last_top - 1000.0) > 1.0:
    raise RuntimeError("Stair run is not continuous: bottom=%.1f top=%.1f" % (first_bottom, last_top))

c2_bounds = bounds_for_actor(actors["WB_C2_StreetFloor"])
if overlaps_xy(stair_bounds, c2_bounds):
    raise RuntimeError("Combined stairs overlap the C2 street floor")

c2_overlaps = []
stair_instance_bounds = [
    instanced_cube_bounds(stairs, stair_components[0].get_instance_transform(index, False))
    for index in range(stair_instances)
]
for label, actor in actors.items():
    if not label.startswith("WB_C2_"):
        continue
    c2_actor_bounds = bounds_for_actor(actor)
    if any(overlaps_xy(bounds, c2_actor_bounds) for bounds in stair_instance_bounds):
        c2_overlaps.append(label)
if c2_overlaps:
    raise RuntimeError("Combined stairs overlap C2 whitebox actors: " + ", ".join(sorted(c2_overlaps)))

unexpected_stairs = [
    actor.get_actor_label()
    for actor in actors.values()
    if "BossChurchElevation" in [str(tag) for tag in actor.tags]
    and actor.get_actor_label().startswith("WB_E_EntranceStair_")
]
if unexpected_stairs:
    raise RuntimeError("Old independent stair actors remain: " + ", ".join(sorted(unexpected_stairs)))

unreal.log(
    "BOSS_CHURCH_ELEVATION_AUDIT_OK stair_actor=%s stair_instances=%d stair_bounds=(%.1f,%.1f,%.1f,%.1f,%.1f,%.1f) boss_top=%.1f church_bottom=%.1f plateau_top=%.1f c2_top=%.1f boss_spawn_z=%.1f"
    % (stairs.get_actor_label(), stair_instances, stair_bounds[0], stair_bounds[1], stair_bounds[2], stair_bounds[3], stair_bounds[4], stair_bounds[5], boss_top, church_bottom, plateau_top, c2_top, spawn_z)
)
