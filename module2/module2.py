
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

# ChatGPT Connect
import os
import openai
os.environ.get('OPENAI_API_KEY') is None
os.environ["OPENAI_API_KEY"] = 'sk-'    # 실행 시 api 를 입력하세요.
openai.api_key = os.getenv("OPENAI_API_KEY")

name='B-1-1-Unit1' # 테스트용 분석 대상
# 테스트용 전처리 데이터/모듈 1에서 생성됨
preprocessed_data="BehaviorName: 전술기동\
- 시작 시각: 60\
- 종료 시각: 150\
\
BehaviorName: 전술기동\
- 시작 시각: 180\
- 종료 시각: 9180"

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