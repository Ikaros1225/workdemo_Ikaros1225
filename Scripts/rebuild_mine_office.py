import math
import unreal


MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
TAG = "GraytownWhitebox"
CUBE_PATH = "/Engine/BasicShapes/Cube.Cube"
WALL_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_63_76_86"
TRIM_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_45_48_51"
FLOOR_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_45_48_51"
GLASS_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_15_40_56"
DOOR_MATERIAL_PATH = "/Game/WhiteboxMaterials/MI_Graytown_86_51_30"
ANCHOR_LABEL = "WB_D_MineOffice"
PREFIX = "WB_D_MineOffice"
TEMP_MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap_MineOffice_Updated_20260924_1535"


def material(path):
    obj = unreal.load_asset(path)
    if not obj:
        raise RuntimeError("Missing material: " + path)
    return obj


def world_point(cx, cy, yaw_degrees, local_x, local_y, z):
    angle = math.radians(yaw_degrees)
    x = cx + local_x * math.cos(angle) - local_y * math.sin(angle)
    y = cy + local_x * math.sin(angle) + local_y * math.cos(angle)
    return (x, y, z)


def spawn_box(label, location, size, mat, rotation=None, collision=True):
    rot = rotation or unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(float(location[0]), float(location[1]), float(location[2])),
        rot,
    )
    if not actor:
        raise RuntimeError("Could not spawn " + label)
    actor.set_actor_label(label)
    actor.tags = [TAG, "Whitebox", "MineOffice"]
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(unreal.load_asset(CUBE_PATH))
    comp.set_material(0, mat)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION
    )
    comp.set_editor_property("can_ever_affect_navigation", collision)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    return actor


def get_actors():
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

actors = get_actors()
anchors = [a for a in actors if a.get_actor_label() == ANCHOR_LABEL]
if len(anchors) != 1:
    raise RuntimeError("Expected exactly one MineOffice anchor; found %d" % len(anchors))

anchor = anchors[0]
loc = anchor.get_actor_location()
rot = anchor.get_actor_rotation()
scale = anchor.get_actor_scale3d()
cx, cy = loc.x, loc.y
yaw = rot.yaw

# Preserve the current 11 x 8.5 m rotated footprint while replacing the solid block.
# Local X is 11 m and local Y is 8.5 m; the existing door faces world +X.
width = abs(scale.x) * 100.0
depth = abs(scale.y) * 100.0
wall_thickness = 35.0
wall_top = 420.0
floor_top = 0.0
door_width = 160.0
door_height = 230.0
door_half = door_width / 2.0
half_w = width / 2.0
half_d = depth / 2.0
floor_z = floor_top - 10.0
wall_z = (floor_top + wall_top) / 2.0

wall_mat = material(WALL_MATERIAL_PATH)
trim_mat = material(TRIM_MATERIAL_PATH)
floor_mat = material(FLOOR_MATERIAL_PATH)
glass_mat = material(GLASS_MATERIAL_PATH)
door_mat = material(DOOR_MATERIAL_PATH)

# Remove only this building's old closed block, blocked entrance, and rebuildable pieces.
for actor in actors:
    label = actor.get_actor_label()
    if label.startswith(PREFIX) and actor != anchor:
        unreal.EditorLevelLibrary.destroy_actor(actor)

anchor_mesh = anchor.get_component_by_class(unreal.StaticMeshComponent)
anchor_mesh.set_static_mesh(None)
anchor.tags = list(set(anchor.tags + [TAG, "Whitebox", "MineOfficeAnchor"]))

# One continuous ground-level interior, with no step, stair, or raised threshold.
spawn_box(PREFIX + "_Floor", world_point(cx, cy, yaw, 0, 0, floor_z), (width, depth, 20), floor_mat,
          unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))

# The two long facades run along local X.  The local -Y facade keeps the
# current mine-yard-facing entrance; the local +Y facade is solid.
segment = (width - door_width) / 2.0
for suffix, center_x in (("Left", door_half + segment / 2.0),
                         ("Right", -door_half - segment / 2.0)):
    spawn_box(PREFIX + "_Wall_Entry_%s" % suffix,
              world_point(cx, cy, yaw, center_x, -half_d + wall_thickness / 2.0, wall_z),
              (segment, wall_thickness, wall_top), wall_mat,
              unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
spawn_box(PREFIX + "_Wall_Entry_DoorHeader",
          world_point(cx, cy, yaw, 0, -half_d + wall_thickness / 2.0, (door_height + wall_top) / 2.0),
          (door_width, wall_thickness, wall_top - door_height), wall_mat,
          unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
spawn_box(PREFIX + "_Wall_Back",
          world_point(cx, cy, yaw, 0, half_d - wall_thickness / 2.0, wall_z),
          (width, wall_thickness, wall_top), wall_mat,
          unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))

# North and south walls use an offset high window that is decorative and non-blocking.
window_width = 220.0
window_height = 115.0
window_center_z = 315.0
window_bottom = window_center_z - window_height / 2.0
window_top = window_center_z + window_height / 2.0
side_segment = (depth - window_width) / 2.0
for side_name, local_x in (("North", half_w - wall_thickness / 2.0),
                           ("South", -half_w + wall_thickness / 2.0)):
    side_rot = unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0)
    for suffix, local_y in (("Left", -window_width / 2.0 - side_segment / 2.0),
                            ("Right", window_width / 2.0 + side_segment / 2.0)):
        spawn_box(PREFIX + "_Wall_%s_%s" % (side_name, suffix),
                  world_point(cx, cy, yaw, local_x, local_y, wall_z),
                  (wall_thickness, side_segment, wall_top), wall_mat, side_rot)
    spawn_box(PREFIX + "_Wall_%s_BelowWindow" % side_name,
              world_point(cx, cy, yaw, local_x, 0, (floor_top + window_bottom) / 2.0),
              (wall_thickness, window_width, window_bottom - floor_top), wall_mat, side_rot)
    spawn_box(PREFIX + "_Wall_%s_AboveWindow" % side_name,
              world_point(cx, cy, yaw, local_x, 0, (window_top + wall_top) / 2.0),
              (wall_thickness, window_width, wall_top - window_top), wall_mat, side_rot)
    glass_x = local_x - (8.0 if side_name == "North" else -8.0)
    spawn_box(PREFIX + "_Window_%s_Glass" % side_name,
              world_point(cx, cy, yaw, glass_x, 0, window_center_z),
              (8.0, window_width - 20.0, window_height - 20.0), glass_mat,
              unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0), collision=False)

# A slim open leaf reads as a real entrance but stays outside the walkable doorway.
door_leaf_x = -door_half - 12.0
door_leaf_y = -half_d + 55.0
spawn_box(PREFIX + "_DoorFrame_Left", world_point(cx, cy, yaw, -door_half - 10, -half_d + 8, door_height / 2.0),
          (20, 42, door_height), trim_mat, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
spawn_box(PREFIX + "_DoorFrame_Right", world_point(cx, cy, yaw, door_half + 10, -half_d + 8, door_height / 2.0),
          (20, 42, door_height), trim_mat, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
spawn_box(PREFIX + "_DoorFrame_Top", world_point(cx, cy, yaw, 0, -half_d + 8, door_height + 9),
          (door_width + 40, 42, 18), trim_mat, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
spawn_box(PREFIX + "_Door_Leaf_Open",
          world_point(cx, cy, yaw, door_leaf_x, door_leaf_y, door_height / 2.0),
          (12, 90, door_height - 15), door_mat, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
spawn_box(PREFIX + "_Door_Hinge_Post",
          world_point(cx, cy, yaw, door_leaf_x, door_leaf_y, door_height / 2.0),
          (18, 14, door_height - 8), trim_mat, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))

# Single shallow roof; no intermediate floor, stairs, or upper-level geometry is created.
spawn_box(PREFIX + "_Roof", world_point(cx, cy, yaw, 0, 0, wall_top + 35),
          (width, depth, 70), trim_mat, unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))

# The gas-station light is 120 lm / 900 cm; use a softer, tighter fixture for this office.
light = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.RectLight,
    unreal.Vector(*[float(v) for v in world_point(cx, cy, yaw, -25, 0, 360)]),
    unreal.Rotator(pitch=-90.0, yaw=yaw + 180.0, roll=180.0),
)
if not light:
    raise RuntimeError("Could not spawn MineOffice interior light")
light.set_actor_label(PREFIX + "_Interior_Light")
light.tags = [TAG, "Whitebox", "MineOfficeLight"]
light_comp = light.get_component_by_class(unreal.RectLightComponent)
for key, value in (("intensity", 90.0), ("attenuation_radius", 760.0),
                   ("source_width", 600.0), ("source_height", 420.0),
                   ("cast_shadows", False), ("indirect_lighting_intensity", 1.0),
                   ("mobility", unreal.ComponentMobility.MOVABLE)):
    light_comp.set_editor_property(key, value)

# Ensure the existing mine-yard floor meets the office threshold at exactly Z=0.
mine_yard = [a for a in get_actors() if a.get_actor_label() == "WB_D_MineYard"]
if len(mine_yard) != 1:
    raise RuntimeError("Expected exactly one mine yard floor; found %d" % len(mine_yard))
yard_origin, yard_extent = mine_yard[0].get_actor_bounds(False)
if abs((yard_origin.z + yard_extent.z) - floor_top) > 1.0:
    raise RuntimeError("Mine yard floor top is not at Z=0: %.1f" % (yard_origin.z + yard_extent.z))

# Make the resulting office actors easy to isolate, then persist only the current map.
office_actors = [a for a in get_actors() if a.get_actor_label().startswith(PREFIX)]
if len(office_actors) < 20:
    raise RuntimeError("MineOffice rebuild is incomplete: %d actors" % len(office_actors))
if unreal.EditorAssetLibrary.does_asset_exist(TEMP_MAP_PATH):
    raise RuntimeError("Temporary map already exists; refusing to overwrite: " + TEMP_MAP_PATH)
if not unreal.EditorLoadingAndSavingUtils.save_map(world, TEMP_MAP_PATH):
    raise RuntimeError("Could not save the rebuilt temporary map")
unreal.log("MINE_OFFICE_REBUILD_OK source=%s temp=%s actors=%d world_footprint=(%.0f,%.0f) floor_top=%.0f door_clear=(%.0f,%.0f) light=(90lm,760cm) levels=1 stairs=0" % (
    MAP_PATH, TEMP_MAP_PATH, len(office_actors), depth, width, floor_top, door_width, door_height))
