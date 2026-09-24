import unreal

unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, -10000), unreal.Rotator())
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sub.k2_gather_subobject_data_for_instance(actor)
params = unreal.AddNewSubobjectParams()
params.parent_handle = handles[0]
params.new_class = unreal.InstancedStaticMeshComponent.static_class()
params.conform_transform_to_parent = False
result = sub.add_new_subobject(params)
unreal.log('ISM_RESULT=%s' % (result,))
components = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
unreal.log('ISM_COMPONENTS=%s' % components)
if components:
    comp = components[0]
    comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))
    transform = unreal.Transform(
        unreal.Vector(1, 2, 3),
        unreal.Rotator(0, 0, 0),
        unreal.Vector(1, 2, 3),
    )
    idx = comp.add_instance(transform)
    unreal.log('ISM_INSTANCE=%s count=%s' % (idx, comp.get_instance_count()))
unreal.EditorLevelLibrary.destroy_actor(actor)
