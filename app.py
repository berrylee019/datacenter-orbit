import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json
import pandas as pd
from datetime import datetime
from openai import OpenAI
from geopy.geocoders import Nominatim

# 1. Streamlit 페이지 기본 설정 (최상단 고정 및 여백 최소화)
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🚨 [구글 시트 라이브러리 연동 안전 검사]
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("❌ 'st-gsheets-connection' 라이브러리가 누락되었습니다.")
    st.stop()

# 🤖 [글로벌 인프라 자동 업데이트 에이전트 엔진 구역]
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")

def run_infra_agent_pipeline():
    """백그라운드에서 최신 인프라 뉴스를 분석하여 data.json을 자동으로 갱신하는 에이전트"""
    if "OPENAI_API_KEY" not in st.secrets:
        return "NO_API_KEY"
        
    try:
        existing_data = []
        if os.path.exists(DATA_FILE_PATH):
            with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                
        next_id = max([item['id'] for item in existing_data]) + 1 if existing_data else 1
        
        sample_news = """
        [인프라 속보] 아마존 AWS, 아일랜드 더블린에 500억 달러 투입해 250MW 규모의 차세대 AI 데이터센터 추가 착공 발표. 
        엔비디아 블랙웰 인프라 탑재 및 아일랜드 국동 전력 그리드 직접 연계 체결 성공하며 가동률 최고조 예상.
        """
        
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
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
            "lat": 0.0,
            "lng": 0.0,
            "location_string": "기사에 언급된 구체적인 도시/국가 명칭 (예: Dublin, Ireland)",
            "type": "AIDC" 또는 "SMR",
            "load": "000 MW (기사에 언급된 전력량, 없으면 대기 또는 추정치)",
            "source": "전력 공급원 설명",
            "status": "active" 또는 "saturated" 또는 "smr",
            "carbon": "high" 또는 "mid" 또는 "low" 또는 "zero",
            "desc": "기사 내용을 요약한 한글 한 문장 설명.",
            "architecture": "사용된 GPU 칩셋이나 원전 아키텍처 명칭"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        new_infra_item = json.loads(response.choices[0].content.strip())
        
        if any(item['name'] == new_infra_item['name'] for item in existing_data):
            return "DUPLICATE"
            
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
            
        return "SUCCESS"
    except Exception as e:
        return f"AGENT_EXCEPTION_{str(e)}"

# 2. GitHub Issue 생성 시스템
def create_github_issue(email, dc_name="미지정"):
    if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
        return "SECRETS_ERROR"
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": f"🚨 [InfraPulse] {email} 구독 신청",
        "body": f"### 📬 새로운 프로 버전 대기 신청\n- **이메일:** `{email}`\n- **관제 타깃:** {dc_name}\n",
        "labels": ["lead", "pro-waitlist"]
    }
    try:
        requests.post(url, json=data, headers=headers)
        return "SUCCESS"
    except:
        return "EXCEPTION"

# 📊 [구글 시트 첫 번째 탭 자동 적재 엔진]
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        return "GSHEETS_SECRETS_ERROR"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(ttl=0)
        
        new_data = pd.DataFrame({
            "Email": [email],
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Name": ["InfraPulse_User"],
            "Note": [f"인프라관제: {dc_name}"]
        })
        
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        conn.update(data=updated_df)
        return "SUCCESS"
    except Exception as e:
        return f"GSHEETS_EXCEPTION_{str(e)}"

# 3. URL 파라미터 / 순정 폼 제출 통합 처리 분기점
query_params = st.query_params
lead_email = query_params.get("email")
lead_target = query_params.get("target", "글로벌 메인 대기")

# 파이썬 순정 버튼 혹은 자바스크립트 리다이렉트로 신호가 인입되었을 때
if query_params.get("submit_lead") == "true" and lead_email:
    st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
    with st.spinner("리드를 즉시 동기화 중..."):
        sheet_status = append_to_gsheets_connection(lead_email, lead_target)
        create_github_issue(lead_email, lead_target)
        
        if sheet_status == "SUCCESS":
            st.balloons()
            st.success(f"🎉 성공: {lead_email} 등록 완료되었습니다!")
            
            def reset_to_main():
                st.query_params.clear()
                st.rerun()
            st.button("🌐 글로벌 관제탑 지도로 돌아가기", on_click=reset_to_main, type="primary")
            st.stop()
        else:
            st.error(f"❌ 구글 시트 연동 실패 에러코드: {sheet_status}")
            if st.button("메인화면 복귀"):
                st.query_params.clear()
                st.rerun()
            st.stop()

# 4. 상단 타이틀 레이아웃
st.markdown("<h3 style='margin:0; padding:0;'>🌐 InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑</h3>", unsafe_allow_html=True)

# 💡 [대격변] 숨겨진 녹색 버튼을 상단에 '순정 가로 바(Bar)' 형태로 전면 전진 배치!
st.markdown("<div style='background-color:#1e293b; padding:10px; border-radius:8px; margin-bottom:10px;'>", unsafe_allow_html=True)
form_col1, form_col2, form_col3 = st.columns([2, 2, 1])

with form_col1:
    input_email = st.text_input("📧 Pro 버전 얼리버드 대기열 등록 (월 49,000원 ➡️ 24,000원 할인)", placeholder="이메일 주소를 입력하세요", label_visibility="collapsed")
with form_col2:
    input_target = st.selectbox("우선 관제 희망 타깃", [
        "글로벌 전체 관제", "xAI 멤피스 콜로서스 1", "네이버 하이퍼스케일 각 세종", 
        "MS-블랙록 버지니아 허브", "미시간 팰리세이드 SMR", "하남 데이터센터", "구글 세인트 토마스 AIDC", "메타 인디애나 AI 클러스터", "MS-오픈AI 스타게이트 (비밀기지 예정지)", "해남 솔라시도 데이터센터 파크", "카카오 데이터센터 안산 (AIDC 고도화 라인)", "테라파워 와이오밍 케머러 SMR 기지", "네이버 하이퍼스케일 각 춘천", "기타 지역"
    ], label_visibility="collapsed")
with form_col3:
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #22c55e !important;
            color: white !important;
            border: none !important;
            width: 100%;
        }
        </style>""", unsafe_allow_html=True)
    submit_clicked = st.button("얼리버드 사전 예약 🚀")

# 5. 🛠️ 버튼 클릭 처리 부분 보정 (st.rerun / no-op 완벽 우회 구역)
if submit_clicked:
    if input_email and "@" in input_email:
        # 세션 스테이트에 리드 신호를 기록하여 콜백 함수 내부 호출 구조를 우회합니다.
        st.session_state["submit_lead_triggered"] = True
        st.session_state["lead_email_val"] = input_email
        st.session_state["lead_target_val"] = input_target
    else:
        st.error("올바른 이메일 형식을 기재해 주십시오.")
st.markdown("</div>", unsafe_allow_html=True)

# 💡 세션 스테이트가 감지되면 메인 루프 안전 구역에서 파라미터를 교체하고 정상적인 재실행 트래킹을 수행합니다.
if st.session_state.get("submit_lead_triggered", False):
    st.session_state["submit_lead_triggered"] = False  # 무한 루프 방지 단선
    st.query_params.update(
        submit_lead="true", 
        email=st.session_state["lead_email_val"], 
        target=st.session_state["lead_target_val"]
    )
    st.rerun()  # 안전 구역에서의 단발성 강제 리프레시 실행

# 지도가 스크롤바 없이 꽉 차게 들어오도록 만드는 CSS 압축 패키지
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0.5rem !important; 
            padding-bottom: 0rem !important; 
            padding-left: 0.5rem !important; 
            padding-right: 0.5rem !important;
        }
        iframe {
            display: block; 
            width: 100% !important; 
            border: none !important;
            margin-bottom: 0px !important;
        }
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 6. HTML 파일 로드 및 주입
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    tooltip_extension_script = """
    <script>
    const architectureMap = {
        "xAI 멤피스 콜로서스 1 (앤트로픽 임대)": "NVIDIA Liquid-cooled H100 (100K) & Blackwell B200 Mixed",
        "네이버 하이퍼스케일 각 세종": "NVIDIA H100 / Intel Gaudi 3 & NAVER-Samsung LP-DDR AI chip",
        "MS-블랙록 버지니아 글로벌 허브": "NVIDIA Blackwell NVL72 / Custom Azure Maia 100",
        "미시간 팰리세이드 SMR 착공지": "Next-Gen AI Clusters (Blackwell Ultra / Rubin Ready)",
        "하남 데이터센터": "NVIDIA A100 / H100 Mixed (Domestic Cloud & Inference)"
    };

    function injectArchitectureSpec() {
        const popupTargets = document.querySelectorAll('.leaflet-popup-content, .popup-content, #sidebar, .info-panel');
        popupTargets.forEach(container => {
            if (!container) return;
            if (container.innerHTML.includes('효율성:') && !container.innerHTML.includes('Primary Architecture:')) {
                let matchedArch = "NVIDIA H100 / Blackwell Mixed";
                for (const dcName in architectureMap) {
                    if (container.innerHTML.includes(dcName)) {
                        matchedArch = architectureMap[dcName];
                        break;
                    }
                }
                let currentHtml = container.innerHTML;
                const targetPattern = /(효율성:\\s*\\d+(?:\\.\\d+)?\\s*PFLOPS\\/MW)/i;
                if (targetPattern.test(currentHtml)) {
                    container.innerHTML = currentHtml.replace(targetPattern, `$1<br>• <b>Primary Architecture:</b> ${matchedArch}`);
                } else {
                    container.innerHTML += `<div style="margin-top: 2px;">• <b>Primary Architecture:</b> ${matchedArch}</div>`;
                }
            }
        });
    }

    const popupObserver = new MutationObserver((mutations) => {
        for (let mutation of mutations) {
            if (mutation.addedNodes.length) injectArchitectureSpec();
        }
    });
    popupObserver.observe(document.body, { childList: true, subtree: true });

    window.addEventListener('click', function() {
        setTimeout(injectArchitectureSpec, 50);
        setTimeout(injectArchitectureSpec, 200);
    });
    </script>
    """
    html_code = html_code.replace("</body>", tooltip_extension_script)
    components.html(html_code, height=750, scrolling=False)
    
    # 🤖 대시보드 로드 시 백그라운드에서 조용히 자동 업데이트 에이전트 구동
    agent_status = run_infra_agent_pipeline()
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
