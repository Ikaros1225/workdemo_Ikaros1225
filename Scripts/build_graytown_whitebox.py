import unreal

TAG = "GraytownWhitebox"
MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
CUBE = "/Engine/BasicShapes/Cube.Cube"
CYLINDER = "/Engine/BasicShapes/Cylinder.Cylinder"
BASE_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"
MATERIALS = {}


def cm(value):
    return float(value)


def zone_material(color):
    key = tuple(color)
    if key not in MATERIALS:
        parent = unreal.load_asset(BASE_MATERIAL)
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        package_path = "/Game/WhiteboxMaterials"
        unreal.EditorAssetLibrary.make_directory(package_path)
        asset_name = "MI_Graytown_%d_%d_%d" % tuple(int(v * 255) for v in color)
        mat = unreal.EditorAssetLibrary.load_asset(package_path + "/" + asset_name)
        if not mat:
            factory = unreal.MaterialInstanceConstantFactoryNew()
            mat = asset_tools.create_asset(asset_name, package_path, unreal.MaterialInstanceConstant, factory)
            unreal.MaterialEditingLibrary.set_material_instance_parent(mat, parent)
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                mat, "Color", unreal.LinearColor(*color, 1.0)
            )
            unreal.MaterialEditingLibrary.update_material_instance(mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mat)
        MATERIALS[key] = mat
    return MATERIALS[key]


def spawn_box(label, x, y, z, sx, sy, sz, color=(0.42, 0.44, 0.45)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(cm(x), cm(y), cm(z)),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(label)
    actor.tags = [TAG, "Whitebox"]
    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh_component.set_static_mesh(unreal.load_asset(CUBE))
    mesh_component.set_material(0, zone_material(color))
    actor.set_actor_scale3d(unreal.Vector(cm(sx) / 100.0, cm(sy) / 100.0, cm(sz) / 100.0))
    return actor


def spawn_cylinder(label, x, y, z, radius, height, color=(0.42, 0.44, 0.45)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(cm(x), cm(y), cm(z)),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(label)
    actor.tags = [TAG, "Whitebox"]
    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh_component.set_static_mesh(unreal.load_asset(CYLINDER))
    mesh_component.set_material(0, zone_material(color))
    actor.set_actor_scale3d(unreal.Vector(cm(radius) / 50.0, cm(radius) / 50.0, cm(height) / 100.0))
    return actor


def delete_previous():
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if TAG in actor.tags:
            unreal.EditorLevelLibrary.destroy_actor(actor)


def set_label(actor, text):
    actor.set_actor_label(text)
    actor.tags = [TAG, "Whitebox"]


def spawn_label(label, text, x, y, z, color=(1.0, 1.0, 1.0)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(cm(x), cm(y), cm(z)),
        unreal.Rotator(0.0, 90.0, 0.0),
    )
    set_label(actor, label)
    component = actor.get_component_by_class(unreal.TextRenderComponent)
    component.set_editor_property("text", text)
    component.set_editor_property("world_size", 120.0)
    component.set_editor_property("text_render_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    return actor


def build():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError("Could not load " + MAP_PATH)

    delete_previous()

    # 150 x 150 m boundary; origin is the center, +Y is north.
    spawn_box("WB_BoundaryGround_150m", 0, 0, -20, 15000, 15000, 40, (0.18, 0.19, 0.20))

    # South entry / wasteland tutorial area.
    A = (0.56, 0.36, 0.18)
    spawn_box("WB_A_Wasteland_Backdrop", 0, -6200, 250, 9000, 3200, 500, A)
    spawn_box("WB_A_LeftRock", -3600, -6200, 400, 900, 1200, 800, A)
    spawn_box("WB_A_RightRock", 3300, -5850, 350, 1100, 900, 700, A)
    spawn_box("WB_A_Choke_WestWall", -4200, -4550, 650, 1800, 700, 1300, A)
    spawn_box("WB_A_Choke_EastWall", 4200, -4550, 650, 1800, 700, 1300, A)
    spawn_box("WB_A_MainApproach", 0, -4550, 100, 1500, 4500, 200, A)

    # West gas station platform (+2 m), kept as a readable whitebox mass.
    B = (0.16, 0.38, 0.42)
    spawn_box("WB_B_GasStation_Platform", -5000, -2500, 100, 3900, 3400, 200, B)
    spawn_box("WB_B_GasStation_Building", -5550, -2400, 350, 2000, 1200, 600, B)
    spawn_box("WB_B_GasStation_Canopy", -4300, -2350, 300, 1100, 1500, 140, B)
    spawn_box("WB_B_GasStation_CanopyPost_L", -4800, -2350, 220, 120, 120, 400, B)
    spawn_box("WB_B_GasStation_CanopyPost_R", -3800, -2350, 220, 120, 120, 400, B)
    for i, (x, y) in enumerate([(-4200, -2900), (-3900, -2900), (-4200, -3250)]):
        spawn_cylinder("WB_B_OilBarrel_%02d" % i, x, y, 120, 70, 120, (0.75, 0.32, 0.08))
    # Collapsed overpass: 30 m long, deck top at roughly 4 m for third-person sightlines.
    spawn_box("WB_B_Overpass_CollapsedDeck", -5000, -1000, 250, 3000, 400, 300, B)
    spawn_box("WB_B_Overpass_CollapsedRamp", -3400, -1600, 200, 500, 1000, 400, B)
    spawn_box("WB_B_Overpass_CollapsedEnd", -6500, -1000, 220, 800, 500, 440, B)

    # C1 lower street: 36 m long, 25 m combat street, simple building pockets.
    C1 = (0.30, 0.40, 0.45)
    spawn_box("WB_C1_StreetFloor", 0, -2350, 120, 4200, 3600, 200, C1)
    spawn_box("WB_C1_WestHouse_A", -1450, -2850, 350, 1100, 900, 600, C1)
    spawn_box("WB_C1_WestHouse_B", -1450, -1700, 300, 1100, 800, 500, C1)
    spawn_box("WB_C1_EastShop_A", 1450, -2850, 350, 1100, 850, 600, C1)
    spawn_box("WB_C1_EastShop_B", 1450, -1750, 350, 1100, 800, 600, C1)
    spawn_box("WB_C1_WestBackAlleyWall", -2550, -2350, 350, 300, 3600, 600, C1)
    spawn_box("WB_C1_EastBackAlleyWall", 2550, -2350, 350, 300, 3600, 600, C1)
    spawn_box("WB_C1_CoverCar", 0, -2550, 250, 900, 350, 300, C1)

    # East mine yard and cave entrance, the mandatory detour around the hard lock.
    D = (0.25, 0.30, 0.34)
    spawn_box("WB_D_MineYard", 5000, -2350, 120, 3900, 3400, 200, D)
    spawn_box("WB_D_MineOffice", 4450, -2850, 350, 1100, 850, 600, D)
    spawn_box("WB_D_MineCave_West", 6000, -1000, 550, 1200, 2500, 1000, D)
    spawn_box("WB_D_MineCave_East", 7450, -1000, 550, 900, 2500, 1000, D)
    spawn_box("WB_D_CaveRoof", 6750, -1000, 1200, 3000, 2500, 250, D)
    spawn_box("WB_D_MineShaft_Elevator", 5850, -3000, 450, 500, 500, 800, D)
    spawn_box("WB_D_TransportTunnelFloor", 2500, -3450, -2800, 6500, 500, 200, D)
    spawn_box("WB_D_TransportTunnelRoof", 2500, -3450, -1700, 6500, 500, 200, D)
    spawn_box("WB_D_TransportTunnelWestWall", 2500, -3750, -2250, 6500, 200, 1100, D)
    spawn_box("WB_D_TransportTunnelEastWall", 2500, -3150, -2250, 6500, 200, 1100, D)
    spawn_box("WB_D_TransportTunnelMouth", 180, -3450, -2250, 800, 500, 1100, D)

    # Collapsed-building division band and central fog hard lock.
    LOCK = (0.42, 0.16, 0.48)
    # Low collapsed-building band: marks the district edge without becoming a sightline wall.
    spawn_box("WB_Lock_DivisionBand_West", -3900, 0, 150, 4200, 700, 300, LOCK)
    spawn_box("WB_Lock_DivisionBand_East", 3900, 0, 150, 4200, 700, 300, LOCK)
    # The hard lock is a low debris mound, readable as blocked but kept below camera eye line.
    spawn_box("WB_Lock_FogGate_LowDebris", 0, 0, 80, 1500, 500, 160, LOCK)
    spawn_box("WB_Lock_FogGate_LeftDebris", -900, 0, 60, 250, 700, 120, LOCK)
    spawn_box("WB_Lock_FogGate_RightDebris", 900, 0, 60, 250, 700, 120, LOCK)

    spawn_label("WB_Label_Spawn", "荒原教学区", 0, -6100, 900, (1.0, 0.75, 0.30))
    spawn_label("WB_Label_GasStation", "加油站", -5000, -2500, 900, (0.35, 0.90, 0.95))
    spawn_label("WB_Label_C1", "C1 中下街区", 0, -2350, 900, (0.55, 0.85, 0.95))
    spawn_label("WB_Label_Mine", "旧矿井", 5000, -2350, 900, (0.60, 0.85, 0.80))
    spawn_label("WB_Label_HardLock", "蚀雾封锁·硬锁", 0, 0, 2200, (1.0, 0.35, 0.85))
    spawn_label("WB_Label_Direction", "主线：南→北    支路：向东绕行", 0, -4300, 1600, (1.0, 0.85, 0.25))

    player_start = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(0.0, -6900.0, 120.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    set_label(player_start, "WB_PlayerStart_SouthWasteland")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.log("Graytown whitebox built: scene geometry only, no enemies")


build()
