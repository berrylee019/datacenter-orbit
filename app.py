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

# 🚨 [1단계] 자바스크립트 postMessage를 수신해서 부모 창 주소를 갱신하는 리스너
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

# 🚨 [2단계] 주소창 쿼리 리스너 수신부 & 레이아웃 전면 분리 트릭
# 리드가 제출되어 새로고침되었을 때는 하단 메인 HTML 지도를 렌더링하지 않고 완료 페이지를 독립적으로 띄웁니다.
query_params = st.query_params

if query_params.get("submit_lead") == "true":
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    if lead_email:
        # 상단 여백 확보 및 중앙 정렬 서식
        st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
        
        with st.spinner("🚀 GitHub Issues 인프라로 리드를 즉시 송출 중..."):
            success = create_github_issue(lead_email, lead_target)
            
            if success:
                st.balloons()
                
                # 멋지게 커스텀된 대기 명단 접수 완료 대시보드 박스 출력
                st.success(f"🎉 성공: {lead_email} 명단 등록 및 GitHub Issues 연동 완료!")
                
                st.info(f"📋 **접수 세부 정보**\n- **신청 계정:** {lead_email}\n- **우선 관제 타깃:** {lead_target}")
                
                # 원상복귀 버튼 배치 (클릭 시 주소창을 완전히 비우고 깔끔하게 처음 1페이지 지도로 컴백)
                def reset_to_main():
                    st.query_params.clear()
                    st.rerun()
                
                st.button("🌐 글로벌 인프라 관제탑 화면으로 돌아가기", on_click=reset_to_main, type="primary")
                st.stop()  # 코드 진행을 여기서 완전히 멈춰서 아래 HTML 지도가 어설프게 로드되는 것을 원천 차단합니다.

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

# 4. HTML 파일 로드 및 고안정성 주입 스크립트 빌드
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # Form 제출 리스너 등록 및 Leaflet 지도 타일 깨우기 파이프라인 주입
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

    // 폼 제출 이벤트 바인딩
    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);

    // iframe 로딩 지연으로 인한 지도 뭉개짐/흰 화면 현상 강제 리프레시
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

    # 5. 컴포넌트 실행 (일반 상태일 때는 시원하게 전체화면 지도가 나옴)
    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
