import random
import logging


class WeatherAgent:
    """간단한 날씨 정보 제공 에이전트"""

    logger = logging.getLogger(__name__)

    async def get_weather(self, location: str, date: str) -> str:
        self.logger.debug("WeatherAgent.get_weather called: location=%s date=%s", location, date)
        conditions = ["맑음", "흐림", "비", "눈"]
        return random.choice(conditions)
