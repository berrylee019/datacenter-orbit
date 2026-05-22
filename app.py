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

# 🚨 [수정 및 안착] 스트림릿 고유의 기본 쿼리 찌꺼기 필터링 시스템
# 자바스크립트가 명확하게 이메일 전송 패킷을 쏘아 올렸을 때만 주소창 변조가 발동하도록 통제합니다.
message_listener = """
<script>
window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        // 스트림릿 기본 주소의 쿼리 찌꺼기를 완전히 청소하고 베이스 주소만 추출
        const cleanUrl = new URL(window.location.origin + window.location.pathname);
        
        // 오직 폼 제출용 핵심 파라미터만 엄격하게 주입
        cleanUrl.searchParams.set("submit_lead", "true");
        cleanUrl.searchParams.set("email", event.data.email);
        cleanUrl.searchParams.set("target", event.data.target);
        
        // 부모 창 강제 리로딩 및 전송 실행
        window.location.href = cleanUrl.toString();
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

# 🚨 [3. 분기점 통제] 오직 명시적 파라미터가 성립될 때만 2페이지 활성화
query_params = st.query_params

# 스트림릿 자체 세션 매개변수와 구분하기 위해 대조식으로 엄격히 필터링
if query_params.get("submit_lead") == "true" and query_params.get("email"):
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    with st.spinner("🚀 GitHub Issues 인프라로 리드를 즉시 송출 중..."):
        success = create_github_issue(lead_email, lead_target)
        
        if success:
            st.balloons()
            st.success(f"🎉 성공: {lead_email} 명단 등록 및 GitHub Issues 연동 완료!")
            st.info(f"📋 **접수 세부 정보**\n- **신청 계정:** {lead_email}\n- **우선 관제 타깃:** {lead_target}")
            
            def reset_to_main():
                st.query_params.clear()
                st.rerun()
            
            st.button("🌐 글로벌 인프라 관제탑 화면으로 돌아가기", on_click=reset_to_main, type="primary")
            st.stop() # 2페이지 활성화 시 지도가 하단에 이중으로 덧그려지는 것 완전 차단

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
    
    # 폼 내부 이벤트 핸들러 및 타일 깨우기 연속 파이프라인 주입
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

    // 폼 제출 리스너 수동 결합
    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);

    // iframe 리사이즈 대응 지도 타일 갱신 스크립트
    function triggerMapRefresh() {
        if (typeof map !== 'undefined' && map !== null) {
            map.invalidateSize({ animate: true });
        }
    }

    window.addEventListener('load', triggerMapRefresh);
    setTimeout(triggerMapRefresh, 300);
    setTimeout(triggerMapRefresh, 1000);
    setTimeout(triggerMapRefresh, 2500); 
    </script>
    """
    html_code = html_code.replace("</body>", f"{bridge_script}</body>")

    # 6. 컴포넌트 실행 (첫 진입 시 무조건 시원한 1페이지 전체 지도가 표출됨)
    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
