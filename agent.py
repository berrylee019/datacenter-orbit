import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from openai import OpenAI
from geopy.geocoders import Nominatim

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

def fetch_realtime_tech_news():
    """Google News RSS 피드에서 글로벌 인프라(AIDC, SMR) 최신 뉴스 타이틀 10개를 긁어옵니다."""
    url = "https://news.google.com/rss/search?q=data+center+power+OR+data+center+construction+OR+SMR+nuclear&hl=en-US&gl=US&ceid=US:en"
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
        
        prompt = f"""
        당신은 글로벌 AI 데이터센터 및 SMR 인프라 전문 분석 에이전트입니다.
        아래 뉴스 기사를 읽고, 제공된 기존 서비스의 스키마 구조형식에 맞게 오직 새로운 인프라 데이터 1개만 JSON 객체로 추출하세요.
        텍스트 설명이나 마크다운 블록 없이 오직 순수한 JSON만 반환해야 합니다.

        [뉴스 기사]
        {sample_news}

        [필수 스키마 형식]
        {{
            "id": {next_id},
            "name": "인프라 이름 (예: 아마존 더블린 AWS AIDC)",
            "type": "AIDC" 또는 "SMR",
            "load": "250 MW",
            "source": "전력 공급원 설명",
            "status": "active",
            "desc": "기사 내용을 요약한 한글 한 문장 설명.",
            "location_string": "Dublin, Ireland"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        new_infra_item = json.loads(response.choices[0].content.strip())
        
        # 중복 검사
        if any(item['name'] == new_infra_item['name'] for item in existing_data):
            print("⚠️ 중복 데이터 발견: 스킵합니다.")
            return
            
        location_str = new_infra_item.get("location_string", "Dublin")
        location = geolocator.geocode(location_str)
        if location:
            new_infra_item["lat"] = round(location.latitude, 4)
            new_infra_item["lng"] = round(location.longitude, 4)
        else:
            new_infra_item["lat"] = 53.3498
            new_infra_item["lng"] = -6.2603
            
        if "location_string" in new_infra_item:
            del new_infra_item["location_string"]
            
        existing_data.append(new_infra_item)
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
        print("✅ 성공: data.json에 새로운 인프라 데이터가 추가되었습니다.")
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    run_infra_agent_pipeline()
