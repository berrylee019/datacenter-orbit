from utils.dedup import is_same_facility

existing = {
    "id": 235,
    "name": "GS 동해 북평 메가 AI 데이터센터 캠퍼스",
    "lat": 37.4902,
    "lng": 129.1125,
    "type": "AIDC"
}

new_same = {
    "name": "GS 동해 북평 AI 데이터센터",
    "lat": 37.4910,
    "lng": 129.1130,
    "type": "AIDC"
}

new_diff = {
    "name": "Microsoft Cheyenne AIDC",
    "lat": 41.14,
    "lng": -104.82,
    "type": "AIDC"
}

result1 = is_same_facility(new_same, existing)
result2 = is_same_facility(new_diff, existing)

print(f"같은 시설 테스트 (True여야 함): {result1}")
print(f"다른 시설 테스트 (False여야 함): {result2}")

# GitHub Actions에서 실패/성공으로 보여주기 위해
assert result1 == True, "중복 감지 실패!"
assert result2 == False, "다른 시설을 중복으로 잘못 판단!"
print("✅ 모든 테스트 통과!")
