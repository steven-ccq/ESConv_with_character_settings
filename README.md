# ESConv_with_character_settings
## 文件说明
- dial_settings.json 人物设定字段
- self_instruct self-instruct的py文件目录
- scripts self-instruct的sh脚本目录
- fill_profile.py 调用chatGPT填充稀疏的json格式profile
- gen_background.py 调用chatGPT，根据json格式profile生成人物背景
- gen_dial_prompt.py 用于对话生成的prompt
- filled_profile.jsonl 填充完的json格式profile
- seeker_background.jsonl seeker的人物背景
- supporter_background.jsonl supporter的人物背景

## 工作流
1. 获取丰富的json格式profile
2. 将json格式profile转换为文本描述型的人物背景
3. 综合人物背景和记忆，prompt后调用chatGPT生成对话
