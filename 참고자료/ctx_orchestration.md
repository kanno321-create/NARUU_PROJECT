\# ORCHESTRATION RULES



\## 모듈 vs 시나리오

\- 단일 API·단일 변환: 모듈 툴

\- 2스텝 이상·검증/분기 포함: 시나리오 툴(On-Demand)



\## 호출 순서(권장)

getIdea → writeScript → makeAudio → makeImage → assembleVideo → save/report → (approve) → upload



\## 실패 대처

\- 인코딩 오류: FFmpeg 재래핑(mp4: faststart), 샘플레이트/비트레이트 재설정

\- 파일 링크 불량: 파일 실주소 확보 후 재시도

\- 과도 길이: 스크립트 15–20% 요약 재생성



