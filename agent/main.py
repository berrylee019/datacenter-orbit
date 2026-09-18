"""
InfraPulse Live Auto Fetcher - 형님 전자동 버전
- RSS 라이브 스크래핑 + Nominatim 지오코딩 (API KEY 없음)
- 매일 09:00 KST GitHub Actions에서 --auto로 실행
"""
import json
import os
import sys
import re
import random
import time
from datetime import datetime
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    import requests
except ImportError:
    requests = None

from utils.dedup import is_same_facility

DATA_PATH = os.path.join(BASE_DIR, "data.json")
POOL_PATH = os.path.join(BASE_DIR, "agent", "auto_pool.json")
SUMMARY_PATH = os.path.join(BASE_DIR, "last_update_summary.json")

# 무료 RSS - 키 필요 없음
RSS_FEEDS = [
    "https://www.datacenterdynamics.com/en/news/rss.xml",
    "https://www.datacenterknowledge.com/rss.xml",
]

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

def save_summary(added_items):
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
        "count": len(added_items),
        "items": []
    }
    for item in added_items:
        region = "Unknown"
        # 간단 지역 분류
        lat = float(item.get('lat', 0))
        lng = float(item.get('lng', 0))
        if 1 < lat < 7 and 99 < lng < 120:
            region = "🇲🇾🇸🇬 말레이시아/싱가포르 (Johor)"
        elif 8 < lat < 37 and 68 < lng < 97:
            region = "🇮🇳 인도"
        elif 20 < lat < 50 and -130 < lng < -60:
            region = "🇺🇸 미국"
        elif 30 < lat < 46 and 128 < lng < 146:
            region = "🇯🇵 일본"
        elif 36 < lat < 39 and 126 < lng < 130:
            region = "🇰🇷 한국"
        elif 22 < lat < 27 and 113 < lng < 115:
            region = "🇭🇰 홍콩"
        elif lat > 50 or (lng > -10 and lng < 40):
            region = "🇪🇺 유럽"
        elif 12 < lat < 30 and 50 < lng < 80:
            region = "🇦🇪 중동 (UAE/사우디)"
        
        summary["items"].append({
            "name": item.get('name'),
            "region": region,
            "load": item.get('load'),
            "lat": item.get('lat'),
            "lng": item.get('lng'),
            "desc": item.get('desc','')[:120]
        })
    with open(SUMMARY_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary

def get_next_id(data_list):
    return max([i.get('id', 0) for i in data_list if isinstance(i.get('id'), int)] + [0]) + 1

def extract_mw(text):
    m = re.search(r'(\d+(?:\.\d+)?)\s*(GW|MW)', text, re.I)
    if m:
        val = float(m.group(1))
        unit = m.group(2).upper()
        if unit == 'GW':
            val *= 1000
        return f"{int(val)}MW"
    return None

def geocode_nominatim(query):
    """Nominatim 무료 지오코딩 - 키 없음, 형님"""
    if not requests:
        return None
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": "InfraPulseBot/1.0 (berrylee019)"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200 and r.json():
            j = r.json()[0]
            return float(j['lat']), float(j['lon'])
    except Exception as e:
        print(f"Geocode fail {query}: {e}")
    return None

def fetch_rss_candidates():
    candidates = []
    if not requests:
        print("requests 없음 - RSS 스킵")
        return candidates
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Fetching RSS: {feed_url}")
            r = requests.get(feed_url, timeout=15, headers={"User-Agent": "InfraPulseBot/1.0"})
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            # RSS 2.0
            for item in root.findall('.//item')[:20]:
                title = item.findtext('title') or ''
                desc = item.findtext('description') or ''
                text = f"{title} {desc}"
                if 'data center' not in text.lower() and 'datacenter' not in text.lower() and 'AIDC' not in text:
                    continue
                mw = extract_mw(text)
                if not mw:
                    continue
                # 지역 추출 - 간단 키워드
                loc_keywords = [
                    "Johor", "Malaysia", "Singapore", "Hyderabad", "Mumbai", "Chennai", "India",
                    "Virginia", "Texas", "Arizona", "Ohio", "Wisconsin", "Atlanta", "Memphis",
                    "Frankfurt", "Madrid", "London", "Tokyo", "Osaka", "Seoul", "Sydney",
                    "Abu Dhabi", "Dubai", "Riyadh"
                ]
                loc = None
                for kw in loc_keywords:
                    if kw.lower() in text.lower():
                        loc = kw
                        break
                if not loc:
                    continue
                latlng = geocode_nominatim(f"{loc} data center")
                if not latlng:
                    continue
                lat, lng = latlng
                # 약간의 랜덤 지터 - 같은 도시 중복 방지
                lat += random.uniform(-0.15, 0.15)
                lng += random.uniform(-0.15, 0.15)
                
                cand = {
                    "name": title[:90],
                    "lat": round(lat, 4),
                    "lng": round(lng, 4),
                    "load": mw,
                    "source": f"Grid + {feed_url.split('/')[2]}",
                    "desc": desc[:200].replace('\n',' '),
                    "type": "AIDC",
                    "status": "active"
                }
                candidates.append(cand)
                print(f"  -> RSS 후보: {cand['name']} | {mw} | {loc}")
                time.sleep(1.2) # Nominatim 예의 - 1초 대기
        except Exception as e:
            print(f"RSS 에러 {feed_url}: {e}")
            continue
    return candidates

def load_pool():
    if not os.path.exists(POOL_PATH):
        return []
    with open(POOL_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_and_update(new_items):
    if not new_items:
        return [], 0
    data_list, wrapper = load_data()
    next_id = get_next_id(data_list)
    added = []
    for new in new_items:
        dup = False
        for exist in data_list:
            if is_same_facility(new, exist):
                print(f"[중복] {new['name']} -> 기존 ID {exist.get('id')}")
                dup = True
                break
        if not dup:
            new['id'] = next_id
            next_id += 1
            data_list.append(new)
            added.append(new)
            print(f"[신규] ID {new['id']} 추가: {new['name']}")
    if added:
        save_data(data_list, wrapper)
        summary = save_summary(added)
        print(f"\n=== 오늘 요약 ===")
        for it in summary['items']:
            print(f"- {it['region']}: {it['name']} ({it['load']})")
    print(f"결과: 신규 {len(added)}개 추가")
    return added, len(added)

def fetch_auto_candidates(count=3):
    # 1. 라이브 RSS 먼저
    live = fetch_rss_candidates()
    # 2. 풀에서 보충
    pool = load_pool()
    data_list, _ = load_data()
    
    # 풀에서 아직 없는 것 필터
    pool_filtered = []
    for p in pool:
        if not any(is_same_facility(p, e) for e in data_list):
            if not any(is_same_facility(p, l) for l in live):
                pool_filtered.append(p)
    
    # 라이브 + 풀 합치기
    all_candidates = live + pool_filtered
    print(f"전체 후보: 라이브 {len(live)} + 풀 {len(pool_filtered)} = {len(all_candidates)}")
    
    # 중복 제거 후 랜덤 3개
    random.seed(datetime.now().strftime("%Y-%m-%d"))
    if len(all_candidates) >= count:
        return random.sample(all_candidates, count)
    return all_candidates

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true')
    parser.add_argument('--count', type=int, default=3)
    parser.add_argument('--file', type=str)
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            j = json.load(f)
            items = j['data'] if isinstance(j, dict) and 'data' in j else j
            if isinstance(items, dict): items = [items]
        process_and_update(items)
    elif args.auto:
        items = fetch_auto_candidates(count=args.count)
        process_and_update(items)
