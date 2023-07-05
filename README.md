# ESConv_with_character_settings
**工作进程**
**7/4 缓解礼貌语气的问题，语言风格更接近聊天；加强了对话与人设的相关性**
**TODO refine第二人称人设描述，比较第二人称与第一人称设定的对话效果**

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
