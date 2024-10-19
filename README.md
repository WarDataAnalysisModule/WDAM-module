# 🧑‍🏫 프로젝트 소개
안녕하세요, 파도입니다.

본 프로젝트에서는 **대규모 인공지능 언어모델을 활용한 전장 지식 자동 생성 기술 연구개발**이라는 주제로, 
방대하고 복잡한 시계열 수치 형식의 전장 관측 데이터를 분석하기 위하여 이 프로젝트를 진행하게 됐습니다. 
기존의 사람이 하던 일을 생성형 AI로 대체하여 전장 상황을 이해하고, 정확한 정보를 효율적으로 분석하도록 하는 것을 목표로 하였습니다.

저희는 편리하게 데이터를 업로드하고, 분석할 수 있는 전장 데이터 분석 모듈, **WDAM** 웹 애플리케이션을 제작하였습니다.

⭐ 이 리포지토리는 WDAM 웹 애플리케이션 제작 프로젝트에서 **ChatGPT API를 이용한 데이터 전처리 및 분석 모듈 파트** 작업을 관리하는 리포지토리입니다.

# 🖥️ 개발 환경
- Python
- OpenAI의 ChatGPT API


# ⚙️ 구성
사용자는 미리 정해진 다섯 가지 형식의 데이터 파일을 업로드할 수 있습니다.
업로드된 데이터는 데이터베이스 내 알맞는 테이블에 저장되며
사용자가 쉽게 유용한 분석 결과를 얻을 수 있도록 다음과 같은 분석 특성 선택지를 제공합니다.

1. 부대 이동 속도/위치 변화
2. 인원/장비/자원 변화
3. 부대의 전투력
4. 부대의 피해상황
5. 부대의 행동
6. 개체 탐지 기록
7. 부대별 초기 정보
   
## Module 1: 데이터 전처리 모듈
데이터 전처리 모듈에서는 사용자가 선택한 분석 대상(ex 단위 부대)와 특성에 맞추어
데이터베이스에서 필요한 데이터를 추출하며
이를 분석하기 좋은 형태로 요약하거나 형식에 맞게 정리하는 전처리 과정을 거칩니다.

![전처리모듈](https://github.com/user-attachments/assets/35bb7339-b4a5-4343-a769-6e924a4197ed)

## Module 2: 데이터 분석 모듈
데이터 분석 모듈에서는 모듈 1에서 전처리한 데이터를 통해
유용한 분석 결과를 생성합니다.
텍스트 형태의 분석 결과 뿐 아니라 시각 자료 생성을 위한 코드 작성 기능을 추가하였습니다.
생성된 이미지는 AWS S3 스토리지에 저장합니다.

![분석모듈](https://github.com/user-attachments/assets/fd316f28-361e-4376-a89c-0404a39a7ebf)


# 프로젝트 주의사항
프론트엔드 코드는 프론트엔드 리포지토리에서 따로 관리되며, localhost 환경이 아닌 AWS 인스턴스 환경을 기준으로 프로젝트를 진행하였습니다.
또한 ChatGPT API, Database key 등 민감한 정보는 업로드하지 않았습니다.

코드 참고 시 주의하시기 바랍니다.

---
contanct us: 팀장 이소영 soo7132@naver.com
