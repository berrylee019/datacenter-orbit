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
# iframe의 postMessage 유실 문제를 완벽하게 우회합니다.
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
    
    # postMessage 대신 부모 창의 주소를 직접 바꿔 브릿지를 태우는 안전 설계 스크립트
    bridge_script = """
    <script>
    function handleFakeDoorSubmit(e) {
        e.preventDefault();
        const emailInput = e.target.querySelector('input[type="email"]').value;
        const dcName = selectedNode ? selectedNode.name : "일반 메인 대기";

        // 부모 창(Streamlit)의 오리진 주소 획득
        const parentOrigin = window.parent.location.origin;
        const parentPath = window.parent.location.pathname;
        
        // 쿼리 스트링 매개변수 빌드
        const targetUrl = `${parentOrigin}${parentPath}?submit_lead=true&email=${encodeURIComponent(emailInput)}&target=${encodeURIComponent(dcName)}`;
        
        alert(`감사합니다! 얼리버드 대기 명단 등록이 완료되었습니다.\\n\\n출시 즉시 안내서와 50% 할인 혜택을 발송해 드리겠습니다.`);
        
        // 부모 창의 주소를 강제로 변경하여 Streamlit 백엔드를 깨웁니다.
        window.parent.location.href = targetUrl;
    }
    </script>
    """
    html_code = html_code.replace("</body>", f"{bridge_script}</body>")

    # 6. 컴포넌트 실행 (수신처리는 상단의 3번 리스너가 전담하므로 반환값은 렌더링용으로만 사용)
    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
