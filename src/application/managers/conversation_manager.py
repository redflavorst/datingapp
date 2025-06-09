from typing import Optional

from ...domain.entities.conversation import (
    Conversation,
    ConversationTurn,
    ConversationState,
    UserQuery,
)
from .context_store import ContextStore
import logging


class ConversationManager:
    """대화 상태 관리 및 저장소 연동"""

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.store = ContextStore()

    def start_conversation(
        self, session_id: str, user_query: UserQuery
    ) -> Conversation:
        self.logger.debug("start_conversation: session_id=%s", session_id)
        conversation = Conversation(session_id=session_id, initial_query=user_query)
        self.store.save(session_id, conversation)
        return conversation

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        return self.store.load(session_id)

    def update_turn(self, session_id: str, turn: ConversationTurn):
        self.logger.debug("update_turn: session_id=%s turn_id=%s", session_id, turn.turn_id)
        conversation = self.store.load(session_id)
        if conversation:
            conversation.add_turn(turn)
            self.store.update(session_id, conversation)

    def update_state(self, session_id: str, new_state: ConversationState):
        self.logger.debug("update_state: session_id=%s new_state=%s", session_id, new_state)
        conversation = self.store.load(session_id)
        if conversation:
            conversation.current_state = new_state
            self.store.update(session_id, conversation)
