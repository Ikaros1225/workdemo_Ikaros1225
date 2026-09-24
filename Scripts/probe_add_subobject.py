import unreal

unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, -10000), unreal.Rotator())
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
unreal.log('ADD_PROBE_SUB=%s' % sub)
handles = sub.k2_gather_subobject_data_for_instance(actor)
unreal.log('ADD_PROBE_HANDLES=%s' % len(handles))
for idx, handle in enumerate(handles):
    unreal.log('ADD_PROBE_HANDLE_%d=%s' % (idx, handle))
    try:
        data = sub.k2_find_subobject_data_from_handle(handle)
        unreal.log('ADD_PROBE_DATA_%d=%s' % (idx, data))
        unreal.log('ADD_PROBE_DATA_METHODS_%d=%s' % (idx, [x for x in dir(data) if not x.startswith('_')]))
    except Exception as exc:
        unreal.log_error('ADD_PROBE_DATA_ERROR_%d=%s' % (idx, exc))

try:
    params = unreal.AddNewSubobjectParams()
    params.parent_handle = handles[0]
    params.new_class = unreal.StaticMeshComponent.static_class()
    params.conform_transform_to_parent = False
    result = sub.add_new_subobject(params)
    unreal.log('ADD_PROBE_RESULT=%s' % (result,))
    new_data = sub.k2_find_subobject_data_from_handle(result[0])
    unreal.log('ADD_PROBE_NEW_DATA_METHODS=%s' % [x for x in dir(new_data) if not x.startswith('_')])
    for prop in ('weak_object_ptr', 'handle', 'parent_object_handle', 'children_handles'):
        try:
            unreal.log('ADD_PROBE_NEW_DATA_PROP_%s=%s' % (prop, new_data.get_editor_property(prop)))
        except Exception as exc:
            unreal.log_error('ADD_PROBE_NEW_DATA_PROP_%s_ERROR=%s' % (prop, exc))
    for method in ('get_object', 'get_object_for_instance', 'get_component_template'):
        try:
            unreal.log('ADD_PROBE_NEW_DATA_%s=%s' % (method, getattr(new_data, method)()))
        except Exception as exc:
            unreal.log_error('ADD_PROBE_NEW_DATA_%s_ERROR=%s' % (method, exc))
    unreal.log('ADD_PROBE_ACTOR_COMPONENTS=%s' % actor.get_components_by_class(unreal.StaticMeshComponent))
except Exception as exc:
    unreal.log_error('ADD_PROBE_ERROR=%s' % exc)

unreal.EditorLevelLibrary.destroy_actor(actor)
