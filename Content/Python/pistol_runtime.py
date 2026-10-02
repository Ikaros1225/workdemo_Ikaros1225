"""PIE-only pistol interaction prototype.

This intentionally runs only in the editor's PIE game world. It does not
write actors or geometry into the map package.
"""

import unreal
import builtins
import math
import time


TICK_HANDLE = None
STATE = {
    "world": None,
    "pickup": None,
    "character": None,
    "controller": None,
    "notice": None,
    "notice_text": None,
    "notice_class": None,
    "aim_camera": None,
    "aim_mesh": None,
    "camera_manager": None,
    "original_fov": None,
    "original_view_target": None,
    "weapon_actor": None,
    "world_key": None,
    "has_pistol": False,
    "aiming": False,
    "last_prompt": None,
    "prompt_until": 0.0,
    "pickup_destroy_at": 0.0,
    "pickup_destroy_actor": None,
    "camera_component": None,
    "spring_arm": None,
    "original_arm_length": None,
    "last_probe_log": 0.0,
    "runtime_logged": False,
}


def _valid(obj):
    try:
        return obj is not None and unreal.SystemLibrary.is_valid(obj)
    except Exception:
        return obj is not None


def _game_world():
    try:
        subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = subsystem.get_game_world() if subsystem else None
        if _valid(world):
            return world
        # World-partition PIE can expose the game world through PIE-worlds
        # before get_game_world() is updated.
        for owner in (subsystem, unreal.EditorLevelLibrary):
            if owner is None:
                continue
            try:
                worlds = owner.get_pie_worlds()
                for candidate in worlds or []:
                    if _valid(candidate):
                        return candidate
            except Exception:
                pass
    except Exception:
        pass
    return None


def _key(name):
    key = unreal.Key()
    key.set_editor_property("key_name", unreal.Name(name))
    return key


F_KEY = _key("F")
RMB_KEY = _key("RightMouseButton")
LMB_KEY = _key("LeftMouseButton")


def _find_actor_by_label(world, label):
    if not _valid(world):
        return None
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        try:
            if actor.get_actor_label() == label or actor.get_name().startswith(label):
                return actor
        except Exception:
            pass
    return None


def _find_character(world):
    try:
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        character = unreal.GameplayStatics.get_player_character(world, 0)
        if _valid(pc) and _valid(character):
            return pc, character
    except Exception:
        pass
    # Fallback for PIE sessions where PlayerController is not registered yet.
    try:
        for pawn in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Pawn):
            try:
                if pawn.is_player_controlled():
                    controller = pawn.get_controller()
                    if _valid(controller):
                        return controller, pawn
            except Exception:
                pass
    except Exception:
        pass
    return None, None


def _show_text(world, message, duration=0.0):
    # PrintText is a real viewport message and survives even if the existing
    # WBP_Notice has no discoverable named TextBlock through Python.
    unreal.SystemLibrary.print_string(
        world,
        message,
        True,
        False,
        unreal.LinearColor(1.0, 0.88, 0.55, 1.0),
        duration,
        unreal.Name("PistolRuntimeNotice"),
    )


def _ensure_notice(world, controller):
    """Create the existing notice widget once per PIE world when possible."""
    notice = STATE.get("notice")
    if _valid(notice):
        return notice
    try:
        asset = unreal.load_asset("/Game/ThirdPerson/Blueprints/WBP_Notice")
        notice_class = asset.generated_class() if asset else None
        if notice_class is None:
            return None
        notice = unreal.new_object(notice_class, outer=controller)
        notice.set_owning_player(controller)
        notice.add_to_viewport(100)
        STATE["notice"] = notice
        STATE["notice_class"] = notice_class
        try:
            candidate = notice.get_editor_property("NoticeText")
            if _valid(candidate) and hasattr(candidate, "set_text"):
                STATE["notice_text"] = candidate
        except Exception:
            pass
        return notice
    except Exception as exc:
        unreal.log_warning("PISTOL_RUNTIME_NOTICE_WIDGET_UNAVAILABLE %s" % exc)
        return None


def _set_notice_widget(world, controller, message):
    notice = _ensure_notice(world, controller)
    if not _valid(notice):
        return False
    text_value = unreal.TextLibrary.conv_string_to_text(message)
    text_widget = STATE.get("notice_text")
    try:
        if _valid(text_widget) and hasattr(text_widget, "set_text"):
            text_widget.set_text(text_value)
            text_widget.set_visibility(unreal.ESlateVisibility.VISIBLE)
            return True
        notice.set_editor_property("NoticeText", text_value)
        return True
    except Exception as exc:
        unreal.log_warning("PISTOL_RUNTIME_NOTICE_WIDGET_SET_FAILED %s" % exc)
        return False


def _view_ray(controller, length):
    location, rotation = controller.get_player_view_point()
    return location, location + _forward_vector(rotation) * length, rotation


def _forward_vector(rotation):
    pitch = math.radians(rotation.get_editor_property("pitch"))
    yaw = math.radians(rotation.get_editor_property("yaw"))
    return unreal.Vector(math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))


def _trace(world, start, end, ignored):
    try:
        channel = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
    except Exception:
        channel = unreal.TraceTypeQuery(0)
    try:
        return unreal.SystemLibrary.line_trace_single(
            world,
            start,
            end,
            channel,
            True,
            ignored,
            unreal.DrawDebugTrace.NONE,
            True,
            unreal.LinearColor(1, 0, 0, 1),
            unreal.LinearColor(0, 1, 0, 1),
            0.05,
        )
    except Exception as exc:
        unreal.log_warning("PISTOL_RUNTIME_TRACE_FAILED %s" % exc)
        return None


def _hit_actor(hit):
    if hit is None:
        return None
    try:
        data = hit.to_tuple()
        actor = data[9] if len(data) > 9 else None
        return actor if _valid(actor) else None
    except Exception:
        return None


def _notice(world, message, seconds=0.0):
    now = unreal.SystemLibrary.get_game_time_in_seconds(world)
    if STATE.get("last_prompt") == message and seconds <= 0.0 and now < STATE.get("prompt_until", 0.0):
        return
    display_time = seconds if seconds > 0.0 else 0.85
    controller = STATE.get("controller")
    widget_ok = _valid(controller) and _set_notice_widget(world, controller, message)
    if not widget_ok:
        _show_text(world, message, display_time)
    STATE["last_prompt"] = message
    STATE["prompt_until"] = now + (seconds if seconds > 0.0 else 0.6)


def _hide_notice(world):
    notice = STATE.get("notice")
    if _valid(notice):
        try:
            text_widget = STATE.get("notice_text")
            if _valid(text_widget) and hasattr(text_widget, "set_text"):
                text_widget.set_text(unreal.TextLibrary.conv_string_to_text(""))
                text_widget.set_visibility(unreal.ESlateVisibility.HIDDEN)
            else:
                notice.set_editor_property("NoticeText", unreal.TextLibrary.conv_string_to_text(""))
        except Exception:
            pass
    if STATE.get("last_prompt") is not None:
        _show_text(world, "", 0.01)
    STATE["last_prompt"] = None
    STATE["prompt_until"] = 0.0


def _destroy_after_pickup(actor):
    if _valid(actor):
        try:
            actor.destroy_actor()
        except Exception:
            pass
    STATE["pickup"] = None


def _schedule_destroy(world, actor):
    # A short one-shot timer is attached to a transient Python UObject. The
    # editor tick callback remains alive for the PIE session.
    STATE["pickup_destroy_at"] = unreal.SystemLibrary.get_game_time_in_seconds(world) + 2.0
    STATE["pickup_destroy_actor"] = actor


def _spawn_pie_actor(world, class_path):
    """Use UE's runtime Summon command so the actor belongs to the PIE world."""
    try:
        expected_class = unreal.load_class(None, class_path)
        expected_path = expected_class.get_path_name() if expected_class else None
        before = set(a.get_path_name() for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
        summon_path = "CameraActor" if class_path == "/Script/Engine.CameraActor" else class_path
        unreal.SystemLibrary.execute_console_command(world, "Summon " + summon_path)
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            try:
                actual_class = actor.get_class().get_path_name()
                if actor.get_path_name() not in before and actual_class == expected_path:
                    return actor
            except Exception:
                pass
    except Exception as exc:
        unreal.log_warning("PISTOL_RUNTIME_SPAWN_FAILED %s: %s" % (class_path, exc))
    return None


def _ensure_weapon_copy(world, original):
    weapon = STATE.get("weapon_actor")
    if _valid(weapon):
        return weapon
    weapon = _spawn_pie_actor(
        world,
        "/Game/Weapons_Free/Meshes/Actors/AC_pistol_001.AC_pistol_001_C",
    )
    if _valid(weapon):
        STATE["weapon_actor"] = weapon
        weapon.set_actor_enable_collision(False)
        weapon.set_actor_hidden_in_game(True)
        if _valid(original):
            weapon.set_actor_location(original.get_actor_location(), False, True)
    return weapon


def _create_aim_camera(world, character, controller):
    """Create a transient first-person camera without changing the pawn camera.

    The pawn's third-person camera and spring arm remain untouched, so the
    original view can be restored exactly when RMB is released.
    """
    try:
        camera = STATE.get("aim_camera")
        if not _valid(camera):
            camera = _spawn_pie_actor(world, "/Script/Engine.CameraActor")
            STATE["aim_camera"] = camera
        if not _valid(camera):
            return None
        camera_component = camera.get_component_by_class(unreal.CameraComponent)
        if _valid(camera_component):
            camera_component.set_field_of_view(78.0)
        try:
            eye_location, eye_rotation = character.get_actor_eyes_view_point()
            camera.set_actor_location_and_rotation(eye_location, eye_rotation, False, True)
        except Exception:
            pass
        controller.set_view_target_with_blend(camera, 0.12)
        return camera
    except Exception as exc:
        unreal.log_warning("PISTOL_RUNTIME_AIM_CAMERA_UNAVAILABLE %s" % exc)
        return None


def _enter_aim(world, character, controller):
    if STATE["aiming"]:
        return
    # Save the exact third-person view target before switching cameras.
    if STATE.get("original_view_target") is None:
        try:
            STATE["original_view_target"] = controller.get_view_target()
        except Exception:
            STATE["original_view_target"] = character
    camera = _create_aim_camera(world, character, controller)
    if not _valid(camera):
        try:
            STATE["camera_manager"] = controller.get_editor_property("player_camera_manager")
        except Exception:
            return
    STATE["aiming"] = True
    try:
        mesh = character.get_editor_property("mesh")
        mesh.set_editor_property("owner_no_see", True)
    except Exception:
        pass
    camera = STATE.get("aim_camera")
    camera_component = STATE.get("camera_component")
    weapon = STATE.get("weapon_actor")
    if _valid(camera_component) and _valid(weapon):
        try:
            weapon.get_editor_property("root_component").attach_to_component(
                camera_component,
                unreal.Name("None"),
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                False,
            )
            weapon.set_actor_relative_location(unreal.Vector(42.0, 15.0, -16.0))
            weapon.set_actor_relative_rotation(unreal.Rotator(0.0, 0.0, 0.0))
            weapon.set_actor_hidden_in_game(False)
        except Exception as exc:
            unreal.log_warning("PISTOL_RUNTIME_WEAPON_CAMERA_ATTACH_FAILED %s" % exc)
    elif _valid(camera) and _valid(weapon):
        try:
            weapon.attach_to_actor(
                camera,
                unreal.Name("None"),
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                False,
            )
            weapon.set_actor_relative_location(unreal.Vector(42.0, 15.0, -16.0))
            weapon.set_actor_relative_rotation(unreal.Rotator(0.0, 0.0, 0.0))
            weapon.set_actor_hidden_in_game(False)
        except Exception as exc:
            unreal.log_warning("PISTOL_RUNTIME_WEAPON_ATTACH_FAILED %s" % exc)
    _notice(world, "瞄准模式", 0.8)


def _exit_aim(world, character, controller):
    if not STATE["aiming"]:
        return
    STATE["aiming"] = False
    try:
        mesh = character.get_editor_property("mesh")
        mesh.set_editor_property("owner_no_see", False)
    except Exception:
        pass
    camera = STATE.get("aim_camera")
    # Restore the view target that was active before RMB, including a custom
    # third-person camera. If it could not be saved, log a manual fallback.
    original_view_target = STATE.get("original_view_target")
    if not _valid(original_view_target):
        unreal.log_warning("PISTOL_RUNTIME_CAMERA_RESTORE_MANUAL_REQUIRED")
        original_view_target = character
    if _valid(controller) and _valid(original_view_target):
        try:
            controller.set_view_target_with_blend(original_view_target, 0.0)
        except Exception:
            try:
                controller.set_view_target_with_blend(original_view_target, 0.12)
            except Exception:
                unreal.log_warning("PISTOL_RUNTIME_CAMERA_RESTORE_FAILED")
    spring_arm = STATE.get("spring_arm")
    if _valid(spring_arm) and STATE.get("original_arm_length") is not None:
        try:
            spring_arm.set_editor_property("target_arm_length", STATE["original_arm_length"])
        except Exception:
            pass
    if _valid(STATE.get("weapon_actor")):
        try:
            STATE["weapon_actor"].set_actor_hidden_in_game(True)
            STATE["weapon_actor"].detach_from_actor()
        except Exception:
            pass
    if _valid(camera):
        if camera is STATE.get("aim_camera"):
            camera.destroy_actor()
    STATE["aim_camera"] = None
    STATE["original_view_target"] = None
    STATE["camera_component"] = None
    STATE["spring_arm"] = None
    STATE["original_arm_length"] = None


def _fire(world, character, controller):
    start, end, rotation = _view_ray(controller, 10000.0)
    hit = _trace(world, start, end, [character])
    target = _hit_actor(hit)
    if target is not None:
        try:
            unreal.GameplayStatics.apply_point_damage(
                target,
                25.0,
                _forward_vector(rotation),
                hit,
                controller,
                character,
                unreal.DamageType.static_class(),
            )
        except Exception as exc:
            unreal.log_warning("PISTOL_RUNTIME_DAMAGE_FAILED %s" % exc)
    try:
        unreal.SystemLibrary.draw_debug_line(world, start, end, unreal.LinearColor(1, 0.72, 0.25, 1), 0.08, 1.0)
    except Exception:
        pass


def _update_aim_camera(character, controller):
    camera = STATE.get("aim_camera")
    if not _valid(camera):
        return
    try:
        eye_location, _ = character.get_actor_eyes_view_point()
        control_rotation = controller.get_control_rotation()
        camera_location = eye_location + _forward_vector(control_rotation) * 8.0
        camera.set_actor_location_and_rotation(camera_location, control_rotation, False, True)
    except Exception as exc:
        unreal.log_warning("PISTOL_RUNTIME_CAMERA_UPDATE_FAILED %s" % exc)


def _reset_session():
    STATE.update({
        "world": None,
        "world_key": None,
        "pickup": None,
        "notice": None,
        "notice_text": None,
        "notice_class": None,
        "character": None,
        "controller": None,
        "aim_camera": None,
        "weapon_actor": None,
        "camera_manager": None,
        "original_fov": None,
        "original_view_target": None,
        "has_pistol": False,
        "aiming": False,
        "last_prompt": None,
        "prompt_until": 0.0,
        "pickup_destroy_at": 0.0,
        "pickup_destroy_actor": None,
        "camera_component": None,
        "spring_arm": None,
        "original_arm_length": None,
        "last_probe_log": 0.0,
        "runtime_logged": False,
    })


def _tick(delta_seconds):
    world = _game_world()
    if not _valid(world):
        now_monotonic = time.monotonic()
        if now_monotonic - STATE.get("last_probe_log", 0.0) > 3.0:
            unreal.log("PISTOL_RUNTIME_WAITING_FOR_PIE_WORLD")
            STATE["last_probe_log"] = now_monotonic
        if STATE.get("world_key") is not None:
            _reset_session()
        return

    try:
        world_key = world.get_path_name()
    except Exception:
        world_key = str(world)
    if world_key != STATE.get("world_key"):
        _reset_session()
        STATE["world"] = world
        STATE["world_key"] = world_key

    controller, character = _find_character(world)
    if not _valid(controller) or not _valid(character):
        now_monotonic = time.monotonic()
        if now_monotonic - STATE.get("last_probe_log", 0.0) > 3.0:
            unreal.log("PISTOL_RUNTIME_PIE_WORLD_READY_WAITING_FOR_PLAYER")
            STATE["last_probe_log"] = now_monotonic
        return
    STATE["world"] = world
    STATE["controller"] = controller
    STATE["character"] = character
    if not STATE.get("runtime_logged"):
        try:
            pickup_probe = _find_actor_by_label(world, "AC_pistol_001")
            unreal.log("PISTOL_RUNTIME_PIE_ACTIVE character=%s pickup=%s" % (character.get_name(), pickup_probe.get_name() if pickup_probe else "None"))
        except Exception:
            unreal.log("PISTOL_RUNTIME_PIE_ACTIVE")
        STATE["runtime_logged"] = True

    now = unreal.SystemLibrary.get_game_time_in_seconds(world)
    if STATE.get("last_prompt") is not None and STATE.get("prompt_until", 0.0) > 0.0 and now >= STATE["prompt_until"]:
        _hide_notice(world)
    destroy_at = STATE.get("pickup_destroy_at", 0.0)
    if destroy_at and now >= destroy_at:
        _destroy_after_pickup(STATE.get("pickup_destroy_actor"))
        STATE["pickup_destroy_at"] = 0.0
        STATE["pickup_destroy_actor"] = None

    if not STATE["has_pistol"]:
        pickup = STATE.get("pickup")
        if not _valid(pickup):
            pickup = _find_actor_by_label(world, "AC_pistol_001")
            STATE["pickup"] = pickup
        if _valid(pickup):
            start, end, _ = _view_ray(controller, 320.0)
            hit = _trace(world, start, end, [character])
            target = _hit_actor(hit)
            try:
                close_enough = character.get_horizontal_distance_to(pickup) <= 260.0 and abs(character.get_vertical_distance_to(pickup)) <= 180.0
            except Exception:
                close_enough = False
            if target is pickup or (close_enough and target is None):
                _notice(world, "按 F 拾取手枪", 0.0)
                if controller.was_input_key_just_pressed(F_KEY):
                    STATE["has_pistol"] = True
                    pickup.set_actor_hidden_in_game(True)
                    pickup.set_actor_enable_collision(False)
                    pickup.set_life_span(2.0)
                    _ensure_weapon_copy(world, pickup)
                    _schedule_destroy(world, pickup)
                    _notice(world, "已拾取手枪", 2.0)
            elif STATE.get("last_prompt") == "按 F 拾取手枪":
                _hide_notice(world)
        elif STATE.get("last_prompt") == "按 F 拾取手枪":
            _hide_notice(world)

    if STATE["has_pistol"]:
        if controller.is_input_key_down(RMB_KEY):
            _enter_aim(world, character, controller)
            _update_aim_camera(character, controller)
            if controller.was_input_key_just_pressed(LMB_KEY):
                _fire(world, character, controller)
        elif STATE["aiming"]:
            _exit_aim(world, character, controller)


def start():
    global TICK_HANDLE
    previous = getattr(builtins, "_graytown_pistol_runtime_tick", None)
    if previous is not None:
        try:
            unreal.unregister_slate_post_tick_callback(previous)
        except Exception:
            pass
    TICK_HANDLE = unreal.register_slate_post_tick_callback(_tick)
    builtins._graytown_pistol_runtime_tick = TICK_HANDLE
    unreal.log("PISTOL_RUNTIME_REGISTERED")


start()
