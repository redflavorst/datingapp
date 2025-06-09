# src/application/agents/dialog/dialog_agent.py
from typing import Dict, List, Optional, Tuple, Any
import re
from datetime import datetime
import uuid

from ....domain.entities.conversation import (
    Conversation, ConversationTurn, UserQuery, 
    ConversationState, InteractionType
)

class DialogAgent:
    """기본 대화 에이전트 - 사용자와의 상호작용을 관리"""
    
    def __init__(self):
        self.conversation_memory: Dict[str, Conversation] = {}
        
    async def start_conversation(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """새로운 대화 시작"""
        
        # 사용자 질의 파싱
        user_query = await self.parse_user_query(user_input, session_id)
        
        # 대화 객체 생성
        conversation = Conversation(
            session_id=session_id,
            initial_query=user_query,
            current_state=ConversationState.INITIAL_PLANNING
        )
        
        # 메모리에 저장
        self.conversation_memory[session_id] = conversation
        
        # 초기 응답 생성
        response = await self._generate_initial_response(user_query)
        
        # 대화 턴 기록
        turn = ConversationTurn(
            turn_id=f"turn_{len(conversation.turns) + 1}",
            user_input=user_input,
            agent_response=response,
            interaction_type=InteractionType.INITIAL_QUERY,
            state_after=ConversationState.INITIAL_PLANNING
        )
        
        conversation.add_turn(turn)
        
        return response, {"conversation_state": conversation.current_state.value}
    
    async def handle_user_input(self, session_id: str, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """사용자 입력 처리"""
        
        conversation = self.conversation_memory.get(session_id)
        if not conversation:
            # 세션이 없으면 새로 시작
            return await self.start_conversation(session_id, user_input)
        
        # 현재 상태에 따른 처리
        response, next_state = await self._process_by_state(conversation, user_input)
        
        # 대화 턴 기록
        turn = ConversationTurn(
            turn_id=f"turn_{len(conversation.turns) + 1}",
            user_input=user_input,
            agent_response=response,
            interaction_type=self._determine_interaction_type(conversation, user_input),
            state_after=next_state
        )
        
        conversation.add_turn(turn)
        
        return response, {
            "conversation_state": conversation.current_state.value,
            "awaiting_input": conversation.awaiting_user_input
        }
    
    async def parse_user_query(self, user_input: str, session_id: str) -> UserQuery:
        """사용자 질의 파싱"""
        
        query = UserQuery(
            text=user_input,
            session_id=session_id
        )
        
        # 위치 추출
        query.location = self._extract_location(user_input)
        
        # 예산 추출
        query.budget = self._extract_budget(user_input)
        
        # 날짜 추출
        query.date = self._extract_date(user_input)
        
        # 선호도 추출
        interests = self._extract_interests(user_input)
        if interests:
            query.add_preference("interests", interests)
        
        # 파싱 완료 표시
        query.parsed = True
        query.confidence_score = self._calculate_confidence(query)
        
        return query
    
    def _extract_location(self, text: str) -> Optional[str]:
        """위치 정보 추출"""
        # 주요 도시/지역 패턴
        locations = [
            "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
            "제주", "강남", "홍대", "명동", "인사동", "이태원", "신촌", "압구정",
            "강북", "강동", "강서", "관악", "노원", "도봉", "동대문", "마포",
            "서대문", "성동", "성북", "송파", "양천", "영등포", "용산", "은평",
            "종로", "중구", "중랑"
        ]
        
        for location in locations:
            if location in text:
                return location
        
        return None
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """예산 정보 추출"""
        # "10만원", "100000원", "10만", "100000" 패턴
        patterns = [
            r'(\d+)만원',      # 10만원
            r'(\d+)만',        # 10만
            r'(\d+)원',        # 100000원 (5자리 이상)
            r'예산.*?(\d+)만', # 예산은 10만
            r'(\d+)정도'       # 10만 정도
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = int(match.group(1))
                # 만원 단위인지 원 단위인지 판단
                if '만' in pattern or amount < 1000:
                    return float(amount * 10000)
                else:
                    return float(amount)
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """날짜 정보 추출 (간단한 패턴)"""
        date_patterns = [
            "오늘", "내일", "모레", "이번주", "다음주", "주말", "토요일", "일요일"
        ]
        
        for pattern in date_patterns:
            if pattern in text:
                return pattern
        
        return None
    
    def _extract_interests(self, text: str) -> List[str]:
        """관심사/선호도 추출"""
        interests = []
        
        # 카테고리 키워드 맵핑
        category_keywords = {
            "문화재": ["문화재", "궁", "고궁", "한옥", "전통", "역사"],
            "카페": ["카페", "커피", "디저트", "브런치"],
            "박물관": ["박물관", "미술관", "갤러리", "전시"],
            "쇼핑": ["쇼핑", "백화점", "마트", "시장", "구매"],
            "공원": ["공원", "산책", "자연", "숲"],
            "레스토랑": ["레스토랑", "식당", "맛집", "음식", "식사"],
            "전망대": ["전망", "뷰", "야경", "타워"],
            "테마파크": ["놀이공원", "테마파크", "롤러코스터"],
            "해변": ["바다", "해변", "해수욕장", "바닷가"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                interests.append(category)
        
        return interests
    
    def _calculate_confidence(self, query: UserQuery) -> float:
        """파싱 신뢰도 계산"""
        score = 0.0
        
        if query.has_location():
            score += 0.4
        if query.has_budget():
            score += 0.3
        if query.get_interests():
            score += 0.2
        if query.date:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _generate_initial_response(self, user_query: UserQuery) -> str:
        """초기 응답 생성"""
        
        if user_query.confidence_score < 0.3:
            # 정보가 부족한 경우
            return self._generate_clarification_request(user_query)
        
        # 기본 정보가 있는 경우
        response = f"✨ {user_query.location}에서 데이트 계획을 세워드릴게요!\n\n"
        
        # 파악된 정보 확인
        if user_query.has_budget():
            response += f"💰 예산: {int(user_query.budget):,}원\n"
        
        if user_query.get_interests():
            interests_str = ", ".join(user_query.get_interests())
            response += f"🎯 관심사: {interests_str}\n"
        
        response += "\n🔍 맞춤 관광지를 찾아보고 있어요. 잠시만 기다려주세요!"
        
        return response
    
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