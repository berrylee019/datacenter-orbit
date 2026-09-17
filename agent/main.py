import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from utils.dedup import is_same_facility

DATA_PATH = os.path.join(BASE_DIR, "data.json")

def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict) and "data" in data:
            return data["data"], data
        return data, None

def save_data(data_list, wrapper):
    if wrapper is not None:
        wrapper["data"] = data_list
        final = wrapper
    else:
        final = data_list
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"✅ data.json 저장 완료 (총 {len(data_list)}개)")

def get_next_id(data_list):
    if not data_list:
        return 1
    return max([item.get('id', 0) for item in data_list]) + 1

def process_and_update(new_items):
    data_list, wrapper = load_data()
    next_id = get_next_id(data_list)
    added = 0
    updated = 0
    for new in new_items:
        duplicate = None
        for exist in data_list:
            if is_same_facility(new, exist):
                duplicate = exist
                break
        if duplicate:
            print(f"[중복] {new['name']} -> 기존 ID {duplicate['id']}와 동일")
            if duplicate.get('status') != new.get('status'):
                duplicate['status'] = new.get('status')
                updated += 1
        else:
            new['id'] = next_id
            next_id += 1
            data_list.append(new)
            print(f"[신규] ID {new['id']} 추가: {new['name']}")
            added += 1
    if added > 0 or updated > 0:
        save_data(data_list, wrapper)
    else:
        print("변경 사항 없음")
    return added, updated

if __name__ == "__main__":
    # 네가 수동으로 넣은 바로 그 데이터
    test_news = []
    process_and_update(test_news)