
import json
from math import radians, sin, cos, sqrt, atan2

DATA_PATH = "data.json"

def haversine(lat1,lng1,lat2,lng2):
    R=6371.0
    dlat=radians(lat2-lat1)
    dlng=radians(lng2-lng1)
    a=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlng/2)**2
    return R*2*atan2(sqrt(a),sqrt(1-a))

with open(DATA_PATH,'r',encoding='utf-8') as f:
    raw=json.load(f)
    lst = raw['data'] if isinstance(raw, dict) and 'data' in raw else raw

print(f"Before: {len(lst)}")

# 보호해야 할 진짜 캠퍼스 / 인접 클러스터 ID
PROTECTED_IDS = {5, 55, 149,150,151,152,153,154, 254,255}  # 하남,고양삼송,DFW 6개, SV10/11
PROTECTED_COORDS = [
    (37.5502,127.2031), (37.6534,126.8955), # 하남, 고양
    (32.9567,-96.7169),(32.9592,-96.7144),(32.9548,-96.7188),(32.9548,-96.7202),(32.9581,-96.7161),(32.9575,-96.7175), # DFW
    (37.3875,-121.9635),(37.3892,-121.9618) # SV
]

# 중복 판단: 완전 동일 좌표 + 이름 유사만 중복으로 봄
seen_exact = {}
deduped = []
removed = []

for item in lst:
    lat = item.get('lat')
    lng = item.get('lng')
    iid = item.get('id')
    
    # 보호 ID는 무조건 유지
    if iid in PROTECTED_IDS:
        deduped.append(item)
        seen_exact[(lat,lng)] = item
        continue
    
    key = (round(lat,4) if lat else None, round(lng,4) if lng else None)
    
    # 완전 동일 좌표가 이미 있으면 중복 체크
    if key in seen_exact:
        # DFW/SV/하남처럼 좌표가 미세하게 다른 건 이미 보호됨, 여기까지 온 건 완전 동일 좌표
        # Pecos, Louisiana, Cheyenne, Texas Central, Ohio, Kansas SMR만 삭제 대상
        # 이름이 Pecos/Louisiana/Cheyenne/Texas/Ohio/SMR 키워드 포함이면 삭제
        name = item.get('name','').lower()
        is_hotspot_duplicate = any(k in name for k in ['pecos','louisiana','cheyenne','ohio nuclear','smr facility','texas ai datacenter phase','pecos aidc phase'])
        # 또는 완전 동일 좌표가 핫스팟 좌표이면 삭제
        hotspot_coords = [(30.7857,-102.8065),(30.8704,-92.0071),(31.2639,-98.5456),(41.14,-104.8202),(40.4173,-82.9071),(39.7837,-100.4459)]
        if (lat,lng) in hotspot_coords or is_hotspot_duplicate:
            removed.append(item)
            continue
    
    seen_exact[key]=item
    deduped.append(item)

# ID 재부여 (보호 ID는 기존 ID 유지, 나머지만 재부여? 아니면 전체 재부여 - 여기선 전체 재부여하되 보호목록 로그)
for i, it in enumerate(deduped, start=1):
    # 기존 ID가 보호목록이면 로그만 남기고 새 ID로 변경 - 실제 서비스에선 기존 ID 유지 권장
    it['id']=i

if isinstance(raw, dict) and 'data' in raw:
    raw['data']=deduped
else:
    raw=deduped

with open(DATA_PATH,'w',encoding='utf-8') as f:
    json.dump(raw,f,ensure_ascii=False,indent=2)

print(f"After: {len(deduped)}")
print(f"Removed: {len(removed)}")
print(f"Protected kept: {len([x for x in deduped if x.get('name','').lower().find('dallas')>-1 or x.get('id') in [5,55]])}")
for r in removed[:15]:
    print(f" - ID {r.get('id')} {r.get('name')} @ {r.get('lat')},{r.get('lng')}")
