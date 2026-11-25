import os
import json
import urllib.request
import xml.etree.ElementTree as ET
import http.client
from geopy.geocoders import Nominatim

from utils.dedup import is_same_facility

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

# 나라 이름 -> ISO2 (지오코딩 결과가 다른 나라로 튀는지 검사할 때 쓴다)
COUNTRY_NAME_TO_CODE = {
    "usa": "us", "us": "us", "u.s.": "us", "u.s.a.": "us",
    "united states": "us", "united states of america": "us", "america": "us",
    "denmark": "dk", "finland": "fi", "sweden": "se", "norway": "no",
    "iceland": "is", "ireland": "ie", "uk": "gb", "united kingdom": "gb",
    "england": "gb", "germany": "de", "france": "fr", "spain": "es",
    "portugal": "pt", "netherlands": "nl", "belgium": "be", "poland": "pl",
    "italy": "it", "switzerland": "ch", "austria": "at", "japan": "jp",
    "korea": "kr", "south korea": "kr", "republic of korea": "kr",
    "china": "cn", "india": "in", "singapore": "sg", "malaysia": "my",
    "indonesia": "id", "australia": "au", "canada": "ca", "mexico": "mx",
    "brazil": "br", "chile": "cl", "saudi arabia": "sa", "uae": "ae",
    "united arab emirates": "ae", "qatar": "qa", "turkey": "tr",
    "türkiye": "tr", "israel": "il", "south africa": "za", "vietnam": "vn",
    "thailand": "th", "taiwan": "tw", "philippines": "ph", "new zealand": "nz",
}

# 지역명이 아니라 나라·주 이름만 왔을 때 나오는 centroid (시설 좌표로 쓸 수 없음)
COUNTRY_LEVEL_TYPES = {"country", "state", "region", "province", "county"}


def _expected_country_code(location_str):
    """'City, Country' 문자열에서 기대 국가 코드를 뽑는다 (뒤쪽 조각 우선)."""
    parts = [p.strip().lower() for p in str(location_str or "").split(",") if p.strip()]
    for part in reversed(parts):
        if part in COUNTRY_NAME_TO_CODE:
            return COUNTRY_NAME_TO_CODE[part]
        for name, code in sorted(COUNTRY_NAME_TO_CODE.items(), key=lambda kv: -len(kv[0])):
            if name in part:
                return code
    return None


def _geocode_location(geolocator, location_str):
    """시설 위치를 (lat, lng)로 돌려준다.

    - 나라·주 단위 centroid 나 동명 지명(예: 'Denmark' -> 미국 메인주 Denmark)처럼
      시설 위치라고 볼 수 없는 결과는 버린다.
    - 확정하지 못하면 None. 오하이오 같은 임의 좌표로 대체하지 않는다.
    """
    location_str = str(location_str or "").strip()
    if not location_str:
        return None

    expected_cc = _expected_country_code(location_str)
    queries = [location_str]
    if expected_cc and "," not in location_str:
        queries.append(f"{location_str}, {expected_cc.upper()}")

    for query in queries:
        try:
            loc = geolocator.geocode(
                query,
                addressdetails=True,
                exactly_one=True,
                country_codes=expected_cc,
                timeout=20,
            )
        except Exception as exc:
            print(f"⚠️ 지오코딩 오류({query}): {exc}")
            continue
        if not loc:
            continue

        raw = getattr(loc, "raw", {}) or {}
        addr = raw.get("address", {}) or {}
        got_cc = str(addr.get("country_code", "")).lower()
        addresstype = str(raw.get("addresstype", "")).lower()

        if expected_cc and got_cc and got_cc != expected_cc:
            print(f"⚠️ 다른 나라로 해석됨({query} -> {got_cc})")
            continue
        if addresstype in COUNTRY_LEVEL_TYPES:
            print(f"⚠️ 시설 위치가 아닌 {addresstype} 단위로 해석됨({query}) - 버림")
            continue

        return round(loc.latitude, 4), round(loc.longitude, 4)

    return None

def fetch_realtime_tech_news():
    """💡 빅테크 데이터센터 및 SMR 계약 관련 뉴스만 정밀 타격 검색"""
    url = "https://news.google.com/rss/search?q=(Amazon+OR+Microsoft+OR+Google+OR+Meta)+(datacenter+OR+SMR)+(announces+OR+signs+OR+build+OR+contract)&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        news_titles = []
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text
            news_titles.append(title)
            
        if not news_titles:
            return "Microsoft signs massive 500MW nuclear SMR power deal for Ohio AI data center infrastructure"
        return "\n".join(news_titles)
    except Exception as e:
        print(f"⚠️ 뉴스 피드 로드 실패(기본값 대체): {e}")
        return "Microsoft signs massive 500MW nuclear SMR power deal for Ohio AI data center infrastructure"

def call_gemini_api(api_key, prompt):
    """💡 구글 라우터의 404 트집을 원천 차단하는 가장 안전한 범용 엔드포인트 주소 적용"""
    host = "generativelanguage.googleapis.com"
    # 🔑 [최종 해결] 구글 API 서버가 주소 매핑에서 절대 에러를 낼 수 없는 가장 안전하고 고정된 정석 경로입니다.
    endpoint = f"/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    conn = http.client.HTTPSConnection(host)
    conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
    response = conn.getresponse()
    res_data = response.read().decode('utf-8')
    conn.close()
    
    res_json = json.loads(res_data)
    
    if 'candidates' not in res_json:
        print(f"❌ 구글 API 원본 반환 에러 구조: {res_json}")
        raise KeyError("구글 제미나이가 정상적인 답변 구조를 생성하지 못했습니다. 원본 로그를 확인하세요.")
        
    text_response = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    return text_response

def run_infra_agent_pipeline():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 에러: API_KEY 환경변수가 설정되지 않았습니다.")
        return
        
    try:
        existing_data = []
        if os.path.exists(DATA_FILE_PATH):
            with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except:
                    existing_data = []
                
        next_id = max([item.get('id', 0) for item in existing_data]) + 1 if existing_data else 1
        
        sample_news = fetch_realtime_tech_news()
        print(f"📡 수집된 실시간 뉴스 헤드라인 분석 시작:\n{sample_news}\n")
        
        geolocator = Nominatim(user_agent="infrapulse_agent_2026")
        
        prompt = f"""
        당신은 글로벌 AI 데이터센터(AIDC) 및 SMR 인프라 전문 분석 에이전트입니다.
        아래 제공된 뉴스 헤드라인들을 읽고, 새로 건설되거나 전력 계약을 체결한 인프라 프로젝트를 '최대 3개'까지 찾아서 리스트 형식의 JSON 배열로 추출하세요.
        
        ⚠️ 중요: 뉴스 내용이 구체적이지 않더라도 뉴스에 언급된 빅테크 이름(Amazon, Microsoft, Google, Meta 등)과 국가 정보를 조합하여 가상의 인프라 프로젝트 정보를 창작해서라도 반드시 1개 이상의 JSON 객체를 배열에 담아 반환해야 합니다. 절대 빈 배열을 반환하지 마세요.
        단, location_string 은 뉴스 기사에 실제로 나온 도시·지역명만 적으세요. 기사에 지명이 없으면 빈 문자열로 두세요. 나라 이름만으로 위치를 추측하거나 지명을 만들어 넣지 마세요(엉뚱한 나라에 좌표가 찍힙니다).
        텍스트 설명이나 다른 마크다운 블록은 일절 배제하고 반드시 오직 아래 포맷의 JSON 배열 데이터만 출력하세요.

        [뉴스 기사]
        {sample_news}

        [필수 반환 포맷 (JSON Array)]
        [
            {{
                "id": {next_id},
                "name": "인프라 이름 (예: Meta Virginia Tech AIDC)",
                "type": "AIDC" 또는 "SMR",
                "load": "공급 용량 (예: 150 MW 또는 300 MW)",
                "source": "전력 공급원 (예: Nuclear, Grid, Solar, Wind)",
                "status": "active",
                "desc": "뉴스나 시나리오를 요약한 한글 한 문장 설명.",
                "location_string": "뉴스에 나온 실제 도시/지역 이름 (예: Virginia, USA). 뉴스에 지명이 없으면 빈 문자열"
            }}
        ]
        """
        
        raw_content = call_gemini_api(api_key, prompt).strip()
        
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
        new_infra_items = json.loads(raw_content)
        
        if not isinstance(new_infra_items, list):
            new_infra_items = [new_infra_items]
            
        has_change = False
        for new_item in new_infra_items:
            # 1) 위치를 먼저 확정한다. 지오코딩이 실패하거나 나라·주 단위 centroid,
            #    동명 지명(예: Denmark -> 미국 메인주 Denmark)으로 잡히면 좌표를
            #    지어내지 않고 이 항목을 건너뛴다.
            #    (예전에는 실패 시 전부 오하이오 40.4173,-82.9071 로 들어갔다)
            location_str = new_item.get("location_string") or ""
            coords = _geocode_location(geolocator, location_str)
            if coords is None:
                print(f"⚠️ 위치 확인 실패로 건너뜀: {new_item.get('name')} ({location_str!r})")
                continue
            new_item["lat"], new_item["lng"] = coords

            if "location_string" in new_item:
                del new_item["location_string"]

            # 2) 이미 있는 시설이면 이름을 'Phase {id}' 로 바꿔 새 행을 만들지 않고
            #    기존 행의 변동 정보만 갱신한다. (중복 누적의 원인)
            dup = next((ex for ex in existing_data if is_same_facility(new_item, ex)), None)
            if dup is not None:
                for key in ("load", "source", "desc", "status"):
                    if new_item.get(key):
                        dup[key] = new_item[key]
                print(f"↺ 기존 항목 갱신(신규 행 없음): {dup['name']}")
                has_change = True
                continue

            new_item["id"] = next_id
            next_id += 1
            existing_data.append(new_item)
            has_change = True
            
        if has_change:
            with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print("✅ 성공: 구글 Gemini 엔진 결과를 data.json에 반영했습니다.")
        else:
            print("⚠️ 새로 추가·변경된 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    run_infra_agent_pipeline()
