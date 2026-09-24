import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
REPORT_PATH = "G:/UE/project/workdemo/Saved/test_spawn_final_audit.txt"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if actor.get_class().get_name() != "PlayerStart":
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    rows.append((
        actor.get_actor_label(),
        str(actor.get_editor_property("player_start_tag")),
        (round(location.x, 1), round(location.y, 1), round(location.z, 1)),
        (round(rotation.pitch, 1), round(rotation.yaw, 1), round(rotation.roll, 1)),
        [str(tag) for tag in actor.tags],
    ))

rows.sort()
with open(REPORT_PATH, "w", encoding="utf-8") as report:
    report.write("Final PlayerStart audit\nMap: %s\nCount: %d\n\n" % (MAP_PATH, len(rows)))
    for label, start_tag, location, rotation, tags in rows:
        report.write("%s\t%s\tloc=%s\trot=%s\ttags=%s\n" % (label, start_tag, location, rotation, tags))
unreal.log("Final PlayerStart audit written: %s (count=%d)" % (REPORT_PATH, len(rows)))
