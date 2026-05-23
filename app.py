import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json
from datetime import datetime

# 1. Streamlit 페이지 기본 설정 (최상단 규칙 준수)
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🚨 [구글 시트 라이브러리 안전 탑재]
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("❌ 'st-gsheets-connection' 라이브러리가 누락되었습니다. requirements.txt에 추가 후 Reboot 해주십시오, 형님.")
    st.stop()

# 🚨 [보안 강화] 주소창 쿼리 스트링 가로채기 파이프라인
message_listener = """
<script>
window.addEventListener("message", function(event) {
    // 보안 통과를 위해 모든 PostMessage 소스를 허용하되 SUBMIT_LEAD 타입 신호 정밀 트래킹
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        const cleanUrl = new URL(window.parent.location.href);
        cleanUrl.searchParams.set("submit_lead", "true");
        cleanUrl.searchParams.set("email", encodeURIComponent(event.data.email));
        cleanUrl.searchParams.set("target", encodeURIComponent(event.data.target));
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
                f"- **우선 관제 타깃:** {dc_name}\n\n"
                f"--- \n*본 이슈는 InfraPulse 고안정성 주소창 리스너에 의해 자동 생성되었습니다.*",
        "labels": ["lead", "pro-waitlist"]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            return "SUCCESS"
        else:
            return f"API_ERROR_{response.status_code}_{response.text}"
    except Exception as e:
        return f"EXCEPTION_{str(e)}"

# 📊 [추가된 엔지니어링: st.connection 기반 구글 시트 저장부]
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        return "GSHEETS_SECRETS_ERROR"
    try:
        # 거북목 AI에서 쓰던 세팅 그대로 커넥션 생성
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 기본 시트1(첫 번째 워크시트) 데이터 로드 (캐시 제거)
        existing_data = conn.read(worksheet=0, ttl=0)
        
        # 현재 시간 기록
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 새 데이터 행 매핑 구조 빌드
        new_row = {
            existing_data.columns[0]: current_time,
            existing_data.columns[1]: email,
            "서비스명": "InfraPulse",
            "관심 인프라 타깃": dc_name
        }
        
        # 판다스 concat 결합 처리로 안정성 확보
        import pandas as pd
        new_row_df = pd.DataFrame([new_row])
        updated_data = pd.concat([existing_data, new_row_df], ignore_index=True)
        
        # 구글 시트1 업데이트 밀어넣기
        conn.update(worksheet=0, data=updated_data)
        return "SUCCESS"
    except Exception as e:
        return f"GSHEETS_EXCEPTION_{str(e)}"

# 3. 분기점 통제 (리드 제출 가로채기 엔진)
query_params = st.query_params
if query_params.get("submit_lead") == "true" and query_params.get("email"):
    from urllib.parse import unquote
    lead_email = unquote(query_params.get("email"))
    lead_target = unquote(query_params.get("target", "일반 메인 대기"))
    
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    
    # 2중 파이프라인 가동 (구글 시트 연동 우선 배치 및 깃허브 동시 시도)
    with st.spinner("🚀 거북목 AI 공유 시트 및 GitHub 인프라로 리드를 연동 중..."):
        sheet_status = append_to_gsheets_connection(lead_email, lead_target)
        github_status = create_github_issue(lead_email, lead_target)
        
        # 구글 시트나 깃허브 둘 중 하나라도 성공하면 유저에게 성공 마크 부여
        if sheet_status == "SUCCESS":
            st.balloons()
            st.success(f"🎉 성공: {lead_email} 명단이 거북목 AI 공유 구글 시트에 안전하게 통합되었습니다!")
            if github_status != "SUCCESS":
                st.warning(f"⚠️ 참고: 구글 시트는 저장 완료되었으나, GitHub 연동은 비활성 상태입니다. (코드: {github_status})")
                
            st.info(f"📋 **접수 세부 정보**\n- **신청 계정:** {lead_email}\n- **우선 관제 타깃:** {lead_target}")
            
            def reset_to_main():
                st.query_params.clear()
                st.rerun()
            st.button("🌐 글로벌 인프라 관제탑 화면으로 돌아가기", on_click=reset_to_main, type="primary")
            st.stop()
            
        elif sheet_status == "GSHEETS_SECRETS_ERROR":
            st.error("❌ 전송 실패: Streamlit Secrets에 [connections.gsheets] 설정 블록이 누락되었습니다.")
            st.stop()
        else:
            st.error(f"❌ 구글 시트 통신 오류 발생. (상세 코드: {sheet_status})")
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
    
    # 아키텍처 실시간 매핑 딕셔너리
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

    # 🌟 [개조] 입력한 폼 데이터를 최상위 부모 윈도우(Streamlit)로 강력 송출하는 스크립트
    bridge_script = """
    <script>
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        try {
            const emailInput = e.target.querySelector('input[type="email"]').value;
            const dcName = (typeof selectedNode !== 'undefined' && selectedNode) ? selectedNode.name : "일반 메인 대기";
            
            alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
            
            // iframe 보안 장벽을 뚫기 위해 postMessage의 대상을 명확히 부모(parent)로 지정
            window.parent.postMessage({ 
                type: "SUBMIT_LEAD", 
                email: emailInput, 
                target: dcName 
            }, "*");
        } catch(err) {
            alert("제출 처리 중 오류 발생: " + err.message);
        }
    }
    
    function bindFormSubmit() {
        const form = document.getElementById('proWaitlistForm');
        if (form) {
            form.removeAttribute('onsubmit'); // 기존 인라인 이벤트 핸들러 제거
            form.removeEventListener('submit', handleFakeDoorSubmit);
            form.addEventListener('submit', handleFakeDoorSubmit);
        }
    }
    
    // 클릭 및 마커 로드 이벤트와 지속 동기화
    window.addEventListener('click', function() { setTimeout(bindFormSubmit, 150); });
    const formObserver = new MutationObserver(() => { bindFormSubmit(); });
    formObserver.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    combined_scripts = f"{tooltip_extension_script}{bridge_script}</body>"
    html_code = html_code.replace("</body>", combined_scripts)
    components.html(html_code, height=900, scrolling=True)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
