import subprocess
import sys
import re

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 필요한 패키지 목록
required_packages = [
    "mysql-connector-python",
    "pandas",
    "openai"
]

# 패키지 설치
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install_package(package)

# -*- coding: utf-8 -*-
import mysql.connector
import pandas as pd     # Chat GPT에게 넘겨주기 위해 데이터프레임->텍스트로 변환
import os
import openai
import sys

"""
brief: 데이터베이스와 연결
return: conn, cursor 객체
"""
def DatabaseConnect():
    conn = mysql.connector.connect(
                
            )
    cursor=conn.cursor(buffered=True) # 커서 생성
    return conn, cursor

###################################################################################################

"""
brief: 사용자가 선택한 부대의 ID를 Unit_List 테이블에서 찾기
param1: 부대명
param2: 유저 인덱스
param3: 시뮬레이션 일자
param4: 데이터베이스 커서
return: 부대 ID
"""
def FindID(name, user_idx, log_created, cursor):
    query = "SELECT list_idx FROM unit_list WHERE unit_name = %s AND user_idx=%s AND simulation_time=%s"
    cursor.execute(query, (name,user_idx, log_created))
    id = cursor.fetchone()
    id=id[0]
    return id

###################################################################################################
"""
brief: '1. 부대 속도 위치 변화' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 유저 인덱스
param3: 시뮬레이션 일자
param4: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_UnitSpeed(id, user_idx, log_created, cursor):

#     print("ID:", id)
#     print("User ID:", user_idx)
#     print("Log Created:", log_created)

    query = "SELECT simulation_time, position_lat, position_lon, position_alt, speed FROM unit_attributes WHERE list_idx = %s AND created_at=%s AND user_idx=%s"
    cursor.execute(query, (id, log_created, user_idx))
    result=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'positionLat', 'positionLon', 'positionAlt', 'speed'])

    # 텍스트로 변환
    input_texts=[]
    input_texts.append("SimulationTime \t positionLat \t positionLon \t positionAlt \t speed")
    for index, row in dataframe.iterrows():
        text=f"{row['SimulationTime']} \t {row['positionLat']} \t {row['positionLon']} \t {row['positionAlt']} \t {row['speed']}"
        input_texts.append(text)

    input_texts='\n'.join(input_texts)
    return input_texts

###################################################################################################
"""
brief: '2. 인원/장비 수량 변화' 특성 로그 선택
param1: 부대 ID
param2: 유저 인덱스
param3: 시뮬레이션 일자
param4: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_Event(id, user_idx, log_created, cursor):

#     print("ID:", id)
#     print("User ID:", user_idx)
#     print("Log Created:", log_created)

    # init 파일에서 초기 상태를 추출
    query1 = "SELECT unit_name, status, member, equipment, supply FROM unit_init WHERE list_idx = %s AND created_at = %s AND user_idx = %s"
    cursor.execute(query1, (id, log_created, user_idx))
    result1 = cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe1=pd.DataFrame(result1, columns=['unit_name', 'status', 'member', 'equipment', 'supply'])

    # 텍스트로 변환
    input_texts=[]
    input_texts.append("해당 부대의 초기 상태 및 인원, 장비 수량")
    input_texts.append("id \t unit_name \t status \t member \t equipment \t supply")
    for index, row in dataframe1.iterrows():
        text=f"{id} \t {row['unit_name']} \t {row['status']} \t {row['member']} \t {row['equipment']} \t {row['supply']}"
        input_texts.append(text)

    # event 파일에서 해당 부대 데이터 추출
    query2 = "SELECT source_list_idx, target_list_idx, simulation_time, behavior_name, source_member, target_member, \
        source_equipment, target_equipment, source_supply, target_supply, distance FROM event \
            WHERE (source_list_idx = %s OR target_list_idx = %s) AND created_at=%s AND user_idx=%s"
    cursor.execute(query2, (id,id, log_created, user_idx))
    result2=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe2=pd.DataFrame(result2, columns=['source_list_idx', 'target_list_idx', 'simulation_time', 'behavior_name', 'source_member', \
                                              'target_member', 'source_equipment', 'target_equipment', \
                                              'source_supply', 'target_supply', 'distance' ])

    input_texts.append("사격 이벤트 기록")
    input_texts.append("source_unit_id\t target_unit_id \t simulation_time \t behavior_name \t source_member \t target_member \t \
        source_equipment \t target_equipment \t source_supply \t target_supply \t distance")
    for index, row in dataframe2.iterrows():
        text=f"{row['source_list_idx']} \t {row['target_list_idx']} \t {row['simulation_time']} \t {row['behavior_name']} \
            \t {row['source_member']}\t {row['target_member']}\t {row['source_equipment']}\t {row['target_equipment']}\
            \t {row['source_supply']}\t {row['target_supply']}\t {row['distance']}"
        input_texts.append(text)

    input_texts_str = "\n".join(input_texts)
    return input_texts_str

###################################################################################################

"""
brief: '3. 부대의 전투력' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 유저 인덱스
param3: 시뮬레이션 일자
param4: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_Unit_CombatCapability(id, user_idx, log_created, cursor):
    query = """
    SELECT simulation_time, damage_state, power
    FROM (
        SELECT
            simulation_time,
            damage_state,
            power,
            LAG(power) OVER (ORDER BY simulation_time) AS prev_power
        FROM unit_attributes
        WHERE list_idx = %s AND created_at=%s AND user_idx=%s
    ) subquery
    WHERE power != prev_power OR prev_power IS NULL
    """
    cursor.execute(query, (id, log_created, user_idx ))
    result = cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe = pd.DataFrame(result, columns=['SimulationTime', 'DamageState', 'Power'])

    # 텍스트로 변환
    input_texts = []
    for index, row in dataframe.iterrows():
        text = f"SimulationTime: {row['SimulationTime']}, DamageState: {row['DamageState']}, Power: {row['Power']}"
        input_texts.append(text)

    input_texts = '\n'.join(input_texts)
    return input_texts

###################################################################################################


"""
brief: '4. 부대의 피해상황' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 유저 인덱스
param3: 시뮬레이션 일자
param4: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_Unit_DamageStatus(id, user_idx, log_created, cursor):
    query1 = """
    SELECT 
        simulation_time,
        behavior_name
    FROM event
    WHERE target_list_idx = %s AND created_at=%s AND user_idx=%s
    """
    cursor.execute(query1, (id, log_created, user_idx))
    result1 = cursor.fetchall()
    dataframe1 = pd.DataFrame(result1, columns=['SimulationTime', 'BehaviorName'])

    # 두 번째 쿼리
    query2 = """
    SELECT simulation_time, damage_state, power
    FROM (
        SELECT
            simulation_time,
            damage_state,
            power,
            LAG(power) OVER (ORDER BY simulation_time) AS prev_power
        FROM unit_attributes
        WHERE list_idx = %s AND created_at=%s AND user_idx=%s
    ) subquery
    WHERE power != prev_power OR prev_power IS NULL
    """
    cursor.execute(query2, (id, log_created, user_idx))
    result2 = cursor.fetchall()
    dataframe2 = pd.DataFrame(result2, columns=['SimulationTime', 'DamageState', 'Power'])

    # 두 데이터프레임 결합
    dataframe = pd.merge(dataframe1, dataframe2, on='SimulationTime', how='outer')

    # 텍스트로 변환
    input_texts = []
    for index, row in dataframe.iterrows():
        text = (f"SimulationTime: {row['SimulationTime']}, "
                f"BehaviorName: {row['BehaviorName']}, "
                f"DamageState: {row['DamageState']}, "
                f"Power: {row['Power']}")
        input_texts.append(text)

    input_texts = '\n'.join(input_texts)
    return input_texts

###################################################################################################

"""
brief: '5. 부대 행동' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 유저 인덱스
param3: 시뮬레이션 일자
param4: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_UnitBehavior(id, user_idx, log_created, cursor):
    query = "SELECT simulation_time, behavior_name, status FROM unit_behavior WHERE list_idx = %s AND created_at=%s AND user_idx=%s"
    cursor.execute(query, (id,log_created,user_idx))
    result=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'BehaviorName', 'Status'])

    # 텍스트로 변환
    input_texts=[]
    for index, row in dataframe.iterrows():
        text=f"SimulationTime: {row['SimulationTime']}, BehaviorName: {row['BehaviorName']}, Status: {row['Status']}"
        input_texts.append(text)

    input_texts='\n'.join(input_texts)
    return input_texts

###################################################################################################

"""
brief: '6. 개체 탐지' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 유저 idx
param3: 시뮬레이션 시간
param4: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_ObjectDetection(id, user_idx, log_created, cursor):
    #detectedEntity가 존재하는 경우에만 가져와야 함
    query = """
    SELECT simulation_time, detected_entity_id, detected_entity_distance, power, damage_state 
    FROM unit_attributes 
    WHERE list_idx = %s 
      AND user_idx = %s 
      AND created_at = %s 
      AND detected_entity_id != '[]'
    """
    cursor.execute(query, (id, user_idx, log_created,))

    result=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'Detected_Entity_ID', 'Detected_Entity_Distance', 'Power', 'DamageState'])

    # 텍스트로 변환
    input_texts=[]
    for index, row in dataframe.iterrows():
        text=f"SimulationTime: {row['SimulationTime']}, Detected_Entity_ID: {row['Detected_Entity_ID']}, Detected_Entity_Distance: {row['Detected_Entity_Distance']}, Power: {row['Power']}, DamageState: {row['DamageState']}"
        input_texts.append(text)

    input_texts='\n'.join(input_texts)
    return input_texts

"""
brief: '7. 부대 정보' 특성 전처리를 위한 로그 선택
param1: 유저 idx
param2: 시뮬레이션 시간
param3: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_info(user_idx, log_created, cursor):
    query = """
    SELECT unit_name, status, member, equipment, supply
    FROM unit_init 
    WHERE user_idx = %s 
      AND created_at = %s 
    """

    cursor.execute(query, (user_idx, log_created,))
    result=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['UnitName', 'Status', 'Member', 'Equipment', 'Supply'])

    # 텍스트로 변환
    input_texts=[]
    for index, row in dataframe.iterrows():
        text=f"UnitName: {row['UnitName']}, Status: {row['Status']}, Member: {row['Member']}, Equipment: {row['Equipment']}, Supply: {row['Supply']}"
        input_texts.append(text)

    input_texts='\n'.join(input_texts)
    return input_texts
###################################################################################################

"""
brief: 6번 개체 탐지 속성 분석 시 DB에서 읽어온 데이터 정리
"""
def extract_data(input_texts):
    # 정규 표현식을 사용하여 각 값을 추출하는 패턴 설정
    pattern = r"SimulationTime: (\d+), Detected_Entity_ID: \[([\d;]*?)\], Detected_Entity_Distance: \[([\d.;]*?)\], Power: (\d+(?:\.\d+)?), DamageState: (\w+)"

    matches = re.findall(pattern, input_texts)

    result = []

    for match in matches:
        simulation_time = match[0]
        entity_ids = match[1].split(';')
        distances = match[2].split(';')
        power = match[3]
        damage_state = match[4]

        for i in range(len(entity_ids)):
            entity_id = entity_ids[i]
            distance = distances[i]
            text=f"SimulationTime: {simulation_time}, Detected_Entity_ID: {entity_id}, Detected_Entity_Distance: {distance}, Power: {power}, DamageState: {damage_state}"
            result.append(text)

    result='\n'.join(result)
    return result

###################################################################################################

"""
brief: ChatGPT가 전처리 데이터 생성 명령
param1: 추출된 로그로 작성된 메시지
return: 전처리 데이터 텍스트
"""
def DataPreprocessing(openai, messages):
    chat_completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    result=chat_completion.choices[0].message.content
    return result

###################################################################################################

"""
brief: 데이터베이스 연결 끊기
param1: mysql conn
param2: 커서
"""
def DatabaseDeconnect(conn, cursor):
    cursor.close()
    conn.commit()
    conn.close()

"""
breif: ChatGPT API에 입력할 메시지 작성
param1: input_texts 추출한 로그
"""
def CreateMessage(characteristic, input_texts):
    messages = []
    if characteristic=="부대 이동 속도 / 위치 변화":  # 1
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다.\n"

                )
            },
            {
                "role": "user",
                "content": "오직 주어진 데이터에서만 추출하고, 정확히 검토하라. 데이터는 다음 필드로 구성되어 있다: "
                           "simulation time(시간 sec), positionLat(위도), positionLon(경도), positionAlt(고도), speed(이동 속도 km/h).\n"
                           "반드시 첫 번째 데이터와 마지막 데이터를 포함하여, "
                           "첫 번째 데이터와 마지막 데이터 사이의 simulation time을 기준으로 300초 간격의 데이터들을 추출하라."
            },
            {
                "role":"assistant",
                "content":(input_texts)
            }
        ]
    elif characteristic == "부대의 전투력": # 3
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": (
                "Simulation Time과 DamgeState를 이용하여 모든 Power의 상태와 시작 시각을 알려주세요. "
                "다음 예시를 참고하여 형식에 맞춰 알려주세요. "
                "Power: 100\n"
                "- 시작 시각: 30\n"
                "- 상태: NoDamage\n"
                "Power: 63\n"
                "- 시작 시각: 8670\n"
                "- 상태: SlightDamage\n"
            )},
            {"role": "assistant", "content": input_texts}
        ]
    elif characteristic == "부대의 피해 상황": # 4
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": (
                "각 SimulationTime 값이 중복되는 경우, 동일한 SimulationTime 값 중 하나의 행만 선택하고, Power 값이 nan인 행을 제외한 모든 데이터들의 Simulation Time, BehaviorName, DamageState, Power를 알려주세요. "
                "실제 데이터를 분석해서 이 형식으로 출력해주세요. 예시의 값이 아닌, 실제 데이터를 사용해 주세요."
                "아래와 같은 형식으로 알려주세요. "
                "SimulationTime: 8610\n"
                "- BehaviorName: DirectFire\n"
                "- DamageState: SlightDamage\n"
                "- Power: 75.0 \n"
            )},
            {"role": "assistant", "content": input_texts}
        ]
    elif characteristic == "부대 행동": # 5
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": (
                "Simulation Time과 Status를 이용하여 각 BehaviorName의 시작 시각과 종료 시각을 알려주세요. "
                "다음 예시를 참고하여 형식에 맞춰 알려주세요. "
                "BehaviorName: 전술기동\n"
                "- 시작 시각: 60\n"
                "- 종료 시각: 150\n"
                "BehaviorName: 전술기동\n"
                "- 시작 시각: 180\n"
                "- 종료 시각: 9180"
            )},
            {"role": "assistant", "content": input_texts}
        ]
    elif characteristic == "개체 탐지": #6
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": (
                "Simulation Time과 Detected_Entity_Distance를 이용하여 모든 Detected_Entity_ID에 대하여 최초 탐지 시점, 최초 탐지 거리, 최종 탐지 시점, 최종 탐지 거리를 알려주세요."
                "다음 예시를 참고하여 형식에 맞춰 알려주세요."
                "예시: \n"
                "Detected Entity ID: 7 \n"
                "최초 탐지 시점: 8160 \n"
                "최초 탐지 거리: 973.46250 \n"
                "최종 탐지 시점: 8880 \n"
                "최종 탐지 거리: 193.28714 \n"
                " \n"
                "Detected Entity ID: 8 \n"
                "최초 탐지 시점: 8220 \n"
                "최초 탐지 거리: 983.23653 \n"
                "최종 탐지 시점: 8880 \n"
                "최종 탐지 거리: 388.13182 \n"
                " \n"
                "Detected Entity ID: 9 \n"
                "최초 탐지 시점: 8370 \n"
                "최초 탐지 거리: 974.23594 \n"
                "최종 탐지 시점: 8880 \n"
                "최종 탐지 거리: 623.63980 \n"
                " \n"
                "Detected Entity ID: 11 \n"
                "최초 탐지 시점: 8370 \n"
                "최초 탐지 거리: 966.64618 \n"
                "최종 탐지 시점: 8880 \n"
                "최종 탐지 거리: 429.12943 \n"

                "그리고 Simulation Time과 Power를 이용하여 모든 Power의 시작 시각과 종료 시각을 알려주세요. "
                "다음 예시를 참고하여 형식에 맞춰 알려주세요. "
                "예시: \n"
                "Power: 100.0 \n"
                "- 시작 시각: 8160 \n"
                "- 종료 시각: 8550 \n"
                " \n"
                "Power: 96.97 \n"
                "- 시작 시각: 8580 \n"
                "- 종료 시각: 8580 \n"
                " \n"
                "Power: 90.91 \n"
                "- 시작 시각: 8610 \n"
                "- 종료 시각: 8610 \n"
                " \n"
                "Power: 84.85 \n"
                "- 시작 시각: 8640 \n"
                "- 종료 시각: 8640 \n"
                " \n"
                "Power: 66.67 \n"
                "- 시작 시각: 8670 \n"
                "- 종료 시각: 8670 \n"
                " \n"
                "Power: 60.61 \n"
                "- 시작 시각: 8700 \n"
                "- 종료 시각: 8700 \n"
                " \n"
                "Power: 51.52 \n"
                "- 시작 시각: 8730 \n"
                "- 종료 시각: 8790 \n"
                " \n"
                "Power: 48.48 \n"
                "- 시작 시각: 8820 \n"
                "- 종료 시각: 8820 \n"
                " \n"
                "Power: 42.42 \n"
                "- 시작 시각: 8850 \n"
                "- 종료 시각: 8880 \n"

                "마지막으로, Simulation Time과 DamageState를 이용하여 모든 DamageState의 시작 시각과 종료 시각을 알려주세요."
                "다음 예시를 참고하여 형식에 맞춰 알려주세요."
                "예시: \n"
                "DamageState: NoDamage\n"
                "- 시작 시각: 8160\n"
                "- 종료 시각: 8640\n"
                "DamageState: SlightDamage\n"
                "- 시작 시각: 8670\n"
                "- 종료 시각: 8790\n"
                "DamageState: ModerateDamage\n"
                "- 시작 시각: 8820\n"
                "- 종료 시각: 8880\n"
            )},
            {"role": "assistant", "content": input_texts}
        ]

    elif characteristic == "부대 정보": #7
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": (
                "UnitName, Status, Member, Equipment, Supply를 이용하여 각 부대의 부대 이름, 초기 상태, 초기 인원, 초기 장비, 초기 보급품을 알려주세요."
                "다음 예시를 참고하여 형식에 맞춰 알려주세요."
                "예시: \n"
                "부대 이름: B-1-1-Unit1\n"
                "- 초기 상태: NoDamage\n"
                "- 초기 인원: {소/중위;소총;1;1};{하/중사;소총;4;4};{병;소총;19;19};{병;유탄발사기;6;6};{병;기관총;3;3}\n"
                "- 초기 장비: {개인/공용화기;소총;24;24};{개인/공용화기;K201/M203;6;6};{개인/공용화기;K-3;3;3}\n"
                "- 초기 보급품: {직사화기탄;소총탄;3600;3600};{직사화기탄;기관총탄;3000;3000};{직사화기탄;유탄발사기탄;90;90}\n"
            )},
            {"role": "assistant", "content": input_texts}
        ]

    return messages

###################################################################################################

if __name__ == "__main__":

    print("***************\n\n module 1 is processing \n\n***************")

    conn, cursor=DatabaseConnect()

    if len(sys.argv) not in [4, 5]:
        print("인자 전달 개수 이상")
        sys.exit(1)

    temp_file_path = sys.argv[0]
    user_idx = sys.argv[1]
    log_created = sys.argv[2]
    characteristic = sys.argv[3]
    if len(sys.argv) == 5:
        name = sys.argv[4]
    else:
        name = None

    id = FindID(name, user_idx, log_created, cursor)

#     print("Temp File Path:", temp_file_path)
#     print("User ID:", user_idx)
#     print("Log Created:", log_created)
#     print("Characteristic:", characteristic)
#     print("Name:", name)

    # ChatGPT Connect
    os.environ.get('OPENAI_API_KEY') is None
    os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
    openai.api_key = os.getenv("OPENAI_API_KEY")

    input_texts=[]
    messages = []
    preprocessed_data=""

    if characteristic == "부대 이동 속도 / 위치 변화":
        input_texts=Extract_UnitSpeed(id, user_idx, log_created, cursor)
        messages=CreateMessage(characteristic, input_texts)
    elif characteristic == "부대의 전투력":
        input_texts = Extract_Unit_CombatCapability(id, user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
    elif characteristic == "부대의 피해 상황":
        input_texts = Extract_Unit_DamageStatus(id, user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
    elif characteristic == "부대 행동":
        input_texts = Extract_UnitBehavior(id, user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
    elif characteristic == "개체 탐지":
        input_texts = Extract_ObjectDetection(id, user_idx, log_created, cursor)
        converted_data = extract_data(input_texts)
        messages = CreateMessage(characteristic, converted_data)
    elif characteristic == "부대 정보":
        input_texts = Extract_info(user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
    else:
        messages = []
        preprocessed_data=""

    if characteristic=="인원/장비 수량 변화":
        input_texts=Extract_Event(id, user_idx, log_created, cursor)
        preprocessed_data=input_texts
    else:
        preprocessed_data=DataPreprocessing(openai, messages)

    # 전처리된 데이터를 작성할 경로
    output_file_path = os.path.join(os.getcwd(), "preprocessedData.txt")

    # 파일에 데이터 쓰기
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(preprocessed_data)

    print(f"Data written to {output_file_path}")

    DatabaseDeconnect(conn, cursor)
    print(preprocessed_data)