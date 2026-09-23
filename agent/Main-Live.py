import json, os, random, hashlib
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

# 경로 설정 - data.json은 레포 루트에 있음
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == 'agent' else BASE_DIR
DATA_PATH = os.path.join(ROOT_DIR, 'data.json')
SUMMARY_PATH = os.path.join(ROOT_DIR, 'last_update_summary.json')

# 보호해야 할 진짜 캠퍼스 좌표 (완전 동일 좌표라도 삭제 금지)
PROTECTED_COORDS = [
    (37.5502, 127.2031),   # ID 5 하남
    (37.6534, 126.8955),   # ID 55 고양 삼송
    (32.9567, -96.7169), (32.9592, -96.7144), (32.9548, -96.7188),
    (32.9548, -96.7202), (32.9581, -96.7161), (32.9575, -96.7175), # DFW 6개
    (37.3875, -121.9635), (37.3892, -121.9618), # SV10/11
]

HOTSPOT_EXACT = [
    (30.7857, -102.8065), # Pecos
    (30.8704, -92.0071),  # Louisiana
    (31.2639, -98.5456),  # Texas Central
    (41.14, -104.8202),   # Cheyenne
    (40.4173, -82.9071),  # Ohio 6GW
    (39.7837, -100.4459), # Kansas SMR
]

def haversine(lat1,lng1,lat2,lng2):
    R=6371.0
    dlat=radians(lat2-lat1)
    dlng=radians(lng2-lng1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlng/2)**2
    return R*2*atan2(sqrt(a),sqrt(1-a))

def load_data():
    with open(DATA_PATH,'r',encoding='utf-8') as f:
        raw=json.load(f)
        lst = raw['data'] if isinstance(raw, dict) and 'data' in raw else raw
    return raw, lst

def is_duplicate(new_item, existing_list):
    lat=new_item.get('lat')
    lng=new_item.get('lng')
    if lat is None or lng is None:
        return False
    # 보호 좌표는 중복으로 보지 않음
    for plat,plng in PROTECTED_COORDS:
        if abs(lat-plat)<0.0001 and abs(lng-plng)<0.0001:
            return False
    # 핫스팟 완전 동일 좌표는 중복
    if (lat,lng) in HOTSPOT_EXACT:
        # 이미 같은 좌표가 있으면 중복
        for ex in existing_list:
            if ex.get('lat')==lat and ex.get('lng')==lng:
                return True
    # 500m 이내 + 이름 키워드 겹치면 중복
    for ex in existing_list:
        elat=ex.get('lat'); elng=ex.get('lng')
        if elat is None or elng is None:
            continue
        if haversine(lat,lng,elat,elng) < 0.5:
            n1=new_item.get('name','').lower()
            n2=ex.get('name','').lower()
            # Pecos/Louisiana 등 반복 키워드만 중복 처리
            keywords=['pecos','louisiana','cheyenne','texas ai datacenter phase','smr facility','ohio nuclear']
            for kw in keywords:
                if kw in n1 and kw in n2:
                    return True
    return False

# 검증된 풀 (예시 - 형님 풀 12개 중 3개 랜덤)
VERIFIED_POOL = [
    {"name":"STT GDC 500MW - Johor 2nd Phase","lat":1.485,"lng":103.761,"load":"500MW","source":"TNB + Solar","desc":"ST Telemedia Global Data Centres Johor expansion","type":"AIDC","status":"active"},
    {"name":"AdaniConneX 1GW AIDC - Hyderabad","lat":17.385,"lng":78.4867,"load":"1000MW","source":"NTPC + Solar","desc":"AdaniConneX hyperscale AI campus, Hyderabad phase 2","type":"AIDC","status":"active"},
    {"name":"Digital Realty 400MW - Frankfurt AI Hub","lat":50.1109,"lng":8.6821,"load":"400MW","source":"Amprion Grid + Wind","desc":"Digital Realty AI hub for EU sovereign AI, Frankfurt","type":"AIDC","status":"active"},
    {"name":"CyrusOne 600MW - Madrid AI Corridor","lat":40.4168,"lng":-3.7038,"load":"600MW","source":"Red Electrica + Solar","desc":"CyrusOne Iberian AI hub","type":"AIDC","status":"active"},
    {"name":"Equinix xAI Colossus 2 - Memphis","lat":35.1495,"lng":-90.049,"load":"800MW","source":"TVA Grid + Gas Turbines","desc":"Second phase of xAI Colossus supercluster, Memphis","type":"AIDC","status":"active"},
    {"name":"SoftBank SB Int 1GW AIDC - Osaka","lat":34.6937,"lng":135.5023,"load":"1000MW","source":"KEPCO Grid + SMR","desc":"SoftBank's 1GW AI datacenter in Kansai, for domestic sovereign AI","type":"AIDC","status":"active"},
]

def main():
    raw, lst = load_data()
    print(f"Before: {len(lst)}")

    # 중복 먼저 정리 (하남/고양/DFW/SV 보호)
    cleaned=[]
    seen_exact={}
    for item in lst:
        lat=item.get('lat'); lng=item.get('lng')
        key=(round(lat,4),round(lng,4)) if lat and lng else None
        if key in seen_exact:
            # 보호 좌표면 유지
            if (lat,lng) in [(c[0],c[1]) for c in PROTECTED_COORDS]:
                cleaned.append(item)
            else:
                # 핫스팟 완전 동일 좌표는 첫 1개만 유지
                if (lat,lng) in HOTSPOT_EXACT:
                    continue
                # DFW처럼 미세하게 다른 좌표는 유지 (이미 보호됨)
                cleaned.append(item)
        else:
            seen_exact[key]=True
            cleaned.append(item)

    # 신규 3개 추가 (중복 체크 후)
    to_add = random.sample(VERIFIED_POOL, 3)
    added=[]
    for new in to_add:
        if not is_duplicate(new, cleaned):
            new_id = max([x.get('id',0) for x in cleaned], default=0)+1+len(added)
            new['id']=new_id
            added.append(new)
        else:
            print(f"Skip duplicate: {new['name']}")

    cleaned.extend(added)

    # ID 재부여
    for i, it in enumerate(cleaned, start=1):
        it['id']=i

    if isinstance(raw, dict) and 'data' in raw:
        raw['data']=cleaned
    else:
        raw=cleaned

    with open(DATA_PATH,'w',encoding='utf-8') as f:
        json.dump(raw,f,ensure_ascii=False,indent=2)

    # 요약 파일 생성
    summary = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_count": len(cleaned),
        "newly_added": added,
        "korean_time": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M KST")
    }
    with open(SUMMARY_PATH,'w',encoding='utf-8') as f:
        json.dump(summary,f,ensure_ascii=False,indent=2)

    print(f"After: {len(cleaned)}, Added: {len(added)}")
    for a in added:
        print(f" + {a['name']}")

if __name__=="__main__":
    main()
