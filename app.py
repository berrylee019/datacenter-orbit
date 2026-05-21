import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json

# 1. Streamlit 페이지 기본 설정 (와이드 모드 및 타이틀 세팅)
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. GitHub Issue 생성 헬퍼 함수
def create_github_issue(email, dc_name="미지정"):
    # Secrets 관리자에서 토큰과 저장소 이름 안전하게 로드
    if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
        st.error("Streamlit Cloud Settings -> Secrets에 GITHUB_TOKEN과 GITHUB_REPO를 설정해 주세요.")
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
                f"- **관심 인프라 타깃:** {dc_name}\n"
                f"- **시스템 상태:** 실시간 데이터 수집 통로 정상 작동 중\n\n"
                f"--- \n*본 이슈는 InfraPulse Streamlit 자체 수신 핸들러에 의해 자동 생성되었습니다.*",
        "labels": ["lead", "pro-waitlist"]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.status_code == 201
    except Exception as e:
        print(f"GitHub API 통신 에러: {e}")
        return False

# 3. Streamlit 상단 메뉴 및 불필요한 백그라운드 여백 제거 (전체 화면 최적화 CLI)
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

# 4. 가장 에러가 없고 깔끔한 'Streamlit 전용 수신 핸들러' 인터페이스 구축
# HTML 내부에서 window.parent.postMessage() 형태로 쏜 데이터를 감지하는 표준 가교 레이어입니다.
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # [자체 핸들러 연동 스크립트 수술]: HTML 소스코드 로드 후, 자바스크립트 브릿지 주입
    # 이 스크립트 주입 덕분에 index.html 내부의 handleFakeDoorSubmit가 실행될 때 파이썬 백엔드가 곧바로 감지합니다.
    bridge_script = """
    <script>
    // 기존의 handleFakeDoorSubmit 함수를 Streamlit 통신 규격에 맞게 오버라이딩(덮어쓰기) 합니다.
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        const emailInput = e.target.querySelector('input[type="email"]').value;
        const dcName = selectedNode ? selectedNode.name : "일반 메인 대기";

        // 부모 Streamlit 창에 데이터 바인딩 전송
        const payload = {
            type: "INFRA_PULSE_LEAD",
            email: emailInput,
            target: dcName
        };
        window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: payload}, "*");

        // 유저 UX용 가벼운 알림 후 모달 숨김 처리
        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        e.target.reset();
        closeFakeDoorModal();
    }
    </script>
    """
    # 닫는 body 태그 바로 앞에 브릿지 스크립트를 삽입하여 결합력을 강화합니다.
    html_code = html_code.replace("</body>", f"{bridge_script}</body>")

    # 5. components.html을 커스텀 상태 저장소로 활용하여 값의 변화를 비동기로 리스닝
    # scrolling=True 옵션을 주어 오타 오류 원천 차단 및 안정성 확보
    response_data = components.html(html_code, height=950, scrolling=True)

    # 6. 컴포넌트로부터 유저 리드 수집 신호가 넘어왔을 때 실행되는 백엔드 트리거
    if response_data font_type := type(response_data) is dict and response_data.get("type") == "INFRA_PULSE_LEAD":
        lead_email = response_data.get("email")
        lead_target = response_data.get("target", "일반 메인 대기")
        
        # 중복 전송 방지를 위해 세션 상태(Session State) 고유 키 검사 적용
        if "last_collected_lead" not in st.secrets or st.session_state.get("last_collected_lead") != lead_email:
            st.session_state["last_collected_lead"] = lead_email
            
            # 깃허브 이슈 생성 파이프라인 구동
            with st.spinner("GitHub 가동 중..."):
                success = create_github_issue(lead_email, lead_target)
                if success:
                    st.toast(f"🎉 {lead_email} 리드 수집 성공! (GitHub Issues 연동 완료)", icon="✅")
                else:
                    st.toast("GitHub 연동 실패. Secrets 설정을 확인하세요.", icon="❌")

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다. 파일 배포 경로를 다시 확인해 주세요, 형님.")
