# test/unit/application/agents/test_dialog_agent.py
import pytest
from unittest.mock import AsyncMock, patch # AsyncMock 추가
import json

# 경로가 프로젝트 루트 기준이므로 src부터 시작하도록 수정
from src.application.agents.dialog.dialog_agent import DialogAgent
from src.domain.entities.conversation import UserQuery # UserQuery import 추가

class TestDialogAgent:
    """대화 에이전트 테스트"""

    @pytest.fixture
    def dialog_agent(self):
        # DialogAgent 생성 시 API 키 로드를 시도하므로, 테스트 중에는
        # 실제 API 키가 없어도 되도록 gemini_model을 모킹하거나 None으로 설정할 수 있습니다.
        # 여기서는 __init__에서 GOOGLE_API_KEY 환경 변수가 없으면 model이 None이 되도록 처리되어 있습니다.
        # 테스트 시 GOOGLE_API_KEY가 설정되어 있지 않다고 가정하고 진행합니다.
        # 만약 키가 설정되어 있다면, 각 테스트에서 gemini_model.generate_content_async를 모킹해야 합니다.
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key_for_init_not_to_fail_hard'}):
             # DialogAgent가 내부적으로 genai.configure를 호출하므로, 이를 모킹할 수도 있습니다.
            with patch('google.generativeai.configure') as mock_configure, \
                 patch('google.generativeai.GenerativeModel') as mock_generative_model:
                
                # GenerativeModel 인스턴스 모킹
                mock_model_instance = AsyncMock()
                mock_generative_model.return_value = mock_model_instance
                
                agent = DialogAgent()
                # 테스트에서 사용할 수 있도록 모킹된 모델 인스턴스를 agent에 할당
                agent.gemini_model = mock_model_instance 
                return agent


    @pytest.mark.asyncio
    async def test_start_conversation(self, dialog_agent, mocker): # mocker 추가
        """대화 시작 테스트"""
        session_id = "test_session_001"
        user_input = "서울에서 데이트 계획 짜줘"

        # parse_user_query 내부의 _extract_entities_with_gemini가 호출되므로 모킹 필요
        # 또는 _extract_entities_with_gemini 자체를 모킹할 수도 있습니다.
        # 여기서는 gemini_model.generate_content_async를 모킹합니다.
        mock_gemini_response_text = """
        {
            "location": "서울",
            "budget": null,
            "date": null,
            "interests": []
        }
        """
        if dialog_agent.gemini_model: # 모델이 초기화된 경우에만 모킹
            dialog_agent.gemini_model.generate_content_async.return_value = AsyncMock(text=mock_gemini_response_text)
        else: # 모델 초기화 안된 경우, _extract_entities_with_gemini가 {} 반환하도록
            mocker.patch.object(dialog_agent, '_extract_entities_with_gemini', return_value={
                "location": "서울", "budget": None, "date": None, "interests": []
            })


        response_tuple = await dialog_agent.start_conversation(session_id, user_input)
        # start_conversation이 튜플 (str, dict)를 반환한다고 가정
        assert isinstance(response_tuple, tuple)
        assert len(response_tuple) == 2
        response, metadata = response_tuple

        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(metadata, dict)
        assert "conversation_state" in metadata
        assert dialog_agent.get_conversation(session_id) is not None

    @pytest.mark.asyncio
    async def test_parse_user_query_full_info(self, dialog_agent, mocker):
        """사용자 질의 파싱 - 모든 정보 추출 테스트"""
        user_input = "강남에서 내일 저녁 7시에 5만원으로 맛집 탐방하고 영화 보고 싶어"
        session_id = "test_session_parse_full"

        expected_entities_dict = {
            "location": "강남",
            "budget": 50000,
            "date": "내일 저녁 7시",
            "interests": ["맛집 탐방", "영화 감상"]
        }
        mock_response_text = f"""
        ```json
        {json.dumps(expected_entities_dict)}
        ```
        """
        if dialog_agent.gemini_model:
            dialog_agent.gemini_model.generate_content_async.return_value = AsyncMock(text=mock_response_text)
        else:
             mocker.patch.object(dialog_agent, '_extract_entities_with_gemini', return_value=expected_entities_dict)


        query = await dialog_agent.parse_user_query(user_input, session_id)

        assert isinstance(query, UserQuery)
        assert query.text == user_input
        assert query.entities["location"] == "강남"
        assert query.entities["budget"] == 50000
        assert query.entities["date"] == "내일 저녁 7시"
        assert query.entities["interests"] == ["맛집 탐방", "영화 감상"]
        # parse_user_query에서 intent를 entities.get("intent", "unknown")으로 가져오므로
        # _extract_entities_with_gemini가 intent를 반환하지 않으면 "unknown"이 됩니다.
        assert query.intent == "unknown" 

    @pytest.mark.asyncio
    async def test_parse_user_query_partial_info_budget_missing(self, dialog_agent, mocker):
        """사용자 질의 파싱 - 일부 정보(예산 누락) 추출 테스트"""
        user_input = "홍대에서 오늘 영화 보고 싶어"
        session_id = "test_session_parse_partial"

        expected_entities_dict = {
            "location": "홍대",
            "budget": None, # 예산 언급 없음
            "date": "오늘",
            "interests": ["영화 감상"]
        }
        mock_response_text = json.dumps(expected_entities_dict) # 코드 블록 없이 반환되는 경우
        
        if dialog_agent.gemini_model:
            dialog_agent.gemini_model.generate_content_async.return_value = AsyncMock(text=mock_response_text)
        else:
            mocker.patch.object(dialog_agent, '_extract_entities_with_gemini', return_value=expected_entities_dict)

        query = await dialog_agent.parse_user_query(user_input, session_id)

        assert query.entities["location"] == "홍대"
        assert query.entities["budget"] is None
        assert query.entities["date"] == "오늘"
        assert query.entities["interests"] == ["영화 감상"]

    @pytest.mark.asyncio
    async def test_extract_entities_with_gemini_no_relevant_info(self, dialog_agent, mocker):
        """_extract_entities_with_gemini - 관련 정보 없는 질의 테스트"""
        user_input = "오늘 날씨 어때?"
        expected_entities_dict = {
            "location": None,
            "budget": None,
            "date": "오늘", # '오늘'은 날짜로 인식될 수 있음
            "interests": None # 또는 [] - 프롬프트에 따라 달라짐
        }
        # 프롬프트는 언급 없으면 null 또는 빈 리스트/문자열로 설정하라고 되어있음
        # 실제 Gemini 응답을 모킹
        mock_response_text = f"""
        {{
            "location": null,
            "budget": null,
            "date": "오늘",
            "interests": null
        }}
        """
        if dialog_agent.gemini_model:
            dialog_agent.gemini_model.generate_content_async.return_value = AsyncMock(text=mock_response_text)
        else:
            # 이 테스트는 _extract_entities_with_gemini를 직접 테스트하므로, gemini_model이 None이면 스킵
             if not dialog_agent.gemini_model: pytest.skip("Gemini model not initialized")


        entities = await dialog_agent._extract_entities_with_gemini(user_input)
        
        # 실제 Gemini의 동작에 따라 location, interests가 null 또는 빈 문자열/리스트일 수 있습니다.
        # 프롬프트의 예시와 지시를 기반으로 기대값을 설정합니다.
        assert entities.get("location") is None
        assert entities.get("budget") is None
        assert entities.get("date") == "오늘" # "오늘"은 추출될 수 있음
        assert entities.get("interests") is None # 또는 []

    @pytest.mark.asyncio
    async def test_extract_entities_with_gemini_invalid_json_response(self, dialog_agent, mocker):
        """_extract_entities_with_gemini - Gemini가 잘못된 JSON 반환 시 테스트"""
        user_input = "아무거나 보여줘"
        # Gemini가 JSON 형식이 아닌 응답을 보냈다고 가정
        mock_response_text = "죄송합니다, 잘 이해하지 못했어요. 장소, 날짜, 예산, 관심사를 알려주시겠어요?"
        
        if dialog_agent.gemini_model:
            dialog_agent.gemini_model.generate_content_async.return_value = AsyncMock(text=mock_response_text)
        else:
            if not dialog_agent.gemini_model: pytest.skip("Gemini model not initialized")

        entities = await dialog_agent._extract_entities_with_gemini(user_input)

        # _extract_entities_with_gemini는 파싱 실패 시 {"error": ..., "raw_response": ...} 또는 빈 {}를 반환할 수 있음
        # 현재 구현은 print 후 {} 또는 에러가 포함된 dict를 반환
        assert "error" in entities or not entities # 빈 딕셔너리일 수도 있음
        if "raw_response" in entities:
            assert entities["raw_response"] == mock_response_text


    @pytest.mark.asyncio
    async def test_extract_entities_with_gemini_model_not_initialized(self, mocker):
        """_extract_entities_with_gemini - Gemini 모델 미초기화 시 테스트"""
        # DialogAgent를 생성할 때 GOOGLE_API_KEY가 없도록 하여 gemini_model이 None이 되도록 함
        with patch.dict('os.environ', {}, clear=True): # API 키 없는 환경
            with patch('google.generativeai.configure'), patch('google.generativeai.GenerativeModel'):
                agent_no_model = DialogAgent()
        
        assert agent_no_model.gemini_model is None # 모델이 None인지 확인
        
        user_input = "테스트 입력"
        entities = await agent_no_model._extract_entities_with_gemini(user_input)
        
        assert entities == {} # 모델 없으면 빈 딕셔너리 반환

    @pytest.mark.asyncio
    async def test_handle_user_input_new_conversation(self, dialog_agent, mocker):
        """handle_user_input - 새 대화 시작 테스트"""
        session_id = "new_session_handle"
        user_input = "부산 여행 계획 세워줘"

        # start_conversation 내부에서 parse_user_query -> _extract_entities_with_gemini 호출
        mock_entities = {"location": "부산", "budget": None, "date": None, "interests": ["여행"]}
        
        # start_conversation이 호출될 것이므로 해당 메서드 자체를 모킹하거나
        # 내부의 gemini 호출을 모킹합니다.
        # 여기서는 start_conversation이 반환하는 값을 모킹하여 간단히 테스트합니다.
        mock_start_conv_response = ("부산 여행 계획을 세워드릴게요!", {"conversation_state": "INITIAL_PLANNING"})
        mocker.patch.object(dialog_agent, 'start_conversation', return_value=mock_start_conv_response)

        response, metadata = await dialog_agent.handle_user_input(session_id, user_input)

        dialog_agent.start_conversation.assert_called_once_with(session_id, user_input)
        assert response == mock_start_conv_response[0]
        assert metadata == mock_start_conv_response[1]

    @pytest.mark.asyncio
    async def test_handle_user_input_existing_conversation(self, dialog_agent, mocker):
        """handle_user_input - 기존 대화 처리 테스트"""
        session_id = "existing_session_handle"
        user_input = "다른 장소는 없어?"

        # 먼저 대화를 하나 생성해둡니다.
        initial_query_mock = UserQuery(text="첫 질문", session_id=session_id, entities={})
        conversation_mock = mocker.Mock()
        conversation_mock.initial_query = initial_query_mock
        conversation_mock.current_state = "AWAITING_USER_CLARIFICATION" # 예시 상태
        dialog_agent.conversation_memory[session_id] = conversation_mock
        
        # _process_by_state가 호출될 것이므로 이를 모킹
        mock_process_response = ("다른 장소를 찾아볼게요.", {"conversation_state": "PLANNING_IN_PROGRESS"})
        mocker.patch.object(dialog_agent, '_process_by_state', return_value=mock_process_response)

        response, metadata = await dialog_agent.handle_user_input(session_id, user_input)

        dialog_agent._process_by_state.assert_called_once_with(conversation_mock, user_input)
        assert response == mock_process_response[0]
        assert metadata == mock_process_response[1]

    # 여기에 _generate_initial_response, _generate_clarification_request, 
    # _process_by_state의 각 상태별 핸들러(_handle_initial_planning 등)에 대한 테스트 추가 가능
    # 해당 메서드들은 내부 로직이 복잡하고 다른 에이전트나 LLM 호출을 포함할 수 있으므로
    # 각 메서드의 책임에 맞게 적절히 모킹하여 테스트해야 합니다.
