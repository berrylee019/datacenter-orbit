import streamlit as st
import requests
import json
import os
import streamlit.components.v1 as components

# 1. Streamlit 페이지 기본 설정 (전체 화면 확장을 위해 와이드 모드 활성화)
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 상단 Streamlit 기본 메뉴 및 하단 워터마크 숨기기 (깔끔한 UI용)
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0rem;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 2. index.html 파일 읽기
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 3. HTML 컴포넌트를 전체 화면 크기로 렌더링 (높이는 브라우저 환경에 맞게 조절)
    components.html(html_code, height=900, scroller=True)
else:
    st.error("index.html 파일을 찾을 수 없습니다. 저장소 루트 경로를 확인해 주세요.")


# --- Streamlit Secrets에서 보안 환경변수 안전하게 로드 ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = st.secrets["GITHUB_REPO_OWNER"]
REPO_NAME = st.secrets["GITHUB_REPO_NAME"]

# 프론트엔드와 통신하기 위한 간단한 데이터 중계 처리기
# Streamlit 앱 실행 시 URL에 ?action=submit_lead 처럼 값이 들어올 때 작동하는 백엔드 로직입니다.
query_params = st.query_params

if "action" in query_params and query_params["action"] == "submit_lead":
    try:
        # 프론트엔드에서 보낸 파라미터 캐치
        user_email = query_params.get("email", "알 수 없음")
        target_dc = query_params.get("dc", "알 수 없음")
        
        # GitHub Issues API 엔드포인트 구성
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"
        
        # GitHub API가 요구하는 인증 헤더 세팅 (Secrets 토큰 주입)
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # 이슈 카드 내용 자동 조립
        issue_data = {
            "title": f"🔥 [Pro 대기명단] {target_dc} - {user_email}",
            "body": f"### 📊 프리미엄 구독 리드 자동 수집\n\n- **신청자 이메일:** {user_email}\n- **관심 데이터센터:** {target_dc}\n- **유입 경로:** SMR 그리드 선 가상 결합 시뮬레이터 팝업\n\n*본 이슈는 Streamlit Secrets 보안 환경을 거쳐 GitHub API를 통해 안전하게 자동 발행되었습니다.*",
            "labels": ["lead", "premium-waitlist"]
        }
        
        # GitHub API로 실제 생성 요청 전송
        response = requests.post(url, headers=headers, json=issue_data)
        
        if response.status_code == 201:
            st.write(json.dumps({"status": "success", "message": "Issue created successfully"}))
        else:
            st.write(json.dumps({"status": "failed", "error": response.text}))
            
    except Exception as e:
        st.write(json.dumps({"status": "error", "message": str(e)}))
        
    st.stop() # API 응답 후 화면 렌더링 중단
