import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import json

# 1. Streamlit 페이지 기본 설정 (상단 바 및 기본 여백 최적화)
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🚨 [보안 장벽 우회 리스너] iframe 내부의 자바스크립트가 보낸 패킷을 수신하는 보이지 않는 컴포넌트
# 스트림릿 자체의 세션 쿼리 찌꺼기를 완전히 청소하고, 오직 이메일 제출 신호가 올 때만 주소창을 변조합니다.
message_listener = """
<script>
window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        // 스트림릿 기본 URL의 노이즈를 제거하고 베이스 주소만 추출
        const cleanUrl = new URL(window.location.origin + window.location.pathname);
        
        // 오직 폼 제출용 핵심 파라미터만 엄격하게 주입
        cleanUrl.searchParams.set("submit_lead", "true");
        cleanUrl.searchParams.set("email", event.data.email);
        cleanUrl.searchParams.set("target", event.data.target);
        
        // 부모 창 자체를 새로고침하며 데이터 투하
        window.location.href = cleanUrl.toString();
    }
});
</script>
"""
components.html(message_listener, height=0, width=0)


# 2. 🚨 GitHub API 연동 및 디버깅 강화 함수
def create_github_issue(email, dc_name="미지정"):
    # Streamlit Cloud의 Secrets 설정 여부 검증
    if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
        st.error("❌ Streamlit Secrets에 GITHUB_TOKEN 또는 GITHUB_REPO가 설정되지 않았습니다.")
        return False
        
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]  # 형식: "유저이름/저장소이름" (예: "berrylee019/datacenter-orbit")
    
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
        
        # 성공 시 (201 Created 반환)
        if response.status_code == 201:
            return True
        else:
            # 실패 시 GitHub API가 뱉은 상세 에러 내용을 스트림릿 화면에 바로 출력 (디버깅용)
            st.error(f"❌ GitHub API 오류 발생 (Status Code: {response.status_code})")
            st.code(response.text, language="json")
            return False
            
    except Exception as e:
        st.error(f"❌ GitHub 통신 중 예외 에러 발생: {str(e)}")
        return False


# 3. 🛡️ [고안정성 네이티브 분기점 통제부]
query_params = st.query_params

# 사용자가 전송 버튼을 눌러 명시적인 파라미터가 성립될 때만 '성공 리포트 뷰'를 활성화
if query_params.get("submit_lead") == "true" and query_params.get("email"):
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    with st.spinner("🚀 GitHub Issues 인프라로 리드를 즉시 송출 중..."):
        success = create_github_issue(lead_email, lead_target)
        
        if success:
            st.balloons()  # 축하 풍선 이펙트
            st.success(f"🎉 성공: {lead_email} 명단 등록 및 GitHub Issues 연동 완료!")
            st.info(f"📋 **접수 세부 정보**\n- **신청 계정:** {lead_email}\n- **우선 관제 타깃:** {lead_target}")
            
            # 원래 관제탑 지도로 돌아가는 리셋 함수
            def reset_to_main():
                st.query_params.clear()
                st.rerun()
            
            st.button("🌐 글로벌 인프라 관제탑 화면으로 돌아가기", on_click=reset_to_main, type="primary")
            st.stop()  # 완료 화면 시 지도가 하단에 이중으로 로드되는 현상을 원천 차단


# 4. Streamlit 상단 메뉴 및 불필요한 백그라운드 여백 제거 CSS
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


# 5. HTML 파일 로드 및 자바스크립트 브릿지 스크립트 강제 주입
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 🛠️ index.html 내부의 Form (#proWaitlistForm)을 가로채고, 지도 흰 화면 현상까지 동시에 방어하는 통합 스크립트
    bridge_script = """
    <script>
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        const emailInput = e.target.querySelector('input[type="email"]').value;
        const dcName = typeof selectedNode !== 'undefined' && selectedNode ? selectedNode.name : "일반 메인 대기";

        // 1. 유저에게 브라우저 기본 알림창 띄우기
        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        
        // 2. iframe 보안 장벽을 뚫고 상위 스트림릿 리스너로 데이터 송출 (postMessage)
        window.parent.postMessage({
            type: "SUBMIT_LEAD",
            email: emailInput,
            target: dcName
        }, "*");
    }

    // HTML이 완전히 안착하면 폼 제출 이벤트 바인딩
    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);

    // ⚡ iframe 초기 생성 시 지도가 찌그러지거나 하얗게 멈추는 현상 강제 부수기 파이프라인
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

    # 6. 컴포넌트 렌더링 실행 (평소에는 시원한 풀스크린 지도가 나옵니다)
    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
