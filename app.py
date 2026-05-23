import streamlit as st
import os
import requests
import json
import pandas as pd
from datetime import datetime

# 1. Streamlit 페이지 기본 설정 (최상단 고정)
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

# 📊 [거북목 AI 100% 복제형 구글 시트 직통 엔진]
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        return "GSHEETS_SECRETS_ERROR"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 거북목 AI 구글 시트 데이터 규격 일치화
        new_data = pd.DataFrame({
            "Email": [email],
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Name": ["InfraPulse_Direct"],
            "Note": [f"관제타깃: {dc_name}"]
        })
        
        # 기존 시트1 데이터 로드 후 병합
        existing_data = conn.read(worksheet="시트1", ttl=0)
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 저장
        conn.update(worksheet="시트1", data=updated_df)
        return "SUCCESS"
    except Exception as e:
        return f"GSHEETS_EXCEPTION_{str(e)}"

# 3. 사이드바 또는 상단 관제탑 헤더 레이아웃 구성
st.markdown("### 🌐 InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑")

# 📊 글로벌 총합 메트릭 바
col1, col2, col3 = st.columns(3)
col1.metric(label="⚡ Total Global IT Power Capacity", value="14.2 GW", delta="+.8 GW (MoM)")
col2.metric(label="🤖 Est. Global AI Compute Power", value="245.8 EFLOPS", delta="+12.4% (QoQ)")
col3.metric(label="💡 Avg. Compute-to-Power Efficiency", value="18.4 PFLOPS/MW", delta="Optimal", delta_color="normal")
st.markdown("---")

# 🚀 [대격변] 거북목 AI 순정 폼 메커니즘 전면 배치
# iframe 내부가 아니라, 스트림릿 영역에 입력창을 완전히 꺼내어 브라우저 차단을 원천 봉쇄합니다.
with st.sidebar:
    st.subheader("🚀 Pro 버전 얼리버드 대기열")
    st.write("~~정가 49,000원/월~~ ➡️ **특별가: 24,000원/월**")
    
    with st.form("infrapulse_waitlist_form"):
        user_email = st.text_input("이메일 주소", placeholder="example@email.com")
        target_dc = st.selectbox("우선 관제 희망 타깃", [
            "글로벌 전체 관제", 
            "xAI 멤피스 콜로서스 1", 
            "네이버 하이퍼스케일 각 세종", 
            "MS-블랙록 버지니아 허브", 
            "미시간 팰리세이드 SMR", 
            "하남 데이터센터"
        ])
        submit_btn = st.form_submit_button("사전 예약 및 얼리버드 신청 🚀", use_container_width=True)
        
        if submit_btn:
            if user_email and "@" in user_email:
                with st.spinner("구글 시트 동기화 중..."):
                    status = append_to_gsheets_connection(user_email, target_dc)
                    create_github_issue(user_email, target_dc)
                    
                    if status == "SUCCESS":
                        st.success("🎉 등록 완료! 거북목 AI 시트에 안전하게 연동되었습니다.")
                        st.balloons()
                    elif status == "GSHEETS_SECRETS_ERROR":
                        st.error("❌ Secrets에 [connections.gsheets] 설정 블록이 보이지 않습니다.")
                    else:
                        st.error(f"❌ 시트 저장 실패: {status}")
            else:
                st.error("올바른 이메일 형식을 입력해 주십시오.")

# 4. 스타일 무력화 및 지도 표출
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem;}
        iframe {display: block; width: 100%; border: none;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 5. HTML 파일 로드 및 구조 주입 (아키텍처 스펙 기능은 그대로 보존)
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
    </body>
    """
    html_code = html_code.replace("</body>", tooltip_extension_script)
    
    # 순정 폼이 사이드바에 완전히 나갔으므로 iframe은 스크롤 없이 크게 배치합니다.
    st.components.html(html_code, height=850, scrolling=False)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
