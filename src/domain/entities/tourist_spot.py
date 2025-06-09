# src/domain/entities/tourist_spot.py
from dataclasses import dataclass, field
from datetime import time, datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

class SpotCategory(Enum):
    """관광지 카테고리"""
    CULTURAL_SITE = "문화재"
    CAFE = "카페"
    RESTAURANT = "레스토랑"
    MUSEUM = "박물관"
    PARK = "공원"
    SHOPPING = "쇼핑"
    VIEWPOINT = "전망대"
    THEME_PARK = "테마파크"
    BEACH = "해변"
    GALLERY = "갤러리"

class PriceRange(Enum):
    """가격대"""
    FREE = "무료"
    LOW = "1만원 미만"
    MEDIUM = "1-3만원"
    HIGH = "3-5만원"
    PREMIUM = "5만원 이상"

@dataclass
class Location:
    """위치 정보"""
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    
    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError("위도는 -90도에서 90도 사이여야 합니다")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("경도는 -180도에서 180도 사이여야 합니다")
    
    def distance_to(self, other: 'Location') -> float:
        """다른 위치와의 거리 계산 (km, 간단한 계산)"""
        lat_diff = abs(self.latitude - other.latitude)
        lng_diff = abs(self.longitude - other.longitude)
        # 간단한 거리 계산 (정확하지 않음, 나중에 개선)
        return ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # 대략적인 km 변환

@dataclass
class TouristSpot:
    """관광지 엔티티"""
    
    # 기본 정보
    id: str
    name: str
    category: SpotCategory
    location: Location
    
    # 평가 정보
    rating: float
    review_count: int = 0
    
    # 운영 정보
    opening_hours: Dict[str, str] = field(default_factory=dict)  # {"월": "09:00-18:00"}
    estimated_duration: int = 60  # 분 단위
    
    # 비용 정보
    price_range: PriceRange = PriceRange.FREE
    estimated_cost: int = 0  # 원 단위
    
    # 설명
    description: str = ""
    highlights: List[str] = field(default_factory=list)  # 주요 특징
    tips: List[str] = field(default_factory=list)  # 방문 팁
    
    # 접근성
    accessibility_info: str = ""
    parking_available: bool = False
    
    # 연락처
    contact_info: Optional[str] = None
    website: Optional[str] = None
    
    def __post_init__(self):
        if not (0 <= self.rating <= 5):
            raise ValueError("평점은 0점에서 5점 사이여야 합니다")
        if self.estimated_duration <= 0:
            raise ValueError("예상 소요시간은 양수여야 합니다")
        if self.estimated_cost < 0:
            raise ValueError("예상 비용은 음수일 수 없습니다")
    
    def is_highly_rated(self) -> bool:
        """높은 평점인지 확인 (4.0점 이상)"""
        return self.rating >= 4.0
    
    def is_within_budget(self, budget: int) -> bool:
        """예산 내에 있는지 확인"""
        return self.estimated_cost <= budget
    
    def is_open_at(self, check_time: time, weekday: str) -> bool:
        """특정 시간에 열려있는지 확인"""
        if weekday not in self.opening_hours:
            return False
        
        hours = self.opening_hours[weekday]
        if hours == "24시간" or hours == "연중무휴":
            return True
        
        if "-" not in hours:
            return False
        
        try:
            open_str, close_str = hours.split("-")
            open_time = time.fromisoformat(open_str)
            close_time = time.fromisoformat(close_str)
            return open_time <= check_time <= close_time
        except (ValueError, AttributeError):
            return False
    
    def calculate_visit_cost(self, num_people: int) -> int:
        """인원수에 따른 총 비용 계산"""
        return self.estimated_cost * num_people
    
    def get_category_emoji(self) -> str:
        """카테고리별 이모지 반환"""
        emoji_map = {
            SpotCategory.CULTURAL_SITE: "🏛️",
            SpotCategory.CAFE: "☕",
            SpotCategory.RESTAURANT: "🍽️",
            SpotCategory.MUSEUM: "🏛️",
            SpotCategory.PARK: "🌳",
            SpotCategory.SHOPPING: "🛍️",
            SpotCategory.VIEWPOINT: "🌆",
            SpotCategory.THEME_PARK: "🎢",
            SpotCategory.BEACH: "🏖️",
            SpotCategory.GALLERY: "🎨"
        }
        return emoji_map.get(self.category, "📍")

@dataclass
class Transportation:
    """교통 정보"""
    mode: str  # "walking", "public_transport", "taxi", "driving"
    duration: int  # 분
    distance: float  # km
    cost: int = 0  # 원
    instructions: List[str] = field(default_factory=list)
    
    def is_free(self) -> bool:
        """무료 교통수단인지 확인"""
        return self.cost == 0

@dataclass
class DatePlanItem:
    """데이트 계획 항목"""
    
    # 시간 정보
    start_time: time
    end_time: time
    
    # 장소 정보
    spot: TouristSpot
    
    # 교통 정보 (다음 장소로의 이동)
    transportation_to_next: Optional[Transportation] = None
    
    # 추가 정보
    notes: str = ""
    priority: int = 1  # 1=높음, 5=낮음
    
    def get_duration_minutes(self) -> int:
        """소요 시간 계산 (분)"""
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        
        # 다음 날로 넘어가는 경우 처리
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        return int((end_dt - start_dt).total_seconds() / 60)
    
    def get_total_cost(self, num_people: int = 2) -> int:
        """총 비용 계산 (장소 비용 + 교통비)"""
        spot_cost = self.spot.calculate_visit_cost(num_people)
        transport_cost = self.transportation_to_next.cost if self.transportation_to_next else 0
        return spot_cost + transport_cost
    
    def has_time_conflict(self, other: 'DatePlanItem') -> bool:
        """다른 계획 항목과 시간 충돌이 있는지 확인"""
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)

@dataclass
class DatePlan:
    """데이트 계획 전체"""
    
    # 기본 정보
    plan_id: str
    title: str
    date: datetime
    
    # 계획 항목들
    items: List[DatePlanItem] = field(default_factory=list)
    
    # 요약 정보
    total_estimated_cost: int = 0
    total_duration_minutes: int = 0
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # 옵션
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def add_item(self, item: DatePlanItem):
        """계획 항목 추가"""
        self.items.append(item)
        self._recalculate_totals()
        self.last_modified = datetime.now()
    
    def remove_item(self, index: int):
        """계획 항목 제거"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._recalculate_totals()
            self.last_modified = datetime.now()
    
    def _recalculate_totals(self):
        """총 비용과 시간 재계산"""
        self.total_estimated_cost = sum(item.get_total_cost() for item in self.items)
        self.total_duration_minutes = sum(item.get_duration_minutes() for item in self.items)
    
    def get_total_spots(self) -> int:
        """총 방문 장소 수"""
        return len(self.items)
    
    def get_categories(self) -> List[SpotCategory]:
        """포함된 카테고리 목록"""
        return list(set(item.spot.category for item in self.items))
    
    def get_start_time(self) -> Optional[time]:
        """시작 시간"""
        if self.items:
            return min(item.start_time for item in self.items)
        return None
    
    def get_end_time(self) -> Optional[time]:
        """종료 시간"""
        if self.items:
            return max(item.end_time for item in self.items)
        return None
    
    def has_time_conflicts(self) -> List[tuple]:
        """시간 충돌 확인"""
        conflicts = []
        for i, item1 in enumerate(self.items):
            for j, item2 in enumerate(self.items[i+1:], i+1):
                if item1.has_time_conflict(item2):
                    conflicts.append((i, j))
        return conflicts
    
    def is_within_budget(self, budget: int) -> bool:
        """예산 내에 있는지 확인"""
        return self.total_estimated_cost <= budget
    
    def get_timeline_summary(self) -> List[str]:
        """타임라인 요약"""
        timeline = []
        for item in sorted(self.items, key=lambda x: x.start_time):
            emoji = item.spot.get_category_emoji()
            timeline.append(
                f"{item.start_time.strftime('%H:%M')}-{item.end_time.strftime('%H:%M')} "
                f"{emoji} {item.spot.name}"
            )
        return timeline