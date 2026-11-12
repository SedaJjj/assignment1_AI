
def bayesian_reasoning(roads, road_reports, road_probabilities):
    # Estimate the state (open, congested or blocked) of each road using
    # weather and noisy reports from road_reports and road_probabilities.

    grouped_roads = groupByRoad(roads, road_reports)

    solutions = bayesRule(grouped_roads, road_probabilities)

    passToSearch(grouped_roads, solutions)



def groupByRoad(roads, road_reports):
    # Group the observations.

    grouped = {road : [] for road in roads}
    for road_report in road_reports:
        grouped[road_report.road].append(road_report)
    return grouped



def bayesRule(grouped_roads, road_probabilities):
    # Apply Bayes' Rule and normalize

    states = ["Open", "Congested", "Blocked"]
    weather = ["Clear", "Rain", "Storm"]
    sources = {"Citizen": "citizen_report", "Police": "police_report", "Sensor": "sensor_report"}
    solutions = {}

    for road, reports in grouped_roads.items():
        solutions[road] = {}

        for S in states:
            if len(reports) >= 1:
                W = reports[0].weather
                prior = road_probabilities["road_status_given_weather"][W][S]
            else:
                prior = 0
                for w in weather:
                    prior += (road_probabilities["road_status_given_weather"][w][S]
                              * road_probabilities["weather_prior"][w])

            product = 1
            for road_report in reports:
                repstatus = road_report.reported_status
                product *= road_probabilities[sources[road_report.source]][S][repstatus]

            solutions[road][S] = prior * product

        total_score = sum(solutions[road].values())
        for S in states:
            solutions[road][S] = solutions[road][S]/total_score

    return solutions



def passToSearch(grouped_roads, solutions):
    # Pass to Search: Pick the state with the highest probability.

    for road in grouped_roads:
        best_state = max(solutions[road], key=solutions[road].get)
        road.estimated_state = best_state