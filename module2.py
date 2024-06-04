
"""
분석
"""
def AnaylizeData(openai,messages):
    chat_completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    result=chat_completion.choices[0].message.content
    return result

###################################################################################################

"""
breif: ChatGPT API에 입력할 메시지 작성
param1: input_texts 추출한 로그
"""
def CreateMessage(characteristic, preprocessed_data, name):
    messages = []
    if characteristic == "부대 행동":
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 해당 부대가 주로 수행한 과업은 무엇인지, \
             각 과업에 소요한 시간은 얼마인지, 무슨 과업을 수행했는지 등을 알려주세요.\
             예시: 청군 1대대-1중대는 최초 전술기동 후 점령 과업을 수행하였습니다.\
             부대가 주로 수행한 과업은 '점령'입니다.       "},
            {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
        ]
    return messages



# -*- coding: utf-8 -*-
import sys

if __name__ == "__main__":

    # ChatGPT Connect
    import os
    import openai
    os.environ.get('OPENAI_API_KEY') is None
    os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if len(sys.argv) > 2:
        characteristic = sys.argv[1]
        name = sys.argv[2]
        preprocessed_data = sys.argv[3]
    else:
        print("인자 전달 개수 이상")

    if characteristic == "부대 행동":
        messages = CreateMessage(characteristic, preprocessed_data, name)

    result=AnaylizeData(openai, messages)

    # 파일로 저장
    with open("src/main/java/com/back/wdam/analyze/resources/result.txt", "w", encoding="utf-8") as file:
        file.write(result)

    print(result)