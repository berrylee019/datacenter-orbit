import json
import os
import sys
import argparse
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
    return max([item.get('id', 0) for item in data_list if isinstance(item.get('id'), int)] + [0]) + 1

def process_and_update(new_items):
    if not new_items:
        print("신규 항목 없음")
        return 0, 0
    data_list, wrapper = load_data()
    next_id = get_next_id(data_list)
    added = 0
    updated = 0
    for new in new_items:
        # 필수 필드 체크
        if not new.get('name') or not new.get('lat') or not new.get('lng'):
            print(f"[스킵] 필수 필드 없음: {new}")
            continue
        duplicate = None
        for exist in data_list:
            if is_same_facility(new, exist):
                duplicate = exist
                break
        if duplicate:
            print(f"[중복] {new['name']} -> 기존 ID {duplicate['id']}와 동일")
            if duplicate.get('status') != new.get('status') and new.get('status'):
                duplicate['status'] = new.get('status')
                updated += 1
        else:
            new['id'] = next_id
            next_id += 1
            # 기본값 보정
            new.setdefault('type', 'AIDC')
            new.setdefault('status', 'active')
            data_list.append(new)
            print(f"[신규] ID {new['id']} 추가: {new['name']}")
            added += 1
    if added > 0 or updated > 0:
        save_data(data_list, wrapper)
    else:
        print("변경 사항 없음")
    print(f"\n결과: 신규 {added}개 추가, {updated}개 업데이트")
    return added, updated

def load_from_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = json.load(f)
        if isinstance(content, dict) and 'data' in content:
            return content['data']
        if isinstance(content, list):
            return content
        return [content]

def fetch_auto_candidates():
    """--auto 모드: 환경변수 TODAY_JSON 또는 today.json 파일에서 읽음. 
    GitHub Actions에서 Meta AI가 매일 주는 3개를 주입하는 용도"""
    # 1. 환경변수 우선
    env_json = os.getenv("TODAY_JSON")
    if env_json:
        try:
            data = json.loads(env_json)
            return data if isinstance(data, list) else [data]
        except Exception as e:
            print(f"TODAY_JSON 파싱 실패: {e}")
    # 2. today.json 파일
    today_path = os.path.join(BASE_DIR, "today.json")
    if os.path.exists(today_path):
        print(f"today.json 발견, 로드 중: {today_path}")
        return load_from_file(today_path)
    # 3. 아무것도 없으면 안내
    print("⚠️  --auto 모드: today.json 또는 TODAY_JSON 환경변수가 없습니다.")
    print("매일 오전 9시 Meta AI가 주는 today_3 리스트를 today.json으로 저장 후 실행하세요.")
    return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InfraPulse Data Updater")
    parser.add_argument('--auto', action='store_true', help='today.json 또는 TODAY_JSON 환경변수에서 자동 로드')
    parser.add_argument('--file', type=str, help='특정 JSON 파일에서 로드 (예: --file today.json)')
    args = parser.parse_args()

    if args.file:
        items = load_from_file(args.file)
        process_and_update(items)
    elif args.auto:
        items = fetch_auto_candidates()
        process_and_update(items)
    else:
        # 기존 수동 테스트용 - 비어있음
        test_news = []
        process_and_update(test_news)
