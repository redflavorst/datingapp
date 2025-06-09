# src/domain/entities/conversation.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class ConversationState(Enum):
    """대화 상태"""
    INITIAL_PLANNING = "initial_planning"
    AWAITING_USER_SELECTION = "awaiting_user_selection"
    PLANNING_IN_PROGRESS = "planning_in_progress"
    PRESENTING_RESULTS = "presenting_results"
    AWAITING_FEEDBACK = "awaiting_feedback"
    HANDLING_QUESTIONS = "handling_questions"
    MODIFYING_PLAN = "modifying_plan"
    PLAN_CONFIRMED = "plan_confirmed"

class InteractionType(Enum):
    """상호작용 타입"""
    INITIAL_QUERY = "initial_query"
    SELECTION_REQUIRED = "selection_required"
    CLARIFICATION_NEEDED = "clarification_needed"
    INFORMATION_REQUEST = "information_request"
    PLAN_MODIFICATION = "plan_modification"
    GENERAL_QUESTION = "general_question"
    CONFIRMATION = "confirmation"

@dataclass
class ConversationTurn:
    """대화의 한 턴을 나타내는 엔티티"""
    
    # 기본 데이터
    turn_id: str
    user_input: str
    agent_response: str
    interaction_type: InteractionType
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 컨텍스트 데이터
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    state_before: Optional[ConversationState] = None
    state_after: Optional[ConversationState] = None
    
    def is_recent(self, minutes: int = 30) -> bool:
        """최근 대화인지 확인"""
        now = datetime.now()
        diff = (now - self.timestamp).total_seconds() / 60
        return diff <= minutes
    
    def is_question(self) -> bool:
        """사용자가 질문을 했는지 확인"""
        question_indicators = ["?", "어떻", "뭐", "언제", "어디", "왜", "어떤", "얼마"]
        return any(indicator in self.user_input for indicator in question_indicators)
    
    def get_user_input_length(self) -> int:
        """사용자 입력 길이"""
        return len(self.user_input)

@dataclass
class UserQuery:
    """사용자 질의를 나타내는 엔티티"""
    
    # 원본 데이터
    text: str
    session_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 파싱된 데이터
    location: Optional[str] = None
    budget: Optional[float] = None
    date: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # 메타데이터
    parsed: bool = False
    confidence_score: float = 0.0
    
    def add_preference(self, key: str, value: Any):
        """선호도 추가"""
        self.preferences[key] = value
    
    def has_location(self) -> bool:
        """위치 정보가 있는지 확인"""
        return self.location is not None and self.location.strip() != ""
    
    def has_budget(self) -> bool:
        """예산 정보가 있는지 확인"""
        return self.budget is not None and self.budget > 0
    
    def get_interests(self) -> List[str]:
        """관심사 목록 반환"""
        return self.preferences.get("interests", [])
    
    def is_complete(self) -> bool:
        """기본 정보가 모두 있는지 확인"""
        return self.has_location() and len(self.get_interests()) > 0

@dataclass
class Conversation:
    """전체 대화 세션을 나타내는 엔티티"""
    
    # 기본 정보
    session_id: str
    user_id: Optional[str] = None
    current_state: ConversationState = ConversationState.INITIAL_PLANNING
    
    # 대화 데이터
    initial_query: Optional[UserQuery] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    
    # 상태 데이터
    awaiting_user_input: bool = False
    expected_input_type: Optional[InteractionType] = None
    
    # 컨텍스트 데이터
    collected_data: Dict[str, Any] = field(default_factory=dict)
    current_plan: Optional[Dict[str, Any]] = None
    
    # 시간 정보
    started_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, turn: ConversationTurn):
        """새로운 대화 턴 추가"""
        turn.state_before = self.current_state
        self.turns.append(turn)
        if turn.state_after:
            self.current_state = turn.state_after
        self.last_updated = datetime.now()
    
    def get_total_turns(self) -> int:
        """총 대화 턴 수"""
        return len(self.turns)
    
    def get_last_user_input(self) -> Optional[str]:
        """마지막 사용자 입력"""
        if self.turns:
            return self.turns[-1].user_input
        return None
    
    def get_last_agent_response(self) -> Optional[str]:
        """마지막 에이전트 응답"""
        if self.turns:
            return self.turns[-1].agent_response
        return None
    
    def is_long_conversation(self) -> bool:
        """긴 대화인지 확인 (10턴 이상)"""
        return len(self.turns) >= 10
    
    def get_conversation_duration_minutes(self) -> int:
        """대화 지속 시간 (분)"""
        if not self.turns:
            return 0
        
        last_turn = self.turns[-1]
        duration = (last_turn.timestamp - self.started_at).total_seconds() / 60
        return int(duration)
    
    def set_awaiting_input(self, input_type: InteractionType):
        """사용자 입력 대기 상태 설정"""
        self.awaiting_user_input = True
        self.expected_input_type = input_type
        self.last_updated = datetime.now()
    
    def clear_awaiting_input(self):
        """사용자 입력 대기 상태 해제"""
        self.awaiting_user_input = False
        self.expected_input_type = None
        self.last_updated = datetime.now()
    
    def update_collected_data(self, key: str, value: Any):
        """수집된 데이터 업데이트"""
        self.collected_data[key] = value
        self.last_updated = datetime.now()
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """사용자 선호도 조합"""
        prefs = {}
        
        # 초기 질의에서 추출된 선호도
        if self.initial_query:
            prefs.update(self.initial_query.preferences)
        
        # 대화 중 수집된 추가 선호도
        prefs.update(self.collected_data.get("preferences", {}))
        
        return prefs