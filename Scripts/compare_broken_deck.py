import json
import unreal

AUDIT_PATH = "G:/UE/project/workdemo/Saved/gasstation_side_route_audit.json"
OUT_PATH = "G:/UE/project/workdemo/Saved/broken_deck_current.json"

def vec(v): return [round(float(v.x), 4), round(float(v.y), 4), round(float(v.z), 4)]
def rot(v): return [round(float(v.pitch), 4), round(float(v.yaw), 4), round(float(v.roll), 4)]
def fp(actor, actors):
    data={"label":actor.get_actor_label(),"class":actor.get_class().get_name(),"location":vec(actor.get_actor_location()),"rotation":rot(actor.get_actor_rotation()),"scale":vec(actor.get_actor_scale3d()),"tags":sorted(str(t) for t in actor.tags),"parent":actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else ""}
    data["children"]=sorted(a.get_actor_label() for a in actors if a.get_attach_parent_actor()==actor)
    comps=[]
    for c in actor.get_components_by_class(unreal.SceneComponent):
        item={"name":c.get_name(),"class":c.get_class().get_name()}
        for p in ("relative_location","relative_rotation","relative_scale3d"):
            try:
                value=c.get_editor_property(p); item[p]=vec(value) if p != "relative_rotation" else rot(value)
            except Exception: pass
        try:
            mesh=c.get_editor_property("static_mesh"); item["static_mesh"] = mesh.get_path_name() if mesh else ""
        except Exception: item["static_mesh"]=""
        try: item["collision_enabled"]=str(c.get_editor_property("collision_enabled"))
        except Exception: item["collision_enabled"]=""
        try: item["collision_profile"]=str(c.get_editor_property("collision_profile_name"))
        except Exception: item["collision_profile"]=""
        comps.append(item)
    data["components"]=sorted(comps,key=lambda x:x["name"])
    return data

def main():
    unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
    actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
    root=[a for a in actors if a.get_actor_label()=='WB_B_Overpass_BrokenDeck'][0]
    selected=[root]; changed=True
    while changed:
        changed=False
        for actor in actors:
            if actor not in selected and any(actor.get_attach_parent_actor()==p for p in selected): selected.append(actor); changed=True
    current=sorted([fp(a,actors) for a in selected],key=lambda x:x['label'])
    with open(OUT_PATH,'w',encoding='utf-8') as f: json.dump(current,f,ensure_ascii=True,indent=2)
    with open(AUDIT_PATH,'r',encoding='utf-8') as f: audit=json.load(f)
    before=audit['overpass_fingerprint_before']
    unreal.log('BROKEN_COMPARE_COUNT before=%d current=%d' % (len(before),len(current)))
    for key in ('label','class','location','rotation','scale','tags','parent','children'):
        b={row['label']:row.get(key) for row in before}; c={row['label']:row.get(key) for row in current}
        if b != c: unreal.log('BROKEN_COMPARE_DIFF key=%s before=%s current=%s' % (key,b,c))
    for row in current:
        old=next((x for x in before if x['label']==row['label']),None)
        if old:
            old_comp={x['name']:x for x in old['components']}; new_comp={x['name']:x for x in row['components']}
            if old_comp.keys()!=new_comp.keys(): unreal.log('BROKEN_COMPARE_COMPONENT_NAMES label=%s before=%s current=%s' % (row['label'],sorted(old_comp),sorted(new_comp)))
            for name in sorted(set(old_comp)&set(new_comp)):
                for key in ('class','relative_location','relative_rotation','relative_scale3d','static_mesh','collision_enabled','collision_profile'):
                    if old_comp[name].get(key)!=new_comp[name].get(key): unreal.log('BROKEN_COMPARE_COMPONENT_DIFF label=%s comp=%s key=%s before=%s current=%s' % (row['label'],name,key,old_comp[name].get(key),new_comp[name].get(key)))
    unreal.log('BROKEN_COMPARE_DONE')

main()
