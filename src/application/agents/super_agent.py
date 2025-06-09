from typing import List, Dict, Any

from .research.tourist_spot_researcher import TouristSpotResearcher
from .planning.schedule_planner import SchedulePlanner
from ...domain.entities.tourist_spot import TouristSpot


class SuperAgent:
    """여러 서브 에이전트를 조정하는 간단한 Super Agent"""

    def __init__(self):
        self.researcher = TouristSpotResearcher()
        self.planner = SchedulePlanner()

    async def search_spots(
        self, location: str, interests: List[str], budget: int
    ) -> List[TouristSpot]:
        return await self.researcher.search_spots(
            location, interests, budget_per_spot=budget
        )

    async def create_plan(
        self, spots: List[TouristSpot], user_prefs: Dict[str, Any], date
    ) -> Any:
        return await self.planner.create_date_plan(spots, user_prefs, date)
