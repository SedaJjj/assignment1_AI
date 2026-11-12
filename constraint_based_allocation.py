from search import search

PRIORITY_WEIGHTS = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1
}


def allocate_responders(incidents, responders, adjacency_list, max_speed):
    # 1. Group incidents by timestamp so we only process incidents known at time t
    timestamps = sorted(list(set(inc.timestamp for inc in incidents)))

    plan = []
    handled_incidents = []
    unassigned_incidents = []

    for current_time in timestamps:
        # Add newly appeared incidents at current_time to our active queue
        new_incidents = [inc for inc in incidents if inc.timestamp == current_time]
        unassigned_incidents.extend(new_incidents)

        # Drop incidents whose deadline has already passed
        unassigned_incidents = [
            inc for inc in unassigned_incidents if inc.deadline >= current_time
        ]

        # Order variables (incidents) by highest priority first, then earliest deadline
        unassigned_incidents.sort(
            key=lambda inc: (-PRIORITY_WEIGHTS.get(inc.priority, 0), inc.deadline)
        )

        # 2. Build the domain for each incident (valid responders & their routes)
        domains = {}
        for inc in unassigned_incidents:
            domains[inc] = []
            for resp in responders:
                # Hard Constraint 1: Capability match
                if inc.required_capability not in resp.capabilities:
                    continue

                # Responder can start either at current_time, or when they finish their current job
                start_time = max(current_time, resp.available_time)

                # Hard Constraint 2: Reachability (find fastest path via A*)
                path, travel_time = search(
                    resp.current_location, inc.location, adjacency_list, max_speed
                )
                if path is None:
                    continue

                arrival_time = start_time + travel_time

                # Hard Constraint 3: Deadline must be met upon arrival
                if arrival_time <= inc.deadline:
                    response_time = arrival_time - inc.timestamp
                    domains[inc].append((resp, path, start_time, arrival_time, response_time))

        # 3. Solve CSP for current batch using Backtracking Search
        best_assignment = solve_csp_backtracking(unassigned_incidents, domains)

        # 4. Commit assignments that start at current_time (online execution)
        still_waiting = []
        for inc in unassigned_incidents:
            if inc in best_assignment and best_assignment[inc] is not None:
                resp, path, start_time, arrival_time, response_time = best_assignment[inc]

                # If the responder is free right now (start_time == current_time), dispatch them!
                # (Or commit immediately since the responder is reserved for this incident)
                plan.append({
                    "responder_id": resp.responder_id,
                    "incident_id": inc.incident_id,
                    "path": path,
                    "time": start_time
                })

                # Update responder state for future timestamps
                resp.current_location = inc.location
                resp.available_time = arrival_time + inc.time_required
                resp.availability = "Busy"

                handled_incidents.append((inc, resp, start_time, arrival_time, response_time))
            else:
                # Keep unassigned incidents in queue in case a responder frees up at a later timestamp
                still_waiting.append(inc)

        unassigned_incidents = still_waiting

    return plan, handled_incidents


def solve_csp_backtracking(incidents_batch, domains):
    best_solution = {}
    # Track best score: (number of incidents assigned, priority score, -total_response_time)
    best_score = (-1, -1, float('-inf'))

    def backtrack(idx, current_assignment, used_responders, count, prio_sum, total_resp_time):
        nonlocal best_solution, best_score

        # Base case: all incidents in the batch have been considered
        if idx == len(incidents_batch):
            score = (count, prio_sum, -total_resp_time)
            if score > best_score:
                best_score = score
                best_solution = current_assignment.copy()
            return

        inc = incidents_batch[idx]

        # Try assigning each valid responder in the incident's domain
        for option in domains[inc]:
            resp, path, start_time, arrival_time, response_time = option

            # Hard Constraint 4: Exclusivity (one responder per incident in this batch)
            if resp not in used_responders:
                used_responders.add(resp)
                current_assignment[inc] = option

                backtrack(
                    idx + 1,
                    current_assignment,
                    used_responders,
                    count + 1,
                    prio_sum + PRIORITY_WEIGHTS.get(inc.priority, 1),
                    total_resp_time + response_time
                )

                # Backtrack (undo choice)
                used_responders.remove(resp)
                del current_assignment[inc]

        # Also allow leaving the incident unassigned if no responder is free/valid
        current_assignment[inc] = None
        backtrack(idx + 1, current_assignment, used_responders, count, prio_sum, total_resp_time)
        del current_assignment[inc]

    backtrack(0, {}, set(), 0, 0, 0.0)
    return best_solution