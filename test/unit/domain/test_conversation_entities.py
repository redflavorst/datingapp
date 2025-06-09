import pytest
from datetime import datetime
from src.domain.entities.conversation import (
    Conversation, ConversationTurn, UserQuery,
    ConversationState, InteractionType
)

class TestUserQuery:
    """사용자 질의 엔티티 테스트"""
    
    def test_create_user_query(self):
        """기본 사용자 질의 생성 테스트"""
        query = UserQuery(
            text="서울에서 데이트 계획 짜줘",
            session_id="test_session_001"
        )
        
        assert query.text == "서울에서 데이트 계획 짜줘"
        assert query.session_id == "test_session_001"
        assert query.parsed == False
        assert query.confidence_score == 0.0
    
    def test_add_preference(self):
        """선호도 추가 테스트"""
        query = UserQuery(text="test", session_id="test")
        query.add_preference("interests", ["문화재", "카페"])
        
        assert query.preferences["interests"] == ["문화재", "카페"]
    
    def test_has_location(self):
        """위치 정보 확인 테스트"""
        query = UserQuery(text="test", session_id="test")
        
        # 위치 없음
        assert query.has_location() == False
        
        # 위치 있음
        query.location = "서울"
        assert query.has_location() == True
        
        # 빈 문자열
        query.location = ""
        assert query.has_location() == False
    
    def test_is_complete(self):
        """완전성 확인 테스트"""
        query = UserQuery(text="test", session_id="test")
        
        # 불완전
        assert query.is_complete() == False
        
        # 위치 + 관심사
        query.location = "서울"
        query.add_preference("interests", ["문화재"])
        assert query.is_complete() == True

class TestConversation:
    """대화 엔티티 테스트"""
    
    def test_add_turn(self):
        """대화 턴 추가 테스트"""
        conversation = Conversation(session_id="test_session")
        
        turn = ConversationTurn(
            turn_id="turn_001",
            user_input="안녕",
            agent_response="안녕하세요",
            interaction_type=InteractionType.INITIAL_QUERY,
            state_after=ConversationState.PLANNING_IN_PROGRESS
        )
        
        conversation.add_turn(turn)
        
        assert len(conversation.turns) == 1
        assert conversation.current_state == ConversationState.PLANNING_IN_PROGRESS