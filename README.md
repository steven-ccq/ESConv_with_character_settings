# ESConv_with_character_settings
**工作进程**

**[7.5] 缓解礼貌语气的问题，语言风格更接近聊天；加强了对话与人设的相关性**

**[7.6] 经过反复对比，第二人称人设似乎可以达到比第一人称的表现要好，因此暂定接下来的对话生成中使用第二人称的方式作为人设背景**

**[7.8] 生成了一批新的profile，可见seeker_background.jsonl和supporter_background.jsonl，特征语义表达更丰富**

**[TODO] 正在调整prompt**

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
