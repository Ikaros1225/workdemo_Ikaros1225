import unreal
world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for actor in sorted(actors, key=lambda a: a.get_actor_label()):
    if actor.get_actor_label().startswith('WB_D_MineOffice'):
        unreal.log('MAIN_OFFICE_LABEL=%s class=%s' % (actor.get_actor_label(), actor.get_class().get_name()))
