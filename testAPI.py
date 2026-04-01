import requests
import json
from dotenv import load_dotenv
import os
from collections import defaultdict
from datetime import datetime, timezone


load_dotenv()
TOKEN = os.getenv("TOKEN")
COURSE_IDS = os.getenv("COURSE_ID").split(",")

BASE_URL = "https://smuhsd.instructure.com/api/v1"

CONSTRUCT = f"{BASE_URL}/courses/{COURSE_IDS[0]}"


GET = ["assignments", "students/submissions", "assignment_groups", "enrollments"] # what can be called from api

headers = {"Authorization" : f"Bearer {TOKEN}"} # to gain access to student data, needs to change depending on student

PER_PAGE = {"per_page": 100}
params_submissions = PER_PAGE | {"student_ids[]": "self"}
params_assignments = PER_PAGE
params_groups = PER_PAGE
params_enrollments = PER_PAGE | {"user_id": "self", "type[]": "StudentEnrollment"}

# gets all data from the student submission, like whether work is missing
submission_response = requests.get(f"{CONSTRUCT}/{GET[1]}", headers=headers, params=params_submissions)
submission_data = submission_response.json()

# used to determine what category of assignment (in form of ID) it is, like if it's a test, quiz, homework, participation, etc.
assignment_response = requests.get(f"{CONSTRUCT}/{GET[0]}", headers=headers, params=params_assignments)
assignment_data = assignment_response.json()

# to get assignment category name and weight through group ID
group_response = requests.get(f"{CONSTRUCT}/{GET[2]}", headers=headers, params=params_groups)
group_data = group_response.json()

enrollment_response = requests.get(f"{CONSTRUCT}/{GET[3]}", headers=headers, params=params_enrollments)
enrollment_data = enrollment_response.json()

# print(json.dumps(group_data, indent=2))

assignment_map = {a["id"] : a for a in assignment_data}
group_map = {g["id"] : g for g in group_data}

# print(group_map)

# if all(g["group_weight"] == 0 for g in group_map.values()):
#     for gID in group_map:
#         group_map[gID]["group_weight"] = None
    

for s in submission_data:
    assignment = assignment_map.get(s["assignment_id"]) # conversion of submission to assignment (to get category ID)

    if assignment: # to see if there is anything in the dict

        group_id = assignment["assignment_group_id"]

        group = group_map.get(group_id)

        # print(assignment["name"], "| Group ID:", assignment["assignment_group_id"])
        # print(assignment["name"], "| Group Name:", group["name"], "| Weight:", group["group_weight"])


# # accumulate points per group
# group_points = defaultdict(lambda: {"earned": 0, "possible": 0})
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

# calculate weighted grade
total_grade = 0

# unweighted calculation
if all(g["group_weight"] == 0 for g in group_map.values()):
    total_earned = total_possible = 0

    for group_id, points in group_points.items():
        if (not group):
            continue
        total_earned += points["earned"]
        total_possible += points["possible"]
    total_grade = (total_earned/total_possible) * 100

# weighted calculation
else:
    total_weight = 0
    print("Category Breakdown:")
    for group_id, points in group_points.items():
        group = group_map.get(group_id)
        if (not group):
            continue
        if (points["possible"] == 0):
            del group_points[group_id]
            continue
        total_weight += group["group_weight"]

    print(group_points)

    for group_id, points in group_points.items():
        category_pct = (points["earned"] / points["possible"]) * 100
        weight = group["group_weight"] / (total_weight/100) 
        contribution = (category_pct * weight) / 100

        total_grade += contribution

        print(f" {group['name']}: {category_pct:.1f}% (weight: {weight}%) → contributes {contribution:.1f}%")

print(f"\nOverall: {total_grade:.1f}%")





today = datetime.now(timezone.utc)

upcoming = []
for s in submission_data:
    due = s.get("cached_due_date")
    if due and s["workflow_state"] == "unsubmitted":
        due_date = datetime.fromisoformat(due.replace("Z", "+00:00"))
        if due_date > today:
            upcoming.append(s)
print(f"Upcoming unsubmitted: {len(upcoming)}")
