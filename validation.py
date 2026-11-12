def validate_plan(plan, city_graph, responders, incidents, tolerance=1e-2):
    errors = []

    # Create lookup dictionaries by ID

    resp_map = {r.responder_id: r for r in responders}
    inc_map = {i.incident_id: i for i in incidents}
    road_map = {(r.fromNode.id, r.toNode.id): r for r in city_graph.roads}

    seen_incidents = set()
    assignments_by_responder = {r.responder_id: [] for r in responders}

    for idx, entry in enumerate(plan):
        r_id = entry.get("responder_id")
        i_id = entry.get("incident_id")
        path = entry.get("path", [])
        start_time = entry.get("time")

        # Check 1: Valid IDs and duplicate incident assignments
        if r_id not in resp_map:
            errors.append(f"Assignment {idx}: Unknown responder '{r_id}'.")
            continue
        if i_id not in inc_map:
            errors.append(f"Assignment {idx}: Unknown incident '{i_id}'.")
            continue
        if i_id in seen_incidents:
            errors.append(f"Assignment {idx}: Incident '{i_id}' is assigned multiple times.")
        seen_incidents.add(i_id)

        resp = resp_map[r_id]
        inc = inc_map[i_id]

        # Check 2: Required capability
        if inc.required_capability not in resp.capabilities:
            errors.append(
                f"Assignment {idx} ({r_id} -> {i_id}): Responder lacks capability "
                f"'{inc.required_capability}' (has {resp.capabilities})."
            )

        # Check 3: Assignment cannot start before incident appears
        if start_time + tolerance < inc.timestamp:
            errors.append(
                f"Assignment {idx} ({r_id} -> {i_id}): Starts at t={start_time}, "
                f"before incident timestamp t={inc.timestamp}."
            )

        # Check 4: Non-empty path ending at incident location
        if not path:
            errors.append(f"Assignment {idx} ({r_id} -> {i_id}): Path is empty.")
            continue
        if path[-1] != inc.location.id:
            errors.append(
                f"Assignment {idx} ({r_id} -> {i_id}): Path ends at '{path[-1]}', "
                f"but incident is at '{inc.location.id}'."
            )

        # Check 5: Valid connected edges and no Blocked roads
        travel_time = 0.0
        path_valid = True
        for step in range(len(path) - 1):
            u, v = path[step], path[step + 1]
            if (u, v) not in road_map:
                errors.append(
                    f"Assignment {idx} ({r_id} -> {i_id}): Non-existent road '{u} -> {v}'."
                )
                path_valid = False
                break
            road = road_map[(u, v)]
            if road.estimated_state == "Blocked" or road.travel_time is None:
                errors.append(
                    f"Assignment {idx} ({r_id} -> {i_id}): Uses blocked road '{u} -> {v}'."
                )
                path_valid = False
                break
            travel_time += road.travel_time

        if not path_valid:
            continue

        arrival_time = start_time + travel_time
        finish_time = arrival_time + inc.time_required

        # Check 6: Deadline met upon arrival
        if arrival_time - tolerance > inc.deadline:
            errors.append(
                f"Assignment {idx} ({r_id} -> {i_id}): Arrives at t={arrival_time:.2f}, "
                f"missing deadline t={inc.deadline}."
            )

        assignments_by_responder[r_id].append((start_time, arrival_time, finish_time, path, i_id))

    # Check 7: Responder timeline & spatial continuity across multiple assignments
    for r_id, tasks in assignments_by_responder.items():
        if not tasks:
            continue
        resp = resp_map[r_id]
        # Sort tasks chronologically by start_time
        tasks.sort(key=lambda x: x[0])

        expected_loc = resp.start_location.id
        available_at = 0.0 if resp.availability == "Available" else float(resp.time_until_available)

        for start_time, arrival_time, finish_time, path, i_id in tasks:
            if path[0] != expected_loc:
                errors.append(
                    f"Responder {r_id} (Incident {i_id}): Path starts at '{path[0]}', "
                    f"but responder was at '{expected_loc}'."
                )
            if start_time + tolerance < available_at:
                errors.append(
                    f"Responder {r_id} (Incident {i_id}): Dispatched at t={start_time:.2f}, "
                    f"but busy until t={available_at:.2f}."
                )
            expected_loc = path[-1]
            available_at = finish_time

    is_valid = len(errors) == 0
    return is_valid, errors