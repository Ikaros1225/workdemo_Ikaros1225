import unreal

unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
for actor in sorted(unreal.EditorLevelLibrary.get_all_level_actors(), key=lambda item: item.get_actor_label()):
    label = actor.get_actor_label()
    if label.startswith('WB_C2_') or label.startswith('WB_E_EntranceStair_') or label in ('WB_E_RaisedPlateau', 'WB_E_EntranceStairs'):
        loc = actor.get_actor_location()
        origin, extent = actor.get_actor_bounds(False)
        unreal.log('GEOM %s loc=(%.1f,%.1f,%.1f) bounds=(%.1f,%.1f,%.1f) ext=(%.1f,%.1f,%.1f) scale=(%.2f,%.2f,%.2f)' % (
            label, loc.x, loc.y, loc.z, origin.x, origin.y, origin.z, extent.x, extent.y, extent.z,
            actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z))
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            unreal.log('GEOM_COMPONENT %s instances=%d' % (label, component.get_instance_count()))
            if component.get_instance_count() > 0:
                for index in (0, component.get_instance_count() - 1):
                    try:
                        transform = component.get_instance_transform(index, False)
                        unreal.log('GEOM_INSTANCE %s index=%d transform=%s' % (label, index, transform))
                    except Exception as exc:
                        unreal.log_error('GEOM_INSTANCE_ERROR %s index=%d error=%s' % (label, index, exc))
