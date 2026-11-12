
def hiddenMarkovModels(roads, observed_traffic, traffic_probabilities):
    # Infer traffic states (low, medium, high) over time on observed roads.

    grouped_roads = groupByRoad(roads, observed_traffic)

    solutions = Viterbi(grouped_roads, traffic_probabilities)

    passToSearch(grouped_roads, solutions)



def groupByRoad(roads, observed_traffic):
    # Build the observation sequences

    grouped = {road : [] for road in roads}

    for traffic in observed_traffic:
        grouped[traffic.road].append(traffic)

    for road in grouped:
        grouped[road].sort(key=lambda obs: obs.observation_nr)

    return grouped



def Viterbi(grouped_roads, traffic_probabilities):
    states = ["Low", "Medium", "High"]
    solutions = {}

    for road, observations in grouped_roads.items():

        if len(observations) == 0:
            current_probs = traffic_probabilities["initial"].copy()
        else:
            # Step t = 0 (first observation)
            current_probs = {}
            first_obs = observations[0].traffic_observation
            for S in states:
                current_probs[S] = (traffic_probabilities["initial"][S] *
                                    traffic_probabilities["emission"][S][first_obs])

            total = sum(current_probs.values())
            for S in states:
                current_probs[S] /= total

            # Steps t = 1, 2, ... (subsequent observations)
            for obs_obj in observations[1:]:
                obs = obs_obj.traffic_observation
                new_probs = {}

                for S in states:
                    best_transition = max(
                        current_probs[prev_S] * traffic_probabilities["transition"][prev_S][S]
                        for prev_S in states
                    )
                    new_probs[S] = best_transition * traffic_probabilities["emission"][S][obs]

                total = sum(new_probs.values())
                for S in states:
                    new_probs[S] /= total

                current_probs = new_probs

        solutions[road] = current_probs

    return solutions



def passToSearch(grouped_roads, solutions):

    for road in grouped_roads:
        best_traffic = max(solutions[road], key=solutions[road].get)
        road.estimated_traffic = best_traffic
