import streamlit as st
import requests
import json

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
