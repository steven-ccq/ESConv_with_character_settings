import openai
import pandas as pd
import json

OPENAI_API_KEY = "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"
USE_MODEL = "gpt-3.5-turbo"

openai.api_key = OPENAI_API_KEY

def get_data(content):
    response = openai.ChatCompletion.create(
        model=USE_MODEL,
        messages=content
    )

    return response["choices"][0]["message"]["content"]

file_path = './人设对话.xlsx'
df = pd.read_excel(file_path)
profile_list = df['profile']
prompt = """以下是通过json格式给出的人物设定，请根据人物设定中现有的信息，补全其中缺失的值（value）。如果值为"未知"或"不确定"，请充分发挥创作能力，编写一个。输出保留原json格式
{}
输出保留原json格式
"""

for profile in profile_list:
    content = prompt.format(profile)
    content = [
    {'role': 'system', 'content': '你是一名作家，擅长为角色进行人物设定，使角色丰满立体。'},
    {'role': 'user', 'content': content}
]
    n = 0
    while n < 5:
        try:
            resp = get_data(content)
            with open('filled_profile.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps({'profile': resp}, ensure_ascii=False))
                f.write('\n')
            break
        except Exception as e:
            n += 1
    if n == 5:
        with open('filled_profile.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({'profile': profile}, ensure_ascii=False))
            f.write('\n')