import json
import os
from generate_json import classify_input, generate_json
from itertools import zip_longest


output_filename = 'output_data.json'



def extract_all_info(course_class_json, teacher_class_json):
    course_info = {}
    class_info = []

    for grade_data in course_class_json["data"]:
        for course in grade_data["courses"]:
            course_info[course["name"]] = {
                "uid": course["uid"],
                "courseDcode": course["courseDcode"]
            }

        for clazz in grade_data["classes"]:
            class_info.append({
                "gradeName": clazz["gradeName"],
                "name": clazz["name"],
                "uid": clazz["uid"],
                "type": clazz["type"]
            })

    teacher_info = []
    header_teachers = []

    for grade_data in teacher_class_json["data"]["gradeTeacherClassList"]:
        for teacher_class in grade_data["teacherClasses"]:
            teacher_info.append({
                "teacherName": teacher_class["teacher"]["name"],
                "teacherUid": teacher_class["teacher"]["uid"],
                "className": teacher_class["clazz"]["name"],
                "classUid": teacher_class["clazz"]["uid"],
                "courseName": teacher_class["course"]["name"],
                "courseUid": teacher_class["course"]["uid"],
                "courseDcode": teacher_class["course"]["courseDcode"]
            })

        for header_teacher in grade_data.get("headerTeachers", []):
            header_teachers.append({
                "teacherId": header_teacher["teacherId"],
                "teacherName": header_teacher["teacherName"],
                "gradeDcode": header_teacher["gradeDcode"],
                "classId": header_teacher["projectSchoolClassId"]
            })

    return {
        "course_info": course_info,
        "class_info": class_info,
        "teacher_info": teacher_info,
        "header_teachers": header_teachers
    }

def get_period_of_time(time_period):
    time_str = str(time_period).strip()
    time_mapping = {
        "上午": [1, 2, 3, 4],"早上": [1, 2, 3, 4],
        "下午": [6, 7, 8, 9],
        "晚上": [10, 11, 12],
        "全天": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "整天": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "一整天": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    }
    if time_str in time_mapping:
        return time_mapping[time_str]
    else:
        raise ValueError(f"Time '{time_period}' not found in time_mapping.")

def get_day_of_week(day):
    day_str = str(day).strip()
    day_mapping = {
        "周一": 1, "星期一": 1, "1": 1, "一": 1,
        "周二": 2, "星期二": 2, "2": 2, "二": 2,
        "周三": 3, "星期三": 3, "3": 3, "三": 3,
        "周四": 4, "星期四": 4, "4": 4, "四": 4,
        "周五": 5, "星期五": 5, "5": 5, "五": 5,
        "周六": 6, "星期六": 6, "6": 6, "六": 6,
        "周日": 7, "星期日": 7, "7": 7, "日": 7, "天": 7
    }
    if day_str in day_mapping:
        return day_mapping[day_str]
    else:
        raise ValueError(f"Day '{day}' not found in day_mapping.")
    
def preprocess_input(json_input):
    
    for detail in json_input["details"]:
        # Translate and normalize the format of days
        if 'day' in detail:
            detail['day'] = [get_day_of_week(day) for day in detail['day']]

        # Translate the time_periods into periods
        if not detail.get('period') and 'time_period' in detail:
            all_periods = []
            for time_period in detail['time_period']:
                periods_from_time = get_period_of_time(time_period)
                all_periods.extend(periods_from_time)
            detail['period'] = list(set(all_periods)) 
            del detail['time_period']
        
    return json_input
    

def extract_class_data(course_class_data, grade_name):
    return [
        {
            "gradeName": clazz["gradeName"],
            "name": f"{clazz['gradeName']}{clazz['name']}",
            "alias": "",
            "uid": clazz["uid"],
            "type": clazz["type"]
        }
        for clazz in course_class_data["class_info"]
        if clazz["gradeName"] == grade_name
    ]

def extract_course_info(course_class_data, subjects):
    courses = []
    for subject in subjects:
        course_info = course_class_data["course_info"].get(subject)
        if not course_info:
            course_info = {"name": subject, "uid": "", "courseDcode": ""}
        courses.append({"name": subject, "uid": course_info["uid"], "courseDcode": course_info["courseDcode"]})
    return courses

def create_constraint_json(classes, courses, period_days, constraint_type, limits=1, maxlimits=-1):
    return {
        "classes": classes,
        "courses": courses,
        "periodDays": period_days,
        "constraintType": constraint_type,
        "limits": limits,
        "maxlimits": maxlimits
    }

def extract_periods(time_periods, time_period_mapping):
    periods = []
    for time_period in time_periods:
        periods.extend(time_period_mapping.get(time_period, []))
    return periods

def find_relevant_classes(course_class_data, grades, formatted_classes=None):
    if formatted_classes is None:
        formatted_classes = [f"{int(c):02d}班" for c in grades]
    
    return [
        {
            "uid": clazz["uid"],
            "name": f"{clazz['gradeName']}{clazz['name']}"
        }
        for clazz in course_class_data["class_info"]
        if clazz["gradeName"] in grades and clazz["name"] in formatted_classes
    ]

def find_relevant_class(course_class_data, grade, clazz):
    relevant_classes = find_relevant_classes(course_class_data, [grade], [clazz])
    return relevant_classes[0] if relevant_classes else None

def find_teacher_info(course_class_data, teacher_name):
    return next(
        (teacher for teacher in course_class_data["teacher_info"]
         if teacher["teacherName"].strip() == teacher_name),
        None
    )

def find_course_info(course_class_data, subject):
    course_info = course_class_data["course_info"].get(subject)
    if not course_info:
        raise ValueError(f"Course information for subject '{subject}' not found in course_info.")
    return course_info

def find_relevant_teachers(teacher_class_data, grade_name, course_name):
    course_name = course_name.replace("老师", "")  
    return [
        teacher for teacher in teacher_class_data["teacher_info"]
        if grade_name in teacher["className"] and course_name in teacher["courseName"]
    ]

def create_teacher_constraint(teachers, period, day, constraint_type="MUST_ASSIGN"):
    period_days = [{"period": int(period), "dayOfWeek": day}]
    return {
        "teachers": [{"uid": teacher["teacherUid"], "name": teacher["teacherName"]} for teacher in teachers],
        "periodDays": period_days,
        "constraintType": constraint_type,
        "teacherType": "TEACHER"
    }

def create_period_days(day, periods):
    return [{"period": period, "dayOfWeek": day} for period in periods]

def get_teacher_courses(teacher_name, all_info):
    return [
        {
            "name": course["courseName"],
            "uid": course["courseUid"],
            "courseDcode": course["courseDcode"],
            "grade": next((grade["gradeName"] for grade in all_info["class_info"] if grade["uid"] == course["classUid"]), "")
        }
        for course in all_info['teacher_info']
        if course['teacherName'] == teacher_name
    ]

def map_grade_names(courses):
    grade_mapping = {
        "初一": "J1",
        "初二": "J2",
        "初三": "J3"
    }
    for course in courses:
        if course["grade"] in grade_mapping:
            course["grade"] = grade_mapping[course["grade"]]
    return courses

# def build_teacher_clusters(teacher_info, all_info, grades, subjects):
#     class_to_gradeDcode = {clazz["name"]: clazz["gradeDcode"] for clazz in all_info["class_info"]}

#     teacher_clusters = []
#     for teacher in teacher_info:
#         course_name = teacher["courseName"]
#         grade_name = teacher["className"][:2]  # Extract the grade level (e.g., "初一")
#         if grade_name in grades and course_name in subjects:
#             class_name = teacher["className"]
#             grade_dcode = class_to_gradeDcode.get(class_name)

#             if not grade_dcode:
#                 raise ValueError(f"No matching gradeDcode found for class {class_name}")

#             teacher_clusters.append({
#                 "courses": [{
#                     "name": course_name,
#                     "uid": teacher["courseUid"],
#                     "courseDcode": teacher["courseDcode"],
#                     "gradeDcode": grade_dcode,
#                     "checked": True
#                 }],
#                 "teacher": {"uid": teacher["teacherUid"], "name": teacher["teacherName"]},
#                 "minConsecutive": 2,
#                 "maxConsecutive": 2,
#                 "minClusterSize": 2,
#                 "maxClusterSize": 2
#             })
#     return teacher_clusters

# 初一周一第9节体活,周二第9节不排
# def firstScene(json_input, course_class_data):
#     output_list = []
#     grade_name = json_input["details"][0]["grade"][0]
#     subjects = json_input["details"][0]["subject"]
#     days = json_input["details"][0]["day"]
#     periods = json_input["details"][0]["period"]

#     # Extract class information for the given grade
#     classes = [
#         {"name": clazz["name"], "uid": clazz["uid"]}
#         for clazz in course_class_data["class_info"]
#         if clazz["gradeName"] == grade_name
#     ]

#     # Create combined description for all subjects and days
#     for subject in subjects:
#         description = f"{grade_name}" + ", ".join([f"周{day}第{period}节{subject}" for day in days for period in periods])
#         period_days = [{"period": period, "dayOfWeek": day, "remarks": subject} for day in days for period in periods]

#         output = {
#             "constraint": None,
#             "description": description,
#             "disabled": False,
#             "remarks": subject,
#             "invalid": False,
#             "invalidTime": None,
#             "reason": "",
#             "equilibriumConstraintSet": False,
#             "classes": classes,
#             "periodDays": period_days
#         }
#         output_list.append(output)

#     return output_list
# # 初一 语文 周一第九节;周二第九节不排
# 课程课时条件
def firstScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "COURSETIME",
        "constraintJsons": []
    }

    grade_names = json_input["details"][0]["grade"]
    subjects = json_input["details"][0]["subject"]
    days = json_input["details"][0]["day"]
    periods = json_input["details"][0]["period"]

    for grade_name in grade_names:
        print(f"Processing grade: {grade_name}")
        classes = extract_class_data(course_class_data, grade_name)

        for subject, day, period in zip_longest(subjects, days, periods, fillvalue=None):
            if subject is None or day is None or period is None:
                print("Skipping due to missing subject, day, or period.")
                continue

            if subject == "不排":
                constraint_type = "MUST_AVOID"
            else:
                constraint_type = "MUST_ASSIGN"

            courses = extract_course_info(course_class_data, [subject])
            period_days = [{"period": int(period), "dayOfWeek": day}]

            constraint_json = create_constraint_json(classes, courses, period_days, constraint_type)
            output_data["constraintJsons"].append(constraint_json)

    return output_data


# 课程各天条件
# 初一 语文 周一到周五每天最少排一节
def secondScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "COURSEDAYLIMIT",
        "constraintJsons": []
    }

    grade_name = json_input["details"][0]["grade"][0]
    subjects = json_input["details"][0]["subject"]
    days = json_input["details"][0]["day"]

    day_of_weeks = [day for day in days]
    classes = extract_class_data(course_class_data, grade_name)

    for subject in subjects:
        courses = extract_course_info(course_class_data, [subject])
        period_days = [{"period": -1, "dayOfWeek": day} for day in day_of_weeks]
        constraint_json = create_constraint_json(classes, courses, period_days, "MIN_MAX_ASSIGN")
        output_data["constraintJsons"].append(constraint_json)

    return output_data

# 初一 数学 整个周第1节必排一节
# 课程时段条件
def thirdScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "COURSEPERIODLIMIT",
        "constraintJsons": []
    }

    grade_names = json_input["details"][0]["grade"]  
    subjects = json_input["details"][0]["subject"]
    periods = json_input["details"][0]["period"]
    days = json_input["details"][0].get("day", [])

    for grade_name in grade_names:
        print(f"Processing grade: {grade_name}")
        classes = extract_class_data(course_class_data, grade_name)

        for subject in subjects:
            courses = extract_course_info(course_class_data, [subject])

            for period, day in zip_longest(periods, days, fillvalue=None):
                if period is None or day is None:
                    print(f"Skipping due to missing period or day for subject: {subject}")
                    continue

                period_days = [{"period": int(period), "dayOfWeek": day}]
                constraint_json = create_constraint_json(classes, courses, period_days, "MUST_ASSIGN")
                output_data["constraintJsons"].append(constraint_json)

    return output_data

# 初一 语文 周三下午连堂一次
# 课程连堂条件
def fourthScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "CONSECUTIVECOURSE",
        "constraintJsons": []
    }

    grade_name = json_input["details"][0]["grade"][0]
    subjects = json_input["details"][0]["subject"]
    days = json_input["details"][0].get("day", [])
    periods = json_input["details"][0]["period"]



    day_of_week_num = days[0] if days else -1


    classes = extract_class_data(course_class_data, grade_name)

    for subject in subjects:
        course_info = course_class_data["course_info"].get(subject)

        if course_info is None:
            raise ValueError(f"Subject '{subject}' not found in course_info")

        course = {
            "name": subject,
            "uid": course_info["uid"],
            "courseDcode": course_info["courseDcode"]
        }

        period_day_clusters = [[{"period": period, "dayOfWeek": day_of_week_num} for period in periods]]

        constraint_json = {
            "gap": 0,
            "limit": 1,
            "constraintType": "MUST_ASSIGN",
            "classes": classes,
            "periodDayClusters": period_day_clusters,
            "consecutiveType": "FIXED",
            "acourse": course,
            "bcourse": course,
            "perioddayType": "DAY",
            "limitType": "EXACT"
        }

        output_data["constraintJsons"].append(constraint_json)

    return output_data

# 初一 综合实践1与综合实践2不排同一天
# 课程不排同一天条件
def fifthScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "COURSE2COURSE",
        "constraintJsons": []
    }

    grade_name = json_input["details"][0]["grade"][0]
    subjects = json_input["details"][0]["subject"]

    classes = extract_class_data(course_class_data, grade_name)

    if len(subjects) < 2:
        print("Error: Need at least two subjects for this constraint.")
        return None

    prev_subject = subjects[0]
    next_subject = subjects[1]

    prev_course = course_class_data["course_info"].get(prev_subject, {
        "name": prev_subject,
        "uid": "",
        "courseDcode": ""
    })

    next_course = course_class_data["course_info"].get(next_subject, {
        "name": next_subject,
        "uid": "",
        "courseDcode": ""
    })

    constraint_json = {
        "classes": classes,
        "courses": [],
        "periodDays": [],
        "constraintType": "MUST_ASSIGN",
        "prevCourse": {
            "name": prev_course.get("name", prev_subject),
            "uid": prev_course.get("uid", ""),
            "courseDcode": prev_course.get("courseDcode", "")
        },
        "nextCourse": {
            "name": next_course.get("name", next_subject),
            "uid": next_course.get("uid", ""),
            "courseDcode": next_course.get("courseDcode", "")
        },
        "gap": 9,
        "frequency": 0
    }

    output_data["constraintJsons"].append(constraint_json)
    # print(classes)
    return output_data

# 初一初二 信息技术 同一节课最多2个班
# 课程同一节课最多条件
def sixthScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "COURSE2COURSE",
        "constraintJsons": {}  
    }

    grades = json_input["details"][0]["grade"]
    subjects = json_input["details"][0]["subject"]
    limits = int(json_input["details"][0]["max_classes"])

    classes = []
    for grade in grades:
        classes.extend(extract_class_data(course_class_data, grade))

    all_course_infos = []
    for subject in subjects:
        course_infos = extract_course_info(course_class_data, [subject])
        if not course_infos:
            course_infos = [{"name": subject, "uid": "", "courseDcode": ""}]
        all_course_infos.extend(course_infos)

    constraint_json = {
        "type": "MAX_SAME_TIME",
        "constraintType": "MAX_ASSIGN",
        "limits": limits,
        "classes": classes,
        "courses": all_course_infos
    }

    output_data["constraintJsons"] = constraint_json
    # output_data["constraintJsons"]= json.dumps(constraint_json, ensure_ascii=False)
    # print(classes)
    return output_data

# 体育 张佳辉 初一06班;初一07班合班上课
# 课程合班条件
def seventhScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "COURSESAMETIMELIMIT",
        "constraintJson": {}
    }

    grades = json_input["details"][0]["grade"]
    classes = json_input["details"][0]["class"]
    subjects = json_input["details"][0]["subject"] 
    teacher_name = json_input["details"][0]["teacher"][0].strip()

    formatted_classes = [f"{int(c):02d}班" for c in classes]

    relevant_classes = find_relevant_classes(course_class_data, grades, formatted_classes)
    if not relevant_classes:
        raise ValueError(f"No classes found for grades {grades} and classes {formatted_classes}.")

    courses_info = []

    for subject in subjects:
        subject = subject.strip()
        course_info = course_class_data["course_info"].get(subject)
        if not course_info:
            raise ValueError(f"Course information for subject '{subject}' not found in course_info.")
        courses_info.append({
            "name": subject,
            "uid": course_info["uid"],
            "courseDcode": course_info["courseDcode"]
        })

    teacher_info = find_teacher_info(course_class_data, teacher_name)
    if not teacher_info:
        raise ValueError(f"Teacher information for '{teacher_name}' not found in teacher_info.")

    constraint_json = {
        "type": "MERGE_CLASS",
        "constraintType": "MUST_ASSIGN",
        "classes": relevant_classes,
        "courses": courses_info,  
        "teacher": {
            "name": teacher_info["teacherName"],
            "uid": teacher_info["teacherUid"]
        }
    }

    output_data["constraintJson"] = constraint_json

    return output_data

# 初一01班生物与初一03班地理走班关联
# 课程走班关联条件
def eighthScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 984,
        "type": "MOVECOURSE",
        "constraintJson": {}
    }

    grades = json_input["details"][0]["grade"]
    classes = json_input["details"][0]["class"]
    subjects = json_input["details"][0]["subject"]

    formatted_classes = [f"{int(c):02d}班" for c in classes]

    move_course_details = []

    for grade, clazz, subject in zip(grades, formatted_classes, subjects):
        relevant_class = find_relevant_class(course_class_data, grade, clazz)
        if not relevant_class:
            raise ValueError(f"No class found for grade {grade} and class {clazz}.")

        course_info = find_course_info(course_class_data, subject)

        move_course_details.append({
            "classes": [relevant_class],
            "courses": {"name": subject, "uid": course_info["uid"]}
        })

    constraint_json = {
        "type": "MOVECOURSE",
        "moveCourseDetails": move_course_details
    }

    output_data["constraintJson"] = constraint_json

    return output_data

# 课程单双周条件
# 初二 美术(单)与音乐(双) 单双周
def ninthScene(json_input, course_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 985,
        "type": "EVENODDLINK",
        "constraintJson": ""
    }

    grades = json_input["details"][0]["grade"]
    subjects = json_input["details"][0]["subject"]

    classes = []
    for grade in grades:
        classes.extend(extract_class_data(course_class_data, grade))

    if len(subjects) < 2:
        raise ValueError("Error: Need at least two subjects for this constraint.")

    courseA_info = find_course_info(course_class_data, subjects[0])
    courseB_info = find_course_info(course_class_data, subjects[1])

    constraint_json = {
        "type": "EVENODDLINK",
        "constraintType": "MAX_ASSIGN",
        "classes": classes,
        "courses": [],
        "courseA": {
            "name": subjects[0], 
            "uid": courseA_info["uid"]
        },
        "courseB": {
            "name": subjects[1],  
            "uid": courseB_info["uid"]
        },
        "courseAOption": "ODD"  
    }

    output_data["constraintJson"] = constraint_json

    return output_data


# 初一 语文老师 周一第六节 必排
# 教师课时条件
def teacherFirst(json_input, teacher_class_data):
    grade_name = json_input["details"][0]["grade"][0]
    course_name = json_input["details"][0]["teacher"][0]
    day = json_input["details"][0]["day"][0]
    period = json_input["details"][0]["period"][0]

    relevant_teachers = find_relevant_teachers(teacher_class_data, grade_name, course_name)
    if not relevant_teachers:
        print(f"No teachers found for {course_name} in grade {grade_name}.")
        return None

    constraint_json = create_teacher_constraint(relevant_teachers, period, day)

    output_data = {
        "projectId": 458,
        "projectScenarioId": 985,
        "type": "TEACHERTIME",
        "constraintJson": constraint_json
    }

    return output_data

# print("All Extracted Information:", json.dumps(all_info, ensure_ascii=False, indent=4))
# filtered_teacher_info = [
#     teacher for teacher in all_info["teacher_info"] 
#     if "初一" in teacher["className"]
# ]

# print(json.dumps(filtered_teacher_info, ensure_ascii=False, indent=4))
# 初一 数学老师 周五下午 不排
# 教师各天条件
def teacherSecond(json_input, teacher_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 985,
        "type": "TEACHERDAYLIMIT",
        "constraintJson": {}
    }

    grade_name = json_input["details"][0]["grade"][0]
    course_name = json_input["details"][0]["teacher"][0].replace("老师", "")
    day = json_input["details"][0]["day"][0]
    periods = json_input["details"][0]["period"]
    limits = int(json_input["details"][0]["min_classes"])

    # time_period_mapping = {
    #     "上午": [1, 2, 3, 4],
    #     "下午": [6, 7, 8, 9],
    #     "晚上": [10, 11, 12],
    # }

    # periods = get_period_of_time(time_period)
    # if not periods:
    #     print(f"Time period '{time_period}' not found.")
    #     return None

    relevant_teachers = find_relevant_teachers(teacher_class_data, grade_name, course_name)
    if not relevant_teachers:
        print(f"No teachers found for {course_name} in grade {grade_name}.")
        return None

    period_days = create_period_days(day, periods)
    if limits == 0 :
        constraint_type = "MUST_AVOID" 
        max_limit=-1
    else:
        constraint_type ="MUST_ASSIGN"
        max_limit=limits
    
    constraint_json = {
        "teachers": [{"uid": teacher["teacherUid"], "name": teacher["teacherName"]} for teacher in relevant_teachers],
        "periodDays": period_days,
        "constraintType": constraint_type,
        "limits": 1,
        "maxlimits": max_limit
    }

    output_data["constraintJson"] = constraint_json

    return output_data

# 所有老师 整个周第5节 最多排3节
# 教师时段条件
def teacherThird(json_input, teacher_class_data):
    output_data = {
        "projectId": 458,
        "projectScenarioId": 985,
        "type": "TEACHERPERIODLIMIT",
        "constraintJson": {}
    }

    period = int(json_input["details"][0]["period"][0])
    max_num = json_input["details"][0]["max_classes"]

    teachers = [{"uid": teacher["teacherUid"], "name": teacher["teacherName"]} for teacher in teacher_class_data["teacher_info"]]

    if max_num>0:
        max_limits = max_num
    else:
        max_limits = -1  

    constraint_json = {
        "teachers": teachers,
        "periodDays": [{"period": period, "dayOfWeek": -1}], 
        "constraintType": "MIN_MAX_ASSIGN",
        "limits": -1,
        "maxlimits": max_limits
    }

    output_data["constraintJson"] = constraint_json

    return output_data

# 教师不排同时上课条件
# 钟敏 张慧 不排同一节

def teacherForth(json_input, all_info):
    teacher_names = json_input['details'][0]['teacher']
    if len(teacher_names) != 2:
        raise ValueError("Exactly two teacher names must be provided.")

    teacher_a_name, teacher_b_name = teacher_names
    teacher_a_info = find_teacher_info(all_info, teacher_a_name)
    teacher_b_info = find_teacher_info(all_info, teacher_b_name)

    if not teacher_a_info or not teacher_b_info:
        raise ValueError(f"Could not find both teachers in the data: {teacher_a_name}, {teacher_b_name}")

    a_courses = get_teacher_courses(teacher_a_name, all_info)
    b_courses = get_teacher_courses(teacher_b_name, all_info)

    a_courses = map_grade_names(a_courses)
    b_courses = map_grade_names(b_courses)

    constraint_json = {
        "mutexType": "ALL",
        "ateacher": {"name": teacher_a_name, "uid": teacher_a_info["teacherUid"]},
        "aCourses": a_courses,
        "bteacher": {"name": teacher_b_name, "uid": teacher_b_info["teacherUid"]},
        "bCourses": b_courses,
        "error": False
    }

    return {
        "projectId": 458,
        "projectScenarioId": 985,
        "type": "TEACHERTIMEMUTEX",
        "constraintJsons": [constraint_json]
    }


# 教师多班连上条件
# 初二数学老师 不同班级的数学课连着上
def teacherFifth(json_input, all_info):
    teacher_clusters = []
    details = json_input.get("details", [])

    class_to_gradeDcode = {}

    for grade_data in teacher_class_json["data"]["gradeTeacherClassList"]:
        grade_dcode = grade_data["gradeDecode"]
        for teacher_class in grade_data["teacherClasses"]:
            class_name = teacher_class["clazz"]["name"]
            class_to_gradeDcode[class_name] = grade_dcode

    for detail in details:
        grades = detail.get("grade", [])
        teacher_subjects = [subject.replace("老师", "") for subject in detail.get("teacher", [])]

        for teacher in all_info["teacher_info"]:
            course_name = teacher["courseName"]
            grade_name = teacher["className"][:2]  
            if grade_name in grades and course_name in teacher_subjects:
                class_name = teacher["className"]
                grade_dcode = class_to_gradeDcode.get(class_name)

                if grade_dcode is None:
                    raise ValueError(f"No matching gradeDcode found for class {class_name}")

                teacher_clusters.append({
                    "courses": [{
                        "name": course_name,
                        "uid": teacher["courseUid"],
                        "courseDcode": teacher["courseDcode"],
                        "gradeDcode": grade_dcode, 
                        "checked": True
                    }],
                    "teacher": {
                        "uid": teacher["teacherUid"],
                        "name": teacher["teacherName"]
                    },
                    "minConsecutive": 2,
                    "maxConsecutive": 2,
                    "minClusterSize": 2,
                    "maxClusterSize": 2
                })

    constraint_json = {
        "teacherTimeClusters": teacher_clusters
    }

    return {
        "projectId": 458,  
        "projectScenarioId": 985,  
        "type": "TEACHERTIMECLUSTER",
        "constraintJson": constraint_json
    }

with open('class_info.json', 'r', encoding='utf-8') as f1, open('teacher_info.json', 'r', encoding='utf-8') as f2:
    course_class_json = json.load(f1)
    teacher_class_json = json.load(f2)

all_info = extract_all_info(course_class_json, teacher_class_json)

user_input = input("Please enter your input: ")


scenario = classify_input(user_input)
scenario = json.loads(scenario)
# print(scenario)
if "results" in scenario:
    for result in scenario.get("results"):
        print(f"Segment: {result['segment']}")
        print(f"Classification: {result['classification']}")

        json_input = json.loads(generate_json(result['segment'],result['classification']))
        # print(json_input)
        json_input = preprocess_input(json_input)
        print(json_input)
        classification_handler = {
            "课程课时条件": firstScene,
            "课程各天条件": secondScene,
            "课程时段条件": thirdScene,
            "课程连堂条件": fourthScene,
            "课程不排同一天条件": fifthScene,
            "课程同一节课最多条件": sixthScene,
            "课程合班条件": seventhScene,
            "课程走班关联条件": eighthScene,
            "课程单双周条件": ninthScene,
            "教师课时条件": teacherFirst,
            "教师各天条件": teacherSecond,
            "教师时段条件": teacherThird,
            "教师不排同时上课条件": teacherForth,
            "教师多班连上条件": teacherFifth
        }

        # classification = json_input.get("classification")
        handler = classification_handler.get(result['classification'])
        if handler:
            output = handler(json_input, all_info)
            if os.path.exists(output_filename):
                with open(output_filename, 'r', encoding='utf-8') as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:  # In case the file is empty
                        data = []
            else:
                data = []

            data.append(output)

            with open(output_filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)



        # output = sixthScene(json_input, all_info)
        print(json.dumps(output, ensure_ascii=False, indent=4))


# json_input = json.loads(generate_json(user_input))
# print(json_input)
# classification_handler = {
#     "课程课时条件": firstScene,
#     "课程各天条件": secondScene,
#     "课程时段条件": thirdScene,
#     "课程连堂条件": fourthScene,
#     "课程不排同一天条件": fifthScene,
#     "课程同一节课最多条件": sixthScene,
#     "课程合班条件": seventhScene,
#     "课程走班关联条件": eighthScene,
#     "课程单双周条件": firstScene,
#     "教师课时条件": teacherFirst,
#     "教师各天条件": teacherSecond,
#     "教师时段条件": teacherThird,
#     "教师不排同时上课条件": teacherForth,
#     "教师多班连上条件": teacherFifth
# }

# classification = json_input.get("classification")
# handler = classification_handler.get(classification)
# if handler:
#     output = handler(json_input, all_info)



# # output = sixthScene(json_input, all_info)
# print(json.dumps(output, ensure_ascii=False, indent=4))

