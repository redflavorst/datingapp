import asyncio
import uuid
import logging

from src.application.agents.dialog.dialog_agent import DialogAgent

async def interactive_chat() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    agent = DialogAgent()
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    logger.debug("챗봇 세션 %s 시작", session_id)

    print("데이트 플래너 챗봇에 오신 것을 환영합니다!")
    print("종료하려면 'quit' 또는 'exit'을 입력하세요.\n")

    user_input = input("사용자: ").strip()
    if not user_input:
        print("초기 질문이 필요합니다.")
        return

    logger.debug("사용자 입력 초기: %s", user_input)
    response, _ = await agent.start_conversation(session_id, user_input)
    logger.debug("초기 응답: %s", response)
    print(f"에이전트: {response}")

    while True:
        user_input = input("사용자: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            print("대화를 종료합니다.")
            break
        logger.debug("사용자 입력: %s", user_input)
        response, _ = await agent.handle_user_input(session_id, user_input)
        logger.debug("에이전트 응답: %s", response)
        print(f"에이전트: {response}")


def main() -> None:
    try:
        asyncio.run(interactive_chat())
    except KeyboardInterrupt:
        print("\n대화를 종료합니다.")


if __name__ == "__main__":
    main()
