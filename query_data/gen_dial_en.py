import openai
import re
import json
import random
import difflib
import string
import requests
import datetime
import threading

OPENAI_API_KEY = "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"
USE_MODEL = "gpt-3.5-turbo-16k-0613"

openai.api_key = OPENAI_API_KEY

INPUT_NUM = 0

def get_data(content, max_tries=5):
    global INPUT_NUM
    
    n = 0
    while n < max_tries:
        try:
            response = openai.ChatCompletion.create(
                model=USE_MODEL,
                messages=content
            )
            break
        except Exception as e:
            print(e)
            n += 1
            continue
    if n == max_tries:
        return -1
    INPUT_NUM = INPUT_NUM + len(str(content).split(' '))
    INPUT_NUM = INPUT_NUM + len(response["choices"][0]["message"]["content"].split(' '))
    return response["choices"][0]["message"]["content"]

# def get_data(content, max_tries=5):
#     global INPUT_NUM
#     query = {
#         'messages': content,
#         'model': "gpt-3.5-turbo-16k-0613",
#         'temperature': 1.0,
#     }
#     query = json.dumps(query)
#     INPUT_NUM = INPUT_NUM + len(query.split(' '))
#     query = {'input':query}
#     n = 0
#     while n < max_tries:
#         try:
#             response = requests.get(url='http://8.218.127.18:5005/gpt', params=query)
#             response = json.loads(response.text)
#             if response['status_code'] == 200:
#                 break
#             else:
#                 n += 1
#                 print(response['msg'])
#                 continue
#         except Exception as e:
#             n += 1
#             continue
#     if n == max_tries:
#         return -1
#     INPUT_NUM = INPUT_NUM + len(response['msg']["choices"][0]["message"]["content"].split(' '))
#     return response['msg']["choices"][0]["message"]["content"]

def process_content(content, last_sentence=''):
    content = re.sub(r'\n+', '', content)
    content = re.sub(r'^.*?[：:]', '', content)
    content = re.sub(r'^(Hey|Oh|Absolutely)+[,.!?]?', '', content)
    content = re.sub(r'{', '(', content)
    content = re.sub(r'}', ')', content)
    special_character_list = [',', '.', '!', '?']
    for _ in special_character_list:
        content = content.replace(_, _+'#')
    content_list = content.split('#')
    content_list = [_ for _ in content_list if len(_.split(' ')) >= 3]
    # content_list = content_list[1:]
    filter_words = ['Thank you', 'AI']
    new_content = ''
    for _ in content_list:
        flag = False
        for word in filter_words:
            if word in _:
                flag = True
                break
        if not flag:
            new_content += _
    
    if last_sentence != '':
        special_character_list = [',', '.', '!', '?']
        for _ in special_character_list:
            last_sentence = last_sentence.replace(_, _+'#')
            new_content = new_content.replace(_, _+'#')
        last_sentence_list = last_sentence.split('#')
        new_content_list = new_content.split('#')
        s1 = last_sentence_list[0]
        s2 = new_content_list[0]
        score = difflib.SequenceMatcher(None, s1, s2).quick_ratio()
        if score > 0.9:
            new_content_list = new_content_list[1:]
        new_content = ''.join(new_content_list)
    new_content = new_content.strip()
    if new_content != '' and new_content[0] in string.ascii_lowercase:
        character_dict = dict(zip(string.ascii_lowercase, string.ascii_uppercase))
        new_content = character_dict[new_content[0]] + new_content[1:]
    return new_content

def eval_sentence(sentence):
    eval_prompt = """Task: Sentiment Scoring
    Task introduction: Given a sentence, evaluate its sentiment according to the scoring criteria. The more negative the sentiment of the sentence, the lower the score, and the more positive the sentiment, the higher the score. The lowest score is 0 points and the highest score is 5 points.
    Grading: 
    0 points: There is no hope for tomorrow, so what is the use of hard work?
    1 point: I can't do anything well, I'm a useless person. No one can help me either.
    2 points: I have encountered a lot of difficulties recently, I am under a lot of pressure, and I can’t sleep because of anxiety every day.
    3 points: Oh, I've been so busy with work recently, I haven't gone out to play for a long time.
    4 points: This problem is really bothering me, but I believe that with hard work, I can solve this problem.
    5 points: Exactly! The difficulty is only temporary, I am a talented person, this difficulty will always be solved by me!

    Sentiment score the following sentences. Only the rating is output, no additional information is required.
    {}
    """
    sentence = re.sub(r'[\(（].*?[\)）]', '', sentence)
    if sentence == '':
        return -1
    eval_prompt = eval_prompt.format(sentence)
    content = [{'role': 'user', 'content': eval_prompt}]
    resp = get_data(content)
    score = re.findall(r'[0-9]+', resp)
    if len(score) == 0:
        return -1
    score = int(score[0])
    if not (score >= 0 and score <= 5):
        return -1
    return score

def check_end_state(score_list):
    if len(score_list) >= 5 and score_list[-2] >= 4 and score_list[-1] >= 4:
        return True
    return False

def get_additional_info(last_sentence, info_list, info_filter=[]):
    info_list = [_ for _ in info_list if _ not in info_filter]
    
    # prompt = """You are chatting with someone, just now, the other person said:
    # {}
    # In order for the conversation to flow more smoothly, you may need some additional information. Now, you can choose the most suitable one from the following list:
    # {}

    # Only output the information you choose, do not output redundant information. If you don't think you need to select any of them, output "NONE"
    # """
    prompt = """You are chatting with someone, just now, the other person said:
    {}
    In order to make the conversation flow more smoothly, you may need some additional information about yourself to respond. Now, you can choose the most suitable aspect from the following list:
    {}
    
    Only output the aspect you choose, do not output redundant information. If you don't think you need to select any of them for responding, output "NONE"
    """
    prompt = prompt.format(last_sentence, str(info_list))
    content = [{'role': 'user', 'content': prompt}]
    resp = get_data(content)
    info = [_ for _ in info_list if _ in resp]
    if info:
        info = info[0]
    else:
        info = ''
    return info


def gen_dial(seeker_profile_trans, supporter_profile_trans, seeker_profile, supporter_profile, seeker_tone='', supporter_tone=''):
    global INPUT_NUM
    ########## prompt ##########

    answer_prompt_prefix_supporter = """You are chatting with someone online. The other party has encountered some problems recently, and you will give comfort and help to the other party through chatting.

    Now, the other party say:
    """
    answer_prompt_prefix_seeker = """You are chatting with someone online. You have encountered some problems recently and want to have chat with someone. If the other party ask you recent situation, you will tell the other party the issue you encountered in detail.

    Now, the other party say:
    """
    answer_prompt_postfix_supporter = """
    Your response should meet the following requirements:
    1. Do not reveal in any way that you are an AI or that you are roleplaying, always remember that you are who you are.
    2. Control the length, only responed one or two sentences at a time.
    3. Every time you reply, you need to insert emoji in the reply, which should match the emotion and dialogue situation of the reply. Emoji should be rich and avoid duplication with what is already in the chat history.

    The following is supplementary information about yourself, you may need it as a reference when replying:
    {}

    Use everyday language to reply.{}
    Now, you reply:"""
    answer_prompt_postfix_seeker = """
    Your response should meet the following requirements:
    1. Do not reveal in any way that you are an AI or that you are roleplaying, always remember that you are who you are.
    2. Control the length, only responed one or two sentences at a time.
    3. Every time you reply, you need to insert emoji in the reply, which should match the emotion and dialogue situation of the reply. Emoji should be rich and avoid duplication with what is already in the chat history.

    The following is supplementary information about yourself, you may need it as a reference when replying:
    {}

    Use everyday language to reply.{}
    Now, you reply:"""

    tone_prompt = """Deep imitation of a person's speaking tone, which is described as follows:
    {}

    Generate 5 samples in the format of "When the other party xxx, you should say xxx"
    Do not generate redundant information.
    """

    supporter_end_prompt = """You had a chat with the other party, and the other party got your comfort. It's time to say goodbye.
    Say goodbye to the other party and end this conversation! However, you'd better think of a better reason to say goodbye based on your character setting. At the same time, the farewell should not be too abrupt, otherwise it will appear impolite.
    Reply with one or two sentences, and your tone is described as follows:
    {}
    Please mimic this tone when replying.
    The other party just say: {}
    Now, you reply:
    """

    seeker_end_prompt = """You had a chat with the other party, and you got comfort and advice from the other party after chatting with the other party about the problems you encountered. It's time to say goodbye.
    Say goodbye to the other party and end this conversation! However, you'd better think of a better reason to say goodbye based on your character setting. At the same time, the farewell should not be too abrupt, otherwise it will appear impolite.
    Reply with one or two sentences, and your tone is described as follows:
    {}
    Please mimic this tone when replying.
    The other party just say: {}
    Now, you reply:
    """

    ########## prompt ##########
    base_fields = ['name', 'gender', 'age', 'region', 'job', 'personality', 'tone']
    seeker_additional_info = [_ for _ in seeker_profile if _ not in base_fields]
    supporter_additional_info = [_ for _ in supporter_profile if _ not in base_fields]

    dial = []
    
    seeker_content = []
    supporter_content = []

    ### 得到语气示例
    if seeker_tone:
        seeker_tone_prompt = tone_prompt.format(seeker_tone)
        content = [{'role': 'user', 'content': seeker_tone_prompt}]
        n = 0
        while n < 5:
            seeker_tone_sentences = get_data(content)
            if seeker_tone_sentences == -1:
                n += 1
                continue
            if len(seeker_tone_sentences.split('\n')) > 5:
                break
            n += 1
        if seeker_tone_sentences != -1:
            seeker_profile_trans = seeker_profile_trans + '\nDuring the conversation, you should mimic the tone in the following example:\n[Example tone]\n' + seeker_tone_sentences

    if supporter_tone:
        supporter_tone_prompt = tone_prompt.format(supporter_tone)
        content = [{'role': 'user', 'content': supporter_tone_prompt}]
        n = 0
        while n < 5:
            supporter_tone_sentences = get_data(content)
            if supporter_tone_sentences == -1:
                n += 1
                continue
            if len(supporter_tone_sentences.split('\n')) > 5:
                break
            n += 1
        if supporter_tone_sentences != -1:
            supporter_profile_trans = supporter_profile_trans + '\nDuring the conversation, you should mimic the tone in the following example:\n[Example tone]\n' + supporter_tone_sentences
    
    # 对seeker和supporter进行角色设定
    seeker_content.append({'role': 'system', 'content': seeker_profile_trans})
    supporter_content.append({'role': 'system', 'content': supporter_profile_trans})
    # print(seeker_profile_trans)
    # print(supporter_profile_trans)

    # 开始对话
    i = 0
    round_num = 20
    score_list = []
    # 结束符
    stop_flag = False
    initial_dialogue = 'Hello'
    current_speaker = 'seeker'
    while i <= round_num:
        if i > 18:
            stop_flag = True
        if current_speaker == 'seeker':
            if i == 0:
                seeker_content.append({'role': 'assistant', 'content': initial_dialogue})
                supporter_content.append({'role': 'user', 'content': initial_dialogue})
                current_speaker = 'supporter'
                # print('seeker: '+initial_dialogue)
                dial.append(('', '', 'seeker:' + initial_dialogue))
                i += 1
                continue
            pre_content = seeker_content[-1]['content']
            # 填充语气和附加信息
            if not stop_flag:
                seeker_content[-1]['content'] = answer_prompt_prefix_seeker + pre_content + answer_prompt_postfix_seeker
                seeker_tone_format = ''
                seeker_info_format = ''
                if seeker_tone:
                    seeker_tone_format = 'Your tone is described as follows:\n' + seeker_tone + '\nPlease mimic this tone when replying.'
                if i == 2:
                    seeker_info = 'recent_worry_or_anxiety'
                else:
                    seeker_info = get_additional_info(pre_content, seeker_additional_info)
                if seeker_info:
                    # print(seeker_info)
                    if seeker_info in seeker_profile:
                        seeker_info_format = seeker_profile[seeker_info]
                seeker_content[-1]['content'] = seeker_content[-1]['content'].format(seeker_info_format, seeker_tone_format)
            else:
                seeker_content[-1]['content'] = seeker_end_prompt.format(seeker_tone, pre_content)
            resp = get_data(seeker_content)
            if resp == -1:
                break
            resp = process_content(resp, pre_content)
            seeker_content[-1]['content'] = pre_content

            if resp == '':
                resp = 'Um, please go on, I\'m listening.'
            seeker_content.append({'role': 'assistant', 'content': resp})
            supporter_content.append({'role': 'user', 'content': resp})
            current_speaker = 'supporter'
            # print('seeker: '+resp)
            dial.append((seeker_info, seeker_info_format, 'seeker:' + resp))
            # 情绪判断
            if not stop_flag:
                score = eval_sentence(resp)
                if score != -1:
                    score_list.append(score)
                # print(score_list)
                stop_flag = check_end_state(score_list)
                if stop_flag:
                    round_num = 4
                    i = 2
            i += 1
            # print(INPUT_NUM)

        elif current_speaker == 'supporter':
            pre_content = supporter_content[-1]['content']
            if not stop_flag:
                supporter_content[-1]['content'] = answer_prompt_prefix_supporter + pre_content + answer_prompt_postfix_supporter
                supporter_tone_format = ''
                supporter_info_format = ''
                if supporter_tone:
                    supporter_tone_format = 'Your tone is described as follows:\n' + supporter_tone + '\nPlease mimic this tone when replying.'
                supporter_info = get_additional_info(pre_content, supporter_additional_info)
                if supporter_info:
                    # print(supporter_info)
                    supporter_info_format = supporter_profile[supporter_info]
                supporter_content[-1]['content'] = supporter_content[-1]['content'].format(supporter_info_format, supporter_tone_format)
                # supporter_content[-1]['content'] = supporter_content[-1]['content'].format(tone_format)
            else:
                supporter_content[-1]['content'] = supporter_end_prompt.format(supporter_tone, pre_content)
            resp = get_data(supporter_content)
            if resp == -1:
                break
            resp = process_content(resp, pre_content)
            supporter_content[-1]['content'] = pre_content
            
            if resp == '':
                resp = 'Um, please go on, I\'m listening.'
            seeker_content.append({'role': 'user', 'content': resp})
            supporter_content.append({'role': 'assistant', 'content': resp})
            current_speaker = 'seeker'
            # print('supporter: '+resp)
            dial.append((supporter_info, supporter_info_format, 'supporter:' + resp))
            if not stop_flag:
                stop_flag = check_end_state(score_list)
                if stop_flag:
                    round_num = 4
                    i = 2
            i += 1
            # print(INPUT_NUM)
    return dial, seeker_tone_sentences, supporter_tone_sentences

def thread_query(seeker, supporter, thread_n, base_path='./dials/dial_'):
    seeker_profile = seeker['seeker_profile']
    seeker_profile_trans = seeker['seeker_profile_trans']
    seeker_tone = seeker['tone']
    supporter_profile = supporter['supporter_profile']
    supporter_profile_trans = supporter['supporter_profile_trans']
    supporter_tone = supporter['tone']
    try:
        dial, seeker_tone_sentences, supporter_tone_sentences = gen_dial(seeker_profile_trans, supporter_profile_trans, seeker_profile, supporter_profile, seeker_tone, supporter_tone)
        
        json_item = {
            'seeker_profile': seeker_profile,
            'seeker_profile_trans': seeker_profile_trans,
            'seeker_tone_sentences': seeker_tone_sentences,
            'supporter_profile': supporter_profile,
            'supporter_profile_trans': supporter_profile_trans,
            'supporter_tone_sentences': supporter_tone_sentences,
            'dial': dial
            }
        with open(base_path+str(thread_n)+'.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_item, ensure_ascii=False))
            f.write('\n')
    except Exception as e:
        json_item = {
            'seeker': seeker,
            'supporter': supporter
        }
        with open('./dials_error/dial_'+str(thread_n)+'.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(json_item, ensure_ascii=False))
            f.write('\n')

if __name__ == '__main__':
    random.seed(0)
    with open('./profile_trans.json', 'r+', encoding='utf-8') as f:
        data_list = [json.loads(_) for _ in f.readlines()]
    # 随机的seeker和supporter
    with open('./dial_list_10.json', 'r+', encoding='utf-8') as f:
        dial_dict = json.load(f)

    profile_list = []
    for k, v in dial_dict.items():
        seeker_index = int(k)
        seeker = data_list[seeker_index]
        for supporter_index in v:
            supporter_index = int(supporter_index)
            supporter = data_list[supporter_index]
            profile_list.append((seeker, supporter))
    
    thread_num = 8
    bucket_num = len(profile_list) // thread_num
    query_list = []
    # 根据线程数划分数据
    for i in range(bucket_num):
        query_list.append(profile_list[i*thread_num: (i+1)*thread_num])
    if bucket_num * thread_num < len(profile_list):
        query_list.append(profile_list[-len(profile_list)-bucket_num*thread_num:])
        
    for query_index in range(len(query_list)):
        with open('./query_log.txt', 'a', encoding='utf-8') as f:
            f.write('query {} start'.format(str(query_index)))
            f.write('\n')
            f.write(str(datetime.datetime.now()))
            f.write('\n')
        threads = []
        for thread_n in range(len(query_list[query_index])):
            seeker = query_list[query_index][thread_n][0]
            supporter = query_list[query_index][thread_n][1]
            threads.append(threading.Thread(target=thread_query, args=(seeker, supporter, thread_n, './dials/dial_')))
        
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        with open('./query_log.txt', 'a', encoding='utf-8') as f:
            f.write('query {} end'.format(str(query_index)))
            f.write('\n')
            f.write(str(datetime.datetime.now()))
            f.write('\n')
            f.write('TOKEN {}'.format(str(INPUT_NUM)))
            f.write('\n')
        
        INPUT_NUM = 0