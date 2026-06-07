import os
import json
from openai import OpenAI
from geopy.geocoders import Nominatim

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

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
        
        # 💡 테스트용 인프라 속보 샘플 (원하는 크롤링/인입 로직으로 대체 가능)
        sample_news = """
        [인프라 속보] 아마존 AWS, 아일랜드 더블린에 500억 달러 투입해 250MW 규모의 차세대 AI 데이터센터 추가 착공 발표. 
        엔비디아 블랙웰 인프라 탑재 및 아일랜드 국동 전력 그리드 직접 연계 체결 성공하며 가동률 최고조 예상.
        """
        
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