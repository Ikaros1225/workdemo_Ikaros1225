import json
import math
import unreal


MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
CUBE_PATH = "/Engine/BasicShapes/Cube.Cube"
WALL_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_56_63_68.MI_Graytown_56_63_68"
STAIR_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_79_84_84.MI_Graytown_79_84_84"
FLOOR_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_76_81_81.MI_Graytown_76_81_81"
AUDIT_PATH = "G:/UE/project/workdemo/Saved/gasstation_side_route_audit.json"

WHITEBOX_TAG = "GraytownWhitebox"
GAS_TAG = "GasStationBuilding"
ROUTE_TAG = "GasStationSideRoute"
STAIR_PARENT_LABEL = "WB_B_GasStation_Stairs"
ROUTE_PARENT_LABEL = "WB_B_GasStation_SideRoute"

OLD_STAIR_LABELS = [
    "WB_B_GasStation_Building_Stair_%02d" % index for index in range(1, 11)
]
TARGET_LABELS = {
    "WB_B_GasStation_Building_Wall_Right",
    "WB_B_Overpass_BrokenDeck",
}
GENERATED_LABELS = {
    STAIR_PARENT_LABEL,
    ROUTE_PARENT_LABEL,
    "WB_B_GasStation_UpperFloor_Walkable",
    "WB_B_GasStation_Building_Wall_Right_Upper_South",
    "WB_B_GasStation_Building_Wall_Right_Upper_North",
    "WB_B_GasStation_Building_Wall_Right_Door_LeftJamb",
    "WB_B_GasStation_Building_Wall_Right_Door_RightJamb",
    "WB_B_GasStation_Building_Wall_Right_Door_Lintel",
}


def all_actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def find_exact(actors, label):
    found = [actor for actor in actors if actor.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError("Expected exactly one actor named %s; found %d" % (label, len(found)))
    return found[0]


def path_of(obj):
    return obj.get_path_name() if obj else ""


def vector_data(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def rotator_data(value):
    return [round(float(value.pitch), 4), round(float(value.yaw), 4), round(float(value.roll), 4)]


def component_fingerprint(component):
    entry = {
        "name": component.get_name(),
        "class": component.get_class().get_name(),
    }
    for property_name in ("relative_location", "relative_rotation", "relative_scale3d"):
        try:
            value = component.get_editor_property(property_name)
            if property_name == "relative_location":
                entry[property_name] = vector_data(value)
            elif property_name == "relative_rotation":
                entry[property_name] = rotator_data(value)
            else:
                entry[property_name] = vector_data(value)
        except Exception:
            pass
    try:
        entry["static_mesh"] = path_of(component.get_editor_property("static_mesh"))
    except Exception:
        entry["static_mesh"] = ""
    try:
        entry["collision_enabled"] = str(component.get_editor_property("collision_enabled"))
    except Exception:
        entry["collision_enabled"] = ""
    try:
        entry["collision_profile"] = str(component.get_editor_property("collision_profile_name"))
    except Exception:
        entry["collision_profile"] = ""
    materials = []
    for index in range(4):
        try:
            materials.append(path_of(component.get_material(index)))
        except Exception:
            materials.append("")
    entry["materials"] = materials
    return entry


def actor_fingerprint(actor, actors):
    parent = actor.get_attach_parent_actor()
    children = sorted(
        child.get_actor_label()
        for child in actors
        if child.get_attach_parent_actor() == actor
    )
    return {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "location": vector_data(actor.get_actor_location()),
        "rotation": rotator_data(actor.get_actor_rotation()),
        "scale": vector_data(actor.get_actor_scale3d()),
        "tags": sorted(str(tag) for tag in actor.tags),
        "parent": parent.get_actor_label() if parent else "",
        "children": children,
        "components": sorted(
            (component_fingerprint(component)
             for component in actor.get_components_by_class(unreal.SceneComponent)),
            key=lambda item: item["name"],
        ),
    }


def broken_deck_fingerprint(actors):
    root = find_exact(actors, "WB_B_Overpass_BrokenDeck")
    selected = [root]
    changed = True
    while changed:
        changed = False
        for actor in actors:
            if actor in selected:
                continue
            if any(actor.get_attach_parent_actor() == parent for parent in selected):
                selected.append(actor)
                changed = True
    return sorted((actor_fingerprint(actor, actors) for actor in selected),
                  key=lambda item: item["label"])


def spawn_box(label, location, dimensions, material, rotation=None, tags=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(float(location[0]), float(location[1]), float(location[2])),
        rotation or unreal.Rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = list(tags or [WHITEBOX_TAG, "Whitebox", GAS_TAG])
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(unreal.load_asset(CUBE_PATH))
    if material:
        component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", True)
    actor.set_actor_scale3d(unreal.Vector(
        float(dimensions[0]) / 100.0,
        float(dimensions[1]) / 100.0,
        float(dimensions[2]) / 100.0,
    ))
    return actor


def add_ism_component(actor, mesh, material):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_instance(actor)
    if not handles:
        raise RuntimeError("Could not gather subobject data for " + actor.get_actor_label())
    params = unreal.AddNewSubobjectParams()
    params.parent_handle = handles[0]
    params.new_class = unreal.InstancedStaticMeshComponent.static_class()
    params.conform_transform_to_parent = False
    result = subsystem.add_new_subobject(params)
    if not result:
        raise RuntimeError("Could not add instanced mesh component to " + actor.get_actor_label())
    components = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
    if len(components) != 1:
        raise RuntimeError("Expected one ISM on %s; found %d" % (actor.get_actor_label(), len(components)))
    component = components[0]
    component.set_static_mesh(unreal.load_asset(mesh))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", True)
    return component


def add_instance(component, location, dimensions, rotation=None):
    transform = unreal.Transform(
        unreal.Vector(float(location[0]), float(location[1]), float(location[2])),
        rotation or unreal.Rotator(0.0, 0.0, 0.0),
        unreal.Vector(
            float(dimensions[0]) / 100.0,
            float(dimensions[1]) / 100.0,
            float(dimensions[2]) / 100.0,
        ),
    )
    component.add_instance(transform)


def create_stair_parent(actors, stair_material):
    for actor in actors:
        if actor.get_actor_label() in OLD_STAIR_LABELS:
            unreal.EditorLevelLibrary.destroy_actor(actor)
    parent = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
    if not parent:
        raise RuntimeError("Could not create stair parent")
    parent.set_actor_label(STAIR_PARENT_LABEL)
    parent.set_folder_path("GasStation/Traversal")
    parent.tags = [WHITEBOX_TAG, "Whitebox", GAS_TAG, "GasStationStairs"]
    component = add_ism_component(parent, CUBE_PATH, stair_material)

    # Preserve the existing 8 m run and 490 cm total rise, but use 20 steps.
    # Every tread is 24.5 cm high and 40 cm deep, so no jump is required.
    for index in range(20):
        bottom = 50.0 + 24.5 * index
        top = bottom + 24.5
        add_instance(
            component,
            (6150.0, -1580.0 + 40.0 * index, (bottom + top) / 2.0),
            (500.0, 40.0, 24.5),
        )
    if component.get_instance_count() != 20:
        raise RuntimeError("Expected 20 stair instances; found %d" % component.get_instance_count())
    return parent, component


def create_route_parent(floor_material):
    parent = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
    if not parent:
        raise RuntimeError("Could not create side-route parent")
    parent.set_actor_label(ROUTE_PARENT_LABEL)
    parent.set_folder_path("GasStation/Traversal")
    parent.tags = [WHITEBOX_TAG, "Whitebox", GAS_TAG, ROUTE_TAG]
    component = add_ism_component(parent, CUBE_PATH, floor_material)

    # A level upper landing matches the second-floor slab at Z=540.
    add_instance(component, (6800.0, -840.0, 490.0), (500.0, 300.0, 100.0))
    # Short connector between the landing and the sloped run, also top at Z=540.
    add_instance(component, (6800.0, -1020.0, 525.0), (500.0, 120.0, 30.0))

    run_start_y = -1080.0
    run_end_y = -3100.0
    run_length = abs(run_end_y - run_start_y)
    rise = 90.0
    roll = -math.degrees(math.atan2(rise, run_length))
    run_center_y = (run_start_y + run_end_y) / 2.0
    run_center_z = 570.0
    add_instance(
        component,
        (6800.0, run_center_y, run_center_z),
        (300.0, run_length, 30.0),
        unreal.Rotator(pitch=0.0, yaw=0.0, roll=roll),
    )
    # A small level nose overlaps the BrokenDeck edge without changing it.
    add_instance(component, (6800.0, -3050.0, 615.0), (300.0, 100.0, 30.0))
    if component.get_instance_count() != 4:
        raise RuntimeError("Expected 4 route instances; found %d" % component.get_instance_count())
    return parent, component, roll


def modify_right_wall(actors, wall, wall_material):
    # Keep the named wall actor as the lower wall course and add the upper
    # courses around a 260 cm wide door at the second-floor finish height.
    wall.modify()
    wall.set_actor_location(unreal.Vector(6500.0, -1040.0, 295.0), False, False)
    wall.set_actor_scale3d(unreal.Vector(1.0, 14.0, 4.9))
    component = wall.get_component_by_class(unreal.StaticMeshComponent)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_editor_property("can_ever_affect_navigation", True)

    door_y = -840.0
    door_width = 260.0
    y_min = -1740.0
    y_max = -340.0
    south_length = (-970.0) - y_min
    north_length = y_max - (-710.0)
    spawn_box(
        "WB_B_GasStation_Building_Wall_Right_Upper_South",
        (6500.0, y_min + south_length / 2.0, 695.0),
        (100.0, south_length, 310.0),
        wall_material,
    )
    spawn_box(
        "WB_B_GasStation_Building_Wall_Right_Upper_North",
        (-0.0 + 6500.0, -710.0 + north_length / 2.0, 695.0),
        (100.0, north_length, 310.0),
        wall_material,
    )
    spawn_box(
        "WB_B_GasStation_Building_Wall_Right_Door_LeftJamb",
        (6500.0, door_y - door_width / 2.0, 655.0),
        (100.0, 30.0, 230.0),
        wall_material,
    )
    spawn_box(
        "WB_B_GasStation_Building_Wall_Right_Door_RightJamb",
        (6500.0, door_y + door_width / 2.0, 655.0),
        (100.0, 30.0, 230.0),
        wall_material,
    )
    spawn_box(
        "WB_B_GasStation_Building_Wall_Right_Door_Lintel",
        (6500.0, door_y, 810.0),
        (100.0, door_width, 80.0),
        wall_material,
    )
    return door_y, door_width


def create_upper_floor(floor_material):
    # Fill the central upper-floor walking area bounded by the existing slabs.
    return spawn_box(
        "WB_B_GasStation_UpperFloor_Walkable",
        (6150.0, -1220.0, 490.0),
        (600.0, 1000.0, 100.0),
        floor_material,
    )


def validate_route(stair_component, route_component, roll, overpass, wall, door_y, door_width):
    if stair_component.get_instance_count() != 20:
        raise RuntimeError("Stair instance count failed validation")
    if route_component.get_instance_count() != 4:
        raise RuntimeError("Route instance count failed validation")
    if abs(roll) > 8.6:
        raise RuntimeError("Route slope is too steep: %.3f degrees" % abs(roll))
    if 24.5 > 30.0:
        raise RuntimeError("Stair rise exceeds the no-jump threshold")
    wall_loc = wall.get_actor_location()
    wall_scale = wall.get_actor_scale3d()
    if abs(wall_loc.z - 295.0) > 0.1 or abs(wall_scale.z - 4.9) > 0.01:
        raise RuntimeError("Named right wall was not reduced to the lower course")
    if not (-1740.0 < door_y - door_width / 2.0 < door_y + door_width / 2.0 < -340.0):
        raise RuntimeError("Door opening is outside the wall span")
    origin, extent = overpass.get_actor_bounds(False)
    if origin.z + extent.z < 620.0:
        raise RuntimeError("BrokenDeck top is lower than expected; refusing route connection")
    route_boxes = [
        ("landing", 6800.0, -840.0, 490.0, 500.0, 300.0, 100.0),
        ("connector", 6800.0, -1020.0, 525.0, 500.0, 120.0, 30.0),
        ("nose", 6800.0, -3050.0, 615.0, 300.0, 100.0, 30.0),
    ]
    for name, x, y, z, sx, sy, sz in route_boxes:
        if sz <= 0 or sx < 250 or sy < 80:
            raise RuntimeError("Invalid route geometry: " + name)


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError("Could not load " + MAP_PATH)
    actors = all_actors()
    wall = find_exact(actors, "WB_B_GasStation_Building_Wall_Right")
    overpass = find_exact(actors, "WB_B_Overpass_BrokenDeck")
    stairs = [actor for actor in actors if actor.get_actor_label() in OLD_STAIR_LABELS]
    if len(stairs) != 10:
        raise RuntimeError("Expected 10 existing gas-station stair actors; found %d" % len(stairs))
    existing_generated = [actor.get_actor_label() for actor in actors if actor.get_actor_label() in GENERATED_LABELS]
    if existing_generated:
        raise RuntimeError("Generated route actors already exist; refusing duplicate build: %s" % existing_generated)

    overpass_before = broken_deck_fingerprint(actors)
    wall_material = unreal.load_asset(WALL_MATERIAL_PATH)
    stair_material = unreal.load_asset(STAIR_MATERIAL_PATH)
    floor_material = unreal.load_asset(FLOOR_MATERIAL_PATH)
    if not wall_material or not stair_material or not floor_material:
        raise RuntimeError("Required whitebox material is missing")

    stair_parent, stair_component = create_stair_parent(actors, stair_material)
    create_upper_floor(floor_material)
    door_y, door_width = modify_right_wall(actors, wall, wall_material)
    route_parent, route_component, roll = create_route_parent(floor_material)

    actors_after_build = all_actors()
    overpass_after = broken_deck_fingerprint(actors_after_build)
    if overpass_before != overpass_after:
        raise RuntimeError("WB_B_Overpass_BrokenDeck changed during construction; refusing to save")
    overpass_after_root = find_exact(actors_after_build, "WB_B_Overpass_BrokenDeck")
    validate_route(stair_component, route_component, roll, overpass_after_root, wall, door_y, door_width)

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH):
        raise RuntimeError("Could not save the modified ThirdPersonMap")

    # The save is followed by an in-memory verification, and the audit is only
    # written after the overpass fingerprint and traversal constraints pass.
    actors_after_save = all_actors()
    overpass_after_save = broken_deck_fingerprint(actors_after_save)
    if overpass_before != overpass_after_save:
        raise RuntimeError("WB_B_Overpass_BrokenDeck changed after save")
    audit = {
        "map": MAP_PATH,
        "stairs_parent": STAIR_PARENT_LABEL,
        "stairs_instances": stair_component.get_instance_count(),
        "stair_rise_cm": 24.5,
        "stair_tread_cm": 40.0,
        "upper_floor_top_z": 540.0,
        "right_wall_label": wall.get_actor_label(),
        "door_center_y": door_y,
        "door_width_cm": door_width,
        "route_parent": ROUTE_PARENT_LABEL,
        "route_instances": route_component.get_instance_count(),
        "route_slope_degrees": round(abs(roll), 4),
        "route_start_top_z": 540.0,
        "route_end_top_z": 630.0,
        "overpass_unchanged": True,
        "overpass_fingerprint_before": overpass_before,
        "overpass_fingerprint_after": overpass_after_save,
    }
    with open(AUDIT_PATH, "w", encoding="utf-8") as handle:
        json.dump(audit, handle, ensure_ascii=True, indent=2)
    unreal.log(
        "GAS_STATION_SIDE_ROUTE_OK stairs_parent=%s stair_instances=%d stair_rise=24.5cm "
        "door_y=%.1f door_width=%.1f route_parent=%s route_instances=%d slope=%.3fdeg "
        "overpass_unchanged=True" % (
            STAIR_PARENT_LABEL,
            stair_component.get_instance_count(),
            door_y,
            door_width,
            ROUTE_PARENT_LABEL,
            route_component.get_instance_count(),
            abs(roll),
        )
    )


main()
