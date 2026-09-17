import math
from difflib import SequenceMatcher

def haversine(lat1, lon1, lat2, lon2):
    """두 좌표 사이 거리 km 계산"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def normalize_name(name: str) -> str:
    # "GS 동해 북평 메가 AI 데이터센터 캠퍼스" -> "동해북평메가" 같은 핵심만 남기기 위한 전처리
    return name.lower().replace(" ", "").replace("메가", "").replace("ai데이터센터", "").replace("캠퍼스", "")

def is_same_facility(new_item: dict, existing_item: dict, dist_threshold_km=3.0, name_threshold=0.75) -> bool:
    """
    중복 판단 로직. True면 같은 시설.
    """
    try:
        lat1, lng1 = float(new_item['lat']), float(new_item['lng'])
        lat2, lng2 = float(existing_item['lat']), float(existing_item['lng'])
    except (KeyError, ValueError, TypeError):
        # 좌표가 없으면 이름으로만 판단
        lat1 = lng1 = lat2 = lng2 = None

    # 1순위: 좌표 거리 3km 이내면 무조건 같은 부지로 간주
    # 예: 동해 북평산단 내에서 이름이 달라도 같은 곳
    if lat1 is not None and lat2 is not None:
        dist = haversine(lat1, lng1, lat2, lng2)
        if dist < dist_threshold_km:
            return True

    # 2순위: 이름 유사도 + 타입
    # "GS 동해 북평" vs "GS 동해 북평 메가 AI" -> 유사도 높음
    name1 = normalize_name(new_item.get('name', ''))
    name2 = normalize_name(existing_item.get('name', ''))
    
    if not name1 or not name2:
        return False

    similarity = SequenceMatcher(None, name1, name2).ratio()
    
    # 이름이 75% 이상 비슷하고 타입(AIDC, SMR 등)이 같으면 중복
    if similarity >= name_threshold and new_item.get('type') == existing_item.get('type'):
        return True
        
    return False
