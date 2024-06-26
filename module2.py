
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
    elif characteristic == "부대의 전투력":
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 해당 부대의 전투력이 변화된 시각이 언제부터 언제인지, \
             최초 power와 마지막으로 기록된 power를 말해주고, 이들을 비교해서 전투력이 얼마나 감소했는지를 아래와 같은 형식으로 알려주세요.\
             예시: 청군 1대대-1중대의 전투력이 변화된 시각은 1040부터 8940입니다. \
             처음 기록된 전투력은 100이었고, 마지막으로 기록된 전투력은 60으로, 초기에 비해 40% 감소하였습니다.      "},
            {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
        ]
    elif characteristic == "부대의 피해 상황":
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 해당 부대의 Equipment, Member, Supply의 초기 개수와 현재 개수를 모두 알려주세요.  \
             현재 남은 Equipment, Member, Supply의 모든 개수를 알려주세요.\
             아래와 같은 형식으로 알려주세요.\
             예시: 청군 1대대-1중대의 장비는 소총이 30개에서 3개로, K201/M203이 5개에서 2개로 감소했습니다.\
             인원은 소총을 가진 소/중위는 2명에서 1명으로, 소총을 가진 하/중사는 4명에서 1명으로, 소총을 가진 병사는 15명에서 3명으로 감소했습니다.\
             보급품은 소총탄이 2500개에서 2000개로, 기관총탄은 3000개에서 1000개로 감소했습니다.\
             현재 청군 1대대-1중대의 장비는 소총 3개, K201/M203 2개이고, 인원은 소총을 가진 소/중위 1명, 소총을 가진 하/중사 1명, 소총을 가진 병사 3명으로 총 5명이고, 보급품은 소총탄 2000개, 기관총탄 1000개입니다."},
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
    elif characteristic == "부대의 전투력":
        messages = CreateMessage(characteristic, preprocessed_data, name)
    elif characteristic == "부대의 피해 상황":
        messages = CreateMessage(characteristic, preprocessed_data, name)

    result=AnaylizeData(openai, messages)

    # 파일로 저장
    with open("src/main/java/com/back/wdam/analyze/resources/result.txt", "w", encoding="utf-8") as file:
        file.write(result)

    print(result)