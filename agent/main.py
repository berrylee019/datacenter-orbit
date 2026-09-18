import json
import os
import sys
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from utils.dedup import is_same_facility

DATA_PATH = os.path.join(BASE_DIR, "data.json")
POOL_PATH = os.path.join(BASE_DIR, "agent", "auto_pool.json")

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
    return max([item.get('id', 0) for item in data_list if isinstance(item.get('id'), int)] + [0]) + 1

def process_and_update(new_items):
    if not new_items:
        print("신규 항목 없음")
        return 0, 0
    data_list, wrapper = load_data()
    next_id = get_next_id(data_list)
    added = 0
    for new in new_items:
        if not new.get('name') or not new.get('lat') or not new.get('lng'):
            continue
        duplicate = None
        for exist in data_list:
            if is_same_facility(new, exist):
                duplicate = exist
                break
        if duplicate:
            print(f"[중복] {new['name']} -> ID {duplicate['id']}")
        else:
            new['id'] = next_id
            next_id += 1
            new.setdefault('type', 'AIDC')
            new.setdefault('status', 'active')
            data_list.append(new)
            print(f"[신규] ID {new['id']} 추가: {new['name']}")
            added += 1
    if added > 0:
        save_data(data_list, wrapper)
    print(f"결과: 신규 {added}개 추가")
    return added, 0

def load_pool():
    if not os.path.exists(POOL_PATH):
        print(f"POOL 없음: {POOL_PATH}")
        return []
    with open(POOL_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_auto_candidates(count=3):
    """완전 전자동: auto_pool.json에서 아직 data.json에 없는 3개를 랜덤 추출"""
    pool = load_pool()
    data_list, _ = load_data()
    candidates = []
    for p in pool:
        dup = False
        for exist in data_list:
            if is_same_facility(p, exist):
                dup = True
                break
        if not dup:
            candidates.append(p)
    print(f"POOL {len(pool)}개 중 미등록 {len(candidates)}개")
    if len(candidates) == 0:
        return []
    random.seed(datetime.now().strftime("%Y-%m-%d"))
    selected = random.sample(candidates, min(count, len(candidates)))
    return selected

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help='POOL에서 자동으로 3개 추출 (완전자동)')
    parser.add_argument('--file', type=str, help='파일에서 로드')
    parser.add_argument('--count', type=int, default=3, help='추출 개수')
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            items = content['data'] if isinstance(content, dict) and 'data' in content else content
            if isinstance(items, dict): items = [items]
        process_and_update(items)
    elif args.auto:
        items = fetch_auto_candidates(count=args.count)
        process_and_update(items)
    else:
        print("--auto 또는 --file 필요")
