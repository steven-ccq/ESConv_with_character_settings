import openai
import pandas as pd
import json
import re
import time

OPENAI_API_KEY = "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"
USE_MODEL = "gpt-3.5-turbo"
MAX_NUM = 5

openai.api_key = OPENAI_API_KEY

def get_data(content):
    response = openai.ChatCompletion.create(
        model=USE_MODEL,
        messages=content
    )

    return response["choices"][0]["message"]["content"]

def get_profile(profile, mode='all'):
    profile = re.sub(r'\s+', '', profile)
    if mode == 'all':
        profile = re.findall(r'{.*?}', profile)
        if len(profile) != 3:
            return ''
        return profile
    elif mode == 'seeker':
        profile = re.findall(r'seeker_profile[：:"]+{.*?}', profile)
        if not profile:
            return ''
        profile = profile[0]
        profile = re.sub(r'seeker_profile[：:"]+\s+', '', profile)
        return profile
    elif mode == 'supporter':
        profile = re.findall(r'(supporter_profile)?[：:"]+{.*?}', profile)
        if not profile:
            return ''
        profile = profile[0]
        profile = re.sub(r'(supporter_profile)?[：:"]+\s+', '', profile)
        return profile
    elif mode == 'global_settings':
        profile = re.findall(r'global_settings[：:"]+{.*}', profile)
        if not profile:
            return ''
        profile = profile[0]
        profile = re.sub(r'global_settings[：:"]+\s+', '', profile)
        return profile

def parse_global_settings(profile):
    issue = re.findall(r'(?<=问题":").*?(?=",)', profile)
    if issue:
        issue = issue[0]
    else:
        issue = ''
    statement = re.findall(r'(?<=描述":").*?(?=",)', profile)
    if statement:
        statement = statement[0]
    else:
        statement = ''
    return {'issue': issue, 'statement': statement}

trans_prompt = """任务：将以下通过json格式给出的人物设定使用文字描述进行改写。改写时使用第二人称进行描述(你是...)。
人物设定(json格式)：
{}
对未提到的信息，根据已有的设定对其进行补全。
"""

# seeker_background_system = '你正在与别人倾诉烦恼，获取情感支持。你将介绍自己，并分享自己遇到的问题。'
# seeker_background_prompt = """以下是你的个人信息和遇到的问题：
# {seeker_profile}
# 遇到的问题：{issue}
# 问题描述：{statement}

# 根据以上个人信息和遇到的问题，写一个200字左右的简短介绍，讲述你遇到当前问题的原因。你可以发挥想象力，但是故事需要符合你的个人信息。
# 请注意，输出不需要分段。
# """

seeker_system = '任务:人物扮演\n人物设定:\n{}'
seeker_prompt = """以下是你当前遇到的问题:
遇到的问题: {}
问题描述: {}

根据你的人物设定和遇到的问题，写一个200字左右的简短介绍，讲述你自己和遇到当前问题的原因。
你可以发挥想象力，不需要受到人物设定的限制。但是请注意，介绍的语气和内容需要符合人物设定。
输出不需要分段。
"""

experience_system = '任务:人物扮演\n人物设定:\n{}'
experience_prompt = """分享3个让你印象深刻的记忆和3个你最近经历的事情。记忆和事情不一定是真实的，有消极的，也有积极的。你无需受到限制，你可以自由地发挥想象力，但是需要符合你的个人信息。

输出格式：
{
    "印象深刻的记忆": {
        "记忆1": "",
        "记忆2": "",
        "记忆3": ""
    },
    "最近经历的事件": {
        "事件1": "",
        "事件2": "",
        "事件3": ""
    }
}
"""

supporter_system = '任务:人物扮演\n人物设定:\n{}'
supporter_prompt = """写一个200字左右的简短介绍，介绍你自己。
你可以发挥想象力，不需要受到人物设定的限制。但是请注意，介绍的语气和内容需要符合人物设定。
输出不需要分段。
"""

def get_seeker_background(file_path='./filled_profile.jsonl'):
    with open(file_path, 'r+', encoding='utf-8') as f:
        profile_list = [json.loads(_)['profile'] for _ in f.readlines()]

    seeker_item = {
        'profile': '',
        'seeker_profile': '',
        'seeker_profile_trans': '',
        'issue': '',
        'statement': '',
        'background': '',
        'experience': ''
    }
    
    for profile in profile_list:
        # parse profile
        profile_list = get_profile(profile)
        if profile_list:
            seeker_profile = profile_list[1]
            global_settings = profile_list[2]
        else:
            seeker_profile = get_profile(profile, mode='seeker')
            global_settings = get_profile(profile, mode='global_settings')
        parsed_info = parse_global_settings(global_settings)
        issue = parsed_info['issue']
        statement = parsed_info['statement']
        if seeker_profile == '':
            seeker_item['profile'] = profile
            seeker_item['seeker_profile'] = ''
            seeker_item['seeker_profile_trans'] = ''
            seeker_item['background'] = ''
            seeker_item['experience'] = ''
            seeker_item['issue'] = issue
            seeker_item['statement'] = statement
            with open('./seeker_background.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(seeker_item, ensure_ascii=False))
                f.write('\n')
            continue
        # transforme seeker's json profile
        prompt = trans_prompt.format(seeker_profile)
        content = [
            {'role': 'user', 'content': prompt}
        ]
        n = 0
        seeker_profile_trans = ''
        while n < MAX_NUM:
            try:
                seeker_profile_trans = get_data(content)
                break
            except Exception as e:
                n += 1
                time.sleep(10)
        if seeker_profile_trans == '':
            seeker_profile_trans = seeker_profile
        # get seeker's background
        system = seeker_system.format(seeker_profile_trans)
        prompt = seeker_prompt.format(issue, statement)
        content = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ]
        n = 0
        seeker_background = ''
        while n < MAX_NUM:
            try:
                seeker_background = get_data(content)
                break
            except Exception as e:
                n += 1
                time.sleep(10)
        # get seeker's experience
        system = experience_system.format(seeker_profile_trans)
        prompt = experience_prompt
        content = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ]
        n = 0
        seeker_experience = ''
        while n < MAX_NUM:
            try:
                seeker_experience = get_data(content)
                break
            except Exception as e:
                n += 1
                time.sleep(10)
        seeker_item['profile'] = profile
        seeker_item['seeker_profile'] = seeker_profile
        seeker_item['seeker_profile_trans'] = seeker_profile_trans
        seeker_item['background'] = seeker_background
        seeker_item['experience'] = seeker_experience
        seeker_item['issue'] = issue
        seeker_item['statement'] = statement
        with open('./seeker_background.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(seeker_item, ensure_ascii=False))
            f.write('\n')

def get_supporter_background(file_path='./filled_profile.jsonl'):
    with open(file_path, 'r+', encoding='utf-8') as f:
        profile_list = [json.loads(_)['profile'] for _ in f.readlines()]

    supporter_item = {
        'profile': '',
        'supporter_profile': '',
        'supporter_profile_trans': '',
        'background': ''
    }

    for profile in profile_list:
        profile_list = get_profile(profile)
        if profile_list:
            supporter_profile = profile_list[0]
        else:
            supporter_profile = get_profile(profile, mode='supporter')
        if supporter_profile == '':
            supporter_item['profile'] = profile
            supporter_item['supporter_profile'] = ''
            supporter_item['supporter_profile_trans'] = ''
            supporter_item['background'] = ''
            with open('./seeker_background.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(supporter_item, ensure_ascii=False))
                f.write('\n')
            continue
        # transforme supporter's json profile
        prompt = trans_prompt.format(supporter_profile)
        content = [
            {'role': 'user', 'content': prompt}
        ]
        n = 0
        supporter_profile_trans = ''
        while n < MAX_NUM:
            try:
                supporter_profile_trans = get_data(content)
                break
            except Exception as e:
                n += 1
                time.sleep(10)
        if supporter_profile_trans == '':
            supporter_profile_trans = supporter_profile
        # get supporter's background
        system = supporter_system.format(supporter_profile_trans)
        prompt = supporter_prompt
        content = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ]
        n = 0
        supporter_background = ''
        while n < MAX_NUM:
            try:
                supporter_background = get_data(content)
                break
            except Exception as e:
                n += 1
                time.sleep(10)
        supporter_item['profile'] = profile
        supporter_item['supporter_profile'] = supporter_profile
        supporter_item['supporter_profile_trans'] = supporter_profile_trans
        supporter_item['background'] = supporter_background
        with open('./supporter_background.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(supporter_item, ensure_ascii=False))
            f.write('\n')

if __name__ == '__main__':
    # get_seeker_background()
    get_supporter_background()