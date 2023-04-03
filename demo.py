import asyncio
import EdgeGPT
import uuid
import time

import re

COOKIE_FILE_PATH = './cookie.json'
CHATBOT = {}

def getChatBot(token: str) -> tuple:
    global CHATBOT
    if token in CHATBOT:
        chatBot = CHATBOT[token]['chatBot']
        CHATBOT[token]['useTime'] = time.time()
    else:
        chatBot = EdgeGPT.Chatbot(COOKIE_FILE_PATH)
        token = str(uuid.uuid4())
        CHATBOT[token] = {}
        CHATBOT[token]['chatBot'] = chatBot
        CHATBOT[token]['useTime'] = time.time()
    return token, chatBot


def getStyleEnum(style: str) -> EdgeGPT.ConversationStyle:
    enum = EdgeGPT.ConversationStyle
    if style == 'balanced':
        enum = enum.balanced
    elif style == 'creative':
        enum = enum.creative
    elif style == 'precise':
        enum = enum.precise
    return enum


def getAnswer(data: dict) -> str:
    messages = data.get('item').get('messages')
    if 'text' in messages[1]:
        return messages[1].get('text')
    else:
        return messages[1].get('adaptiveCards')[0].get('body')[0].get('text')


def filterAnswer(answer: str) -> str:
    answer = re.sub(r'\[\^.*?\^]', '', answer)
    answer = answer.rstrip()
    return answer


def needReset(data: dict, answer: str) -> bool:
    maxTimes = data.get('item').get('throttling').get('maxNumUserMessagesInConversation')
    nowTimes = data.get('item').get('throttling').get('numUserMessagesInConversation')
    errorAnswers = ['I’m still learning', '我还在学习']
    if [errorAnswer for errorAnswer in errorAnswers if errorAnswer in answer]:
        return True
    elif nowTimes == maxTimes:
        return True
    return False

# 检查token会让整体响应变慢，直接不用就行
# async def checkToken() -> None:
#     global CHATBOT
#     while True:
#         for token in CHATBOT.copy():
#             if time.time() - CHATBOT[token]['useTime'] > 5 * 60:
#                 await CHATBOT[token]['chatBot'].close()
#                 del CHATBOT[token]
#         await asyncio.sleep(60)



async def api(question):
    ## 获取参数，这里可以修改
    global token
    global style

    token, chatBot = getChatBot(token)
    data = await chatBot.ask(question, conversation_style=getStyleEnum(style))

    if data.get('item').get('result').get('value') == 'Throttled':
        print('已上限,24小时后尝试')

    answer = getAnswer(data)
    answer = filterAnswer(answer)

    print(answer)
    if needReset(data, answer):
        await chatBot.reset()
    return answer


#  translate and improved
async def translate(question):
    translate = "I want you to act as an English translator, spelling corrector and improver. I will speak to you in any language and you will detect the language, translate it and answer in the corrected and improved version of my text, in English. I want you to replace my simplified A0-level words and sentences with more beautiful and elegant, upper level English words and sentences. Keep the meaning same, but make them more literary. I want you to only reply the correction, the improvements and nothing else, do not write explanations. My first sentence is \"I‘m ready\""
    await api(translate)
    res = []
    for sen in question:
        res_temp = await api(sen)
        res.append(res_temp)
    return res


# improved expression
async def writer(question):
    prompt = "Can you help me improve my expression.I will provide my text in the following, you only need to answer " \
             "the revise of the text, the rest please do not reply. My first sentence is \"I‘m ready\" "
    await api(prompt)
    res = []
    for sen in question:
        res_temp = await api(sen)
        res.append(res_temp)
    return res


if __name__ == '__main__':
    token = ""  # 连续对话使用的toke，不用修改，默认开启，如果想要关闭，注释140行即可 （连续对话有限制，目前是20次对话）
    style = 'precise'  # bing的对话有三种模式  1.'balanced',  2. 'creative', 3.'precise' 必须选择其中一种

    # 进行内容提升，翻译：  将内容填充在question列表中，每个值相当于对bing一个提问
    print("Mode: translate improved Mode")
    question = ["北京在中国", "我家在北京"]
    asyncio.run(translate(question))

    # example2 将内容填充在question列表中，每个值相当于对bing一个提问
    print("Mode: revise 模式")
    # question = ["Although the instructions stressed that the assessment of word concreteness would be based on \
    #              experiences involving all senses and motor responses, a comparison with the existing concreteness \
    #              norms indicates that participants, as before, largely focused on visual and haptic experiences. ",
    #             "The reported data set is a subset of a comprehensive list of English lemmas and contains all \
    #             lemmas known by at least 85 % of the raters. It can be used in future research as a reference list \
    #             of generally known English lemmas"]
    # asyncio.run(writer(question))   # 内容节选自 Concreteness ratings for 40 thousand generally known English word lemmas

    # example3 连续对话 直接在命令行中运行Edge.py

    # ... 自行设计适合自己的模板
