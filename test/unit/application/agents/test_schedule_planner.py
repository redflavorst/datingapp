import pytest
from datetime import datetime, time
from src.application.agents.planning.schedule_planner import SchedulePlanner
from src.domain.entities.tourist_spot import TouristSpot, Location, SpotCategory, PriceRange

class TestSchedulePlanner:
    """일정 계획 에이전트 테스트"""
    
    @pytest.fixture
    def planner(self):
        return SchedulePlanner()
    
    @pytest.fixture
    def sample_spots(self):
        return [
            TouristSpot(
                id="test_001",
                name="테스트 장소 1",
                category=SpotCategory.CULTURAL_SITE,
                location=Location("테스트1", 37.5796, 126.9770),
                rating=4.5,
                estimated_duration=120,
                estimated_cost=3000
            ),
            TouristSpot(
                id="test_002", 
                name="테스트 장소 2",
                category=SpotCategory.CAFE,
                location=Location("테스트2", 37.5717, 126.9852),
                rating=4.2,
                estimated_duration=90,
                estimated_cost=15000
            )
        ]
    
    @pytest.mark.asyncio
    async def test_create_date_plan(self, planner, sample_spots):
        """데이트 계획 생성 테스트"""
        user_preferences = {
            "start_time": "10:00",
            "budget": 50000,
            "location": "서울",
            "interests": ["문화재", "카페"]
        }
        
        plan = await planner.create_date_plan(
            spots=sample_spots,
            user_preferences=user_preferences,
            date=datetime.now()
        )
        
        assert plan is not None
        assert len(plan.items) > 0
        assert plan.total_estimated_cost <= user_preferences["budget"]