import random


class WeatherAgent:
    """간단한 날씨 정보 제공 에이전트"""

    async def get_weather(self, location: str, date: str) -> str:
        conditions = ["맑음", "흐림", "비", "눈"]
        return random.choice(conditions)
