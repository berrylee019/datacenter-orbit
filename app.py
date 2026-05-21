import streamlit as st
import streamlit.components.v1 as components
import os
import requests

# 1. Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. GitHub Issue 생성 함수 (성공/실패 여부를 정확히 반환)
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
                f"--- \n*본 이슈는 InfraPulse 네이티브 브릿지에 의해 안전하게 생성되었습니다.*",
        "labels": ["lead", "pro-waitlist"]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            return True
        else:
            st.error(f"❌ GitHub API 오류 (Status Code: {response.status_code})")
            st.code(response.text, language="json")
            return False
    except Exception as e:
        st.error(f"❌ GitHub 통신 예외 발생: {str(e)}")
        return False

# 3. 💡 [네이티브 쿼리 파라미터 리스너]
query_params = st.query_params

if query_params.get("submit_lead") == "true":
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    # 즉시 GitHub 이슈 생성 실행
    with st.spinner("🚀 리드를 GitHub Issues 인프라로 안전하게 송출 중..."):
        success = create_github_issue(lead_email, lead_target)
        if success:
            st.success(f"🎉 성공: {lead_email} 명단 등록 및 GitHub Issues 연동 완료!")
            st.balloons()
            
            # 주소창 청소 및 초기화 리로드
            st.query_params.clear()
            st.button("관제탑 화면으로 돌아가기", on_click=st.rerun)
            st.stop()

# 4. Streamlit UI 뷰포트 최적화 스타일 (파싱 에러 방지를 위해 원라인 처리)
hide_menu_style = "<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding: 0rem; margin: 0rem;} iframe {display: block; width: 100vw; height: 100vh; border: none;}</style>"
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 5. 지도 및 인터페이스를 담은 HTML 로드 및 렌더링
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 메인 관제 화면 컴포넌트 출력
    components.html(html_code, height=950, scrolling=True)
else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
