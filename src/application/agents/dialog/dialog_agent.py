# src/application/agents/dialog/dialog_agent.py
import os
import json
import re
from typing import Dict, List, Optional, Tuple, Any

# google-generativeai 라이브러리 import
import google.generativeai as genai
from dotenv import load_dotenv 

# 기존 import 유지 및 UserQuery 경로 확인
from ....domain.entities.conversation import (
    Conversation, ConversationTurn, UserQuery,
    ConversationState, InteractionType
)

# .env 파일에서 환경 변수 로드
# dialog_agent.py 파일의 위치를 기준으로 .env 파일 경로 설정
# (src/application/agents/dialog/dialog_agent.py -> datingapp/.env)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print(f"Warning: .env file not found at {ENV_PATH}. Make sure GOOGLE_API_KEY is set in your environment.")

class DialogAgent:
    """기본 대화 에이전트 - 사용자와의 상호작용을 관리 (Gemini LLM 사용)"""

    def __init__(self):
        self.conversation_memory: Dict[str, Conversation] = {}

        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            print("CRITICAL: GOOGLE_API_KEY가 환경 변수에 설정되지 않았습니다. LLM 기능이 작동하지 않을 수 있습니다.")
            self.gemini_model = None
        else:
            try:
                genai.configure(api_key=google_api_key)
                self.gemini_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash", 
                )
            except Exception as e:
                print(f"Error initializing Gemini model: {e}")
                self.gemini_model = None

    async def _extract_entities_with_gemini(self, text: str) -> Dict[str, Any]:
        """Gemini를 사용하여 사용자 입력에서 주요 정보 추출 (비동기)"""
        if not self.gemini_model:
            print("Error: Gemini model is not initialized. Cannot extract entities.")
            return {}

        prompt = f"""
        다음 사용자 입력에서 데이트 계획과 관련된 주요 정보를 추출하여 JSON 형식으로 반환해주세요.
        추출할 정보는 "location", "budget", "date", "interests" 입니다.
        - location: 장소 (예: "강남", "홍대입구역 근처"). 문자열.
        - budget: 숫자 형태의 예산 (예: 50000, 100000). 숫자. 언급 없으면 null.
        - date: 날짜 또는 시간 관련 표현 (예: "내일 저녁 7시", "주말 오후"). 문자열. 언급 없으면 null.
        - interests: 관심사 또는 활동 목록 (예: ["맛집 탐방", "영화 감상", "산책"]). 문자열 리스트. 언급 없으면 null.

        사용자 입력: "{text}"

        JSON 형식의 응답 예시 (다른 설명 없이 JSON만 반환):
        {{ "location": "강남", "budget": 50000, "date": "내일 저녁 7시", "interests": ["맛집 탐방", "영화 감상"] }}
        만약 특정 정보가 없다면 해당 키의 값은 null 또는 빈 리스트/문자열로 설정해주세요.
        """
        try:
            response = await self.gemini_model.generate_content_async(prompt)
            content_string = ""
            if hasattr(response, 'text') and response.text:
                content_string = response.text
            elif hasattr(response, 'parts') and response.parts:
                 content_string = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                print(f"Warning: Gemini로부터 유효한 응답 텍스트를 받지 못했습니다. Response: {response}")
                return {}
            
            match = re.search(r"```json\s*(\{.*?\})\s*```", content_string, re.DOTALL | re.IGNORECASE)
            if not match:
                match = re.search(r"(\{.*?\})", content_string, re.DOTALL)

            if match:
                json_string = match.group(1)
                entities = json.loads(json_string)
                return entities
            else:
                print(f"Warning: Gemini가 유효한 JSON을 반환하지 않았습니다. 정제된 응답: {content_string}")
                try:
                    return json.loads(content_string) 
                except json.JSONDecodeError as e_json:
                    print(f"Error: Gemini 응답을 JSON으로 파싱하는데 실패했습니다: {e_json}")
                    return {}

        except Exception as e:
            print(f"Gemini 호출 또는 응답 파싱 중 오류 발생: {e}")
            return {}

    async def parse_user_query(self, user_input: str, session_id: str) -> UserQuery:
        query = UserQuery(text=user_input, session_id=session_id)

        if not self.gemini_model:
            print("Warning: Gemini 모델이 초기화되지 않아 질의 파싱을 건너뜁니다.")
            query.parsed = False
            query.confidence_score = 0.0
            return query

        extracted_entities = await self._extract_entities_with_gemini(user_input)

        query.location = extracted_entities.get("location")
        budget_value = extracted_entities.get("budget")
        if isinstance(budget_value, (int, float)):
            query.budget = float(budget_value)
        elif isinstance(budget_value, str):
            try:
                cleaned_budget_str = re.sub(r'[^\d.]', '', budget_value)
                if cleaned_budget_str: query.budget = float(cleaned_budget_str)
                else: query.budget = None
            except ValueError: query.budget = None
        else: query.budget = None

        query.date = extracted_entities.get("date")
        interests_value = extracted_entities.get("interests")
        if isinstance(interests_value, list):
            query.add_preference("interests", [str(i) for i in interests_value if i])
        elif isinstance(interests_value, str) and interests_value:
            query.add_preference("interests", [i.strip() for i in interests_value.split(',') if i.strip()])
        
        if extracted_entities:
            query.parsed = True
            query.confidence_score = self._calculate_confidence_from_gemini(extracted_entities)
        else:
            query.parsed = False
            query.confidence_score = 0.0
        return query

    def _calculate_confidence_from_gemini(self, entities: Dict[str, Any]) -> float:
        score = 0.0
        if entities.get("location"): score += 0.35
        if entities.get("date"): score += 0.25
        interests = entities.get("interests")
        if isinstance(interests, list) and interests: score += 0.20
        elif isinstance(interests, str) and interests: score += 0.10
        if entities.get("budget") is not None: score += 0.10
        return min(score, 1.0)

    async def start_conversation(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, Any]]:
        user_query = await self.parse_user_query(user_input, session_id)
        conversation = Conversation(
            session_id=session_id, initial_query=user_query,
            current_state=ConversationState.INITIAL_PLANNING
        )
        self.conversation_memory[session_id] = conversation
        response = await self._generate_initial_response(user_query)
        turn = ConversationTurn(
            turn_id=f"turn_{len(conversation.turns) + 1}", user_input=user_input,
            agent_response=response, interaction_type=InteractionType.INITIAL_QUERY,
            state_after=ConversationState.INITIAL_PLANNING
        )
        conversation.add_turn(turn)
        return response, {"conversation_state": conversation.current_state.value}

    async def handle_user_input(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, Any]]:
        conversation = self.conversation_memory.get(session_id)
        if not conversation:
            return await self.start_conversation(session_id, user_input)
        
        response, next_state = await self._process_by_state(conversation, user_input)
        
        turn = ConversationTurn(
            turn_id=f"turn_{len(conversation.turns) + 1}", user_input=user_input,
            agent_response=response, 
            interaction_type=self._determine_interaction_type(conversation, user_input),
            state_after=next_state
        )
        conversation.add_turn(turn)
        return response, {
            "conversation_state": conversation.current_state.value,
            "awaiting_input": conversation.awaiting_user_input
        }

    async def _generate_initial_response(self, user_query: UserQuery) -> str:
        if not self.gemini_model and not user_query.parsed:
             return "죄송합니다, 현재 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요. (API 키 또는 LLM 초기화 확인 필요)"
        if user_query.confidence_score < 0.3:
            return self._generate_clarification_request(user_query)
        
        response_parts = ["알겠습니다!"]
        if user_query.location: response_parts.append(f"{user_query.location}에서")
        if user_query.date: response_parts.append(f"{user_query.date}에")
        if user_query.get_preference('interests'): response_parts.append(f"{', '.join(user_query.get_preference('interests'))} 활동을 포함하여")
        if user_query.budget is not None: response_parts.append(f"약 {int(user_query.budget)}원 예산으로")
        response_parts.append("데이트 계획을 세워볼게요. 잠시만 기다려주세요.")
        return " ".join(response_parts)
    
    def _generate_clarification_request(self, user_query: UserQuery) -> str:
        """명확화 질문 생성"""
        
        questions = []
        
        if not user_query.has_location():
            questions.append("📍 어느 지역에서 데이트하고 싶으신가요?")
        
        if not user_query.get_interests():
            questions.append("🎯 어떤 종류의 장소를 선호하시나요? (예: 문화재, 카페, 쇼핑, 공원 등)")
        
        if not user_query.has_budget():
            questions.append("💰 예산은 대략 어느 정도 생각하고 계시나요?")
        
        response = "😊 데이트 계획을 세워드리기 위해 몇 가지 질문드릴게요!\n\n"
        response += "\n".join(questions)
        
        return response
    
    async def _process_by_state(self, conversation: Conversation, user_input: str) -> Tuple[str, ConversationState]:
        """대화 상태별 처리"""
        
        current_state = conversation.current_state
        
        if current_state == ConversationState.INITIAL_PLANNING:
            return await self._handle_initial_planning(conversation, user_input)
        
        elif current_state == ConversationState.AWAITING_USER_SELECTION:
            return await self._handle_user_selection(conversation, user_input)
        
        elif current_state == ConversationState.PRESENTING_RESULTS:
            return await self._handle_result_feedback(conversation, user_input)
        
        else:
            # 기본 처리
            return await self._handle_general_input(conversation, user_input)
    
    async def _handle_initial_planning(self, conversation: Conversation, user_input: str) -> Tuple[str, ConversationState]:
        """초기 계획 단계 처리"""
        
        # 추가 정보 수집
        additional_info = await self.parse_user_query(user_input, conversation.session_id)
        
        # 기존 정보와 병합
        if conversation.initial_query:
            if additional_info.location and not conversation.initial_query.location:
                conversation.initial_query.location = additional_info.location
            
            if additional_info.budget and not conversation.initial_query.budget:
                conversation.initial_query.budget = additional_info.budget
            
            # 선호도 병합
            existing_interests = conversation.initial_query.get_interests()
            new_interests = additional_info.get_interests()
            all_interests = list(set(existing_interests + new_interests))
            conversation.initial_query.add_preference("interests", all_interests)
        
        # 정보가 충분한지 확인
        if conversation.initial_query and conversation.initial_query.is_complete():
            response = "👍 정보를 모두 받았어요! 맞춤 장소들을 찾아보겠습니다..."
            return response, ConversationState.PLANNING_IN_PROGRESS
        else:
            response = self._generate_clarification_request(conversation.initial_query or additional_info)
            return response, ConversationState.INITIAL_PLANNING
    
    async def _handle_user_selection(self, conversation: Conversation, user_input: str) -> Tuple[str, ConversationState]:
        """사용자 선택 처리"""
        
        # 간단한 선택 파싱 (나중에 개선)
        selections = self._parse_selections(user_input)
        
        if selections:
            conversation.update_collected_data("selected_spots", selections)
            response = f"✅ {', '.join(selections)}를 선택하셨네요! 최적의 일정을 계획해보겠습니다."
            return response, ConversationState.PLANNING_IN_PROGRESS
        else:
            response = "죄송해요, 선택을 이해하지 못했어요. 번호나 이름으로 다시 선택해주세요."
            return response, ConversationState.AWAITING_USER_SELECTION
    
    async def _handle_result_feedback(self, conversation: Conversation, user_input: str) -> Tuple[str, ConversationState]:
        """결과에 대한 피드백 처리"""
        
        if any(word in user_input for word in ["좋아", "마음에 들어", "완벽", "확정"]):
            response = "🎉 훌륭해요! 즐거운 데이트 되세요!"
            return response, ConversationState.PLAN_CONFIRMED
        
        elif any(word in user_input for word in ["수정", "바꿔", "다른", "변경"]):
            response = "🔄 어떤 부분을 수정하고 싶으신가요?"
            return response, ConversationState.MODIFYING_PLAN
        
        else:
            response = "더 궁금한 점이 있으시면 언제든 물어보세요!"
            return response, ConversationState.PRESENTING_RESULTS
    
    async def _handle_general_input(self, conversation: Conversation, user_input: str) -> Tuple[str, ConversationState]:
        """일반적인 입력 처리"""
        
        response = "말씀해주신 내용을 처리하고 있어요. 조금만 기다려주세요!"
        return response, conversation.current_state
    
    def _determine_interaction_type(self, conversation: Conversation, user_input: str) -> InteractionType:
        """상호작용 타입 결정"""
        
        if conversation.awaiting_user_input:
            if conversation.expected_input_type:
                return conversation.expected_input_type
        
        # 키워드 기반 분류
        if any(word in user_input for word in ["선택", "고르"]):
            return InteractionType.SELECTION_REQUIRED
        elif "?" in user_input or any(word in user_input for word in ["뭐", "어떤", "언제"]):
            return InteractionType.INFORMATION_REQUEST
        elif any(word in user_input for word in ["수정", "바꿔", "변경"]):
            return InteractionType.PLAN_MODIFICATION
        else:
            return InteractionType.GENERAL_QUESTION
    
    def _parse_selections(self, user_input: str) -> List[str]:
        """사용자 선택 파싱 (간단한 버전)"""
        selections = []
        
        # 숫자 선택 파싱 (1, 2, 3 등)
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            selections.extend([f"option_{num}" for num in numbers])
        
        # 장소명 직접 언급 파싱 (나중에 개선)
        places = ["경복궁", "인사동", "남산", "홍대", "명동"]
        for place in places:
            if place in user_input:
                selections.append(place)
        
        return selections
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """대화 조회"""
        return self.conversation_memory.get(session_id)
    
    def clear_conversation(self, session_id: str):
        """대화 삭제"""
        if session_id in self.conversation_memory:
            del self.conversation_memory[session_id]