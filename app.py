import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json

# 1. Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 🚨 디버깅 정보 출력을 강화한 GitHub Issue 생성 함수
def create_github_issue(email, dc_name="미지정"):
    if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
        st.error("❌ Streamlit Secrets에 GITHUB_TOKEN 또는 GITHUB_REPO가 설정되지 않았습니다.")
        return False
        
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
                f"- **관심 인프라 타깃:** {dc_name}\n\n"
                f"--- \n*본 이슈는 InfraPulse 자체 수신 핸들러에 의해 자동 생성되었습니다.*",
        "labels": ["lead", "pro-waitlist"]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        # 💡 성공 시 (201 Created)
        if response.status_code == 201:
            return True
        else:
            # 💡 실패 시 GitHub이 반환한 상세 에러를 Streamlit 화면에 직접 경고창으로 출력
            st.error(f"❌ GitHub API 오류 발생 (Status Code: {response.status_code})")
            st.code(response.text, language="json")
            return False
            
    except Exception as e:
        st.error(f"❌ GitHub 통신 중 예외 에러 발생: {str(e)}")
        return False

# 3. Streamlit 상단 메뉴 및 불필요한 백그라운드 여백 제거
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0rem; margin: 0rem;}
        iframe {display: block; width: 100vw; height: 100vh; border: none;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 4. HTML 파일 로드 및 스크립트 주입
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    bridge_script = """
    <script>
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        const emailInput = e.target.querySelector('input[type="email"]').value;
        const dcName = selectedNode ? selectedNode.name : "일반 메인 대기";

        const payload = {
            type: "INFRA_PULSE_LEAD",
            email: emailInput,
            target: dcName
        };
        window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: payload}, "*");

        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        e.target.reset();
        closeFakeDoorModal();
    }
    </script>
    """
    html_code = html_code.replace("</body>", f"{bridge_script}</body>")

    # 5. 컴포넌트 실행 및 응답 수신
    response_data = components.html(html_code, height=950, scrolling=True)

    # 6. 유저 리드 신호 처리 핸들러 (수신부 구조 정렬 완료)
    if isinstance(response_data, dict) and response_data.get("type") == "INFRA_PULSE_LEAD":
        lead_email = response_data.get("email")
        lead_target = response_data.get("target", "일반 메인 대기")
        
        # 중복 체크 세션 검증
        if "last_collected_lead" not in st.session_state or st.session_state.get("last_collected_lead") != lead_email:
            st.session_state["last_collected_lead"] = lead_email
            
            with st.spinner("🚀 GitHub Issues 인프라로 리드 송출 중..."):
                success = create_github_issue(lead_email, lead_target)
                if success:
                    st.toast(f"🎉 {lead_email} 리드 수집 성공! (GitHub 연동 완료)", icon="✅")
                    # 💡 백엔드를 즉시 리로드하여 다음 입력을 받을 수 있도록 뷰포트를 리셋합니다.
                    st.rerun()
        else:
            st.toast("⚠️ 중복된 이메일 주소입니다. 다른 이메일로 테스트해 보세요.", icon="ℹ️")

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
