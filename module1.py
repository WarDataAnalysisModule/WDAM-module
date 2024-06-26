import subprocess
import sys

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
param2: 데이터베이스 커서
return: 부대 ID
"""
def FindID(name, cursor):
    query = "SELECT list_idx FROM unit_list WHERE unit_name = %s"
    cursor.execute(query, (name,))
    id = cursor.fetchone()
    id=id[0]
    return id

###################################################################################################

"""
brief: '부대 행동' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_UnitBehavior(id, cursor):
    query = "SELECT simulation_time, behavior_name, status FROM unit_behavior WHERE list_idx = %s"
    cursor.execute(query, (id,))
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
brief: '부대의 전투력' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_Unit_CombatCapability(id, cursor):
    query = """
    SELECT simulation_time, damage_state, power
    FROM (
        SELECT
            simulation_time,
            damage_state,
            power,
            LAG(power) OVER (ORDER BY simulation_time) AS prev_power
        FROM unit_attributes
        WHERE list_idx = %s
    ) subquery
    WHERE power != prev_power OR prev_power IS NULL
    """
    cursor.execute(query, (id, ))
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
brief: '부대의 피해상황' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_Unit_DamageStatus(id, cursor):
    query = """
    SELECT 
        CASE
            WHEN target_list_idx = %s THEN target_equipment
        END AS Equipment,
        CASE
            WHEN target_list_idx = %s THEN target_member
        END AS Member,
        CASE
            WHEN target_list_idx = %s THEN target_supply
        END AS Supply,
        simulation_time,
        behavior_name,
        CASE
            WHEN target_list_idx = %s THEN source_list_idx
        END AS Enemy
    FROM event
    WHERE target_list_idx = %s
    """
    cursor.execute(query, (id, id, id, id, id))
    result = cursor.fetchall()

    # 추출한 데이터로부터 데이터프레임 생성
    dataframe = pd.DataFrame(result, columns=['Equipment', 'Member', 'Supply', 'SimulationTime', 'BehaviorName', 'Enemy'])

    # 텍스트로 변환
    input_texts = []
    for index, row in dataframe.iterrows():
        text = f"SimulationTime: {row['SimulationTime']}, Equipment: {row['Equipment']}, Member: {row['Member']}, Supply: {row['Supply']}, BehaviorName: {row['BehaviorName']}, Enemy: {row['Enemy']}"
        input_texts.append(text)

    input_texts = '\n'.join(input_texts)
    return input_texts

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
    if characteristic == "부대 행동":
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
    elif characteristic == "부대의 전투력":
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
    elif characteristic == "부대의 피해 상황":
        messages = [
            {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
            {"role": "user", "content": (
                "-가 있는 행을 뺀 나머지 중에 마지막으로 작성된 Simulation Time, Equipment, Memeber, Supply을 알려주세요. "
                "아래와 같은 형식에 맞춰 알려주세요. "
                "SimulationTime: 8610\n"
                "- Equipment: {개인/공용화기;소총;24;20};{개인/공용화기;K201/M203;6;5};{개인/공용화기;K-3;3;3}\n"
                "- Memeber: {소/중위;소총;1;1};{하/중사;소총;4;4};{병;소총;19;15};{병;유탄발사기;6;5};{병;기관총;3;3}\n"
                "- Supply: {직사화기탄;소총탄;3600;3600};{직사화기탄;기관총탄;3000;3000};{직사화기탄;유탄발사기탄;90;90}\n"
            )},
            {"role": "assistant", "content": input_texts}
        ]
    return messages

###################################################################################################

if __name__ == "__main__":

    conn, cursor=DatabaseConnect()

    if len(sys.argv) > 2:
        characteristic = sys.argv[1]
        name = sys.argv[2]
    else:
        print("인자 전달 개수 이상")
        sys.exit(1)

    id = FindID(name, cursor)


    # ChatGPT Connect
    os.environ.get('OPENAI_API_KEY') is None
    os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if characteristic == "부대 행동":
        input_texts = Extract_UnitBehavior(id, cursor)
        messages = CreateMessage(characteristic, input_texts)
    elif characteristic == "부대의 전투력":
        input_texts = Extract_Unit_CombatCapability(id, cursor)
        messages = CreateMessage(characteristic, input_texts)
    elif characteristic == "부대의 피해 상황":
        input_texts = Extract_Unit_DamageStatus(id, cursor)
        messages = CreateMessage(characteristic, input_texts)
    else:
        messages = []

    preprocessed_data=DataPreprocessing(openai, messages)

    # 파일로 저장
    with open("src/main/java/com/back/wdam/analyze/resources/preprocessedData.txt", "w", encoding="utf-8") as file:
        file.write(preprocessed_data)
    
    DatabaseDeconnect(conn, cursor)
    print(preprocessed_data)