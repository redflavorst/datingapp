# datingapp

이 프로젝트는 데이트 장소 추천 및 일정을 계획해주는 챗봇 예시입니다.

## 실행 방법

1. 필요한 패키지 설치
   ```bash
   pip install -r requirements.txt  # 의존 패키지 설치
   ```
   *또는 코드에서 사용되는 `google-generativeai`, `python-dotenv` 등을 수동으로 설치합니다.*

2. 환경 변수 준비
   - `GOOGLE_API_KEY` 값을 `.env` 파일에 넣거나 환경 변수로 설정합니다.

3. 애플리케이션 실행
   ```bash
   python src/main.py
   ```
   실행 후 나타나는 프롬프트에 질문을 입력하면 챗봇과 대화를 시작할 수 있습니다. 종료하려면 `quit` 또는 `exit` 을 입력합니다.
