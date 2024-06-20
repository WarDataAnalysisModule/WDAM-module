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
    else:
        messages = []

    preprocessed_data=DataPreprocessing(openai, messages)

    # 파일로 저장
    with open("src/main/java/com/back/wdam/analyze/resources/preprocessedData.txt", "w", encoding="utf-8") as file:
        file.write(preprocessed_data)

    DatabaseDeconnect(conn, cursor)
    print(preprocessed_data)
