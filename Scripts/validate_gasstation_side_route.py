import json
import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
AUDIT_PATH = "G:/UE/project/workdemo/Saved/gasstation_side_route_audit.json"

def vec(v):
    return [round(float(v.x), 4), round(float(v.y), 4), round(float(v.z), 4)]

def rot(v):
    return [round(float(v.pitch), 4), round(float(v.yaw), 4), round(float(v.roll), 4)]

def fp(actor, actors):
    data = {"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
            "location": vec(actor.get_actor_location()), "rotation": rot(actor.get_actor_rotation()),
            "scale": vec(actor.get_actor_scale3d()), "tags": sorted(str(t) for t in actor.tags),
            "parent": actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else ""}
    data["children"] = sorted(child.get_actor_label() for child in actors if child.get_attach_parent_actor() == actor)
    comps = []
    for c in actor.get_components_by_class(unreal.SceneComponent):
        item = {"name": c.get_name(), "class": c.get_class().get_name()}
        for p in ("relative_location", "relative_rotation", "relative_scale3d"):
            try:
                value = c.get_editor_property(p)
                item[p] = vec(value) if p != "relative_rotation" else rot(value)
            except Exception: pass
        try: item["static_mesh"] = c.get_editor_property("static_mesh").get_path_name() if c.get_editor_property("static_mesh") else ""
        except Exception: item["static_mesh"] = ""
        try: item["collision_enabled"] = str(c.get_editor_property("collision_enabled"))
        except Exception: item["collision_enabled"] = ""
        try: item["collision_profile"] = str(c.get_editor_property("collision_profile_name"))
        except Exception: item["collision_profile"] = ""
        materials = []
        for index in range(4):
            try:
                material = c.get_material(index)
                materials.append(material.get_path_name() if material else "")
            except Exception:
                materials.append("")
        item["materials"] = materials
        comps.append(item)
    data["components"] = sorted(comps, key=lambda x: x["name"])
    return data

def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world: raise RuntimeError("Could not load map")
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    by_label = {a.get_actor_label(): a for a in actors}
    for name in ("WB_B_Overpass_BrokenDeck", "WB_B_GasStation_Stairs", "WB_B_GasStation_SideRoute", "WB_B_GasStation_UpperFloor_Walkable"):
        if name not in by_label: raise RuntimeError("Missing expected actor: " + name)
    stair_comp = by_label["WB_B_GasStation_Stairs"].get_components_by_class(unreal.InstancedStaticMeshComponent)
    route_comp = by_label["WB_B_GasStation_SideRoute"].get_components_by_class(unreal.InstancedStaticMeshComponent)
    if len(stair_comp) != 1 or stair_comp[0].get_instance_count() != 20: raise RuntimeError("Stair validation failed")
    if len(route_comp) != 1 or route_comp[0].get_instance_count() != 4: raise RuntimeError("Route validation failed")
    wall = by_label["WB_B_GasStation_Building_Wall_Right"]
    if abs(wall.get_actor_location().z - 295.0) > 0.1: raise RuntimeError("Wall lower course Z mismatch")
    if abs(wall.get_actor_scale3d().z - 4.9) > 0.01: raise RuntimeError("Wall lower course height mismatch")
    overpass = by_label["WB_B_Overpass_BrokenDeck"]
    with open(AUDIT_PATH, "r", encoding="utf-8") as handle: audit = json.load(handle)
    selected = [overpass]
    changed = True
    while changed:
        changed = False
        for actor in actors:
            if actor in selected:
                continue
            if any(actor.get_attach_parent_actor() == parent for parent in selected):
                selected.append(actor)
                changed = True
    current = sorted((fp(actor, actors) for actor in selected), key=lambda item: item["label"])
    before = audit["overpass_fingerprint_before"]
    after = audit["overpass_fingerprint_after"]
    if current not in (before, after) or before != after:
        unreal.log("BROKEN_VALIDATE_COUNT before=%d current=%d" % (len(before), len(current)))
        before_by_label = {row["label"]: row for row in before}
        current_by_label = {row["label"]: row for row in current}
        for label in sorted(set(before_by_label) | set(current_by_label)):
            if before_by_label.get(label) != current_by_label.get(label):
                unreal.log("BROKEN_VALIDATE_DIFF label=%s before=%s current=%s" % (label, before_by_label.get(label), current_by_label.get(label)))
        raise RuntimeError("BrokenDeck fingerprint mismatch")
    unreal.log("GAS_STATION_SIDE_ROUTE_VALIDATED stairs=20 route=4 overpass_unchanged=True")

main()
