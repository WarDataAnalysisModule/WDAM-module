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
            host="localhost",
            user="root",
            password="",
            database="wdam"
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

    # 관측 시간, 위치, 속도 추출
    query = "SELECT simulation_time, position_lat, position_lon, position_alt, speed FROM unit_attributes WHERE list_idx = %s AND created_at=%s AND user_idx=%s"
    cursor.execute(query, (id,log_created,user_idx))
    result=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'positionLat', 'positionLon', 'positionAlt', 'speed'])

    # 텍스트로 변환
    input_texts=[]
    input_texts.append("SimulationTime \t positionLat \t positionLon \t positionAlt \t speed")
    for index, row in dataframe.iterrows():
        text=f"{row['SimulationTime']} \t {row['positionLat']} \t {row['positionLon']} \t {row['positionAlt']} \t {row['speed']}"
        input_texts.append(text)

    return input_texts

"""
brief: 데이터 길이가 길 때 적당한 크기로 자르는 함수
split_input_texts_2는 2개로 자르고
split_input_texts_3는 3개로 자른다.
"""
def split_input_texts_2(input_texts):
    header = input_texts[0]  # 첫 번째 줄은 헤더
    split_index = 150  # 헤더 포함 150번째 인덱스를 기준으로 분할 (즉, 150번째 데이터 행 이후)
    
    input_texts1 = input_texts[:split_index]
    input_texts2 = [header] + input_texts[split_index:]
    
    return input_texts1, input_texts2

def split_input_texts_3(input_texts):
    header = input_texts[0]  # 첫 번째 줄은 헤더
    total_lines = len(input_texts)
    
    # 헤더를 제외한 데이터의 시작 인덱스
    data_start_index = 1

    # 데이터를 3등분하기 위한 인덱스 계산
    part1_end_index = data_start_index + (total_lines - data_start_index) // 3
    part2_end_index = part1_end_index + (total_lines - data_start_index) // 3

    input_texts1 = input_texts[:part1_end_index]
    input_texts2 = [header] + input_texts[part1_end_index:part2_end_index]
    input_texts3 = [header] + input_texts[part2_end_index:]
    
    return input_texts1, input_texts2, input_texts3
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
    # init 파일에서 초기 상태를 추출
    query1 = "SELECT unit_name, status, member, equipment, supply FROM unit_init WHERE list_idx = %s AND created_at=%s AND user_idx=%s"
    cursor.execute(query1, (id,log_created,user_idx))
    result1=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe1=pd.DataFrame(result1, columns=['unit_name', 'status', 'member', 'equipment', 'supply'])

    # 텍스트로 변환
    input_texts=[]
    input_texts.append("해당 부대의 초기 상태 및 인원, 장비 수량\n")
    input_texts.append("unit_idx \t unit_name \t status \t member(계급;무장;최대인원;현재인원) \t equipment(종류;장비명;최대수량;현재수량) \t supply(종류;품명;최대수량;현재수량)\n")
    for index, row in dataframe1.iterrows():
        text=f"{id} \t {row['unit_name']} \t {row['status']} \t {row['member']} \t {row['equipment']} \t {row['supply']}\n"
        input_texts.append(text)

    # event 파일에서 해당 부대 데이터 추출
    query2 = "SELECT source_list_idx, target_list_idx, simulation_time, source_member, target_member, \
        source_equipment, target_equipment, source_supply, target_supply\
              FROM event WHERE (source_list_idx = %s OR target_list_idx = %s) AND created_at=%s AND user_idx=%s"
    cursor.execute(query2, (id,id,log_created,user_idx))
    result2=cursor.fetchall()
    
    # 추출한 데이터로부터 데이터프레임 생성
    dataframe2=pd.DataFrame(result2, columns=['source_list_idx', 'target_list_idx', 'simulation_time', 'source_member',\
                                              'target_member', 'source_equipment', 'target_equipment',\
                                                 'source_supply', 'target_supply'])
    
    # 데이터프레임의 길이
    df_length = len(dataframe2)
    input_texts.append("사격 이벤트 기록\n")
    input_texts.append("source_list_idx\t target_list_idx \t simulation_time \n")
    for index, row in dataframe2.iterrows():
        if index != df_length - 1:
            text=f"{row['source_list_idx']} \t {row['target_list_idx']} \t {row['simulation_time']}\n"
        else:
            text=f"{row['source_list_idx']} \t {row['target_list_idx']} \t {row['simulation_time']}\n"
            input_texts.append(text)
            input_texts.append("마지막 전투 결과\n")
            if row['source_list_idx'] == id:
                text = f"{row['simulation_time']} \t {row['source_member']} \t {row['source_equipment']} \t {row['source_supply']}\n"
                input_texts.append("simulation_time \t member(계급;무장;최대인원;현재인원) \t equipment(종류;장비명;최대수량;현재수량) \t \
                                   supply(종류;품명;최대수량;현재수량)\n")
            else:
                text = f"{row['simulation_time']} \t {row['target_member']} \t {row['target_equipment']} \t {row['target_supply']}\n"
                input_texts.append("simulation_time \t member(계급;무장;최대인원;현재인원) \t equipment(종류;장비명;최대수량;현재수량) \t \
                                   supply(종류;품명;최대수량;현재수량)\n")
        input_texts.append(text)

    # 전체 부대 id, 이름 목록 추출
    query3= "SELECT list_idx, unit_name FROM unit_list WHERE simulation_time=%s AND user_idx=%s"
    cursor.execute(query3, (log_created,user_idx))
    result3=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe3=pd.DataFrame(result3, columns=['list_idx', 'unit_name' ])
    input_texts.append("전체 부대 목록\n")
    input_texts.append("unit idx \t unit name\n")
    for index, row in dataframe3.iterrows():
        text=f"{row['list_idx']} \t {row['unit_name']}\n"
        input_texts.append(text)

    input_texts='\n'.join(input_texts)
    return input_texts
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
    # 총 관측 시간 추출
    query1="SELECT MAX(simulation_time) AS last_simulation_time FROM unit_behavior WHERE list_idx = %s AND created_at=%s AND user_idx=%s"
    cursor.execute(query1,(id,log_created, user_idx))
    time=cursor.fetchone()[0]

    # 과업 수행 기록 추출
    query = "SELECT simulation_time, behavior_name, status FROM unit_behavior WHERE list_idx = %s AND created_at=%s AND user_idx=%s"
    cursor.execute(query, (id,log_created,user_idx))
    result=cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'BehaviorName', 'Status'])

    # 텍스트로 변환
    input_texts=[]
    simulaition_time=f"총 관측 시간: {time}"
    input_texts.append(simulaition_time)
    for index, row in dataframe.iterrows():
        text=f"SimulationTime: {row['SimulationTime']}, BehaviorName: {row['BehaviorName']}, Status: {row['Status']}"
        input_texts.append(text)

    input_texts='\n'.join(input_texts)
    print(input_texts)
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
###################################################################################################

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
param1: 전처리 데이터
return: 전처리 데이터(형식을 알아보기 쉽게)
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
        model="gpt-3.5-turbo-0125",
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
            {   "role": "system",
                "content": ("당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다.\n" )},
            {
                "role": "user",
                "content": "데이터는 다음과 같은 필드로 이루어져 있습니다.. "
                "simulation time(시간 sec), positionLat(위도), positionLon(경도), positionAlt(고도), speed(이동 속도 km/h).\n"
                "첫 번째 행의 데이터와 마지막 행의 데이터 사이의 simulationTime을 기준으로 300초 간격의 데이터들을 추출하세요.\n"
                "추출한 데이터에는 반드시 첫 번째 행의 데이터와 마지막 행의 데이터가 있어야 합니다.\n"
                "다음 예시를 참고하여 형식에 맞춰 알려주세요.\n\n"
                "이 예시에서 첫 번째 데이터는 simulaition time이 10일 때이고, 마지막 데이터는 simulation time이 3100일 때입니다.\n"
                "결과는 다음과 같아야 합니다. 문장 없이 다음과 같은 형식으로만 답하세요.\n\n"
                "10\t30.0\t100.0\t50.0\t2\n"
                "310\t31.0\t120.0\t50.0\t2\n"
                "610\t32.1\t100.0\t50.0\t2\n"
                "910\t32.1\t100.0\t50.0\t2\n"
                "1210\t32.1\t100.0\t50.0\t2\n"
                "1510\t32.1\t100.0\t50.0\t2\n"
                "1810\t32.1\t100.0\t50.0\t2\n"
                "2110\t32.1\t100.0\t50.0\t2\n"
                "2410\t32.1\t100.0\t50.0\t2\n"
                "2710\t32.1\t100.0\t50.0\t2\n"
                "3010\t32.1\t100.0\t50.0\t2\n"
                "3100\t32.1\t100.0\t50.0\t2\n"
            },
            {   "role":"assistant","content": "전처리해야 하는 데이터:\n"+input_texts}
        ]
    elif characteristic=="인원/장비 수량 변화": #2
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": 
                "이 데이터는 순서대로 '해당 부대의 초기 상태 및 인원, 장비 수량', '사격 이벤트 기록', '마지막 전투 기록', '전체 부대 목록'이다.\n"
                "'사격 이벤트 기록'에서 source는 공격의 주체이고 target은 공격의 대상이다. 해당 부대는 source일수도, target일 수도 있다. \n"
                "'해당 부대의 초기 상태 및 인원, 장비 수량'을 이용하여 최대 값이 아닌 현재 값을 기준으로 초기 인원, 장비 수량을 명시하라.\n"
                "'마지막 전투 기록'을 이용하여 최대 값이 아닌 현재 값을 기준으로 최종 인원, 장비 수량을 명시하라."
                "'사격 이벤트 기록'에서 첫번째 simulation_time과 마지막 전투 기록의 simulaition_time을 이용하여 해당 부대가 전투를 치른 총 시간을 구하라."
                "'사격 이벤트 기록'의 source_unit_id 또는 target_unit_id과 '전체 부대 목록'을 확인하여 전체 부대 중 해당 부대와 교전한 부대들을 목록으로 정리하라.\n"
                "다음 예시를 보고 형식에 맞춰 답변하라.\n"
                "만약 주어진 데이터가 다음과 같다면,\n\n"
                "해당 부대의 초기 상태 및 인원, 장비 수량\n"
                "unit_idx \t unit_name \t status \t member(계급;무장;최대인원;현재인원) \t equipment(종류;장비명;최대수량;현재수량) \t supply(종류;품명;최대수량;현재수량)\n"
                "10 \t A-1-1 \t No Damage \t [{소/중위;소총;1;1};{하/중사;소총;5;5};{병;소총;20;20};{병;유탄발사기;5;5};{병;기관총;3;3}] \t "
                "[{개인/공용화기;소총;50;50};{개인/공용화기;K201/M203;6;6};{개인/공용화기;K-3;3;3}] \t [{직사화기탄;소총탄;3600;3600};{직사화기탄;기관총탄;3000;3000};{직사화기탄;유탄발사기탄;90;90}]\n"
                "사격 이벤트 기록\n"
                "source_list_idx \t target_list_idx \t simulation_time\n"
                "10 \t 5 \t 3000\n"
                "6 \t 10 \t 3010\n"
                "10 \t 6 \t 3015\n"
                "10 \t 5 \t 3020\n"
                "5 \t 10 \t 3040\n"
                "마지막 전투 기록\n"
                "simulation_time \t member(계급;무장;최대인원;현재인원) \t equipment(종류;장비명;최대수량;현재수량) \t supply(종류;품명;최대수량;현재수량)\n"
                "3040 \t [{소/중위;소총;1;1};{하/중사;소총;5;5};{병;소총;20;10};{병;유탄발사기;5;0};{병;기관총;3;1}] \t "
                "[{개인/공용화기;소총;50;30};{개인/공용화기;K201/M203;6;3};{개인/공용화기;K-3;3;3}] \t "
                "[{직사화기탄;소총탄;3600;1000};{직사화기탄;기관총탄;3000;1000};{직사화기탄;유탄발사기탄;90;30}]\n"
                "전체 부대 목록\n"
                "1 \t B-1\n"
                "5 \t B-13\n"
                "6 \t B-14\n"
                "(생략)\n\n"
                "\n결과는 다음과 같아야 한다.\n\n"
                "1. A-1-1 부대 초기 인원, 장비 수량:\n"
                "- 인원: 소/중위(소총) 1명, 하/중사(소총) 5명, 병사(소총) 20명, 병사(유탄발사기) 5명, 병사(기관총) 3명\n"
                "- 장비 수량: 소총 50개, K201/M203 6개, K-3 3개\n"
                "- 자원품 수량: 소총탄 3600개, 기관총탄 3000개, 유탄발사기탄 90개\n\n"
                "2. A-1-1 부대 최종 인원, 장비 수량:\n"
                "- 인원: 소/중위(소총) 1명, 하/중사(소총) 5명, 병사(소총) 10명, 병사(유탄발사기) 0명, 병사(기관총) 1명\n"
                "- 장비 수량: 소총 30개, K201/M203 3개, K-3 3개\n"
                "- 자원품 수량: 소총탄 1000개, 기관총탄 1000개, 유탄발사기탄 30개\n\n"
                "3. 전투 시간: \n"
                "3000~3040초\n\n"
                "4. A-1-1과 교전한 부대 목록:\n"
                "- B-13\n"
                "- B-14\n"
            },
            {"role": "assistant", "content": input_texts}
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
                "Simulation Time과 Status를 이용하여 모든 과업(Behavior Name)별로 시작 시각과 종료 시각을 알려주세요. "
                "다음 예시를 참고하여 형식에 맞춰 알려주세요.\n\n"
                "만약 주어진 데이터가 다음과 같다면,\n"
                "총 관측 시간: 120000\n"
                "SimulationTime: 30, BehaviorName: 점령, Status: Running\n"
                "SimulationTime: 100, BehaviorName: 점령, Status: Finished\n"
                "SimulationTime: 120, BehaviorName: 공격, Status: Running\n"
                "SimulationTime: 300, BehaviorName: 공격, Status: Finished\n"
                "결과는 아래와 같아야 합니다.\n"
                "총 관측 시간: 120000\n"
                "1. 과업명: 점령\n"
                "- 시작 시각: 30\n"
                "- 종료 시각: 100\n"
                "- 소요 시간: 70\n"
                "2. 과업명: 공격\n"
                "- 시작 시각: 120\n"
                "- 종료 시각: 300\n"
                "- 소요 시간: 180\n"
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

    # ChatGPT Connect
    os.environ.get('OPENAI_API_KEY') is None
    os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
    openai.api_key = os.getenv("OPENAI_API_KEY")

    input_texts=[]
    messages = []
    preprocessed_data=""

    if characteristic == "부대 이동 속도 / 위치 변화":
        input_texts=Extract_UnitSpeed(id, user_idx, log_created, cursor)
        # 긴 데이터는 잘라서 넣기(3개로 나눔)
        input_texts1, input_texts2, input_texts3=split_input_texts_3(input_texts)
        input_texts1='\n'.join(input_texts1)
        input_texts2='\n'.join(input_texts2)
        input_texts3='\n'.join(input_texts3)
        # chatGPT에도 3번에 나누어 전달
        messages1=CreateMessage(characteristic, input_texts1)
        preprocessed_data1=DataPreprocessing(openai, messages1)
        if input_texts2!=None:
            messages2=CreateMessage(characteristic, input_texts2)
            preprocessed_data2=DataPreprocessing(openai, messages2)
        if input_texts3!=None:
            messages3=CreateMessage(characteristic, input_texts3)
            preprocessed_data3=DataPreprocessing(openai, messages3)
        # 완성된 3개의 전처리 결과를 합침
        preprocessed_data="SimulationTime \t positionLat \t positionLon \t positionAlt \t speed\n"+preprocessed_data1+"\n"+preprocessed_data2+"\n"+preprocessed_data3
    elif characteristic == "인원/장비 수량 변화":
        input_texts=Extract_Event(id, user_idx, log_created, cursor)
        messages=CreateMessage(characteristic, input_texts)
        preprocessed_data=DataPreprocessing(openai, messages)
    elif characteristic == "부대의 전투력":
        input_texts = Extract_Unit_CombatCapability(id, user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
        preprocessed_data=DataPreprocessing(openai, messages)
    elif characteristic == "부대의 피해 상황":
        input_texts = Extract_Unit_DamageStatus(id, user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
        preprocessed_data=DataPreprocessing(openai, messages)
    elif characteristic == "부대 행동":
        input_texts = Extract_UnitBehavior(id, user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
        preprocessed_data=DataPreprocessing(openai, messages)
    elif characteristic == "개체 탐지":
        input_texts = Extract_ObjectDetection(id, user_idx, log_created, cursor)
        converted_data = extract_data(input_texts)
        messages = CreateMessage(characteristic, converted_data)
        preprocessed_data=DataPreprocessing(openai, messages)
    elif characteristic == "부대 정보":
        input_texts = Extract_info(user_idx, log_created, cursor)
        messages = CreateMessage(characteristic, input_texts)
        preprocessed_data=DataPreprocessing(openai, messages)
    else:
        messages = []
        preprocessed_data=""

    # 전처리된 데이터를 작성할 경로
    output_file_path = os.path.join(os.getcwd(), "preprocessedData.txt")

    # 파일에 데이터 쓰기
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(preprocessed_data)

    print(f"Data written to {output_file_path}")

    DatabaseDeconnect(conn, cursor)
    print(preprocessed_data)
