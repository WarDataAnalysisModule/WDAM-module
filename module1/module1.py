
"""
brief: 데이터베이스와 연결
return: conn, cursor 객체
"""
def DatabaseConnect():
    # 실제 구현된 데이터베이스 확인 후 수정해야 함
    conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",    # 실행 시 비밀번호를 입력하세요.
            database="wdamDB"
        )
    cursor=conn.cursor(buffered=True) # 커서 생성
    return conn, cursor

"""
테스트용 데이터베이스 데이터 입력
"""
def InsultTestData(cursor):
    from datetime import datetime
    date_str='20230116174254'
    date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%S')  # 문자열을 datetime 객체로 변환

    # 데이터베이스 초기화(데이터 삭제)
    query = "DELETE FROM UnitBehavior"
    cursor.execute(query)
    query = "DELETE FROM init"
    cursor.execute(query)

    # 데이터베이스에 데이터 입력
    # UnitBehavior table
    query = "INSERT INTO UnitBehavior (idx, UnitId, CreatedAt, SimulationTime, BehaviorName, Status) VALUES (%s, %s, %s, %s, %s, %s)"
    values = [
        (1, 2, date_obj, 60, '전술기동', 'Running'),
        (2, 3, date_obj, 60, '전술기동', 'Running'),
        (3, 2, date_obj, 150, '전술기동', 'Finished'),
        (4, 2, date_obj, 180, '전술기동', 'Running'),
        (5, 2, date_obj, 9180, '전술기동', 'Finished')
    ]
    cursor.executemany(query, values)

    # init table
    query = "INSERT INTO init (UnitId, UnitName, Symbol, Status, Member, Equipment, Supply, CreatedAt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    values = [
        (2, 'B-1-1-Unit1', 'SFG-UCI----D---', 'No Damage', '[{소/중위;소총;1;1};{하/중사;소총;4;4};{병;소총;19;19};{병;유탄발사기;6;6};{병;기관총;3;3}]',\
              '[{개인/공용화기;소총;24;24};{개인/공용화기;K201/M203;6;6};{개인/공용화기;K-3;3;3}]',\
                '[{직사화기탄;소총탄;3600;3600};{직사화기탄;기관총탄;3000;3000};{직사화기탄;유탄발사기탄;90;90}]', date_obj),
        (3, 'B-1-1-Unit2', 'SFG-UCI----E---', 'No Damage', '[{소/중위;소총;1;1};{하/중사;소총;4;4};{병;소총;19;19};{병;유탄발사기;6;6};{병;기관총;3;3}]',\
              '[{개인/공용화기;소총;24;24};{개인/공용화기;K201/M203;6;6};{개인/공용화기;K-3;3;3}]',\
                '[{직사화기탄;소총탄;3600;3600};{직사화기탄;기관총탄;3000;3000};{직사화기탄;유탄발사기탄;90;90}]', date_obj)
    ]
    cursor.executemany(query, values)

"""
brief: 사용자가 선택한 부대의 ID를 init 파일에서 찾기
param1: 부대명
param2: 데이터베이스 커서
return: 부대 ID
"""
def FindID(name, cursor):
    #name='B-1-1-Unit1'
    query = "SELECT UnitId FROM init WHERE UnitName = %s"
    cursor.execute(query, (name,))
    id = cursor.fetchone()
    id=id[0]
    print("찾아낸 부대의 ID: ", id) # print for test
    return id

"""
brief: '부대 행동' 특성 전처리를 위한 로그 선택
param1: 부대 ID
param2: 데이터베이스 커서
return: 추출한 로그
"""
def Extract_UnitBehavior(id, cursor):
    query = "SELECT SimulationTime, BehaviorName, Status FROM UnitBehavior WHERE UnitId = %s"
    cursor.execute(query, (id,))
    result=cursor.fetchall()

    # # print for test
    # print("부대 UnitBehavior 추출 정보:")
    # for row in result:
    #     print("SimulationTime: ", row[0])
    #     print("BehaviorName: ", row[1])
    #     print("Status: ", row[2])
    #     print("------------------------")
    
    # Chat GPT에게 넘겨주기 위해 데이터프레임->텍스트로 변환
    import pandas as pd
    # 추출한 데이터로부터 데이터프레임 생성
    dataframe=pd.DataFrame(result, columns=['SimulationTime', 'BehaviorName', 'Status'])
    print(dataframe)
    # 텍스트로 변환
    input_texts=[]
    for index, row in dataframe.iterrows():
        text=f"SimulationTime: {row['SimulationTime']}, BehaviorName: {row['BehaviorName']}, Status: {row['Status']}"
        input_texts.append(text)
    
    input_texts='\n'.join(input_texts)
    # print for text
    print("추출한 로그"+input_texts)

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

"""
다른 특성 구현 시
messages를 특성별로 user를 바꿔야 함.
"""
messages = [
    {"role": "system", "content": "당신은 주어진 데이터를 분석해야 합니다."},
    {"role": "user", "content": "데이터를 분석하여 해당 부대가 주로 수행한 과업은 무엇인지, \
     각 과업에 소요한 시간은 얼마인지, 무슨 과업을 수행했는지 등을 알려주세요.\
     예시: 청군 1대대-1중대는 최초 전술기동 후 점령 과업을 수행하였습니다.\
    부대가 주로 수행한 과업은 '점령'입니다.       "},
    {"role": "assistant", "content": preprocessed_data+"부대 이름: "+name}
]

result=AnaylizeData(openai, messages)
print(result)