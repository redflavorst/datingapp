import pytest
from src.application.agents.research.tourist_spot_researcher import TouristSpotResearcher

class TestTouristSpotResearcher:
    """관광지 조사 에이전트 테스트"""
    
    @pytest.fixture
    def researcher(self):
        return TouristSpotResearcher()
    
    @pytest.mark.asyncio
    async def test_search_spots(self, researcher):
        """관광지 검색 테스트"""
        spots = await researcher.search_spots("서울", ["문화재"], max_results=5)
        
        assert isinstance(spots, list)
        assert len(spots) > 0
        assert all(spot.location.name == "경복궁" or "서울" in spot.location.address for spot in spots)