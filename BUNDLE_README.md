\# filename: BUNDLE\_README.md

\# -------------------------------------------------------------------------------------------------

\# Naruu Make AI — Video \& Brochure Automation Bundle (Oct 2025)

\# 구성:

\# 1) schemas/\*.json     : 에이전트·도구·시나리오 입·출력 JSON Schema

\# 2) sheets/\*.csv       : 구글시트 구조 샘플

\# 3) blueprints/\*.json  : Make 임포트 블루프린트 (StoryVideoGenerator, BrochureMaker)

\# 4) env/env.sample.json: 키/연결 플레이스홀더



\# 적용 순서(10분):

\# A. Google Sheets에 sheets/\*.csv 구조대로 시트 생성

\# B. Make → Scenarios → ⋯ → Import blueprint → blueprints/\*.json 2개 각각 임포트

\# C. 각 모듈 Connections 맵핑(OpenAI, Google, CloudConvert, Drive, YouTube)

\# D. Scenario Inputs 기본값 확인 → Run once → 성공 시 On-demand Tool로 등록(Agent에서 호출)

\# E. 실패 시 로그 확인 → schemas 참조해 필드 매핑 보정



\# 주의:

\# - Instagram 릴 직접 업로드는 Graph API 권한/규격 제약으로 기본 번들에 미포함(YouTube 우선).

\# - Cloud TTS는 Google TTS 기준. Clova/Polly 사용 시 해당 모듈로 교체.

\# - 이미지 생성은 OpenAI Images(또는 HTTP-API로 대체) 경로 제공.

\# - 영상 합성은 CloudConvert(이미지+오디오 → MP4) 기본, FFmpeg 시나리오 동봉(옵션).

\# -------------------------------------------------------------------------------------------------



