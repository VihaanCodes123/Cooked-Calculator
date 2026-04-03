from api import fetch_course_data

import requests
import json
from dotenv import load_dotenv
import os
from collections import defaultdict
from datetime import datetime, timezone
import concurrent.futures


load_dotenv()
TOKEN = os.getenv("TOKEN")
COURSE_IDS = os.getenv("COURSE_ID").split(",")
COURSE_ID = COURSE_IDS[2]

BASE_URL = "https://smuhsd.instructure.com/api/v1"
with concurrent.futures.ThreadPoolExecutor(max_workers=len(COURSE_IDS)) as executor:
        fetches = list(executor.map(lambda course_id: fetch_course_data(BASE_URL, course_id, TOKEN), COURSE_IDS))

# print(json.dumps(fetches, indent=2))

for fetch in fetches:
    
    
    course_data = fetch["course"]
    submission_data = fetch["submission"]
    assignment_data = fetch["assignment"]
    group_data = fetch["group"]
    enrollment_data = fetch["enrollment"]
    # print(json.dumps(course_data, indent=2))

    # for mapping certain data between calls to each other, based on the ID
    assignment_map = {a["id"] : a for a in assignment_data}
    group_map = {g["id"] : g for g in group_data}

    # name of course
    name = course_data["course_code"]

    # # accumulate points per group
    group_points = {}

    for id, g in group_map.items():
        group_points[g["id"]] = {"weight" : g["group_weight"], "earned": 0, "possible": 0}

    for s in submission_data:
        assignment = assignment_map.get(s["assignment_id"])
        if not assignment:
            continue

        # skip ungraded/missing
        if (s["workflow_state"] != "graded" or s["score"] is None):
            continue

        group_id = assignment["assignment_group_id"]
        group_points[group_id]["earned"] += s["score"]
        group_points[group_id]["possible"] += assignment["points_possible"]


    print(f"{name}:")
    # calculate grade
    total_grade = 0


    # unweighted calculation
    if all(g["group_weight"] == 0 for g in group_map.values()):
        total_earned = total_possible = 0

        for group_id, points in group_points.items():
            if points["possible"] == 0:
                continue
            total_earned += points["earned"]
            total_possible += points["possible"]
        if total_possible > 0:
            total_grade = (total_earned/total_possible) * 100

    # weighted calculation
    else:
        total_weight = 0
        old_group_points = group_points.copy()

        print("Category Breakdown:")
        for group_id, points in old_group_points.items():
            group = group_map.get(group_id)
            if (not group):
                continue
            if (points["possible"] == 0):
                del group_points[group_id]
                continue
            total_weight += group["group_weight"]

        for group_id, points in group_points.items():
            group = group_map.get(group_id)
            category_pct = (points["earned"] / points["possible"]) * 100
            weight = group["group_weight"] / (total_weight/100) 
            contribution = (category_pct * weight) / 100

            total_grade += contribution

            print(f" {group['name']}: {category_pct:.1f}% (weight: {weight:.1f}%) → contributes {contribution:.1f}%")

    print(f"\nOverall: {total_grade:.1f}%\n\n")




    ## See Assignments and weight

    # for s in submission_data:
    #     assignment = assignment_map.get(s["assignment_id"]) # conversion of submission to assignment (to get category ID)

    #     if assignment: # to see if there is anything in the dict

    #         group_id = assignment["assignment_group_id"]

    #         group = group_map.get(group_id)

    #         # print(assignment["name"], "| Group ID:", assignment["assignment_group_id"])
    #         # print(assignment["name"], "| Group Name:", group["name"], "| Weight:", group["group_weight"])

    ## See Upcoming Assignments

    # today = datetime.now(timezone.utc)

    # upcoming = []
    # for s in submission_data:
    #     due = s.get("cached_due_date")
    #     if due and s["workflow_state"] == "unsubmitted":
    #         due_date = datetime.fromisoformat(due.replace("Z", "+00:00"))
    #         if due_date > today:
    #             upcoming.append(s)
    # print(f"Upcoming unsubmitted: {len(upcoming)}")
