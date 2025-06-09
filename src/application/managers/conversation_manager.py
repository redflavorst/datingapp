from typing import Optional

from ...domain.entities.conversation import (
    Conversation,
    ConversationTurn,
    ConversationState,
    UserQuery,
)
from .context_store import ContextStore


class ConversationManager:
    """대화 상태 관리 및 저장소 연동"""

    def __init__(self):
        self.store = ContextStore()

    def start_conversation(
        self, session_id: str, user_query: UserQuery
    ) -> Conversation:
        conversation = Conversation(session_id=session_id, initial_query=user_query)
        self.store.save(session_id, conversation)
        return conversation

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        return self.store.load(session_id)

    def update_turn(self, session_id: str, turn: ConversationTurn):
        conversation = self.store.load(session_id)
        if conversation:
            conversation.add_turn(turn)
            self.store.update(session_id, conversation)

    def update_state(self, session_id: str, new_state: ConversationState):
        conversation = self.store.load(session_id)
        if conversation:
            conversation.current_state = new_state
            self.store.update(session_id, conversation)
