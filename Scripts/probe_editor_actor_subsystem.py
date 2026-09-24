import unreal

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.log('PROBE_SUB_METHODS=%s' % [x for x in dir(sub) if 'component' in x.lower() or 'actor' in x.lower() or 'attach' in x.lower()])
unreal.log('PROBE_UNREAL_COMPONENT_TYPES=%s' % [x for x in dir(unreal) if 'component' in x.lower() and ('static' in x.lower() or 'scene' in x.lower() or 'actor' in x.lower())])
unreal.log('PROBE_ISM_METHODS=%s' % [x for x in dir(unreal.InstancedStaticMeshComponent) if 'instance' in x.lower() or 'static' in x.lower() or 'mesh' in x.lower()])
unreal.log('PROBE_SUBOBJECT_TYPES=%s' % [x for x in dir(unreal) if 'subobject' in x.lower()])
unreal.log('PROBE_SUBOBJECT_SUBSYSTEM_METHODS=%s' % [x for x in dir(unreal.SubobjectDataSubsystem) if 'subobject' in x.lower() or 'component' in x.lower() or 'add' in x.lower()])
unreal.log('PROBE_SUBSYSTEM_ALL_METHODS=%s' % [x for x in dir(unreal.SubobjectDataSubsystem) if not x.startswith('_')])
unreal.log('PROBE_ADD_PARAMS=%s' % [x for x in dir(unreal.AddNewSubobjectParams) if not x.startswith('_')])
