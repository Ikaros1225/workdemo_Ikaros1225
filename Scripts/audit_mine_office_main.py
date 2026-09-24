import unreal


MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
PREFIX = "WB_D_MineOffice"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
labels = {a.get_actor_label(): a for a in actors}
office = {label: a for label, a in labels.items() if label.startswith(PREFIX)}
required = (
    PREFIX,
    PREFIX + "_Floor",
    PREFIX + "_Wall_Back",
    PREFIX + "_Wall_Entry_Left",
    PREFIX + "_Wall_Entry_Right",
    PREFIX + "_Wall_Entry_DoorHeader",
    PREFIX + "_Door_Leaf_Open",
    PREFIX + "_Interior_Light",
    PREFIX + "_Roof",
)
missing = [name for name in required if name not in office]
if missing:
    raise RuntimeError("Missing MineOffice pieces: " + ", ".join(missing))

anchor = office[PREFIX]
anchor_loc = anchor.get_actor_location()
anchor_rot = anchor.get_actor_rotation()
if abs(anchor_rot.yaw - 90.0) > 0.1:
    raise RuntimeError("Unexpected MineOffice yaw: %.1f" % anchor_rot.yaw)

def local_coords(point, origin, yaw):
    import math
    a = math.radians(yaw)
    dx = point.x - origin.x
    dy = point.y - origin.y
    return (dx * math.cos(a) + dy * math.sin(a),
            -dx * math.sin(a) + dy * math.cos(a))

floor_origin, floor_extent = office[PREFIX + "_Floor"].get_actor_bounds(False)
floor_top = floor_origin.z + floor_extent.z
yard = [a for a in actors if a.get_actor_label() == "WB_D_MineYard"]
if len(yard) != 1:
    raise RuntimeError("Expected one MineYard, found %d" % len(yard))
yard_origin, yard_extent = yard[0].get_actor_bounds(False)
yard_top = yard_origin.z + yard_extent.z
if abs(floor_top) > 1.0 or abs(yard_top - floor_top) > 1.0:
    raise RuntimeError("Ground mismatch: office=%.1f yard=%.1f" % (floor_top, yard_top))

left_x, _ = local_coords(office[PREFIX + "_Wall_Entry_Left"].get_actor_location(), anchor_loc, anchor_rot.yaw)
right_x, _ = local_coords(office[PREFIX + "_Wall_Entry_Right"].get_actor_location(), anchor_loc, anchor_rot.yaw)
left_span = office[PREFIX + "_Wall_Entry_Left"].get_actor_scale3d().x * 100.0
right_span = office[PREFIX + "_Wall_Entry_Right"].get_actor_scale3d().x * 100.0
clear_width = abs(left_x - right_x) - (left_span + right_span) / 2.0
header_origin, header_extent = office[PREFIX + "_Wall_Entry_DoorHeader"].get_actor_bounds(False)
door_height = header_origin.z - header_extent.z - floor_top
if clear_width < 150.0 or door_height < 210.0:
    raise RuntimeError("Door opening invalid: width=%.1f height=%.1f" % (clear_width, door_height))
for label in office:
    if any(token in label for token in ("Stair", "SecondFloor", "UpperFloor")):
        raise RuntimeError("Unexpected upper-level actor: " + label)

light = office[PREFIX + "_Interior_Light"].get_component_by_class(unreal.RectLightComponent)
intensity = float(light.get_editor_property("intensity"))
attenuation = float(light.get_editor_property("attenuation_radius"))
if not (60 <= intensity <= 120 and 600 <= attenuation <= 900):
    raise RuntimeError("MineOffice light invalid: %.1f lm / %.1f cm" % (intensity, attenuation))

gas = [a for a in actors if a.get_actor_label().startswith("WB_B_GasStation")]
mine = [a for a in actors if a.get_actor_label().startswith("WB_D_Mine")]
if not gas:
    raise RuntimeError("Gas station actors missing")
if not mine:
    raise RuntimeError("Mine actors missing")

unreal.log("MINE_OFFICE_MAIN_AUDIT_OK actors=%d office=%d gas_station=%d mine=%d door_clear=%.1fcm door_height=%.1fcm floor_top=%.1fcm yard_top=%.1fcm levels=1 light=%.1flm/%.1fcm" % (
    len(actors), len(office), len(gas), len(mine), clear_width, door_height, floor_top, yard_top, intensity, attenuation))
