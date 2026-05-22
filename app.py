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

# 🚨 자바스크립트 postMessage를 수신해서 부모 창 주소를 갱신하는 리스너
message_listener = """
<script>
window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set("submit_lead", "true");
        currentUrl.searchParams.set("email", event.data.email);
        currentUrl.searchParams.set("target", event.data.target);
        window.location.href = currentUrl.toString();
    }
});
</script>
"""
components.html(message_listener, height=0, width=0)

# 2. GitHub Issue 생성 함수
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
                f"--- \n*본 이슈는 InfraPulse 고안정성 주소창 리스너에 의해 자동 생성되었습니다.*",
        "labels": ["lead", "pro-waitlist"]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            return True
        else:
            st.error(f"❌ GitHub API 오류 발생 (Status Code: {response.status_code})")
            st.code(response.text, language="json")
            return False
    except Exception as e:
        st.error(f"❌ GitHub 통신 중 예외 에러 발생: {str(e)}")
        return False

# 3. 주소창 쿼리 리스너 수신부
query_params = st.query_params
if query_params.get("submit_lead") == "true":
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    if lead_email:
        with st.spinner("🚀 GitHub Issues 인프라로 리드를 즉시 송출 중..."):
            success = create_github_issue(lead_email, lead_target)
            if success:
                st.success(f"🎉 성공: {lead_email} 명단 등록 및 GitHub Issues 연동 완료!")
                st.balloons()
                st.query_params.clear()
                st.button("관제탑 화면으로 돌아가기", on_click=st.rerun)
                st.stop()

# 4. Streamlit 상단 메뉴 및 불필요한 백그라운드 여백 제거
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

# 5. HTML 파일 로드 및 고안정성 주입 스크립트 빌드
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 🛠️ [흰 화면 버그 원천 차단] 
    # Form 제출 리스너 등록 뿐만 아니라, 지도가 깨지거나 하얗게 멈추는 현상을 방지하기 위해
    # 로드 직후 / 300ms 뒤 / 1초 뒤 연속으로 map.invalidateSize()를 강제 수행하여 타일을 무조건 깨웁니다.
    bridge_script = """
    <script>
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        const emailInput = e.target.querySelector('input[type="email"]').value;
        const dcName = typeof selectedNode !== 'undefined' && selectedNode ? selectedNode.name : "일반 메인 대기";

        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        
        window.parent.postMessage({
            type: "SUBMIT_LEAD",
            email: emailInput,
            target: dcName
        }, "*");
    }

    // 폼 제출 이벤트 결합
    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);

    // ⚡ [핵심 패치] iframe 로딩 지연으로 인한 지도 뭉개짐/흰 화면 현상 강제 해결 파이프라인
    function triggerMapRefresh() {
        if (typeof map !== 'undefined' && map !== null) {
            map.invalidateSize({ animate: true });
        }
    }

    // 브라우저가 화면을 그리는 마이크로 타이밍마다 연속으로 리프레시 신호를 보내어 하얀 스크린을 강제로 부숩니다.
    window.addEventListener('load', triggerMapRefresh);
    setTimeout(triggerMapRefresh, 300);
    setTimeout(triggerMapRefresh, 1000);
    setTimeout(triggerMapRefresh, 2500); 
    </script>
    """
    html_code = html_code.replace("</body>", f"{bridge_script}</body>")

    # 6. 컴포넌트 실행 (height는 화면 풀사이즈에 맞춰 950~100vh 수준 유지)
    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
