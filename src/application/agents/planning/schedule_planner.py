# src/application/agents/planning/schedule_planner.py
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, time, timedelta
import uuid

from ....domain.entities.tourist_spot import TouristSpot, Transportation
from ....domain.entities.tourist_spot import DatePlan, DatePlanItem

class SchedulePlanner:
    """일정 계획 에이전트"""
    
    def __init__(self):
        pass
    
    async def create_date_plan(self,
                              spots: List[TouristSpot],
                              user_preferences: Dict[str, Any],
                              date: datetime) -> DatePlan:
        """데이트 계획 생성"""
        
        print(f"📅 {len(spots)}개 장소로 일정을 계획하고 있습니다...")
        
        # 기본 설정
        start_time = self._parse_start_time(user_preferences.get("start_time", "10:00"))
        budget = user_preferences.get("budget", float('inf'))
        
        # 장소 최적화 (예산, 거리, 시간 고려)
        optimized_spots = await self._optimize_spots(spots, budget, user_preferences)
        
        # 방문 순서 최적화 (거리 기반)
        ordered_spots = self._optimize_visit_order(optimized_spots)
        
        # 시간 배정
        plan_items = self._allocate_time_slots(ordered_spots, start_time)
        
        # 교통 정보 추가
        plan_items = await self._add_transportation_info(plan_items)
        
        # 데이트 계획 객체 생성
        plan = DatePlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            title=f"{user_preferences.get('location', '서울')} 데이트 플랜",
            date=date,
            items=plan_items
        )
        
        plan._recalculate_totals()
        
        print(f"✅ 일정 계획 완성! 총 {len(plan_items)}개 장소, 예상 비용: {plan.total_estimated_cost:,}원")
        
        return plan
    
    async def _optimize_spots(self, 
                             spots: List[TouristSpot], 
                             budget: float,
                             preferences: Dict[str, Any]) -> List[TouristSpot]:
        """장소 최적화 (예산, 선호도 고려)"""
        
        # 예산별 필터링
        affordable_spots = [spot for spot in spots if spot.is_within_budget(budget // 3)]  # 장소당 예산의 1/3
        
        # 선호도 점수 계산
        scored_spots = []
        for spot in affordable_spots:
            score = self._calculate_spot_score(spot, preferences)
            scored_spots.append((spot, score))
        
        # 점수순 정렬 후 상위 선택
        scored_spots.sort(key=lambda x: x[1], reverse=True)
        max_spots = min(5, len(scored_spots))  # 최대 5개 장소
        
        return [spot for spot, score in scored_spots[:max_spots]]
    
    def _calculate_spot_score(self, spot: TouristSpot, preferences: Dict[str, Any]) -> float:
        """장소별 점수 계산"""
        score = 0.0
        
        # 평점 (40%)
        score += (spot.rating / 5.0) * 0.4
        
        # 선호 카테고리 (30%)
        interests = preferences.get("interests", [])
        if spot.category.value in interests:
            score += 0.3
        
        # 비용 효율성 (20%)
        if spot.estimated_cost == 0:  # 무료
            score += 0.2
        elif spot.estimated_cost < 10000:  # 저렴
            score += 0.15
        elif spot.estimated_cost < 30000:  # 보통
            score += 0.1
        
        # 소요시간 적절성 (10%)
        if 60 <= spot.estimated_duration <= 180:  # 1-3시간
            score += 0.1
        
        return score
    
    def _optimize_visit_order(self, spots: List[TouristSpot]) -> List[TouristSpot]:
        """방문 순서 최적화 (간단한 거리 기반)"""
        
        if len(spots) <= 1:
            return spots
        
        # 시작점을 첫 번째 장소로 설정
        ordered = [spots[0]]
        remaining = spots[1:]
        
        # 가장 가까운 다음 장소를 순차적으로 선택
        while remaining:
            current_location = ordered[-1].location
            closest_spot = min(remaining, 
                             key=lambda s: current_location.distance_to(s.location))
            ordered.append(closest_spot)
            remaining.remove(closest_spot)
        
        return ordered
    
    def _allocate_time_slots(self, spots: List[TouristSpot], start_time: time) -> List[DatePlanItem]:
        """시간 슬롯 배정"""
        
        plan_items = []
        current_time = start_time
        
        for i, spot in enumerate(spots):
            # 시작 시간
            item_start = current_time
            
            # 종료 시간 (예상 소요시간 + 여유시간)
            duration_minutes = spot.estimated_duration + 15  # 15분 여유
            end_dt = datetime.combine(datetime.today(), current_time) + timedelta(minutes=duration_minutes)
            item_end = end_dt.time()
            
            # 계획 항목 생성
            plan_item = DatePlanItem(
                start_time=item_start,
                end_time=item_end,
                spot=spot,
                notes=f"{spot.category.value} 방문"
            )
            
            plan_items.append(plan_item)
            
            # 다음 장소를 위한 시간 설정 (이동시간 포함)
            if i < len(spots) - 1:
                travel_time = 30  # 기본 이동시간 30분
                next_start = datetime.combine(datetime.today(), item_end) + timedelta(minutes=travel_time)
                current_time = next_start.time()
        
        return plan_items
    
    async def _add_transportation_info(self, plan_items: List[DatePlanItem]) -> List[DatePlanItem]:
        """교통 정보 추가"""
        
        for i in range(len(plan_items) - 1):
            current_item = plan_items[i]
            next_item = plan_items[i + 1]
            
            # 간단한 교통 정보 생성
            distance = current_item.spot.location.distance_to(next_item.spot.location)
            
            if distance <= 1.0:  # 1km 이내
                transportation = Transportation(
                    mode="walking",
                    duration=15,
                    distance=distance,
                    cost=0,
                    instructions=[f"{current_item.spot.name}에서 도보로 이동"]
                )
            elif distance <= 5.0:  # 5km 이내
                transportation = Transportation(
                    mode="public_transport",
                    duration=25,
                    distance=distance,
                    cost=1500,
                    instructions=[f"지하철 또는 버스 이용"]
                )
            else:  # 5km 초과
                transportation = Transportation(
                    mode="taxi",
                    duration=int(distance * 3),  # 대략 계산
                    distance=distance,
                    cost=int(distance * 1000),  # km당 1000원 가정
                    instructions=[f"택시 이용 (약 {distance:.1f}km)"]
                )
            
            current_item.transportation_to_next = transportation
        
        return plan_items
    
    def _parse_start_time(self, time_str: str) -> time:
        """시작 시간 파싱"""
        try:
            # "10:00", "오전 10시" 등 처리
            if ":" in time_str:
                return time.fromisoformat(time_str)
            elif "시" in time_str:
                hour = int(time_str.replace("시", "").replace("오전", "").replace("오후", "").strip())
                if "오후" in time_str and hour != 12:
                    hour += 12
                return time(hour, 0)
            else:
                return time(10, 0)  # 기본값
        except:
            return time(10, 0)  # 파싱 실패 시 기본값
    
    async def modify_plan(self, 
                         plan: DatePlan, 
                         modification_type: str,
                         parameters: Dict[str, Any]) -> DatePlan:
        """계획 수정"""
        
        if modification_type == "time_adjustment":
            return await self._adjust_timing(plan, parameters)
        elif modification_type == "budget_adjustment":
            return await self._adjust_budget(plan, parameters)
        elif modification_type == "spot_replacement":
            return await self._replace_spots(plan, parameters)
        else:
            return plan
    
    async def _adjust_timing(self, plan: DatePlan, parameters: Dict[str, Any]) -> DatePlan:
        """시간 조정"""
        
        pace = parameters.get("pace", "normal")  # "relaxed", "normal", "tight"
        
        if pace == "relaxed":
            # 각 장소에서 30분씩 더 머물기
            for item in plan.items:
                end_dt = datetime.combine(datetime.today(), item.end_time) + timedelta(minutes=30)
                item.end_time = end_dt.time()
        
        elif pace == "tight":
            # 각 장소에서 20분씩 단축
            for item in plan.items:
                end_dt = datetime.combine(datetime.today(), item.end_time) - timedelta(minutes=20)
                if end_dt.time() > item.start_time:
                    item.end_time = end_dt.time()
        
        # 시간 재조정으로 인한 연쇄 효과 처리
        self._recalculate_schedule_times(plan)
        
        plan._recalculate_totals()
        return plan
    
    async def _adjust_budget(self, plan: DatePlan, parameters: Dict[str, Any]) -> DatePlan:
        """예산 조정"""
        
        target_budget = parameters.get("target_budget", plan.total_estimated_cost)
        direction = parameters.get("direction", "decrease")  # "increase", "decrease"
        
        if direction == "decrease" and plan.total_estimated_cost > target_budget:
            # 비용이 높은 장소부터 제거 또는 대체
            sorted_items = sorted(plan.items, key=lambda x: x.spot.estimated_cost, reverse=True)
            
            while plan.total_estimated_cost > target_budget and len(plan.items) > 1:
                # 가장 비싼 장소 제거
                expensive_item = sorted_items[0]
                if expensive_item in plan.items:
                    plan.items.remove(expensive_item)
                    sorted_items.remove(expensive_item)
                plan._recalculate_totals()
        
        return plan
    
    async def _replace_spots(self, plan: DatePlan, parameters: Dict[str, Any]) -> DatePlan:
        """장소 교체"""
        
        # 간단한 구현 - 실제로는 더 복잡한 로직 필요
        spot_to_replace = parameters.get("spot_id")
        alternative_spots = parameters.get("alternatives", [])
        
        for i, item in enumerate(plan.items):
            if item.spot.id == spot_to_replace and alternative_spots:
                # 첫 번째 대안으로 교체
                new_spot = alternative_spots[0]
                plan.items[i].spot = new_spot
                break
        
        plan._recalculate_totals()
        return plan
    
    def _recalculate_schedule_times(self, plan: DatePlan):
        """일정 시간 재계산"""
        
        if not plan.items:
            return
        
        # 첫 번째 항목은 그대로 유지
        for i in range(1, len(plan.items)):
            prev_item = plan.items[i - 1]
            current_item = plan.items[i]
            
            # 이전 항목 종료 + 이동시간 = 현재 항목 시작
            travel_time = 30  # 기본 30분
            if prev_item.transportation_to_next:
                travel_time = prev_item.transportation_to_next.duration
            
            new_start = datetime.combine(datetime.today(), prev_item.end_time) + timedelta(minutes=travel_time)
            duration = current_item.get_duration_minutes()
            new_end = new_start + timedelta(minutes=duration)
            
            current_item.start_time = new_start.time()
            current_item.end_time = new_end.time()
    
    def generate_plan_summary(self, plan: DatePlan) -> str:
        """계획 요약 생성"""
        
        summary = f"📅 **{plan.title}**\n\n"
        summary += f"📊 **요약 정보**\n"
        summary += f"   • 총 {plan.get_total_spots()}개 장소\n"
        summary += f"   • 예상 비용: {plan.total_estimated_cost:,}원\n"
        summary += f"   • 총 소요시간: {plan.total_duration_minutes // 60}시간 {plan.total_duration_minutes % 60}분\n\n"
        
        summary += f"🗓️ **상세 일정**\n"
        for i, item in enumerate(plan.items, 1):
            emoji = item.spot.get_category_emoji()
            summary += f"{emoji} **{i}. {item.spot.name}**\n"
            summary += f"   ⏰ {item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')}\n"
            summary += f"   💰 {item.spot.estimated_cost:,}원\n"
            summary += f"   📍 {item.spot.description[:50]}...\n"
            
            if item.transportation_to_next:
                transport = item.transportation_to_next
                summary += f"   🚶‍♀️ 다음 장소까지: {transport.mode} ({transport.duration}분, {transport.cost:,}원)\n"
            
            summary += "\n"
        
        return summary