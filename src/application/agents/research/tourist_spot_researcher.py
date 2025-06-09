# src/application/agents/research/tourist_spot_researcher.py
from typing import List, Dict, Optional, Any
import random
from ....domain.entities.tourist_spot import TouristSpot, Location, SpotCategory, PriceRange

class TouristSpotResearcher:
    """관광지 조사 에이전트"""
    
    def __init__(self):
        # Mock 데이터로 시작 (나중에 실제 API로 교체)
        self.sample_spots = self._load_sample_spots()
    
    async def search_spots(self, 
                          location: str,
                          categories: List[str] = None,
                          budget_per_spot: Optional[int] = None,
                          max_results: int = 10) -> List[TouristSpot]:
        """관광지 검색"""
        
        print(f"🔍 {location}에서 관광지를 검색하고 있습니다...")
        
        # 위치 필터링
        filtered_spots = self._filter_by_location(self.sample_spots, location)
        
        # 카테고리 필터링
        if categories:
            filtered_spots = self._filter_by_categories(filtered_spots, categories)
        
        # 예산 필터링
        if budget_per_spot:
            filtered_spots = self._filter_by_budget(filtered_spots, budget_per_spot)
        
        # 평점순 정렬
        filtered_spots = sorted(filtered_spots, key=lambda x: x.rating, reverse=True)
        
        # 결과 제한
        result = filtered_spots[:max_results]
        
        print(f"✅ {len(result)}개의 관광지를 찾았습니다!")
        
        return result
    
    async def get_detailed_info(self, spot_id: str) -> Optional[Dict[str, Any]]:
        """관광지 상세 정보 조회"""
        
        spot = self._find_spot_by_id(spot_id)
        if not spot:
            return None
        
        # 실제로는 외부 API에서 상세 정보를 가져올 것
        detailed_info = {
            "basic_info": {
                "name": spot.name,
                "category": spot.category.value,
                "rating": spot.rating,
                "review_count": spot.review_count,
                "description": spot.description
            },
            "visit_info": {
                "opening_hours": spot.opening_hours,
                "estimated_duration": spot.estimated_duration,
                "estimated_cost": spot.estimated_cost,
                "price_range": spot.price_range.value
            },
            "location_info": {
                "address": spot.location.address,
                "parking_available": spot.parking_available,
                "accessibility": spot.accessibility_info
            },
            "highlights": spot.highlights,
            "tips": spot.tips,
            "contact": {
                "phone": spot.contact_info,
                "website": spot.website
            },
            "real_time_info": await self._get_real_time_info(spot_id)
        }
        
        return detailed_info
    
    async def _get_real_time_info(self, spot_id: str) -> Dict[str, Any]:
        """실시간 정보 수집 (혼잡도, 대기시간 등)"""
        
        # Mock 실시간 정보
        crowd_levels = ["여유", "보통", "혼잡", "매우 혼잡"]
        weather_conditions = ["맑음", "흐림", "비", "눈"]
        
        return {
            "crowd_level": random.choice(crowd_levels),
            "wait_time": random.randint(0, 30),  # 분
            "weather": random.choice(weather_conditions),
            "special_events": [],
            "last_updated": "방금 전"
        }
    
    def _load_sample_spots(self) -> List[TouristSpot]:
        """샘플 관광지 데이터 로드"""
        
        return [
            # 서울 문화재
            TouristSpot(
                id="seoul_001",
                name="경복궁",
                category=SpotCategory.CULTURAL_SITE,
                location=Location("경복궁", 37.5796, 126.9770, "서울특별시 종로구 사직로 161"),
                rating=4.5,
                review_count=15420,
                opening_hours={
                    "월": "09:00-18:00", "화": "09:00-18:00", "수": "09:00-18:00",
                    "목": "09:00-18:00", "금": "09:00-18:00", "토": "09:00-18:00", "일": "09:00-18:00"
                },
                estimated_duration=120,
                price_range=PriceRange.LOW,
                estimated_cost=3000,
                description="조선왕조의 정궁으로 웅장한 건축미와 역사적 가치를 지닌 곳",
                highlights=["근정전", "경회루", "수문장 교대식"],
                tips=["수문장 교대식은 10:00, 14:00, 15:00에 진행", "한복 착용 시 입장료 무료"],
                accessibility_info="휠체어 접근 가능",
                parking_available=True,
                contact_info="02-3700-3900"
            ),
            
            TouristSpot(
                id="seoul_002",
                name="창덕궁",
                category=SpotCategory.CULTURAL_SITE,
                location=Location("창덕궁", 37.5794, 126.9910, "서울특별시 종로구 율곡로 99"),
                rating=4.6,
                review_count=8750,
                opening_hours={
                    "월": "휴궁", "화": "09:00-18:00", "수": "09:00-18:00",
                    "목": "09:00-18:00", "금": "09:00-18:00", "토": "09:00-18:00", "일": "09:00-18:00"
                },
                estimated_duration=150,
                price_range=PriceRange.LOW,
                estimated_cost=3000,
                description="유네스코 세계문화유산으로 지정된 조선왕조의 이궁",
                highlights=["인정전", "후원", "비원"],
                tips=["후원 관람은 별도 예약 필요", "월요일 휴궁"],
                accessibility_info="일부 구간 계단 있음",
                parking_available=True,
                contact_info="02-3668-2300"
            ),
            
            # 서울 카페
            TouristSpot(
                id="seoul_003",
                name="인사동 전통찻집 거리",
                category=SpotCategory.CAFE,
                location=Location("인사동", 37.5717, 126.9852, "서울특별시 종로구 인사동길"),
                rating=4.2,
                review_count=3240,
                opening_hours={
                    "월": "10:00-22:00", "화": "10:00-22:00", "수": "10:00-22:00",
                    "목": "10:00-22:00", "금": "10:00-22:00", "토": "10:00-22:00", "일": "10:00-22:00"
                },
                estimated_duration=90,
                price_range=PriceRange.MEDIUM,
                estimated_cost=15000,
                description="전통과 현대가 어우러진 특색 있는 찻집들이 모여있는 거리",
                highlights=["전통차", "한과", "전통 공예품"],
                tips=["주말에는 혼잡하니 평일 방문 추천", "전통차 체험 가능"],
                accessibility_info="일반적인 접근성",
                parking_available=False,
                contact_info="02-734-0222"
            ),
            
            TouristSpot(
                id="seoul_004",
                name="홍대 카페거리",
                category=SpotCategory.CAFE,
                location=Location("홍대", 37.5563, 126.9236, "서울특별시 마포구 홍익로"),
                rating=4.0,
                review_count=5670,
                opening_hours={
                    "월": "08:00-24:00", "화": "08:00-24:00", "수": "08:00-24:00",
                    "목": "08:00-24:00", "금": "08:00-02:00", "토": "08:00-02:00", "일": "08:00-24:00"
                },
                estimated_duration=120,
                price_range=PriceRange.MEDIUM,
                estimated_cost=12000,
                description="젊은 감성과 트렌디한 카페들이 가득한 홍대의 명소",
                highlights=["독특한 카페들", "거리 공연", "젊은 분위기"],
                tips=["야간에 더욱 활기차", "주차 어려움"],
                accessibility_info="일반적인 접근성",
                parking_available=False,
                contact_info="02-325-8600"
            ),
            
            # 서울 박물관
            TouristSpot(
                id="seoul_005",
                name="국립중앙박물관",
                category=SpotCategory.MUSEUM,
                location=Location("국립중앙박물관", 37.5240, 126.9803, "서울특별시 용산구 서빙고로 137"),
                rating=4.4,
                review_count=12350,
                opening_hours={
                    "월": "휴관", "화": "10:00-18:00", "수": "10:00-21:00",
                    "목": "10:00-18:00", "금": "10:00-18:00", "토": "10:00-18:00", "일": "10:00-18:00"
                },
                estimated_duration=180,
                price_range=PriceRange.FREE,
                estimated_cost=0,
                description="한국의 역사와 문화를 한눈에 볼 수 있는 대한민국 대표 박물관",
                highlights=["고구려 고분벽화", "백제금동대향로", "반가사유상"],
                tips=["무료 관람", "수요일은 21시까지 야간개장", "월요일 휴관"],
                accessibility_info="휠체어 완전 접근 가능",
                parking_available=True,
                contact_info="02-2077-9000"
            ),
            
            # 부산 관광지
            TouristSpot(
                id="busan_001",
                name="해동용궁사",
                category=SpotCategory.CULTURAL_SITE,
                location=Location("해동용궁사", 35.1882, 129.2233, "부산광역시 기장군 기장읍 용궁길 86"),
                rating=4.3,
                review_count=8920,
                opening_hours={
                    "월": "04:00-20:00", "화": "04:00-20:00", "수": "04:00-20:00",
                    "목": "04:00-20:00", "금": "04:00-20:00", "토": "04:00-20:00", "일": "04:00-20:00"
                },
                estimated_duration=90,
                price_range=PriceRange.FREE,
                estimated_cost=0,
                description="바다 위에 세워진 아름다운 사찰로 일출 명소",
                highlights=["바다 위 사찰", "일출 명소", "108계단"],
                tips=["일출 시간 방문 추천", "새벽 4시부터 개방"],
                accessibility_info="계단이 많아 접근 어려움",
                parking_available=True,
                contact_info="051-722-7744"
            ),
            
            TouristSpot(
                id="busan_002", 
                name="감천문화마을",
                category=SpotCategory.CULTURAL_SITE,
                location=Location("감천문화마을", 35.0975, 129.0106, "부산광역시 사하구 감내2로 203"),
                rating=4.1,
                review_count=15600,
                opening_hours={
                    "월": "09:00-18:00", "화": "09:00-18:00", "수": "09:00-18:00",
                    "목": "09:00-18:00", "금": "09:00-18:00", "토": "09:00-18:00", "일": "09:00-18:00"
                },
                estimated_duration=120,
                price_range=PriceRange.LOW,
                estimated_cost=5000,
                description="알록달록한 집들이 계단식으로 배치된 부산의 마추픽추",
                highlights=["계단식 마을", "포토존", "예술작품"],
                tips=["편한 신발 착용 권장", "사진 촬영 명소"],
                accessibility_info="경사가 심해 접근 어려움",
                parking_available=True,
                contact_info="051-204-1444"
            )
        ]
    
    def _filter_by_location(self, spots: List[TouristSpot], location: str) -> List[TouristSpot]:
        """위치별 필터링"""
        filtered = []
        
        for spot in spots:
            # 간단한 문자열 매칭 (나중에 더 정교하게 개선)
            if (location in spot.location.name or 
                location in spot.location.address or
                location in spot.id):
                filtered.append(spot)
        
        return filtered
    
    def _filter_by_categories(self, spots: List[TouristSpot], categories: List[str]) -> List[TouristSpot]:
        """카테고리별 필터링"""
        category_map = {
            "문화재": SpotCategory.CULTURAL_SITE,
            "카페": SpotCategory.CAFE,
            "레스토랑": SpotCategory.RESTAURANT,
            "박물관": SpotCategory.MUSEUM,
            "공원": SpotCategory.PARK,
            "쇼핑": SpotCategory.SHOPPING,
            "전망대": SpotCategory.VIEWPOINT
        }
        
        target_categories = []
        for cat in categories:
            if cat in category_map:
                target_categories.append(category_map[cat])
        
        if not target_categories:
            return spots
        
        return [spot for spot in spots if spot.category in target_categories]
    
    def _filter_by_budget(self, spots: List[TouristSpot], budget_per_spot: int) -> List[TouristSpot]:
        """예산별 필터링"""
        return [spot for spot in spots if spot.is_within_budget(budget_per_spot)]
    
    def _find_spot_by_id(self, spot_id: str) -> Optional[TouristSpot]:
        """ID로 관광지 찾기"""
        for spot in self.sample_spots:
            if spot.id == spot_id:
                return spot
        return None
    
    async def get_recommendations_for_preferences(self, 
                                                location: str,
                                                user_preferences: Dict[str, Any]) -> List[TouristSpot]:
        """사용자 선호도 기반 추천"""
        
        # 기본 검색
        spots = await self.search_spots(
            location=location,
            categories=user_preferences.get("interests", []),
            budget_per_spot=user_preferences.get("budget_per_spot"),
            max_results=20
        )
        
        # 선호도 점수 계산
        scored_spots = []
        for spot in spots:
            score = self._calculate_preference_score(spot, user_preferences)
            scored_spots.append((spot, score))
        
        # 점수순 정렬
        scored_spots.sort(key=lambda x: x[1], reverse=True)
        
        return [spot for spot, score in scored_spots[:10]]
    
    def _calculate_preference_score(self, spot: TouristSpot, preferences: Dict[str, Any]) -> float:
        """선호도 점수 계산"""
        score = 0.0
        
        # 기본 평점 (40% 가중치)
        score += spot.rating * 0.4
        
        # 카테고리 선호도 (30% 가중치)
        interests = preferences.get("interests", [])
        if spot.category.value in interests:
            score += 1.5 * 0.3
        
        # 예산 적합성 (20% 가중치)
        budget = preferences.get("budget_per_spot", float('inf'))
        if spot.is_within_budget(budget):
            if spot.estimated_cost == 0:  # 무료인 경우 보너스
                score += 1.0 * 0.2
            else:
                # 예산 대비 비용 비율로 점수 계산
                cost_ratio = spot.estimated_cost / budget
                score += (1.0 - cost_ratio) * 0.2
        
        # 소요시간 적절성 (10% 가중치)
        preferred_duration = preferences.get("preferred_duration", 120)  # 기본 2시간
        time_diff = abs(spot.estimated_duration - preferred_duration) / preferred_duration
        score += max(0, (1.0 - time_diff)) * 0.1
        
        return score