import unreal

TAG = "GraytownWhitebox"
MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
CUBE = "/Engine/BasicShapes/Cube.Cube"
CYLINDER = "/Engine/BasicShapes/Cylinder.Cylinder"
BASE_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"
MATERIALS = {}


def layout_x(label, x):
    # The current UE viewport shows B/D opposite to the layout's left/right.
    # Mirror only those two side regions; central zones and the player start stay put.
    if (label.startswith("WB_B_") or label.startswith("WB_D_") or
            label == "WB_C1_D_Connection" or label in ("WB_Label_GasStation", "WB_Label_Mine")):
        return -float(x)
    return float(x)


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
        unreal.Vector(cm(layout_x(label, x)), cm(y), cm(z)),
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
        unreal.Vector(cm(layout_x(label, x)), cm(y), cm(z)),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(label)
    actor.tags = [TAG, "Whitebox"]
    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh_component.set_static_mesh(unreal.load_asset(CYLINDER))
    mesh_component.set_material(0, zone_material(color))
    actor.set_actor_scale3d(unreal.Vector(cm(radius) / 50.0, cm(radius) / 50.0, cm(height) / 100.0))
    return actor


def spawn_door(label, x, y, z, width, height, orientation="x", color=(0.10, 0.12, 0.13)):
    """A readable whitebox doorway: two jambs, a lintel, and a recessed dark panel."""
    depth = 80
    jamb = 70
    sill = 15
    if orientation == "x":
        spawn_box(label + "_LeftJamb", x - width / 2.0, y, z + height / 2.0, jamb, depth, height, color)
        spawn_box(label + "_RightJamb", x + width / 2.0, y, z + height / 2.0, jamb, depth, height, color)
        spawn_box(label + "_Lintel", x, y, z + height, width + jamb, depth, jamb, color)
        spawn_box(label + "_Panel", x, y + 8, z + height / 2.0, width - jamb, 12, height - sill, (0.035, 0.045, 0.055))
    else:
        spawn_box(label + "_LeftJamb", x, y - width / 2.0, z + height / 2.0, depth, jamb, height, color)
        spawn_box(label + "_RightJamb", x, y + width / 2.0, z + height / 2.0, depth, jamb, height, color)
        spawn_box(label + "_Lintel", x, y, z + height, depth, width + jamb, jamb, color)
        spawn_box(label + "_Panel", x + 8, y, z + height / 2.0, 12, width - jamb, height - sill, (0.035, 0.045, 0.055))


def spawn_window(label, x, y, z, width, height, orientation="x"):
    glass = (0.06, 0.16, 0.22)
    frame = (0.15, 0.18, 0.19)
    if orientation == "x":
        spawn_box(label + "_Glass", x, y, z, width, 30, height, glass)
        spawn_box(label + "_Top", x, y - 18, z + height / 2.0, width + 60, 45, 35, frame)
        spawn_box(label + "_Bottom", x, y - 18, z - height / 2.0, width + 60, 45, 35, frame)
        spawn_box(label + "_Left", x - width / 2.0, y - 18, z, 35, 45, height, frame)
        spawn_box(label + "_Right", x + width / 2.0, y - 18, z, 35, 45, height, frame)
    else:
        spawn_box(label + "_Glass", x, y, z, 30, width, height, glass)
        spawn_box(label + "_Top", x - 18, y, z + height / 2.0, 45, width + 60, 35, frame)
        spawn_box(label + "_Bottom", x - 18, y, z - height / 2.0, 45, width + 60, 35, frame)
        spawn_box(label + "_Left", x - 18, y - width / 2.0, z, 45, 35, height, frame)
        spawn_box(label + "_Right", x - 18, y + width / 2.0, z, 45, 35, height, frame)


def delete_previous():
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if TAG in actor.tags:
            unreal.EditorLevelLibrary.destroy_actor(actor)


def delete_template_whitebox():
    """Remove the original Third Person template's LevelPrototyping actors."""
    for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        if TAG in actor.tags:
            continue
        mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh = mesh_component.get_editor_property("static_mesh") if mesh_component else None
        mesh_path = mesh.get_path_name() if mesh else ""
        if actor.get_class().get_name() == "StaticMeshActor" and mesh_path.startswith("/Game/LevelPrototyping/Meshes/"):
            unreal.EditorLevelLibrary.destroy_actor(actor)
        elif actor.get_class().get_name() in ("PlayerStart", "TextRenderActor"):
            # The map's original spawn marker and tutorial text are replaced below.
            unreal.EditorLevelLibrary.destroy_actor(actor)


def set_label(actor, text):
    actor.set_actor_label(text)
    actor.tags = [TAG, "Whitebox"]


def spawn_label(label, text, x, y, z, color=(1.0, 1.0, 1.0)):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(cm(layout_x(label, x)), cm(y), cm(z)),
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
    delete_template_whitebox()

    # 150 x 150 m boundary; origin is the center, +Y is north.
    spawn_box("WB_BoundaryGround_150m", 0, 0, -20, 15000, 15000, 40, (0.18, 0.19, 0.20))

    # South entry / wasteland tutorial area.
    A = (0.56, 0.36, 0.18)
    spawn_box("WB_A_Wasteland_Backdrop", 0, -5900, -20, 15000, 3200, 40, A)
    spawn_box("WB_A_LeftRock", -3600, -6200, 400, 900, 1200, 800, A)
    spawn_box("WB_A_RightRock", 3300, -5850, 350, 1100, 900, 700, A)
    spawn_box("WB_A_Choke_WestWall", -4200, -4550, 650, 1800, 700, 1300, A)
    spawn_box("WB_A_Choke_EastWall", 4200, -4550, 650, 1800, 700, 1300, A)
    spawn_box("WB_A_MainApproach", 0, -5900, -100, 1500, 3200, 200, A)

    # West gas station platform (+2 m), kept as a readable whitebox mass.
    B = (0.16, 0.38, 0.42)
    spawn_box("WB_B_GasStation_Platform", -5000, -1800, 100, 3900, 3400, 200, B)
    spawn_box("WB_B_GasStation_Building", -5550, -1300, 300, 2000, 1200, 600, B)
    spawn_door("WB_B_GasStation_Door", -5550, -1900, 0, 850, 220, "x", B)
    spawn_window("WB_B_GasStation_Window", -5200, -1900, 380, 650, 450, "x")
    spawn_box("WB_B_GasStation_Canopy", -4300, -2350, 300, 1100, 1500, 140, B)
    spawn_box("WB_B_GasStation_CanopyPost_L", -4800, -2350, 220, 120, 120, 400, B)
    spawn_box("WB_B_GasStation_CanopyPost_R", -3800, -2350, 220, 120, 120, 400, B)
    for i, (x, y) in enumerate([(-4200, -2900), (-3900, -2900), (-4200, -3250)]):
        spawn_cylinder("WB_B_OilBarrel_%02d" % i, x, y, 60, 70, 120, (0.75, 0.32, 0.08))
    # Collapsed overpass: 30 m long, deck top at roughly 4 m for third-person sightlines.
    spawn_box("WB_B_Overpass_CollapsedDeck", -5000, -2450, 250, 3000, 400, 300, B)
    spawn_box("WB_B_Overpass_CollapsedRamp", -3400, -3000, 200, 500, 1000, 400, B)
    spawn_box("WB_B_Overpass_CollapsedEnd", -6500, -2450, 220, 800, 500, 440, B)
    spawn_box("WB_B_Overpass_BrokenDeck", -6750, -2450, 180, 700, 400, 240, B)
    spawn_box("WB_B_Overpass_Support_L", -6000, -2450, 120, 180, 180, 240, B)
    spawn_box("WB_B_Overpass_Support_R", -4050, -2450, 120, 180, 180, 240, B)
    spawn_box("WB_B_Overpass_Railing_Broken", -5000, -2270, 430, 3000, 60, 120, B)

    # C1 lower street: 36 m long, 25 m combat street, simple building pockets.
    C1 = (0.30, 0.40, 0.45)
    spawn_box("WB_C1_StreetFloor", 0, -1900, -100, 6500, 3600, 200, C1)
    spawn_box("WB_C1_WestHouse_A", -1450, -750, 300, 1100, 900, 600, C1)
    spawn_box("WB_C1_WestHouse_B", -1450, -1700, 250, 1100, 800, 500, C1)
    spawn_box("WB_C1_EastShop_A", 1450, -700, 300, 1100, 850, 600, C1)
    spawn_box("WB_C1_EastShop_B", 1450, -1750, 350, 1100, 800, 600, C1)
    spawn_door("WB_C1_WestHouseDoor", -1450, -1200, 0, 700, 220, "x", C1)
    spawn_door("WB_C1_EastShopDoor", 1450, -1125, 0, 700, 220, "x", C1)
    spawn_window("WB_C1_WestHouseWindow", -900, -1200, 330, 450, 350, "x")
    spawn_window("WB_C1_EastShopWindow", 900, -1125, 330, 450, 350, "x")
    spawn_box("WB_C1_WestBackAlleyWall", -2550, -1900, 350, 300, 3600, 600, C1)
    spawn_box("WB_C1_EastBackAlleyWall", 2550, -1900, 350, 300, 3600, 600, C1)
    spawn_box("WB_C1_CoverCar", 0, -1950, 150, 900, 350, 300, C1)

    # East mine yard and cave entrance, the mandatory detour around the hard lock.
    D = (0.25, 0.30, 0.34)
    spawn_box("WB_D_MineYard", 5000, -1800, -100, 3900, 3400, 200, D)
    spawn_box("WB_D_MineApproach", 5550, -500, -100, 1400, 500, 200, D)
    spawn_box("WB_D_MineOffice", 4450, -1500, 300, 1100, 850, 600, D)
    spawn_door("WB_D_MineOfficeDoor", 4450, -1950, 0, 700, 220, "x", D)
    # Open mine cave: layout position x=70~97m, y=53~78m; it crosses the division band.
    spawn_box("WB_D_MineCave_Floor", 5550, 850, -100, 2700, 2500, 200, D)
    spawn_box("WB_D_MineCave_WestWall", 4250, 850, 190, 250, 2500, 380, D)
    spawn_box("WB_D_MineCave_EastWall", 6850, 850, 190, 250, 2500, 380, D)
    spawn_box("WB_D_MineCave_BackWall", 5550, 2100, 190, 2700, 180, 380, D)
    for i, y in enumerate([-1800, -1000, -200]):
        beam_y = 200 + i * 800
        spawn_box("WB_D_MineCave_TimberBeam_%02d" % i, 5550, beam_y, 360, 2450, 120, 120, (0.34, 0.20, 0.12))
        spawn_box("WB_D_MineCave_TimberPost_L_%02d" % i, 4450, beam_y, 230, 120, 120, 340, (0.34, 0.20, 0.12))
        spawn_box("WB_D_MineCave_TimberPost_R_%02d" % i, 6650, beam_y, 230, 120, 120, 340, (0.34, 0.20, 0.12))
    spawn_door("WB_D_MineCaveEntrance", 5550, -400, 0, 1200, 240, "x", D)
    spawn_box("WB_D_MineShaft_Elevator_Base", 6500, 1450, 120, 500, 500, 200, D)
    spawn_box("WB_D_MineShaft_Elevator_Post_L", 6300, 1450, 650, 100, 100, 1200, D)
    spawn_box("WB_D_MineShaft_Elevator_Post_R", 6700, 1450, 650, 100, 100, 1200, D)
    spawn_box("WB_D_MineShaft_Elevator_Header", 6500, 1450, 1250, 600, 120, 120, D)
    spawn_window("WB_D_MineOfficeWindow", 4450, -1950, 330, 450, 280, "x")
    spawn_box("WB_D_TransportTunnelFloor", 2500, -3450, -2800, 6500, 500, 200, D)
    spawn_box("WB_D_TransportTunnelRoof", 2500, -3450, -1700, 6500, 500, 200, D)
    spawn_box("WB_D_TransportTunnelWestWall", 2500, -3750, -2250, 6500, 200, 1100, D)
    spawn_box("WB_D_TransportTunnelEastWall", 2500, -3150, -2250, 6500, 200, 1100, D)
    spawn_box("WB_D_TransportTunnelMouth", 180, -3450, -2250, 800, 500, 1100, D)
    spawn_box("WB_C1_D_Connection", 2550, -2600, -100, 900, 800, 200, D)

    # Collapsed-building division band and central fog hard lock.
    LOCK = (0.42, 0.16, 0.48)
    # Low collapsed-building band: marks the district edge without becoming a sightline wall.
    spawn_box("WB_Lock_DivisionBand_West", -3900, 0, 150, 4200, 700, 300, LOCK)
    spawn_box("WB_Lock_DivisionBand_East", 3900, 0, 150, 4200, 700, 300, LOCK)
    # The hard lock is a low debris mound, readable as blocked but kept below camera eye line.
    spawn_box("WB_Lock_FogGate_LowDebris", 0, 0, 80, 1500, 500, 160, LOCK)
    spawn_box("WB_Lock_FogGate_LeftDebris", -900, 0, 60, 250, 700, 120, LOCK)
    spawn_box("WB_Lock_FogGate_RightDebris", 900, 0, 60, 250, 700, 120, LOCK)
    spawn_door("WB_Lock_BrokenGateFrame", 0, 0, 0, 1500, 210, "x", LOCK)
    spawn_box("WB_Lock_FogRibbon_L", -550, -260, 130, 70, 40, 260, LOCK)
    spawn_box("WB_Lock_FogRibbon_R", 550, -260, 130, 70, 40, 260, LOCK)

    # C2 upper street, 22 m long, with a central combat lane and side pockets.
    C2 = (0.38, 0.43, 0.47)
    spawn_box("WB_C2_StreetFloor", 0, 1600, -100, 7000, 2200, 200, C2)
    spawn_box("WB_C2_WestHouse_A", -1450, 1050, 350, 1100, 700, 600, C2)
    spawn_box("WB_C2_WestHouse_B", -1450, 2050, 300, 1100, 700, 500, C2)
    spawn_box("WB_C2_EastHouse", 1450, 1900, 350, 1100, 900, 600, C2)
    spawn_door("WB_C2_WestHouseDoor", -1450, 700, 0, 700, 220, "x", C2)
    spawn_door("WB_C2_EastHouseDoor", 1450, 1450, 0, 700, 220, "x", C2)
    spawn_box("WB_C2_CoverCar", -250, 1250, 250, 900, 350, 300, C2)
    spawn_box("WB_C2_CoverCar_02", 800, 2000, 250, 900, 350, 300, C2)

    # E north plaza: open 50 m arena, church landmark, four low residual columns and oil puddles.
    E = (0.28, 0.12, 0.42)
    spawn_cylinder("WB_E_BossArena_Floor", 0, 5000, -100, 2500, 200, E)
    spawn_box("WB_E_Church_Landmark", 0, 6800, 500, 2500, 1200, 1000, E)
    spawn_door("WB_E_Church_Door", 0, 6200, 0, 900, 260, "x", E)
    for i, (x, y) in enumerate([(-1350, 4650), (1350, 4650), (-650, 3550), (650, 3550)]):
        spawn_cylinder("WB_E_ResidualColumn_%02d" % i, x, y, 220, 125, 400, E)
    spawn_box("WB_E_OilPuddle_L", -1300, 5200, 35, 800, 400, 70, (0.23, 0.10, 0.06))
    spawn_box("WB_E_OilPuddle_R", 1300, 5200, 35, 800, 400, 70, (0.23, 0.10, 0.06))

    spawn_label("WB_Label_Spawn", "荒原教学区", 0, -6100, 900, (1.0, 0.75, 0.30))
    spawn_label("WB_Label_GasStation", "加油站", -5000, -1800, 900, (0.35, 0.90, 0.95))
    spawn_label("WB_Label_C1", "C1 中下街区", 0, -1900, 900, (0.55, 0.85, 0.95))
    spawn_label("WB_Label_Mine", "旧矿井", 5000, -1800, 900, (0.60, 0.85, 0.80))
    spawn_label("WB_Label_HardLock", "蚀雾封锁·硬锁", 0, 0, 2200, (1.0, 0.35, 0.85))
    spawn_label("WB_Label_C2", "C2 中上街区", 0, 1600, 1100, (0.75, 0.85, 0.95))
    spawn_label("WB_Label_Boss", "E 镇中心广场·Boss场", 0, 5000, 3000, (0.90, 0.65, 1.0))
    spawn_label("WB_Label_Church", "教堂地标", 0, 6800, 1500, (0.95, 0.80, 1.0))
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
