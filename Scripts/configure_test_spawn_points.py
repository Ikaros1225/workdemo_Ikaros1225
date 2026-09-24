import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
WHITEBOX_TAG = "GraytownWhitebox"
MARKER_TAG = "TestSpawnPoint"

SPAWNS = [
    ("测试点_加油站外场", "WBSpawn_GasOutside", (3800.0, -2000.0, 110.0), 0.0),
    ("测试点_加油站一楼", "WBSpawn_GasGroundFloor", (4900.0, -1000.0, 150.0), -90.0),
    ("测试点_加油站二楼", "WBSpawn_GasUpperFloor", (6150.0, -500.0, 640.0), -90.0),
    ("测试点_倒塌高架", "WBSpawn_CollapsedOverpass", (5000.0, -3260.0, 450.0), 0.0),
    ("测试点_C1街区", "WBSpawn_C1", (-500.0, -1500.0, 100.0), 90.0),
    ("测试点_硬锁前", "WBSpawn_HardLockApproach", (0.0, -800.0, 100.0), 90.0),
    ("测试点_C2街区", "WBSpawn_C2", (-2800.0, 1500.0, 100.0), 90.0),
    ("测试点_矿场", "WBSpawn_MineYard", (-6600.0, -3000.0, 100.0), 90.0),
    ("测试点_矿洞", "WBSpawn_MineCave", (-5550.0, 0.0, 100.0), 90.0),
    ("测试点_Boss场", "WBSpawn_BossArena", (0.0, 5550.0, 100.0), 90.0),
]

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
player_starts = [actor for actor in actors if actor.get_class().get_name() == "PlayerStart"]
actor_by_label = {actor.get_actor_label(): actor for actor in actors}

for label, _, _, _ in SPAWNS:
    existing = actor_by_label.get(label)
    if existing and existing.get_class().get_name() != "PlayerStart":
        raise RuntimeError("Actor label already exists with a non-PlayerStart class: " + label)

south_start = next(
    (actor for actor in player_starts
     if str(actor.get_editor_property("player_start_tag")) == "WBSpawn_SouthWasteland"
     or actor.get_actor_label() in ("WB_PlayerStart_SouthWasteland", "测试点_荒原教学区")),
    None,
)
if not south_start:
    raise RuntimeError("The existing WB_PlayerStart_SouthWasteland was not found; refusing to create a replacement.")

south_start.set_editor_property("player_start_tag", "WBSpawn_SouthWasteland")
south_start.set_actor_label("测试点_荒原教学区")
if MARKER_TAG not in [str(tag) for tag in south_start.tags]:
    south_start.tags.append(MARKER_TAG)

for label, start_tag, location, yaw in SPAWNS:
    actor = next(
        (candidate for candidate in player_starts
         if str(candidate.get_editor_property("player_start_tag")) == start_tag),
        None,
    )
    if actor is None:
        actor = actor_by_label.get(label)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PlayerStart,
            unreal.Vector(*location),
            unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0),
        )
        player_starts.append(actor)
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0), False)
    actor.set_actor_label(label)
    actor.set_editor_property("player_start_tag", start_tag)
    tags = [str(tag) for tag in actor.tags]
    for tag in (WHITEBOX_TAG, "Whitebox", MARKER_TAG):
        if tag not in tags:
            actor.tags.append(tag)
            tags.append(tag)

unreal.EditorLevelLibrary.save_current_level()
unreal.log("Configured %d region test spawn points; the original wasteland start was preserved." % (len(SPAWNS) + 1))
