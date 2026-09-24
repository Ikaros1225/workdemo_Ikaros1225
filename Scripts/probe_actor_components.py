import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, -10000), unreal.Rotator())
unreal.log('PROBE_ACTOR_CLASS=%s' % actor.get_class().get_name())
unreal.log('PROBE_ACTOR_METHODS=%s' % [x for x in dir(actor) if 'component' in x.lower() or 'attach' in x.lower() or 'root' in x.lower()])
unreal.log('PROBE_STATIC_METHODS=%s' % [x for x in dir(unreal.StaticMeshComponent) if 'static' in x.lower() or 'attach' in x.lower()])
try:
    comp = actor.add_component_by_class(unreal.StaticMeshComponent, False, unreal.Transform(), 'TestComponent')
    unreal.log('PROBE_ADD_COMPONENT=%s' % comp)
except Exception as exc:
    unreal.log_error('PROBE_ADD_COMPONENT_ERROR=%s' % exc)
unreal.EditorLevelLibrary.destroy_actor(actor)
