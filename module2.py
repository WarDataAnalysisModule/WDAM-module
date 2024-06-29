
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
    elif  characteristic == "개체 탐지":
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 해당 부대가 탐지한 개체, 전투력, 피해 상태를 알려주세요. \
                        Detected_Entity_ID는 탐지된 개체의 ID이다. \
                        탐지된 모든 개체에 대해 분석해주세요. \
             아래는 예시입니다. \
                개체 7: 8280초에 청군 1대대-1중대와의 거리가 973.46250m로 탐지 되었으며, 8880초에 최종 탐지되어 청군 1대대-1중대의 거리는 193.28714m입니다. \
                개체 8: 8220초에 청군 1대대-1중대와의 거리가 983.23653m로 탐지 되었으며, 8910초에 최종 탐지되어 청군 1대대-1중대의 거리는 388.13182m입니다. \
                개체 9: 8220초에 청군 1대대-1중대와의 거리가 974.23594m로 탐지 되었으며, 8880초에 최종 탐지되어 청군 1대대-1중대의 거리는 623.63980m입니다. \
                개체 11: 8430초에 청군 1대대-1중대와의 거리가 966.64618m로 탐지 되었으며, 8880초에 최종 탐지되어 청군 1대대-1중대의 거리는 429.12943m입니다. \
                전투력 변화: 처음 기록된 전투력은 100이었고, 마지막으로 기록된 전투력은 27.27으로, 초기에 비해 30% 감소하였습니다.  \
                피해 상태 변화: 처음 기록된 상태는 NoDamage였고, 마지막으로 기록된 상태는 ModerateDamage입니다. "},
            {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
        ]
    elif characteristic == "부대 정보":
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 각 부대에 대하여 초기 상태와 초기 인원, 초기 장비, 초기 보급품의 개수를 알려주세요.  \
             다음 예시를 참고하여 형식에 맞춰 알려주세요. \
             예시: \
             부대 이름: B-1-1-Unit1(청군 1대대-1중대)\
                - 초기 상태: 아무런 피해 없음\
                - 초기 인원: 소/중위(소총) 1명, 하/중사(소총) 4명, 병(소총) 19명, 병(유탄발사기) 6명, 병(기관총) 3명\
                - 초기 장비: 개인/공용화기(소총) 24개, 개인/공용화기(K201/M203) 6개, 개인/공용화기(K-3) 3개\
                - 초기 보급품: 소총탄 3600발, 기관총탄 3000발, 유탄발사기탄 90발"},
            {"role": "assistant", "content": preprocessed_data}
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
        preprocessed_data = sys.argv[2]
        if len(sys.argv) == 4:
            name = sys.argv[4]
    else:
        print("인자 전달 개수 이상")

    if characteristic == "부대 행동":
        messages = CreateMessage(characteristic, preprocessed_data, name)
    elif characteristic == "부대의 전투력":
        messages = CreateMessage(characteristic, preprocessed_data, name)
    elif characteristic == "부대의 피해 상황":
        messages = CreateMessage(characteristic, preprocessed_data, name)
    elif characteristic == "개체 탐지":
        messages = CreateMessage(characteristic, preprocessed_data, name)
    elif characteristic == "부대 정보":
        name = ""
        messages = CreateMessage(characteristic, preprocessed_data, name)

    result=AnaylizeData(openai, messages)

    # 파일로 저장
    with open("src/main/java/com/back/wdam/analyze/resources/result.txt", "w", encoding="utf-8") as file:
        file.write(result)

    print(result)