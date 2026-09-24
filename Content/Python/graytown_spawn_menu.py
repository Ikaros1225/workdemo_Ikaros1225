"""Editor-only spawn selector for the Graytown whitebox test map.

The menu changes the current UnrealEdEngine Play URL only. It does not move,
duplicate, or edit any PlayerStart or whitebox actor.
"""

import unreal


MENU_OWNER = "GraytownWhiteboxSpawnSelector"
PARENT_MENU = "LevelEditor.MainMenu.Tools"
SUBMENU_NAME = "GraytownWhiteboxSpawnSelector.SubMenu"

SPAWN_POINTS = (
    ("荒原教学区", "WBSpawn_SouthWasteland"),
    ("加油站外场", "WBSpawn_GasOutside"),
    ("加油站一楼", "WBSpawn_GasGroundFloor"),
    ("加油站二楼", "WBSpawn_GasUpperFloor"),
    ("倒塌高架", "WBSpawn_CollapsedOverpass"),
    ("C1 街区", "WBSpawn_C1"),
    ("蚀雾硬锁前", "WBSpawn_HardLockApproach"),
    ("C2 街区", "WBSpawn_C2"),
    ("旧矿井场地", "WBSpawn_MineYard"),
    ("旧矿井洞内", "WBSpawn_MineCave"),
    ("Boss 场", "WBSpawn_BossArena"),
)


def _editor_engine():
    """Return the live UnrealEdEngine object used by the current editor."""
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if not subsystem:
        return None
    return subsystem.get_outer()


def _selected_tag():
    engine = _editor_engine()
    if not engine:
        return ""
    try:
        play_url = str(engine.get_editor_property("InEditorGameURLOptions"))
    except Exception:
        return ""
    if play_url.startswith("#"):
        return play_url[1:].split("?", 1)[0]
    # DefaultEngine.ini keeps the original wasteland start as the fallback.
    return "WBSpawn_SouthWasteland"


def _set_spawn_tag(start_tag):
    engine = _editor_engine()
    if not engine:
        unreal.log_warning("Could not find the live UnrealEdEngine; spawn selection was not changed.")
        return

    # A URL fragment becomes FURL::Portal, which AGameModeBase uses to match
    # PlayerStart.PlayerStartTag. This is intentionally session-only.
    engine.set_editor_property("InEditorGameURLOptions", "#" + start_tag)
    unreal.log("箱庭测试出生点已选择: %s (%s)" % (start_tag, _display_name(start_tag)))


def _display_name(start_tag):
    for label, tag in SPAWN_POINTS:
        if tag == start_tag:
            return label
    return start_tag


@unreal.uclass()
class GraytownSpawnMenuEntry(unreal.ToolMenuEntryScript):
    spawn_tag = unreal.uproperty(str)
    display_name = unreal.uproperty(str)

    @unreal.ufunction(override=True)
    def get_label(self, context):
        return self.display_name

    @unreal.ufunction(override=True)
    def get_tool_tip(self, context):
        return "选择 %s，随后点击 Play 从该区域出生。" % self.display_name

    @unreal.ufunction(override=True)
    def get_check_state(self, context):
        if _selected_tag() == self.spawn_tag:
            return unreal.CheckBoxState.CHECKED
        return unreal.CheckBoxState.UNCHECKED

    @unreal.ufunction(override=True)
    def execute(self, context):
        _set_spawn_tag(self.spawn_tag)


def _make_entry(menu, label, start_tag):
    entry = GraytownSpawnMenuEntry()
    entry.spawn_tag = start_tag
    entry.display_name = label
    entry.init_entry(
        MENU_OWNER,
        menu.menu_name,
        "SpawnPoints",
        "Spawn_" + start_tag,
        label,
        "选择 %s，随后点击 Play 从该区域出生。" % label,
    )
    menu.add_menu_entry_object(entry)


def setup_menu():
    tool_menus = unreal.ToolMenus.get()
    tool_menus.unregister_owner_by_name(MENU_OWNER)

    parent = tool_menus.extend_menu(PARENT_MENU)
    submenu = parent.add_sub_menu(
        owner=MENU_OWNER,
        section_name="Graytown",
        name=SUBMENU_NAME,
        label="箱庭测试出生点",
        tool_tip="选择点击 Play 时使用的测试出生区域。",
    )
    submenu.add_section("SpawnPoints", "测试出生区域")
    for label, start_tag in SPAWN_POINTS:
        _make_entry(submenu, label, start_tag)

    tool_menus.refresh_all_widgets()
    unreal.log("箱庭测试出生点菜单已加载（%d 个区域）" % len(SPAWN_POINTS))


def run():
    """Register the menu; safe to call again after editing this file."""
    setup_menu()


run()
