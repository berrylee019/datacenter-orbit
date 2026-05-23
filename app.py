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

# 🚨 [보안 강화] 주소창 쿼리 스트링 가로채기 파이프라인
message_listener = """
<script>
window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        const cleanUrl = new URL(window.parent.location.href);
        cleanUrl.searchParams.set("submit_lead", "true");
        cleanUrl.searchParams.set("email", event.data.email);
        cleanUrl.searchParams.set("target", event.data.target);
        window.parent.location.href = cleanUrl.toString();
    }
});
</script>
"""
components.html(message_listener, height=0, width=0)

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
        "body": f"### 📬 새로운 프로 버전 대기 신청 리드\n\n"
                f"- **신청 이메일:** `{email}`\n"
                f"- **우선 관제 타깃:** {dc_name}\n\n",
        "labels": ["lead", "pro-waitlist"]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        return "SUCCESS" if response.status_code == 201 else "ERROR"
    except:
        return "EXCEPTION"

# 📊 [거북목 AI 100% 호환 구조 개조 저장부]
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        return "GSHEETS_SECRETS_ERROR"
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 💡 [핵심 변경] 기존 컬럼명을 분석하지 않고, 거북목 AI 시트 규격에 맞춰 강제 매핑합니다.
        new_data = pd.DataFrame({
            "Email": [email],
            "Date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Name": ["InfraPulse_User"],
            "Note": [f"인프라관제: {dc_name}"]
        })
        
        # 시트1의 기존 데이터를 읽어와 하단에 그대로 병합
        existing_data = conn.read(worksheet="시트1", ttl=0)
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 구글 시트 반영
        conn.update(worksheet="시트1", data=updated_df)
        return "SUCCESS"
    except Exception as e:
        return f"GSHEETS_EXCEPTION_{str(e)}"

# 3. 분기점 통제 (리드 제출 가로채기 엔진)
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

    # 🌟 [초강력 하이재킹 엔진 개조] 
    # 특정 ID 양식에 구애받지 않고, 화면에 이메일 폼이 감지되면 무조건 가로채서 대기열 패킷을 던집니다.
    bridge_script = """
    <script>
    function handleUniversalSubmit(e) {
        // 어떤 형태의 이메일 제출 폼이든 원천 가로채기 수행
        const emailInputObj = e.target.querySelector('input[type="email"]');
        if (!emailInputObj) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        try {
            const emailValue = emailInputObj.value;
            const dcName = (typeof selectedNode !== 'undefined' && selectedNode) ? selectedNode.name : "일반 메인 대기";
            
            alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
            
            window.parent.postMessage({ 
                type: "SUBMIT_LEAD", 
                email: emailValue, 
                target: dcName 
            }, "*");
        } catch(err) {
            console.error("Submit intercept error: ", err);
        }
    }
    
    function forceBindAllForms() {
        // index.html 내의 모든 form 태그에 이벤트 강제 주입
        const allForms = document.querySelectorAll('form');
        allForms.forEach(form => {
            form.removeAttribute('onsubmit');
            form.removeEventListener('submit', handleUniversalSubmit);
            form.addEventListener('submit', handleUniversalSubmit);
        });
    }
    
    // 유저 클릭 및 노드 변경 감지 시 실시간 무한 동기화 바인딩
    window.addEventListener('click', function() { setTimeout(forceBindAllForms, 100); });
    const globalFormObserver = new MutationObserver(() => { forceBindAllForms(); });
    globalFormObserver.observe(document.body, { childList: true, subtree: true });
    
    // 최초 실행 확보
    setTimeout(forceBindAllForms, 500);
    </script>
    """
    
    combined_scripts = f"{tooltip_extension_script}{bridge_script}</body>"
    html_code = html_code.replace("</body>", combined_scripts)
    components.html(html_code, height=900, scrolling=True)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
