import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json
import pandas as pd
from datetime import datetime

# 1. Streamlit 페이지 기본 설정 (최상단 고정 및 여백 최소화 셋업)
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

# 📊 [거북목 AI 100% 호환 및 탭 이름 자동 매핑 엔진]
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        return "GSHEETS_SECRETS_ERROR"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 💡 [대격변 조치] worksheet 이름을 명시하지 않고 호출하여 
        # 구글 스프레드시트의 '첫 번째 탭'이 시트1이든 Sheet1이든 상관없이 강제로 긁어옵니다.
        existing_data = conn.read(ttl=0)
        
        new_data = pd.DataFrame({
            "Email": [email],
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Name": ["InfraPulse_User"],
            "Note": [f"인프라관제: {dc_name}"]
        })
        
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 💡 저장할 때도 첫 번째 탭에 다이렉트로 업데이트를 밀어 넣습니다.
        conn.update(data=updated_df)
        return "SUCCESS"
    except Exception as e:
        return f"GSHEETS_EXCEPTION_{str(e)}"

# 3. 주소창 URL 파라미터 가로채기 파이프라인
query_params = st.query_params
if query_params.get("submit_lead") == "true" and query_params.get("email"):
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
    
    with st.spinner("🚀 거북목 AI 공유 시트로 리드를 즉시 동기화 중..."):
        sheet_status = append_to_gsheets_connection(lead_email, lead_target)
        create_github_issue(lead_email, lead_target)
        
        if sheet_status == "SUCCESS":
            st.balloons()
            st.success(f"🎉 성공: {lead_email} 명단이 구글 시트에 합산 완료되었습니다!")
            
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

# 4. 1페이지 스크롤 제로화를 위한 상단 메트릭 가로 압축 배치
st.markdown("<h3 style='margin:0; padding:0;'>🌐 InfraPulse 관제탑</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.metric(label="⚡ Power Capacity", value="14.2 GW", delta="+.8 GW")
col2.metric(label="🤖 AI Compute", value="245.8 EFLOPS", delta="+12.4%")
col3.metric(label="💡 Efficiency", value="18.4 PFLOPS/MW", delta="Optimal")

# 5. 🚨 [지도가 1페이지 안에 딱 들어오게 만드는 마법의 CSS 주입]
# 상단 여백, 테두리 패딩을 소수점 단위까지 압축하여 스크롤바 자체를 지워버립니다.
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0rem !important; 
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

# 6. HTML 파일 로드 및 자바스크립트 주입
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 아키텍처 명세 코드
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

    # 🌟 [최상위 강제 이동 스크립트] 
    # 모바일이나 작은 노트북 화면에서도 절대 튕기지 않고 브라우저 URL 전체를 변경해 버립니다.
    bridge_script = """
    <script>
    function interceptAllFormSubmissions(e) {
        const emailInput = e.target.querySelector('input[type="email"]') || e.target.querySelector('input[placeholder*="이메일"]');
        if (!emailInput) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const emailValue = emailInput.value;
        const dcName = (typeof selectedNode !== 'undefined' && selectedNode && selectedNode.name) ? selectedNode.name : "일반 메인 대기";
        
        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        
        try {
            const parentUrl = new URL(window.parent.location.href);
            parentUrl.searchParams.set("submit_lead", "true");
            parentUrl.searchParams.set("email", emailValue);
            parentUrl.searchParams.set("target", dcName);
            window.parent.location.href = parentUrl.toString();
        } catch(err) {
            window.top.location.href = window.location.origin + `?submit_lead=true&email=${encodeURIComponent(emailValue)}&target=${encodeURIComponent(dcName)}`;
        }
    }
    
    function attachGlobalInterceptor() {
        document.removeEventListener('submit', interceptAllFormSubmissions, true);
        document.addEventListener('submit', interceptAllFormSubmissions, true);
    }
    
    attachGlobalInterceptor();
    window.addEventListener('click', function() { setTimeout(attachGlobalInterceptor, 50); });
    const documentObserver = new MutationObserver(() => { attachGlobalInterceptor(); });
    documentObserver.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    combined_scripts = f"{tooltip_extension_script}{bridge_script}</body>"
    html_code = html_code.replace("</body>", combined_scripts)
    
    # 💡 [크기 최적화] 메트릭 밑 공간에 딱 달라붙도록 높이를 660px로 축소하여 1페이지 내에 완전 박제합니다.
    components.html(html_code, height=660, scrolling=False)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
