import requests

def fetch_course_data (base_url, course_id, user_token):

    CONSTRUCT = f"{base_url}/courses/{course_id}"
    GET = ["assignments", "students/submissions", "assignment_groups", "enrollments"] # what can be called from api

    headers = {"Authorization" : f"Bearer {user_token}"} # to gain access to student data, needs to change depending on student

    PER_PAGE = {"per_page": 100}
    params_courses = PER_PAGE
    params_submissions = PER_PAGE | {"student_ids[]": "self"}
    params_assignments = PER_PAGE
    params_groups = PER_PAGE
    params_enrollments = PER_PAGE | {"user_id": "self", "type[]": "StudentEnrollment"}

    # gets course data, main thing we want is the course name
    course_response = requests.get(f"{CONSTRUCT}", headers = headers, params=params_courses)
    course_data = course_response.json()

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

    return {
        "id" : course_id,
        "course" : course_data,
        "submission" : submission_data,
        "assignment" : assignment_data,
        "group" : group_data,
        "enrollment" : enrollment_data
    }