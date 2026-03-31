import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
COURSE_ID = os.getenv("COURSE_ID")

BASE_URL = "https://smuhsd.instructure.com/api/v1"

CONSTRUCT = f"{BASE_URL}/courses/{COURSE_ID}"


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

# print(json.dumps(group_data, indent=2))

assignment_map = {a["id"] : a for a in assignment_data}
group_map = {g["id"] : g for g in group_data}

for s in submission_data:
    assignment = assignment_map.get(s["assignment_id"]) # conversion of submission to assignment (to get category ID)

    if assignment: # to see if there is anything in the dict

        group_id = assignment["assignment_group_id"]

        group = group_map.get(group_id)

        # print(assignment["name"], "| Group ID:", assignment["assignment_group_id"])
        print(assignment["name"], "| Group Name:", group["name"], "| Weight:", group["group_weight"])




# ASSIGNMENT GROUPS FOR LOOP
# for group in data:
#     print(group["name"], "| Weight:", group.get("group_weight"))