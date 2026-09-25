import json
import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
AUDIT_PATH = "G:/UE/project/workdemo/Saved/gasstation_side_route_audit.json"

def vec(v): return [round(float(v.x), 4), round(float(v.y), 4), round(float(v.z), 4)]
def rot(v): return [round(float(v.pitch), 4), round(float(v.yaw), 4), round(float(v.roll), 4)]

def actor_fp(actor, actors):
    data={"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"location":vec(actor.get_actor_location()),"rotation":rot(actor.get_actor_rotation()),"scale":vec(actor.get_actor_scale3d()),"tags":sorted(str(t) for t in actor.tags),"parent":actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else "","children":sorted(a.get_actor_label() for a in actors if a.get_attach_parent_actor()==actor),"components":[]}
    for c in actor.get_components_by_class(unreal.SceneComponent):
        item={"name":c.get_name(),"class":c.get_class().get_name()}
        for p in ("relative_location","relative_rotation","relative_scale3d"):
            try:
                val=c.get_editor_property(p); item[p]=vec(val) if p != "relative_rotation" else rot(val)
            except Exception: pass
        try: item["static_mesh"]=c.get_editor_property("static_mesh").get_path_name() if c.get_editor_property("static_mesh") else ""
        except Exception: item["static_mesh"]=""
        try: item["collision_enabled"]=str(c.get_editor_property("collision_enabled"))
        except Exception: item["collision_enabled"]=""
        try: item["collision_profile"]=str(c.get_editor_property("collision_profile_name"))
        except Exception: item["collision_profile"]=""
        mats=[]
        for i in range(4):
            try:
                mat=c.get_material(i); mats.append(mat.get_path_name() if mat else "")
            except Exception: mats.append("")
        item["materials"]=mats
        data["components"].append(item)
    data["components"].sort(key=lambda x:x["name"])
    return data

def deck_fp(actors):
    root=[a for a in actors if a.get_actor_label()=="WB_B_Overpass_BrokenDeck"][0]
    selected=[root]; changed=True
    while changed:
        changed=False
        for actor in actors:
            if actor not in selected and any(actor.get_attach_parent_actor()==p for p in selected): selected.append(actor); changed=True
    return sorted((actor_fp(a,actors) for a in selected),key=lambda x:x["label"])

def main():
    world=unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
    audit=json.load(open(AUDIT_PATH,"r",encoding="utf-8"))
    if deck_fp(actors) != audit["overpass_fingerprint_before"]:
        raise RuntimeError("BrokenDeck baseline mismatch before floor correction")
    target=[a for a in actors if a.get_actor_label()=="WB_B_GasStation_UpperFloor_Walkable"]
    if len(target)!=1: raise RuntimeError("Expected one upper floor actor")
    target[0].modify()
    target[0].set_actor_scale3d(unreal.Vector(6.0,10.0,1.0))
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH): raise RuntimeError("Could not save floor correction")
    actors_after=list(unreal.EditorLevelLibrary.get_all_level_actors())
    if deck_fp(actors_after) != audit["overpass_fingerprint_before"]: raise RuntimeError("BrokenDeck changed during floor correction")
    loc=target[0].get_actor_location(); scale=target[0].get_actor_scale3d()
    unreal.log("GAS_STATION_UPPER_FLOOR_CORRECTED loc=%s scale=%s top_z=540.0 bounds_x=(5850,6450) bounds_y=(-1720,-720)" % (loc,scale))

main()
