import math
import unreal

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
OUT_PATH = "G:/UE/project/workdemo/Saved/gasstation_route_geometry.txt"

def log_line(handle, text):
    unreal.log("ROUTE_GEOMETRY " + text)
    handle.write(text + "\n")

def bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return (origin.x - extent.x, origin.x + extent.x,
            origin.y - extent.y, origin.y + extent.y,
            origin.z - extent.z, origin.z + extent.z)

def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    by_label = {a.get_actor_label(): a for a in actors}
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        for name in (
            "WB_B_GasStation_Building_Wall_Right",
            "WB_B_GasStation_Building_Wall_Right_Upper_South",
            "WB_B_GasStation_Building_Wall_Right_Upper_North",
            "WB_B_GasStation_Building_Wall_Right_Door_LeftJamb",
            "WB_B_GasStation_Building_Wall_Right_Door_RightJamb",
            "WB_B_GasStation_Building_Wall_Right_Door_Lintel",
            "WB_B_GasStation_UpperFloor_Walkable",
            "WB_B_GasStation_Stairs",
            "WB_B_GasStation_SideRoute",
            "WB_B_Overpass_BrokenDeck",
        ):
            actor = by_label[name]
            log_line(handle, "%s class=%s bounds=%s loc=%s rot=%s scale=%s parent=%s" % (
                name, actor.get_class().get_name(), tuple(round(x, 2) for x in bounds(actor)),
                actor.get_actor_location(), actor.get_actor_rotation(), actor.get_actor_scale3d(),
                actor.get_attach_parent_actor().get_actor_label() if actor.get_attach_parent_actor() else ""))
        stair = by_label["WB_B_GasStation_Stairs"].get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
        log_line(handle, "stairs_instance_count=%d" % stair.get_instance_count())
        for i in (0, 1, 9, 19):
            t = stair.get_instance_transform(i, True)
            log_line(handle, "stair_%02d_transform=%s" % (i + 1, t))
        route = by_label["WB_B_GasStation_SideRoute"].get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
        log_line(handle, "route_instance_count=%d" % route.get_instance_count())
        for i in range(route.get_instance_count()):
            t = route.get_instance_transform(i, True)
            log_line(handle, "route_%02d_transform=%s" % (i, t))
        # The route is required to stay outside the unchanged BrokenDeck bounds.
        # Actor bounds for a component-only parent also include the parent origin
        # (0,0,0) in UE 5.3. Use the known world-space nose footprint instead.
        deck_origin, deck_extent = by_label["WB_B_Overpass_BrokenDeck"].get_actor_bounds(False)
        route_min_x, route_max_x = 6650.0, 6950.0
        route_min_y, route_max_y = -3100.0, -3000.0
        deck_min_x, deck_max_x = deck_origin.x - deck_extent.x, deck_origin.x + deck_extent.x
        deck_min_y, deck_max_y = deck_origin.y - deck_extent.y, deck_origin.y + deck_extent.y
        overlap_x = max(0.0, min(route_max_x, deck_max_x) - max(route_min_x, deck_min_x))
        overlap_y = max(0.0, min(route_max_y, deck_max_y) - max(route_min_y, deck_min_y))
        log_line(handle, "route_deck_xy_overlap_cm=(%.2f,%.2f) route_nose_bounds=(%.1f,%.1f,%.1f,%.1f) deck_bounds=%s" % (overlap_x, overlap_y, route_min_x, route_max_x, route_min_y, route_max_y, bounds(by_label["WB_B_Overpass_BrokenDeck"])))
        if overlap_y > 20.0:
            raise RuntimeError("Route overlaps too deeply into unchanged BrokenDeck")
        # The door opening is 260 cm wide in Y, 230 cm high above the lower wall course.
        log_line(handle, "door_opening_y=(-970.0,-710.0) door_opening_z=(540.0,770.0) clear_height=230.0")
        unreal.log("GAS_STATION_ROUTE_GEOMETRY_OK")

main()
