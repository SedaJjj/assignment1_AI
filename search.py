import math


def prepareSearch(city_graph):
    # Called once in run.py after Bayesian & HMM

    adjacency_list = createAdjecencyList(city_graph)

    defineEdgeCost(city_graph)

    max_speed = max(road.speed for road in city_graph.roads)

    return adjacency_list, max_speed


def search(start_node, goal_node, adjacency_list, max_speed):
    # Called whenever you need the fastest path between two nodes
    return aStarSearch(start_node, goal_node, adjacency_list, max_speed)


def createAdjecencyList(city):
    # Convert roads into a dictionary mapping neighbors

    adjecency_list = {node : [] for node in city.nodes}

    for node in city.nodes:
        for road in city.roads:
            if road.fromNode == node:
                adjecency_list[node].append(road)

    return adjecency_list




def defineEdgeCost(city):
    # Define Edge Cost (Travel Time)

    state_mult = {"Open" : 1.0, "Congested" : 1.5}
    traffic_mult = {"Low" : 1.0, "Medium" : 1.2, "High" : 1.5}

    for road in city.roads:
        if road.estimated_state == "Blocked":
            road.travel_time = None
        else:
            base_time = road.distance/road.speed
            road.travel_time = (base_time * state_mult[road.estimated_state]
                                * traffic_mult[road.estimated_traffic])





def heuristic(node_a, node_b, max_speed):
    # A^* Search

    dist = math.sqrt((node_a.x - node_b.x) ** 2 + (node_a.y - node_b.y) ** 2)
    return dist / max_speed


def aStarSearch(start_node, goal_node, adjacency_list, max_speed):
    open_set = [start_node]
    g_score = {start_node : 0.0}
    f_score = {start_node: heuristic(start_node, goal_node, max_speed)}
    came_from = {}

    while len(open_set) > 0:
        current = min(open_set, key=lambda n: f_score.get(n, float('inf')))

        if current == goal_node:
            path = [current.id]

            while current in came_from:
                current = came_from[current]
                path.append(current.id)

            path.reverse()
            return path, g_score[goal_node]

        open_set.remove(current)

        for road in adjacency_list[current]:
            if road.estimated_state == ("Blocked"):
                continue
            neighbor = road.toNode
            tentative_g = g_score[current] + road.travel_time

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal_node, max_speed)

                if neighbor not in open_set:
                    open_set.append(neighbor)

    return None, float('inf')

