import streamlit as st
import streamlit.components.v1 as components
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

# 🚨 [구글 시트 라이브러리 연동]
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("❌ 'st-gsheets-connection' 라이브러리가 누락되었습니다.")
    st.stop()

# 2. GitHub Issue 생성 엔지니어링
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
        "title": f"🚨 [New Lead] {email} 구독 신청",
        "body": f"### 📬 새로운 프로 버전 대기 신청 리드\n\n- **신청 이메일:** `{email}`\n- **우선 관제 타깃:** {dc_name}\n\n",
        "labels": ["lead", "pro-waitlist"]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        return "SUCCESS" if response.status_code == 201 else "ERROR"
    except:
        return "EXCEPTION"

# 📊 [거북목 AI 100% 호환 구조 저장부]
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        return "GSHEETS_SECRETS_ERROR"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 새 리드 데이터 프레임 생성 (거북목 시트 구조 그대로 강제 결합)
        new_data = pd.DataFrame({
            "Email": [email],
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Name": ["InfraPulse_User"],
            "Note": [f"인프라관제: {dc_name}"]
        })
        
        # 시트1의 기존 데이터 읽기
        existing_data = conn.read(worksheet="시트1", ttl=0)
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 구글 시트 업데이트 반영
        conn.update(worksheet="시트1", data=updated_df)
        return "SUCCESS"
    except Exception as e:
        return f"GSHEETS_EXCEPTION_{str(e)}"

# 3. 분기점 통제 (자바스크립트가 직접 주소창에 파라미터를 꽂았을 때 작동)
query_params = st.query_params
if query_params.get("submit_lead") == "true" and query_params.get("email"):
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    
    with st.spinner("🚀 거북목 AI 공유 시트로 리드를 즉시 연동 중..."):
        sheet_status = append_to_gsheets_connection(lead_email, lead_target)
        create_github_issue(lead_email, lead_target)
        
        if sheet_status == "SUCCESS":
            st.balloons()
            st.success(f"🎉 성공: {lead_email} 명단이 구글 시트1에 안전하게 합산 보관되었습니다!")
            st.info(f"📋 **접수 세부 정보**\n- **신청 계정:** {lead_email}\n- **우선 관제 타깃:** {lead_target}")
            
            def reset_to_main():
                st.query_params.clear()
                st.rerun()
            st.button("🌐 글로벌 인프라 관제탑 화면으로 돌아가기", on_click=reset_to_main, type="primary")
            st.stop()
        else:
            st.error(f"❌ 구글 시트 저장 오류 발생. (코드: {sheet_status})")
            if st.button("메인화면 복귀"):
                st.query_params.clear()
                st.rerun()
            st.stop()

# 4. 스타일 무력화
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

# 📊 글로벌 총합 메트릭
st.markdown("### 📊 Global AI Infra Real-time Overview")
col1, col2, col3 = st.columns(3)
col1.metric(label="⚡ Total Global IT Power Capacity", value="14.2 GW", delta="+.8 GW (MoM)")
col2.metric(label="🤖 Est. Global AI Compute Power", value="245.8 EFLOPS", delta="+12.4% (QoQ)")
col3.metric(label="💡 Avg. Compute-to-Power Efficiency", value="18.4 PFLOPS/MW", delta="Optimal", delta_color="normal")
st.markdown("---")

# 5. HTML 파일 로드 및 주입 스크립트 빌드
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
                if (typeof selectedNode !== 'undefined' && selectedNode && selectedNode.architecture) {
                    matchedArch = selectedNode.architecture;
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

    # 🌟 [초강력 하이재킹 브릿지 V2] 
    # iframe postMessage 통신 장벽을 우회하고 최상위 부모 스트림릿 주소창에 파라미터를 강제 다이렉트로 내리꽂습니다.
    bridge_script = """
    <script>
    function interceptAllFormSubmissions(e) {
        // 화면 안의 어떤 폼이든 이메일 타입 입력값이 들어있으면 강제 후킹
        const emailInput = e.target.querySelector('input[type="email"]') || e.target.querySelector('input[placeholder*="이메일"]');
        if (!emailInput) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const emailValue = emailInput.value;
        const dcName = (typeof selectedNode !== 'undefined' && selectedNode && selectedNode.name) ? selectedNode.name : "일반 메인 대기";
        
        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        
        // 💡 최상위 부모창(Streamlit 주소창)의 쿼리 매개변수를 직접 변경하여 파이썬 트리거를 직접 깨웁니다.
        try {
            const parentUrl = new URL(window.parent.location.href);
            parentUrl.searchParams.set("submit_lead", "true");
            parentUrl.searchParams.set("email", emailValue);
            parentUrl.searchParams.set("target", dcName);
            window.parent.location.href = parentUrl.toString();
        } catch(err) {
            // 차선책으로 현재 iframe 기준 부모 윈도우 강제 리다이렉트 시도
            window.top.location.href = window.location.origin + `?submit_lead=true&email=${encodeURIComponent(emailValue)}&target=${encodeURIComponent(dcName)}`;
        }
    }
    
    function attachGlobalInterceptor() {
        // 버블링 스테이지에서 모든 submit 이벤트를 원천 포획
        document.removeEventListener('submit', interceptAllFormSubmissions, true);
        document.addEventListener('submit', interceptAllFormSubmissions, true);
    }
    
    // 문서 로드 및 클릭 시 실시간 리스너 락킹
    attachGlobalInterceptor();
    window.addEventListener('click', function() { setTimeout(attachGlobalInterceptor, 50); });
    const documentObserver = new MutationObserver(() => { attachGlobalInterceptor(); });
    documentObserver.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    combined_scripts = f"{tooltip_extension_script}{bridge_script}</body>"
    html_code = html_code.replace("</body>", combined_scripts)
    components.html(html_code, height=900, scrolling=True)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
