
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
def CreateMessage(characteristic, preprocessed_data, name, std_config_path):
    messages = []
    if characteristic=="부대 이동 속도 / 위치 변화": # 1
        with open(std_config_path, "r", encoding="utf-8") as file: # 분석 기준
            std=file.read()
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 한다."},
            {"role": "user", "content": "데이터는 다음 필드로 구성되어 있다."
                                        "simulation time(시간 sec), positionLat(경도), positionLong(위도), positionAlt(고도), speed(이동 속도 km/h)"
                                        "simulation time을 이용하여 총 관측 시간을 구하고,"
                                        "첫 번째 데이터와 마지막 데이터의 경도, 위도, 고도 데이터를 이용하여 총 이동 거리를 구하여라."
                                        "분석 기준에 따라 이동 속도를 분석하라."
                                        "분석 기준: "+std+" "
                                                      "분석 결과의 예시는 다음과 같다."
                                                      "총 관측 시간은 3000초로 50분에 해당합니다"
                                                      "이동 시작 지점은 위도 38.05, 경도 127.16, 고도 103이고, 도착 지점은 위도 38.06, 경도 127.17, 고도 56로"
                                                      "수평 거리와 고도 변화를 고려한 총 이동 거리는 약 1416.07m로, 약 1.42km입니다."
                                                      "대부분 1km/h 이하의 느린 속도로 이동하였습니다."
             },
            {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
        ]
    elif characteristic=="인원/장비 수량 변화": # 2
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 한다."},
            {"role": "user", "content": "주어진 데이터는 "+name+" 부대의 초기 상태 및 인원, 장비 수량에 대한 정보와 "+name+"부대가 참여한 전투를 관측한 기록이다.\
             source는 공격의 주체이고, target은 공격의 대상이다. source_unit_id, target_unit_id로 전투에 참여한 부대의 id를 알 수 있다.\
             가장 마지막 데이터를 통해"+name+" 부대의 최종 인원/장비 수량을 알 수 있다. \
             전투 결과 보고를 목적으로 데이터를 분석하라. 필수적으로 들어가야 하는 내용은 다음과 같다. 정리한 결과를 토대로 해당 부대의 전투에 대해 분석하라.\
             "+name+" 부대의 초기 인원, 장비 수량/\
             "+name+" 부대의 최종 인원, 장비 수량을 초기와 비교하여 손실 분석/\
             전투한 모든 부대들의 id와 "+name+"부대와의 전투로 상대 부대들이 입은 피해와 상대 부대들로 인해 입은 피해를 부대별로 정리.\n\
             데이터는 다음과 같다."+preprocessed_data}
        ]
    elif characteristic == "부대의 전투력": # 3
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 부대의 전투력이 변화된 시각이 언제부터 언제인지, \
             최초 power와 마지막으로 기록된 power를 말해주고, 이들을 비교해서 전투력이 얼마나 감소했는지를 알려주세요.\
             최초 power와 마지막으로 기록된 power 사이의 증가량에서 부대의 전투력이 변화된 시각의 증가량을 나눠서 0.1보다 크다면 급격하게 감소되었다고 아래와 같은 형식으로 알려주세요. \
             예시: \
             청군 1대대-1중대의 전투력은 완만하게 감소되었습니다. \
             청군 1대대-1중대의 전투력이 변화된 시각은 1040부터 8940입니다. \
             처음 기록된 전투력은 100이었고, 마지막으로 기록된 전투력은 60으로, 초기에 비해 40% 감소하였습니다.\
             1040부터 8940까지의 시간동안 전투력은 100에서 60으로 감소하였으므로 부대의 전투력은 완만하게 감소되었습니다. "},
            {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
        ]
    elif characteristic == "부대의 피해 상황": # 4
        messages = messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
            {"role": "user", "content": "데이터를 분석하여 해당 부대에서 power가 가장 많이 줄어든 시간대와 행동이름을 알려주고 \
             부대의 주요 BehaviorName의 종류와 해당 BehaviorName이 포함된 데이터의 비율을 알려주세요.\
             아래와 같은 문장형식으로 알려주세요.\
             예시: \
             청군 4중대-2기관총분대는 2:40에 근접전투로 인하여 가장 큰 손실이 발생하였습니다.\
             청군의 주요 손실 유형은 직접사격이며, 피해 상태의 50%가 직접사격으로 발생하였습니다.\
             따라서 청군 4중대-2기관총분대는 직접사격으로 인하여 부대의 대부분에 피해가 갔습니다."},
            {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
        ]
    elif characteristic == "부대 행동": # 5
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

    print("***************\n\n module 2 is processing \n\n***************")

    # ChatGPT Connect
    import os
    import openai
    os.environ.get('OPENAI_API_KEY') is None
    os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if len(sys.argv) not in [6, 7]:
        print("인자 전달 개수 이상")
        sys.exit(1)

    temp_file_path = sys.argv[0]
    user_idx = sys.argv[1]
    log_created = sys.argv[2]
    characteristic = sys.argv[3]
    preprocessed_data = sys.argv[4]
    std_config_path = sys.argv[5]
    if len(sys.argv) == 7:
        name = sys.argv[6]
    else:
        name = None

    print("std_config_path: ", std_config_path)

    if characteristic=="부대 이동 속도 / 위치 변화":
        messages=CreateMessage(characteristic, preprocessed_data, name, std_config_path)
    elif characteristic == "인원/장비 수량 변화":
        messages = CreateMessage(characteristic, preprocessed_data, name, std_config_path)
    elif characteristic == "부대의 전투력":
        messages = CreateMessage(characteristic, preprocessed_data, name, std_config_path)
    elif characteristic == "부대의 피해 상황":
        messages = CreateMessage(characteristic, preprocessed_data, name, std_config_path)
    elif characteristic == "부대 행동":
        messages = CreateMessage(characteristic, preprocessed_data, name, std_config_path)
    else:
        messages=[]

    result=AnaylizeData(openai, messages)

    # 전처리된 데이터를 작성할 경로
    output_file_path = os.path.join(os.getcwd(), "result.txt")
    # 파일에 데이터 쓰기
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(result)

    print(f"Data written to {output_file_path}")

    print(result)