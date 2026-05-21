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

# 🚨 [신규 추가] 자바스크립트 postMessage를 수신해서 부모 창 주소(Query Parameter)를 직접 갱신하는 보이지 않는 리스너
message_listener = """
<script>
window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        // 부모 창(Streamlit 메인 앱)의 URL을 안전하게 가져와서 파라미터 세팅
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set("submit_lead", "true");
        currentUrl.searchParams.set("email", event.data.email);
        currentUrl.searchParams.set("target", event.data.target);
        
        // 크로스 오리진 차단 없이 부모 창 자체를 새로고침하며 데이터 주입
        window.location.href = currentUrl.toString();
    }
});
</script>
"""
# 0픽셀 크기로 메인 화면 최상단에 안전하게 배치합니다.
components.html(message_listener, height=0, width=0)


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
                f"--- \n*본 이슈는 InfraPulse 고안정성 주소창 리스너에 의해 자동 생성되었습니다.*",
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

# 3. 🛡️ [고안정성 네이티브 주소창 리스너]
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
                
                # 전송 완료 후 주소창을 깨끗하게 비우고 세션 리셋
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

# 5. HTML 파일 로드 및 주소창 변조형 스크립트 주입
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 🛠️ [수정 완료] 직접적인 window.parent 변조 대신 안전하게 postMessage로 부모 창에 데이터를 전달하는 브릿지 스크립트
    bridge_script = """
    <script>
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        const emailInput = e.target.querySelector('input[type="email"]').value;
        const dcName = typeof selectedNode !== 'undefined' && selectedNode ? selectedNode.name : "일반 메인 대기";

        // 1. 사용자에게 완료 알림창 먼저 출력
        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        
        // 2. iframe의 오리진 장벽을 넘어 부모(Streamlit) 리스너로 데이터 송출
        window.parent.postMessage({
            type: "SUBMIT_LEAD",
            email: emailInput,
            target: dcName
        }, "*");
    }

    // 💡 HTML 렌더링 후 폼 제출 이벤트를 가로채도록 리스너 수동 정렬
    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);
    </script>
    """
    html_code = html_code.replace("</body>", f"{bridge_script}</body>")

    # 6. 컴포넌트 실행
    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
