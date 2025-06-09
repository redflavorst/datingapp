class ContextStore:
    """간단한 컨텍스트 저장소 (메모리 기반)"""

    def __init__(self):
        self._store = {}

    def save(self, session_id: str, conversation):
        self._store[session_id] = conversation

    def load(self, session_id: str):
        return self._store.get(session_id)

    def update(self, session_id: str, conversation):
        self._store[session_id] = conversation
