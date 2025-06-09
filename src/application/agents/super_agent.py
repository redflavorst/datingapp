from typing import List, Dict, Any
import logging

from .research.tourist_spot_researcher import TouristSpotResearcher
from .planning.schedule_planner import SchedulePlanner
from ...domain.entities.tourist_spot import TouristSpot

logger = logging.getLogger(__name__)


class SuperAgent:
    """여러 서브 에이전트를 조정하는 간단한 Super Agent"""

    def __init__(self):
        self.researcher = TouristSpotResearcher()
        self.planner = SchedulePlanner()

    async def search_spots(
        self, location: str, interests: List[str], budget: int
    ) -> List[TouristSpot]:
        logger.debug("SuperAgent.search_spots called: location=%s", location)
        return await self.researcher.search_spots(
            location, interests, budget_per_spot=budget
        )

    async def create_plan(
        self, spots: List[TouristSpot], user_prefs: Dict[str, Any], date
    ) -> Any:
        logger.debug("SuperAgent.create_plan called with %d spots", len(spots))
        return await self.planner.create_date_plan(spots, user_prefs, date)
