
"""
brief: 데이터베이스와 연결
return: conn, cursor 객체
"""
def DatabaseConnect():
    # 실제 구현된 데이터베이스 확인 후 수정해야 함
    conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="-",    # 실행 시 본인의 로컬 비밀번호를 입력하세요.
            database="wdam"
        )
    cursor=conn.cursor(buffered=True) # 커서 생성
    return conn, cursor

"""
테스트용 데이터베이스 데이터 입력
후 삭제 예정
"""
def InsultTestData(cursor):
    from datetime import datetime
    date_str='20230116174254'
    date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%S')  # 문자열을 datetime 객체로 변환

    # 데이터베이스 초기화(데이터 삭제)
    query = "DELETE FROM UnitBehavior"
    cursor.execute(query)
    query = "DELETE FROM Unit_List"
    cursor.execute(query)

    # 데이터베이스에 데이터 입력
    # UnitBehavior table
    query = "INSERT INTO UnitBehavior (unitId, simulationTime, behaviorName, status, createdAt) VALUES (%s, %s, %s, %s, %s)"
    values = [
        (2, 60, '전술기동', 'Running', date_obj),
        (3, 60, '전술기동', 'Running', date_obj),
        (2, 150, '전술기동', 'Finished', date_obj),
        (2, 180, '전술기동', 'Running', date_obj),
        (2, 9180, '전술기동', 'Finished', date_obj)
    ]
    cursor.executemany(query, values)

    # UnitList table
    query = "INSERT INTO Unit_List (unitId, unitName, status) VALUES (%s, %s, %s)"
    values = [
        (2, "B-1-1-Unit1","0"),
        (3, "B-1-2-Unit1","0"),
        (4,"B-1-1-Unit2","1")
    ]
    cursor.executemany(query, values)
"""
brief: 사용자가 선택한 부대의 ID를 Unit_List 테이블에서 찾기
param1: 부대명
param2: 데이터베이스 커서
return: 부대 ID
"""
def FindID(name, cursor):
    #name='B-1-1-Unit1'
    query = "SELECT unitId FROM Unit_List WHERE unitName = %s"
    cursor.execute(query, (name,))
    id = cursor.fetchone()
    id=id[0]
    # print("찾아낸 부대의 ID: ", id) # print for test
    return id

"""
brief: '부대 행동' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_UnitBehavior(id, cursor):
    query = "SELECT simulationTime, behaviorName, status FROM UnitBehavior WHERE unitId = %s"
    cursor.execute(query, (id,))
    result=cursor.fetchall()

    """
    # print for test
    print("부대 UnitBehavior 추출 정보:")
    for row in result:
        print("SimulationTime: ", row[0])
        print("BehaviorName: ", row[1])
        print("Status: ", row[2])
        print("------------------------")
    """
    
    # Chat GPT에게 넘겨주기 위해 데이터프레임->텍스트로 변환
    import pandas as pd
    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'BehaviorName', 'Status'])
    # print(dataframe) # print for test
    # 텍스트로 변환
    input_texts=[]
    for index, row in dataframe.iterrows():
        text=f"SimulationTime: {row['SimulationTime']}, BehaviorName: {row['BehaviorName']}, Status: {row['Status']}"
        input_texts.append(text)
    
    input_texts='\n'.join(input_texts)
    # print for test
    # print("추출한 로그"+input_texts)

    return input_texts

"""
brief: ChatGPT가 전처리 데이터 생성 명령
param1: 추출된 로그
return: 전처리 데이터 텍스트
"""
def DataPreprocessing(openai, messages):
    chat_completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    result=chat_completion.choices[0].message.content
    return result

"""
brief: 데이터베이스 연결 끊기
param1: mysql conn
param2: 커서
"""
def DatabaseDeconnect(conn, cursor):
    cursor.close()
    conn.commit()
    conn.close()

# *** main code ***

import mysql.connector
conn, cursor=DatabaseConnect()

InsultTestData(cursor)

name='B-1-1-Unit1' # 테스트용 분석 대상
id=FindID(name, cursor)
input_texts=Extract_UnitBehavior(id, cursor)

DatabaseDeconnect(conn, cursor)

# ChatGPT Connect
import os
import openai
os.environ.get('OPENAI_API_KEY') is None
os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
openai.api_key = os.getenv("OPENAI_API_KEY")

"""
다른 특성 구현 시
messages를 특성별로 user를 바꿔야 함.
"""
messages = [
    {"role": "system", "content": "당신은 주어진 데이터를 분석에 용이한 형태로 전처리해야 합니다."},
    {"role": "user", "content": "Simulation Time과 Status를 이용하여 각 BehaviorName의 시작 시각과 종료 시각을 알려주세요."},
    {"role": "assistant", "content": input_texts}
]

preprocessed_data=DataPreprocessing(openai, messages)
print(preprocessed_data)
