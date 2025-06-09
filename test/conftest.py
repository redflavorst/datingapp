"""테스트 공통 설정"""
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def sample_user_query():
    """샘플 사용자 질의"""
    from src.domain.entities.conversation import UserQuery
    
    return UserQuery(
        text="서울에서 하루 데이트 계획 짜줘. 예산은 10만원이고 문화재랑 카페 좋아해",
        session_id="test_session_001",
        location="서울",
        budget=100000.0,
        preferences={"interests": ["문화재", "카페"]}
    )