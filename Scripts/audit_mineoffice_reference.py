import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    raise RuntimeError("Could not load " + MAP_PATH)

labels = {
    "WB_B_GasStation_Building_Light_Ground",
    "WB_B_GasStation_Building_Wall_Front_Left",
    "WB_B_GasStation_Building_Wall_Back",
    "WB_B_GasStation_Building_Roof",
    "WB_D_MineOffice",
}

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label not in labels:
        continue
    unreal.log("REFERENCE_ACTOR label=%s location=%s rotation=%s scale=%s" % (
        label, actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d()))
    for component in actor.get_components_by_class(unreal.RectLightComponent):
        values = {}
        for prop in ("intensity", "attenuation_radius", "source_width", "source_height",
                     "use_temperature", "temperature", "indirect_lighting_intensity",
                     "cast_shadows", "light_color", "mobility"):
            try:
                values[prop] = str(component.get_editor_property(prop))
            except Exception as exc:
                values[prop] = "unavailable:" + str(exc)
        unreal.log("REFERENCE_LIGHT label=%s properties=%s" % (label, values))
