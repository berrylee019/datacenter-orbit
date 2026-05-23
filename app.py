import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime

# 🚨 [규칙 준수 1순위] st.set_page_config는 다른 모든 스트림릿 명령보다 무조건 최상단에 와야 합니다.
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 필수 라이브러리 체크 (st.set_page_config 아래로 안전하게 이동)
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("❌ 'st-gsheets-connection' 라이브러리가 누락되었습니다. requirements.txt에 추가해 주세요, 형님.")
    st.stop()

# 🚨 [보안 장벽 우회 리스너] iframe 내부 자바스크립트 패킷 수신부
message_listener = """
<script>
window.addEventListener("message", function(event) {
    if (event.data && event.data.type === "SUBMIT_LEAD") {
        const cleanUrl = new URL(window.location.origin + window.location.pathname);
        cleanUrl.searchParams.set("submit_lead", "true");
        cleanUrl.searchParams.set("email", event.data.email);
        cleanUrl.searchParams.set("target", event.data.target);
        window.location.href = cleanUrl.toString();
    }
});
</script>
"""
components.html(message_listener, height=0, width=0)


# 3. 📊 st.connection 기반 구글 시트 데이터 적재 함수
def append_to_gsheets_connection(email, dc_name="미지정"):
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        st.error("❌ Streamlit Secrets에 [connections.gsheets] 설정 블록이 누락되었습니다, 형님.")
        return False
        
    try:
        # 구글 시트 커넥션 생성
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 거북목 AI 시트 데이터프레임 로드 (캐시 비활성화 ttl=0)
        existing_data = conn.read(worksheet=0, ttl=0)
        
        # 현재 시간 기록 (한국 시간 기준)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 📝 새롭게 추가할 인프라펄스 데이터 행 구성
        new_row = {
            existing_data.columns[0]: current_time,
            existing_data.columns[1]: email,
            "서비스명": "InfraPulse",
            "관심 인프라 타깃": dc_name
        }
        
        # 💡 최신 판다스 환경에서 .append() 제거로 인한 경고 및 에러 원천 차단 (concat 사용)
        import pandas as pd
        new_row_df = pd.DataFrame([new_row])
        updated_data = pd.concat([existing_data, new_row_df], ignore_index=True)
        
        # 🚀 수정된 데이터를 구글 시트1에 업데이트
        conn.update(worksheet=0, data=updated_data)
        return True
        
    except Exception as e:
        st.error(f"❌ 구글 커넥션 데이터 전송 중 예외 에러 발생: {str(e)}")
        return False


# 4. 🛡️ [고안정성 네이티브 분기점 통제부]
query_params = st.query_params

if query_params.get("submit_lead") == "true" and query_params.get("email"):
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    with st.spinner("🚀 거북목 AI 공유 시트로 리드를 안전하게 이관 중..."):
        success = append_to_gsheets_connection(lead_email, lead_target)
        
        if success:
            st.balloons()
            st.success(f"🎉 성공: {lead_email} 명단이 구글 시트1에 통합 보관되었습니다!")
            st.info(f"📋 **InfraPulse 관제탑 접수 정보**\n- **신청 계정:** {lead_email}\n- **우선 관제 타깃:** {lead_target}")
            
            def reset_to_main():
                st.query_params.clear()
                st.rerun()
            
            st.button("🌐 글로벌 인프라 관제탑 화면으로 돌아가기", on_click=reset_to_main, type="primary")
            st.stop()


# 5. Streamlit 상단 메뉴 및 불필요한 백그라운드 여백 제거 CSS
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


# 6. HTML 파일 로드 및 자바스크립트 브릿지 스크립트 강제 주입
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
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

    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);

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

    components.html(html_code, height=950, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
