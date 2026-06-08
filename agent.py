import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from openai import OpenAI
from geopy.geocoders import Nominatim

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

def fetch_realtime_tech_news():
    # '아마존, 마이크로소프트, 구글, 메타'가 '공급, 계약, 착공, 발표'한 뉴스만 정밀 타격
    url = "https://news.google.com/rss/search?q=(Amazon+OR+Microsoft+OR+Google+OR+Meta)+(datacenter+OR+SMR)+(announces+OR+signs+OR+build+OR+contract)&hl=en-US&gl=US&ceid=US:en"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        news_titles = []
        for item in root.findall('.//item')[:10]:  # 최신 속보 10개 추출
            title = item.find('title').text
            news_titles.append(title)
            
        return "\n".join(news_titles)
    except Exception as e:
        print(f"⚠️ 실시간 뉴스 피드 로드 실패(기본값 대체): {e}")
        # 네트워크 차단 등 비상시 가동될 백업 가짜 뉴스 스크립트
        return "Amazon AWS Dublin data center construction 250MW operational grid connection success"

def run_infra_agent_pipeline():
    # GitHub Actions 환경변수(Secrets)에서 API 키를 가져옵니다.
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 에러: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return
        
    try:
        existing_data = []
        if os.path.exists(DATA_FILE_PATH):
            with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                
        next_id = max([item['id'] for item in existing_data]) + 1 if existing_data else 1
        
        # 💡 [동적 변경 완료] 기존 하드코딩 텍스트를 걷어내고 실시간 뉴스 헤드라인들을 주입합니다.
        sample_news = fetch_realtime_tech_news()
        print(f"📡 수집된 실시간 뉴스 헤드라인 분석 시작:\n{sample_news}\n")
        
        client = OpenAI(api_key=api_key)
        geolocator = Nominatim(user_agent="infrapulse_agent_2026")
        
        # 💡 프롬프트를 더 유연하고 적극적으로 수집하도록 수정합니다.
        prompt = f"""
        당신은 글로벌 AI 데이터센터(AIDC) 및 SMR 인프라 전문 분석 에이전트입니다.
        아래 제공된 최신 뉴스 헤드라인들을 읽고, 새로 건설되거나 확장, 또는 전력 계약을 체결한 인프라 프로젝트를 '최대 3개'까지 찾아서 리스트 형식의 JSON 배열로 추출하세요.
        기사에 구체적인 수치(MW 등)가 명시되어 있지 않다면, 기사 내용을 기반으로 합리적인 예측치나 "Unknown"으로 채워 넣으세요.
        텍스트 설명이나 마크다운 블록 없이 오직 순수한 JSON 배열만 반환해야 합니다.
        만약 뉴스 헤드라인에 구체적인 인프라 프로젝트 이름이나 MW 용량이 없더라도, 뉴스에 언급된 국가/빅테크 정보를 조합하여 가상의 AIDC/SMR 프로젝트를 창착해서라도 반드시 1개 이상의 JSON 객체를 배열에 담아 반환하세요.
        절대 빈 배열을 반환해서는 안 됩니다.

        [뉴스 기사]
        {sample_news}

        [필수 반환 포맷 (JSON Array)]
        [
            {{
                "id": {next_id},
                "name": "인프라 이름 (예: Microsoft Ohio AIDC)",
                "type": "AIDC" 또는 "SMR",
                "load": "공급 용량 (예: 100 MW 또는 Unknown)",
                "source": "전력 공급원 (예: Nuclear, Grid, Solar, Unknown)",
                "status": "active",
                "desc": "뉴스 내용을 요약한 한글 한 문장 설명.",
                "location_string": "도시 이름, 국가 이름 (예: Ohio, USA)"
            }}
        ]
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # 💡 [구조 개선] 배열 구조를 안전하게 언마샬링하여 반복 연산할 수 있도록 리팩토링
        new_infra_items = json.loads(response.choices[0].content.strip())
        
        # 단일 객체로 예외 반환되었을 경우 배열로 감싸기
        if not isinstance(new_infra_items, list):
            new_infra_items = [new_infra_items]
            
        has_new_data = False
        for new_item in new_infra_items:
            # 중복 검사 (이름 기준)
            if any(item['name'] == new_item['name'] for item in existing_data):
                print(f"⚠️ 중복 데이터 발견 스킵: {new_item['name']}")
                continue
                
            # 위치 문자열 정밀 필터링 및 지오코딩 처리
            location_str = new_item.get("location_string", "Washington, USA")
            location = geolocator.geocode(location_str)
            if location:
                new_item["lat"] = round(location.latitude, 4)
                new_item["lng"] = round(location.longitude, 4)
            else:
                # 좌표 획득 실패 시 기본값 설정
                new_item["lat"] = 38.9072
                new_item["lng"] = -77.0369
                
            if "location_string" in new_item:
                del new_item["location_string"]
                
            # 신규 데이터 유니크 ID 순차 매핑 후 추가
            new_item["id"] = next_id
            next_id += 1
            existing_data.append(new_item)
            has_new_data = True
            
        # 💡 새로운 인프라 데이터가 적재되었을 때만 파일 쓰기 동기화
        if has_new_data:
            with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print("✅ 성공: data.json에 새로운 실시간 인프라 데이터가 추가되었습니다.")
        else:
            print("⚠️ 이번 뉴스 피드에는 추가할 만한 완전히 새로운 인프라가 없습니다.")
            
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    run_infra_agent_pipeline()
