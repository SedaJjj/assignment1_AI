import csv, json
from bayesian_reasoning import bayesian_reasoning
from hidden_Markov_Models import hiddenMarkovModels
from search import prepareSearch, search
from constraint_based_allocation import allocate_responders
from validation import validate_plan

class City:
    def __init__(self, nodes, roads):
        self.nodes = nodes
        self.roads = roads

class Node:
    def __init__(self, node):
        self.id   = node["id"]
        self.name = node["name"]
        self.x    = int(node["x"])
        self.y    = int(node["y"])
        self.type = node["type"]

class Road:
    def __init__(self, road, nodes):
        for node in nodes:
            if node.id == road["from"]:
                self.fromNode = node
            if node.id == road["to"]:
                self.toNode   = node

        self.distance  = int(road["distance"])
        self.road_type = road["road_type"]
        self.speed     = int(road["speed"])

        self.estimated_state   = None
        self.estimated_traffic = None
        self.travel_time       = None

class Responder:
    def __init__(self, responder, nodes):
        self.responder_id         = responder[0]
        self.type                 = responder[1]

        for node in nodes:
            if node.id == responder[2]:
                self.start_location = node

        self.capabilities = [cap.strip() for cap in responder[3].split(";")]
        self.availability         = responder[4]
        self.time_until_available = int(responder[5])

        self.current_location = self.start_location
        self.available_time = 0 if self.availability == "Available" else int(responder[5])


class Incident:
    def __init__(self, incident, nodes):
        self.incident_id         = incident[0]

        for node in nodes:
            if node.id == incident[1]:
                self.location = node

        self.priority            = incident[2]
        self.deadline            = int(incident[3])
        self.required_capability = incident[4]
        self.timestamp           = int(incident[5])
        self.time_required       = int(incident[6])

class ObservedTraffic:
    def __init__(self, observed_traffic, nodes, roads):
        self.observation_nr      = int(observed_traffic[0])

        for node in nodes:
            if   node.id == observed_traffic[1]:
                self.fromNode = node
            elif node.id == observed_traffic[2]:
                self.toNode   = node

        for road in roads:
            if self.fromNode == road.fromNode and self.toNode == road.toNode:
                self.road = road
                break

        self.traffic_observation = observed_traffic[3]

class RoadReport:
    def __init__(self, road_report, nodes, roads):
        for node in nodes:
            if node.id == road_report[0]:
                self.fromNode = node
            elif node.id == road_report[1]:
                self.toNode   = node

        for road in roads:
            if self.fromNode == road.fromNode and self.toNode == road.toNode:
                self.road = road
                break

        self.weather         = road_report[2]
        self.source          = road_report[3]
        self.reported_status = road_report[4]


# The final system should use the provided input data to create a feasible emergency response plan.
# The plan should
#   assign responders to incidents,
#   determine suitable routes through the city graph,
#   and take into account
#       responder availability,
#       required capabilities,
#       incident deadlines,
#       and uncertain road conditions.

def getFileContent(fileName):
    # get content of a file
    file = open(fileName, "r")
    content = file.read()
    file.close()

    return content


with open("city_graph.json", "r") as file:
    reader = json.load(file)

    nodes = []

    for node in reader["nodes"]:
        nodes.append(Node(node))
    roads = []

    for road in reader["roads"]:
        roads.append(Road(road, nodes))

    city_graph = City(nodes,roads)

with open("responders.csv", "r") as file:
    # responders = a list of the emergency responders that must be assigned to incidents
    reader = csv.reader(file)

    responders = []

    next(reader)
    for row in reader:
        responders.append(Responder(row, nodes))

with open("incidents.csv", "r") as file:
    # incidents = a list of the incident stream
    reader = csv.reader(file)

    incidents = []

    next(reader)
    for row in reader:
        incidents.append(Incident(row, nodes))

with open("observed_traffic.csv", "r") as file:
    # observed_traffic = a list of historic traffic data on some roads in the city
    reader = csv.reader(file)
    observed_traffic = []

    next(reader)
    for row in reader:
        if not row:
            continue
        observed_traffic.append(ObservedTraffic(row, nodes, roads))

with open("road_reports.csv", "r") as file:
    # road_reports = a list of noisy reports about road conditions
    reader = csv.reader(file)

    road_reports = []

    next(reader)
    for row in reader:
        if not row:
            continue
        road_reports.append(RoadReport(row, nodes, roads))

with open("road_probabilities.json", "r") as file:
    # road_probabilities = a dictionary of the conditional probability tables with keys
    #   weather_prior{clear, rain, storm}
    #   road_status_given_weather{
    #       clear{open,congested,blocked}
    #       rain{open,congested,blocked}
    #       storm{open,congested,blocked}}
    #   citizen_report{
    #       open{open,congested,blocked}
    #       congested{open,congested,blocked}
    #       blocked{open,congested,blocked}}
    #   police_report{
    #       open{open,congested,blocked}
    #       congested{open,congested,blocked}
    #       blocked{open,congested,blocked}}
    #   sensor_report{
    #       open{open,congested,blocked}
    #       congested{open,congested,blocked}
    #       blocked{open,congested,blocked}}

    road_probabilities = json.load(file)

with open("traffic_probabilities.json", "r") as file:
    # traffic_probabilities = a dictionary of the initial, transition, emission probability with keys
    #   initial{low,medium,high}
    #   transition{
    #       low{low,medium,high}
    #       medium{low,medium,high}
    #       high{low,medium,high}}
    #   emission{
    #       low{low,medium,high}
    #       medium{low,medium,high}
    #       high{low,medium,high}}

    traffic_probabilities = json.load(file)




bayesian_reasoning(roads, road_reports, road_probabilities)

hiddenMarkovModels(roads, observed_traffic, traffic_probabilities)

adjacency_list, max_speed = prepareSearch(city_graph)

plan, handled_incidents = allocate_responders(incidents, responders, adjacency_list, max_speed)

with open("plan.json", "w") as file:
    json.dump(plan, file, indent=4)

num_handled = len(handled_incidents)
total_incidents = len(incidents)
responders_used = len(set(item["responder_id"] for item in plan))

if num_handled > 0:
    avg_response_time = sum(item[4] for item in handled_incidents) / num_handled
else:
    avg_response_time = 0.0

deadlines_met_pct = (num_handled / total_incidents) * 100 if total_incidents > 0 else 0.0

with open("statistics.txt", "w") as file:
    file.write("System statistics:\n\n")
    file.write(f"* {num_handled} incidents handled\n")
    file.write(f"* {responders_used} responders used\n")
    file.write(f"* Average response time: {avg_response_time:.1f} s\n")
    file.write(f"* Deadlines met: {deadlines_met_pct:.1f}%\n")

validate_plan(plan, city_graph, responders, incidents)