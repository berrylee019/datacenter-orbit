import math
import re

def _normalize(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[^a-z0-9가-힣]', '', name)
    return name

def _haversine_km(lat1, lon1, lat2, lon2):
    try:
        R = 6371.0
        dlat = math.radians(float(lat2) - float(lat1))
        dlon = math.radians(float(lon2) - float(lon1))
        a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except:
        return 9999

def is_same_facility(new, existing):
    """
    엄격한 중복 판정 - 폰에서 오작동 방지용으로 대폭 강화
    1. 이름이 거의 동일하면 중복
    2. 거리가 500m 이내 AND 이름 유사도 높을 때만 중복
    3. 그 외는 무조건 신규로 처리 (중복보다 신규 누락 방지가 더 중요)
    """
    if not new or not existing:
        return False
    
    new_name = _normalize(new.get('name',''))
    exist_name = _normalize(existing.get('name',''))
    
    # 이름이 비어있으면 중복 아님
    if not new_name or not exist_name:
        return False

    # 1. 이름 완전 동일 -> 중복
    if new_name == exist_name:
        return True

    # 2. 거리 계산
    try:
        lat1 = float(new.get('lat'))
        lng1 = float(new.get('lng'))
        lat2 = float(existing.get('lat'))
        lng2 = float(existing.get('lng'))
    except:
        # 좌표 없으면 이름으로만 판단, 완전 동일할 때만
        return new_name == exist_name

    dist_km = _haversine_km(lat1, lng1, lat2, lng2)

    # 3. 500m 이내 초근접 + 이름 유사
    if dist_km < 0.5:
        # 한 이름이 다른 이름을 포함하거나, 유사도 높음
        if new_name in exist_name or exist_name in new_name:
            return True
        # 80% 이상 문자 겹침
        # 간단 유사도: 공통 문자 수 / 평균 길이
        common = len(set(new_name) & set(exist_name))
        avg_len = (len(new_name) + len(exist_name)) / 2
        if avg_len > 0 and common / avg_len > 0.8:
            return True
        # 그래도 애매하면 중복 아님으로 처리 (신규로 추가)
        return False
    
    # 4. 500m 이상 떨어져 있으면 절대 중복 아님 (기존 로직이 50km까지 중복으로 본게 문제였음)
    return False
