import unreal

unreal.log('HAS_INSTANCED_STATIC_MESH_ACTOR=%s' % hasattr(unreal, 'InstancedStaticMeshActor'))
unreal.log('ACTOR_CLASSES=%s' % [x for x in dir(unreal) if 'Instanced' in x or 'StaticMeshActor' in x])
