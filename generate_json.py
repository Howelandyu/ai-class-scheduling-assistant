import json
import openai
from openai import OpenAI
client = OpenAI(api_key = '')


def classify_input(user_input):
    classification_prompt = f"""
    基于用户输入，返回一个JSON对象，包含一个数组，其中包含用户输入的情境类型。可能的情况包含：

    1. 课程课时条件：在一周内某天的的某一课时排某堂课或不排课 例：初一 语文 周一第九节;周二第九节不排 
    2. 课程各天条件：在一段时间内进行排课限制 例：初一 语文 周一到周五每天最少排一节 
    3. 课程时段条件：在一周内每天的某一课时排某堂课 例：初一 数学 整个周第1节必排一节 
    4. 课程连堂条件：在一周内某天的某一时间段进行连堂 例：初一 语文 周三下午连堂一次 
    5. 课程不排同一天条件：某两节课不排在同一天 例：初一 综合实践1与综合实践2不排同一天 
    6. 课程同一节课最多条件：某堂课同一节课最多同时排一定数量的班级 例：初一初二 信息技术 同一节课最多2个班 
    7. 课程合班条件：某老师带的某节课给不同班级合班上课 例：体育 张佳辉 初一06班;初一07班合班上课
    8. 课程走班关联条件：某两个班级的某个课程走班关联 例：初一01班生物与初一03班地理走班关联
    9. 课程单双周条件：某两个课程单双周 例：初二 美术(单)与音乐(双) 单双周
    10. 教师课时条件: 教师在一周内某天的某一课时必须排/不排课 例：初一 语文老师 周一第六节 必排
    11. 教师各天条件: 教师在一段时间内的排课限制 例：初一 数学老师 周五下午 不排
    12. 教师时段条件: 教师在一周内每天的某一课时的排课限制 例：所有老师 整个周第5节 最多排3节
    13. 教师不排同时上课条件: 某两名教师不排在同一节 例：钟敏 张慧 不排同一节
    14. 教师多班连上条件: 教师连续上课的情况 例：初二数学老师 不同班级的数学课连着上
    15. 为了照顾刚生完孩子的张老师,周五下午张老师没空

    当用户同时输入多种情境时，将其分别列出。
    当用户输入的某部分不能归类为以上任意情境时，不将其包含在内。

    例如：
    用户输入：“初一 语文 周一第九节;周二第九节不排 ，初一初二 信息技术 同一节课最多2个班 ，明天是晴天”
    输出：
    {{
        "results": [
            {{
                "segment": "初一 语文 周一第九节;周二第九节不排",
                "classification": "课程课时条件"
            }},
            {{
                "segment": "初一初二 信息技术 同一节课最多2个班",
                "classification": "课程同一节课最多条件"
            }}
        ]
    }}


    输出格式：
    {{
        "results": [
            {{
                "segment":"该场景的具体部分",
                "classification":"该场景的分类"
            }}
        ]
    }}
    User input: "{user_input}"
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": classification_prompt}],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content

prompt_templates = {
    "课程课时条件": """
        User Input: "初一周一第9节体活，周二第9节不排"
        Expected JSON Output: {{
            "classification": "课程课时条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周一", "周二"],
                    "period": ["9". "9"],
                    "subject": ["体活", "不排"]
                }}
            ]
        }}
        User Input: "初一英语和综合实践1 周三的第5节和第6节不排"
        Expected JSON Output: {{
            "classification": "课程课时条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周一", "周二"],
                    "period": ["5". "6"],
                    "subject": ["英语", "综合实践1","不排"]
                }}
            ]
        }}
    """,
    "课程各天条件": """
        User Input: "初一 语文 周一到周五每天最少排一节 "
        Expected JSON Output: {{
            "classification": "课程各天条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周一". "周二", "周三", "周四", "周五"],
                    "subject": ["语文"],
                    "max_classes": 1
                }}
            ]
        }}
    """,
    "课程时段条件": """
        User Input: "初一 数学 整个周第1节必排一节"
        Expected JSON Output: {{
            "classification": "课程时段条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周一","周二", "周三", "周四", "周五"]
                    "period": ["1"],
                    "subject": ["数学"],
                    "min_classes": 1
                }}
            ]
        }}
        User Input: "初一初二的劳动课 周五必排1节"
        Expected JSON Output: {{
            "classification": "课程时段条件",
            "details": [
                {{
                    "grade": ["初一", "初二"],
                    "day": ["周五"]
                    "period": ["1"],
                    "subject": ["数学"],
                    "min_classes": 1
                }}
            ]
        }}
        User Input: "初一初二的劳动课 周五必排1节"
        Expected JSON Output: {{
            "classification": "课程时段条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周五"]
                    "period": ["1","2","3","4"],
                    "subject": ["语文","数学","英语"],
                    "min_classes": 4
                }}
            ]
        }}
    """,
    "课程连堂条件": """
        User Input: "初一 语文 周三下午连堂一次"
        Expected JSON Output: {{
            "classification": "课程连堂条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周三"],
                    "time_period": ["下午"],
                    "subject": ["语文"]
                }}
            ]
        }}
        User Input: "初一语文老师周三下午需要安排连堂课"
        Expected JSON Output: {{
            "classification": "课程连堂条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "day": ["周三"],
                    "time_period": ["下午"],
                    "subject": ["语文"]
                }}
            ]
        }}

    """,
    "课程不排同一天条件": """
        User Input: "初一 综合实践1与综合实践2不排同一天"
        Expected JSON Output: {{
            "classification": "课程不排同一天条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "subject": ["综合实践1", "综合实践2"]
                }}
            ]
        }}
    """,
    "课程同一节课最多条件": """
        User Input: "初一初二 信息技术 同一节课最多2个班"
        Expected JSON Output: {{
            "classification": "课程同一节课最多条件",
            "details": [
                {{
                    "grade": ["初一","初二"],
                    "subject": ["信息技术"],
                    "max_classes": 2
                }}
            ]
        }}
    """,
    "课程合班条件": """
        User Input: "体育 张佳辉 初一06班;初一07班合班上课"
        Expected JSON Output: {{
            "classification": "课程合班条件",
            "details": [
                {{
                    "grade": ["初一","初一"],
                    "class": ["6", "7"],
                    "subject": ["体育"],
                    "teacher": ["张佳辉"]
                }}
            ]
        }}
    """,
    "课程走班关联条件": """
        User Input: "初一01班生物与初一03班地理走班关联"
        Expected JSON Output: {{
            "classification": "课程走班关联条件",
            "details": [
                {{
                    "grade": ["初一","初一"],
                    "class": ["1", "3"],
                    "subject": ["生物", "地理"]
                }}
            ]
        }}
    """,
    "课程单双周条件": """
        User Input: "初二 美术(单)与音乐(双) 单双周"
        Expected JSON Output: {{
            "classification": "课程单双周条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "subject": ["美术", "音乐"]
                }}
            ]
        }} （如用户无特殊表明，将单周的课程放在前面）
    """,
    "教师课时条件": """
        User Input: "初一 语文老师 周一第六节 必排"
        Expected JSON Output: {{
            "classification": "教师课时条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "teacher": ["语文老师"],
                    "day": ["周一"],
                    "period": ["6"],
                    "max_classes": 1
                }}
            ]
        }} 
    """,
    "教师各天条件": """
        User Input: "初一 数学老师 周五下午 不排"
        Expected JSON Output: {{
            "classification": "教师各天条件",
            "details": [
                {{
                    "grade": ["初一"],
                    "teacher": ["数学老师"],
                    "day": ["周五"],
                    "time_period": ["下午"],
                    "min_classes": 0
                }}
            ]
        }} 
    """,
    "教师时段条件": """
        User Input: "所有老师 整个周第5节 最多排3节"
        Expected JSON Output: {{
            "classification": "教师时段条件",
            "details": [
                {{
                    "teacher": ["所有老师"],
                    "day": ["周一". "周二", "周三", "周四", "周五"],
                    "period": ["5", "5", "5", "5", "5"],
                    "max_classes": 3
                }}
            ]
        }}
        User Input: "为了照顾刚生完孩子的张老师,周五下午张老师没空"
        Expected JSON Output: {{
            "classification": "教师时段条件",
            "details": [
                {{
                    "teacher": ["张老师"],
                    "day": ["周五"],
                    "period": ["下午"],
                    "max_classes": 0
                }}
            ]
        }}
        User Input: "钟敏 周三第5节第6节 必排"
        Expected JSON Output: {{
            "classification": "教师时段条件",
            "details": [
                {{
                    "teacher": ["钟敏"],
                    "day": ["周三"],
                    "period": ["5","6"],
                    "max_classes": 1
                }}
            ]
        }}
        User Input: "所有老师周四第8节开教师大会，不排课"
        Expected JSON Output: {{
            "classification": "教师时段条件",
            "details": [
                {{
                    "teacher": ["所有老师"],
                    "day": ["周四"],
                    "period": ["8"],
                    "max_classes": 0
                }}
            ]
        }}
    """,
    "教师不排同时上课条件": """
        User Input: "钟敏 张慧 不排同一节"
        Expected JSON Output: {{
            "classification": "教师不排同时上课条件",
            "details": [
                {{
                    "teacher": ["钟敏", "张慧"]
                }}
            ]
        }} 
    """,
    "教师多班连上条件": """
        User Input: "初二数学老师 不同班级的数学课连着上"
        Expected JSON Output: {{
            "classification": "教师多班连上条件",
            "details": [
                {{
                    "grade": ["初二"],
                    "teacher": ["数学老师"]
                }}
            ]
        }} 
        User Input: "初二数学老师希望能够连续教授不同班级的数学课"
        Expected JSON Output: {{
            "classification": "教师多班连上条件",
            "details": [
                {{
                    "grade": ["初二"],
                    "teacher": ["数学老师"]
                }}
            ]
        }} 
    """
}

def generate_json(user_input,classification):
    prompt = f"""
    基于用户输入的情况，提炼出其中的信息并且输出到一个JSON物体。

    可能包含的参数：
    grade：年级，包含“初一”到“初三”
    class：班级，通常以“x班”形式出现，json内需转换为阿拉伯数字表示
    day：一周内的某一天，json内需转换为阿拉伯数字表示。如果包含多天，如“周一到周三”，需分别包括周一、周二、周三三天:[1,2,3]。一整周为周一到周五，周末不上课。
    period：一天内的某一节课，json内需转换为阿拉伯数字表示。如包含多天，需一一对应，如“周一、周二第九节”应该包含"9", "9"两个数字
    subject：课程名称，如“语文”、“数学”。如包含多个课时，需一一对应
    teacher：教师名称，一般为人名
    time_period：某一个时间段，如“上午”、“下午”
    min_classes: 最少排x节课，“必排”的情况下为1
    max_classes: 最多排x节课，“不排”的情况下为0
    记住：需要返回阿拉伯数字的项目，必须为int，不能为string

    例：
    {prompt_templates.get(classification,'Unknown classification. Please return an empty JSON object.')}
    按照例子的格式输出

    现在对于新的用户输入：
    用户输入："{user_input}"
    JSON输出：
    """


    response = client.chat.completions.create(
        model="gpt-4o",  
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )


    return response.choices[0].message.content

#     other：记载额外信息，包含：scenario 2的限制条件，scenario 6最多排课的数量，scenario 10-13对教师的具体排课限制
# 以上参数在json内均为数组
# 不一定要包含所有参数。如果某个参数为空，不包含即可。