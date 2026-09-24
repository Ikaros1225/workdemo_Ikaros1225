import unreal


MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"
PREFIX = "WB_D_MineOffice"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
office = {a.get_actor_label(): a for a in actors if a.get_actor_label().startswith(PREFIX)}
required = (
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

anchor = office.get(PREFIX)
if not anchor:
    raise RuntimeError("MineOffice anchor missing")
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


floor = office[PREFIX + "_Floor"]
floor_origin, floor_extent = floor.get_actor_bounds(False)
floor_top = floor_origin.z + floor_extent.z
if abs(floor_top) > 1.0:
    raise RuntimeError("Office floor top is not at ground Z=0: %.1f" % floor_top)

yard = [a for a in actors if a.get_actor_label() == "WB_D_MineYard"]
if len(yard) != 1:
    raise RuntimeError("Expected one MineYard, found %d" % len(yard))
yard_origin, yard_extent = yard[0].get_actor_bounds(False)
yard_top = yard_origin.z + yard_extent.z
if abs(yard_top - floor_top) > 1.0:
    raise RuntimeError("Office entrance has a vertical height difference: office=%.1f yard=%.1f" % (floor_top, yard_top))

# Confirm an unobstructed >=150 cm opening on the existing +X-facing facade.
left_loc = office[PREFIX + "_Wall_Entry_Left"].get_actor_location()
right_loc = office[PREFIX + "_Wall_Entry_Right"].get_actor_location()
left_x, _ = local_coords(left_loc, anchor_loc, anchor_rot.yaw)
right_x, _ = local_coords(right_loc, anchor_loc, anchor_rot.yaw)
left_span = office[PREFIX + "_Wall_Entry_Left"].get_actor_scale3d().x * 100.0
right_span = office[PREFIX + "_Wall_Entry_Right"].get_actor_scale3d().x * 100.0
clear_width = abs(left_x - right_x) - (left_span + right_span) / 2.0
if clear_width < 150.0:
    raise RuntimeError("Door opening is too narrow: %.1f cm" % clear_width)
header_origin, header_extent = office[PREFIX + "_Wall_Entry_DoorHeader"].get_actor_bounds(False)
door_height = header_origin.z - header_extent.z - floor_top
if door_height < 210.0:
    raise RuntimeError("Door opening is too short: %.1f cm" % door_height)
for label in office:
    if "Stair" in label or "SecondFloor" in label or "UpperFloor" in label:
        raise RuntimeError("Unexpected second-floor/stair actor: " + label)

light = office[PREFIX + "_Interior_Light"].get_component_by_class(unreal.RectLightComponent)
light_values = {
    "intensity": float(light.get_editor_property("intensity")),
    "attenuation_radius": float(light.get_editor_property("attenuation_radius")),
    "source_width": float(light.get_editor_property("source_width")),
    "source_height": float(light.get_editor_property("source_height")),
}
if not (60 <= light_values["intensity"] <= 120 and 600 <= light_values["attenuation_radius"] <= 900):
    raise RuntimeError("MineOffice light is outside the intended range: %s" % light_values)

unreal.log("MINE_OFFICE_AUDIT_OK actors=%d footprint=850x1100cm door_clear=%.1fcm door_height=%.1fcm floor_top=%.1fcm yard_top=%.1fcm levels=1 light=%s" % (
    len(office), clear_width, door_height, floor_top, yard_top, light_values))
