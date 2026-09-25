import unreal
MAP_PATH='/Game/ThirdPerson/Maps/ThirdPersonMap'
def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
    targets=[a for a in actors if a.get_actor_label().startswith('WB_B_GasStation_') and ('Stairs' in a.get_actor_label() or 'SideRoute' in a.get_actor_label() or 'UpperFloor' in a.get_actor_label() or 'Wall_Right_' in a.get_actor_label())]
    if not targets: raise RuntimeError('No generated route actors found')
    for actor in targets:
        for component in actor.get_components_by_class(unreal.PrimitiveComponent):
            if not isinstance(component, (unreal.StaticMeshComponent, unreal.InstancedStaticMeshComponent)):
                continue
            enabled=component.get_collision_enabled()
            if enabled != unreal.CollisionEnabled.QUERY_AND_PHYSICS:
                raise RuntimeError('Collision not enabled for %s/%s: %s' % (actor.get_actor_label(),component.get_name(),enabled))
            unreal.log('ROUTE_COLLISION_OK actor=%s component=%s collision=%s' % (actor.get_actor_label(),component.get_name(),enabled))
    unreal.log('GAS_STATION_ROUTE_COLLISION_VALIDATED actors=%d' % len(targets))
main()
