import csv, json

class Responder:
    def __init__(self, responder):
        self.responder_id         = responder[0]
        self.type                 = responder[1]
        self.start_location       = responder[2]
        self.capabilities         = responder[3]
        self.availability         = responder[4]
        self.time_until_available = responder[5]

class Incident:
    def __init__(self, incident):
        self.incident_id         = incident[0]
        self.location            = incident[1]
        self.priority            = incident[2]
        self.deadline            = incident[3]
        self.required_capability = incident[4]
        self.timestamp           = incident[5]
        self.time_required       = incident[6]

class ObservedTraffic:
    def __init__(self, observed_traffic):
        self.observation_nr      = observed_traffic[0]
        self.fromNode            = observed_traffic[1]
        self.toNode              = observed_traffic[2]
        self.traffic_observation = observed_traffic[3]

class RoadReport:
    def __init__(self, road_report):
        self.fromNode        = road_report[0]
        self.toNode          = road_report[1]
        self.weather         = road_report[2]
        self.source          = road_report[3]
        self.reported_status = road_report[4]


# The final system should use the provided input data to create a feasible emergency response plan. The
# plan should assign responders to incidents, determine suitable routes through the city graph, and take into
# account responder availability, required capabilities, incident deadlines, and uncertain road conditions.

def getFileContent(fileName):
    file = open(fileName, "r")
    content = file.read()
    file.close()

    return content


with open("responders.csv", "r") as file:
    reader = csv.reader(file)

    responders = []

    for row in reader:
        responders.append(Responder(row))
    responders.pop(0)

with open("incidents.csv", "r") as file:
    reader = csv.reader(file)

    incidents = []

    for row in reader:
        incidents.append(Incident(row))
    incidents.pop(0)

with open("observed_traffic.csv", "r") as file:
    reader = csv.reader(file)
    observed_traffic = []

    for row in reader:
        if not row:
            continue
        observed_traffic.append(ObservedTraffic(row))
    observed_traffic.pop(0)

with open("road_reports.csv", "r") as file:
    reader = csv.reader(file)

    road_reports = []

    for row in reader:
        if not row:
            continue
        road_reports.append(RoadReport(row))
    road_reports.pop(0)

with open("city_graph.json", "r") as file:
    city_graph = json.load(file)
    nodes = city_graph["nodes"]
    roads = city_graph["roads"]

with open("road_probabilities.json", "r") as file:
    road_probabilities = json.load(file)

with open("traffic_probabilities.json", "r") as file:
    traffic_probabilities = json.load(file)



# Running this file for a scenario generates two output files:
#   plan.json and
#   statistics.txt

# The file plan.json should contain a list of responder–incident assignments. Each assignment should include:
# • the assigned responder;
# • the incident being handled;
# • the selected route through the graph;
# • the simulation time at which the responder starts the assignment.
# Use the following JSON structure:
# [
#   {
#       " responder_id ": " R1 " ,
#       " incident_id ": " I1 " ,
#       " path ": [" N1 " , " H1 " , " N2 "] ,
#       " time ": 0
#   } ,
#   {
#       " responder_id ": " R2 " ,
#       " incident_id ": " I2 " ,
#       " path ": [" H1 " , " N2 "] ,
#       " time ": 10
#   }
# ]
# The generated plan must be valid. You are responsible for defining the checks needed to establish whether
# routes and assignments are valid under the assignment’s operational constraints. Identify possible errors,
# test for them, and explain any limitations of your validation.

file = open("plan.json", "w")

responder_incident = {}

# file.write("Hallo wereld!")
file.close()

# The file statistics.txt should summarize the system’s performance and include at least:
# • number of incidents handled;
# • number of responders used;
# • average response time;
# • percentage of deadlines met.
# Explain how you calculate these statistics, including how you treat incidents that remain unhandled. Clearly
# state the time units used.
# An example of the expected output is:
# System statistics :
#
# * 5 incidents handled
# * 2 responders used
# * Average response time : 65.7 s
# * Deadlines met : 100.0%



file = open("statistics.txt", "w")
#file.write("Hallo wereld!")
file.close()