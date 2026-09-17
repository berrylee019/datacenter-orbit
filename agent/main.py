import json, os, requests
from datetime import datetime
from dedup import is_same_facility

DATA_PATH = "../data.json" # 레포 루트 기준

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_next_id(data):
    return max([item['id'] for item in data], default=0) + 1

def process_new_findings(new_items, existing_data):
    updated_count = 0
    added_count = 0
    next_id = get_next_id(existing_data)

    for new in new_items:
        found_duplicate = None
        for exist in existing_data:
            if is_same_facility(new, exist):
                found_duplicate = exist
                break
        
        if found_duplicate:
            # 중첩 방지: 기존 내용은 덮어쓰지 않고, status / load / desc 만 업데이트
            print(f"[DUP] 중복 발견 -> 업데이트: {new['name']} == {found_duplicate['name']}")
            # 예: planned -> under_construction 로 변경된 경우만 업데이트
            if found_duplicate.get('status') != new.get('status'):
                found_duplicate['status'] = new['status']
                found_duplicate['desc'] += f" | [{datetime.now().date()} 업데이트] {new['desc']}"
                updated_count += 1
        else:
            # 신규: id 부여하고 추가
            new['id'] = next_id
            next_id += 1
            existing_data.append(new)
            print(f"[NEW] 신규 추가: {new['name']}")
            added_count += 1
            
    return existing_data, added_count, updated_count

# --- 여기가 너가 나한테 시킬 부분 ---
# new_items는 내가 매일 뉴스에서 찾아서 이런 포맷으로 만들어주는 부분
# 예시:
# new_items = [
#   {
#     "name": "GS 동해 북평 메가 AI 데이터센터 캠퍼스",
#     "lat": 37.4902, "lng": 129.1125, "type": "AIDC",
#     "load": "2400 MW", "status": "planned", ...
#   }
# ]

if __name__ == "__main__":
    data = load_data()
    # 실제로는 여기서 Perplexity / 뉴스 API 호출
    new_items_from_news = [] # <- 내가 채워줄 곳
    final_data, added, updated = process_new_findings(new_items_from_news, data)
    
    if added > 0 or updated > 0:
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
