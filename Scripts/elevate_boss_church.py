import unreal


MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
ELEVATION = 1000.0
ELEVATION_TAG = "BossChurchElevation"
WHITEBOX_TAG = "GraytownWhitebox"
WHITEBOX_MATERIAL = "/Game/WhiteboxMaterials/MI_Graytown_71_30_107.MI_Graytown_71_30_107"
CUBE = "/Engine/BasicShapes/Cube.Cube"
BASE_Z = {
    "WB_E_BossArena_Floor": -100.0,
    "WB_E_Church_Door_LeftJamb": 130.0,
    "WB_E_Church_Door_Lintel": 260.0,
    "WB_E_Church_Door_Panel": 130.0,
    "WB_E_Church_Door_RightJamb": 130.0,
    "WB_E_Church_Landmark": 750.0,
    "WB_E_OilPuddle_L": 35.0,
    "WB_E_OilPuddle_R": 35.0,
    "WB_E_ResidualColumn_00": 220.0,
    "WB_E_ResidualColumn_01": 220.0,
    "WB_E_ResidualColumn_02": 220.0,
    "WB_E_ResidualColumn_03": 220.0,
    "WB_Label_Boss": 3000.0,
    "WB_Label_Church": 1500.0,
    "测试点_Boss场": 100.0,
}


def actor_tags(actor):
    return [str(tag) for tag in actor.tags]


def has_tag(actor, tag):
    return tag in actor_tags(actor)


def set_elevated_z(actor, base_z):
    location = actor.get_actor_location()
    actor.modify()
    target_z = base_z + ELEVATION
    actor.set_actor_location(
        unreal.Vector(location.x, location.y, target_z),
        False,
        False,
    )
    return target_z


def add_ism_component(actor):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_instance(actor)
    if not handles:
        raise RuntimeError("Could not gather subobject data for stair actor")

    params = unreal.AddNewSubobjectParams()
    params.parent_handle = handles[0]
    params.new_class = unreal.InstancedStaticMeshComponent.static_class()
    params.conform_transform_to_parent = False
    result = subsystem.add_new_subobject(params)
    if not result:
        raise RuntimeError("Could not add instanced mesh component to stair actor")

    components = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
    if len(components) != 1:
        raise RuntimeError("Expected one stair instanced mesh component, found %d" % len(components))
    return components[0]


def add_box_instance(component, x, y, z, sx, sy, sz):
    transform = unreal.Transform(
        unreal.Vector(x, y, z),
        unreal.Rotator(0.0, 0.0, 0.0),
        unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0),
    )
    component.add_instance(transform)


def spawn_stair_actor(material):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    if not actor:
        raise RuntimeError("Could not spawn stair actor")
    actor.set_actor_label("WB_E_EntranceStairs")
    actor.tags = [WHITEBOX_TAG, "Whitebox", ELEVATION_TAG]

    component = add_ism_component(actor)
    component.set_static_mesh(unreal.load_asset(CUBE))
    if material:
        component.set_material(0, material)

    # Compact L-shaped run: the lower leg clears the entire C2 blockout,
    # then a landing turns north before the final leg meets the raised plateau.
    lower_steps = 16
    lower_x = 4200.0
    lower_first_y = 2725.0
    lower_tread = 50.0
    lower_width = 1200.0
    lower_rise = 500.0 / lower_steps
    for index in range(lower_steps):
        top = lower_rise * (index + 1)
        add_box_instance(
            component,
            lower_x,
            lower_first_y + lower_tread * index,
            top / 2.0,
            lower_width,
            lower_tread,
            top,
        )

    # A broad, level turn keeps the two runs visually connected and gives the
    # player a readable pause before the ceremonial approach to the arena.
    add_box_instance(component, 4200.0, 3975.0, 250.0, 1200.0, 950.0, 500.0)

    upper_steps = 20
    upper_first_x = 4170.0
    upper_tread = 60.0
    upper_y = 4000.0
    upper_width = 900.0
    upper_rise = 500.0 / upper_steps
    for index in range(upper_steps):
        top = 500.0 + upper_rise * (index + 1)
        add_box_instance(
            component,
            upper_first_x - upper_tread * index,
            upper_y,
            top / 2.0,
            upper_tread,
            upper_width,
            top,
        )

    expected_instances = lower_steps + 1 + upper_steps
    if component.get_instance_count() != expected_instances:
        raise RuntimeError(
            "Stair instance count mismatch: expected %d, found %d"
            % (expected_instances, component.get_instance_count())
        )
    return actor, component


def delete_previous_stairs(actors):
    for actor in actors:
        label = actor.get_actor_label()
        generated_label = (
            label == "WB_E_RaisedPlateau"
            or label == "WB_E_EntranceStairs"
            or label.startswith("WB_E_EntranceStair_")
        )
        if has_tag(actor, ELEVATION_TAG) and generated_label:
            unreal.EditorLevelLibrary.destroy_actor(actor)


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError("Could not load " + MAP_PATH)

    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    delete_previous_stairs(actors)

    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    targets = {actor.get_actor_label(): actor for actor in actors if actor.get_actor_label() in BASE_Z}
    missing = sorted(set(BASE_Z) - set(targets))
    if missing:
        raise RuntimeError("Missing Boss/Church actors; refusing to save: " + ", ".join(missing))

    moved_labels = []
    for label, actor in targets.items():
        target_z = set_elevated_z(actor, BASE_Z[label])
        moved_labels.append((label, target_z))
        if abs(actor.get_actor_location().z - target_z) > 1.0:
            raise RuntimeError("Actor did not reach elevated Z: " + label)

    if not any(label == "WB_E_BossArena_Floor" for label, _ in moved_labels):
        raise RuntimeError("Boss arena floor was not found; refusing to save")
    if not any(label == "测试点_Boss场" for label, _ in moved_labels):
        raise RuntimeError("Boss test spawn was not found; refusing to save")

    material = unreal.load_asset(WHITEBOX_MATERIAL)
    plateau = spawn_stair_actor(material)[0]
    plateau.set_actor_label("WB_E_RaisedPlateau")
    plateau_component = plateau.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    # The plateau is kept as a separate, simple blockout actor so the stair
    # assembly can be moved or adjusted without changing the arena geometry.
    plateau_component.clear_instances()
    add_box_instance(plateau_component, 0.0, 6650.0, 900.0, 6000.0, 7200.0, 200.0)

    stairs, stair_component = spawn_stair_actor(material)
    if stairs.get_actor_label() != "WB_E_EntranceStairs":
        raise RuntimeError("Stair actor label was not applied")
    if stair_component.get_instance_count() != 37:
        raise RuntimeError("Expected 37 stair instances")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(
        "Boss/Church elevation applied: moved=%d elevation=%.1fcm stairs=%d"
        % (len(moved_labels), ELEVATION, stair_component.get_instance_count())
    )


main()
