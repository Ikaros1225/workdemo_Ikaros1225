import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
REPORT = "G:/UE/project/workdemo/Saved/graytown_map_audit.txt"
WHITEBOX_TAG = "GraytownWhitebox"


def actor_mesh(actor):
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not comp:
        return ""
    mesh = comp.get_editor_property("static_mesh")
    return mesh.get_path_name() if mesh else ""


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError("Could not load " + MAP_PATH)
    rows = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        tags = [str(t) for t in actor.tags]
        mesh = actor_mesh(actor)
        suspected = (
            WHITEBOX_TAG not in tags
            and mesh in ("/Engine/BasicShapes/Cube.Cube", "/Engine/BasicShapes/Plane.Plane")
        )
        loc = actor.get_actor_location()
        rows.append({
            "name": actor.get_actor_label(),
            "class": actor.get_class().get_name(),
            "tags": tags,
            "mesh": mesh,
            "location": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "suspected_template": suspected,
        })
    rows.sort(key=lambda r: (not r["suspected_template"], r["name"]))
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Graytown map actor audit\n")
        f.write("Map: %s\n\n" % MAP_PATH)
        for r in rows:
            f.write("{name}\t{class}\t{mesh}\ttags={tags}\tloc={location}\tsuspected_template={suspected_template}\n".format(**r))
    unreal.log("Graytown audit written: %s (actors=%d)" % (REPORT, len(rows)))


main()
