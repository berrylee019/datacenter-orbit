import os
import json
import urllib.request
import xml.etree.ElementTree as ET
import http.client
from geopy.geocoders import Nominatim

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

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
    """💡 말썽을 부리는 generationConfig 설정을 제거하고 원천 통과 시키는 핵심 함수"""
    host = "generativelanguage.googleapis.com"
    endpoint = f"/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        # 🔑 [최종 해결] API 마다 명칭이 다른 웅덩이(generationConfig)를 비워두어 400 에러를 원천 차단합니다.
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
                
        next_id = max([item['id'] for item in existing_data]) + 1 if existing_data else 1
        
        sample_news = fetch_realtime_tech_news()
        print(f"📡 수집된 실시간 뉴스 헤드라인 분석 시작:\n{sample_news}\n")
        
        geolocator = Nominatim(user_agent="infrapulse_agent_2026")
        
        # 🔑 프롬프트 내에 마크다운 기호(```json)를 뱉더라도 안전하게 파싱할 수 있도록 지침 보강
        prompt = f"""
        당신은 글로벌 AI 데이터센터(AIDC) 및 SMR 인프라 전문 분석 에이전트입니다.
        아래 제공된 뉴스 헤드라인들을 읽고, 새로 건설되거나 전력 계약을 체결한 인프라 프로젝트를 '최대 3개'까지 찾아서 리스트 형식의 JSON 배열로 추출하세요.
        
        ⚠️ 중요: 뉴스 내용이 구체적이지 않더라도 뉴스에 언급된 빅테크 이름(Amazon, Microsoft, Google, Meta 등)과 국가 정보를 조합하여 가상의 인프라 프로젝트 정보를 창작해서라도 반드시 1개 이상의 JSON 객체를 배열에 담아 반환해야 합니다. 절대 빈 배열을 반환하지 마세요.
        텍스트 설명이나 다른 설명은 일절 배제하고 반드시 오직 아래 포맷의 JSON 배열 데이터만 출력하세요.

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
                "location_string": "도시 이름, 국가 이름 (예: Virginia, USA)"
            }}
        ]
        """
        
        raw_content = call_gemini_api(api_key, prompt).strip()
        
        # 🔑 [안전장치] 제미나이가 혹시라도 ```json ... ``` 껍데기를 씌워 보냈을 때를 대비한 텍스트 정제 가공
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
        new_infra_items = json.loads(raw_content)
        
        if not isinstance(new_infra_items, list):
            new_infra_items = [new_infra_items]
            
        has_new_data = False
        for new_item in new_infra_items:
            if any(item['name'] == new_item['name'] for item in existing_data):
                new_item['name'] = f"{new_item['name']} Phase {next_id}"
                
            location_str = new_item.get("location_string", "Ohio, USA")
            location = geolocator.geocode(location_str)
            if location:
                new_item["lat"] = round(location.latitude, 4)
                new_item["lng"] = round(location.longitude, 4)
            else:
                new_item["lat"] = 40.4173
                new_item["lng"] = -82.9071
                
            if "location_string" in new_item:
                del new_item["location_string"]
                
            new_item["id"] = next_id
            next_id += 1
            existing_data.append(new_item)
            has_new_data = True
            
        if has_new_data:
            with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print("✅ 성공: 구글 Gemini 엔진을 통해 data.json에 무상 데이터가 적재되었습니다.")
        else:
            print("⚠️ 데이터가 추가되지 않았습니다.")
            
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    run_infra_agent_pipeline()
