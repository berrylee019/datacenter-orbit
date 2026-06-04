import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json
import pandas as pd
from datetime import datetime

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
            st.success(f"🎉 성공: {lead_email} 명단이 구글 시트에 정상 합산 완료되었습니다!")
            
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
    # 거북목 AI와 완벽하게 동일한 메커니즘을 가진 순정 "녹색" 제출 버튼
    btn_style = st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #22c55e !important;
            color: white !important;
            border: none !important;
            width: 100%;
        }
        </style>""", unsafe_allow_html=True)
    submit_clicked = st.button("얼리버드 사전 예약 🚀")

# 5. 🛠️ 버튼 클릭 처리 부분 보정 (st.rerun 경고 해결 구역)
if submit_clicked:
    if input_email and "@" in input_email:
        # st.rerun()을 호출하지 않고 쿼리 파라미터만 업데이트하여 샌드박스 경고를 우회합니다.
        st.query_params.update(submit_lead="true", email=input_email, target=input_target)
    else:
        st.error("올바른 이메일 형식을 기재해 주십시오.")
st.markdown("</div>", unsafe_allow_html=True)

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
    
    # 아키텍처 툴팁 기능 명세 스크립트
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
    </body>
    """
    html_code = html_code.replace("</body>", tooltip_extension_script)
    
    # 💡 폼이 상단으로 완전히 대피했으므로, 지도는 스크롤바 없이 아래 빈 공간을 꽉 채우도록 높이를 750px로 시원하게 늘려줍니다.
    components.html(html_code, height=750, scrolling=False)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
