import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime

# 🚨 스트림릿 공식 구글 시트 커넥션 라이브러리 탑재
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("❌ 'st-gsheets-connection' 라이브러리가 누락되었습니다. requirements.txt에 추가해 주세요, 형님.")

# 1. Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="InfraPulse - 글로벌 데이터센터 & 전력 인프라 관제탑",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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


# 2. 📊 st.connection 기반 구글 시트 데이터 적재 함수
def append_to_gsheets_connection(email, dc_name="미지정"):
    # 형님이 복사 붙여넣기 하실 [connections.gsheets] 섹션이 잘 들어왔는지 검증
    if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
        st.error("❌ Streamlit Secrets에 [connections.gsheets] 설정 블록이 누락되었습니다, 형님.")
        return False
        
    try:
        # 💡 거북목 AI 설정 정보 연동 및 시트 커넥션 생성
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 💡 [필수 확인] 거북목 AI가 사용 중인 구글 시트의 전체 데이터를 판다스로 먼저 읽어옵니다.
        # 시트 내용이 비어있거나 읽을 때 에러 방지를 위해 기본 시트1(worksheet=0)을 타깃팅합니다.
        existing_data = conn.read(worksheet=0, ttl=0)
        
        # 현재 시간 기록 (한국 시간 기준)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 📝 새롭게 추가할 인프라펄스 리드 데이터 덩어리 구성
        # 거북목 AI 시트 컬럼 순서가 [시간, 이메일, ...] 형태라면 그대로 일치시켜 줍니다.
        new_row = {
            existing_data.columns[0]: current_time,
            existing_data.columns[1]: email,
            # 만약 거북목 AI 시트에 '서비스명'이나 '관심타깃' 컬럼이 아직 없다면 판다스가 자동으로 우측에 열을 확장해서 넣어줍니다.
            "서비스명": "InfraPulse",
            "관심 인프라 타깃": dc_name
        }
        
        # 기존 데이터프레임 하단에 새 행 추가
        updated_data = existing_data.append(new_row, ignore_index=True)
        
        # 🚀 수정된 전체 데이터셋을 구글 시트1에 덮어쓰기식으로 전송 (가장 확실한 네이티브 적재 방식)
        conn.update(worksheet=0, data=updated_data)
        return True
        
    except Exception as e:
        st.error(f"❌ 구글 커넥션 데이터 전송 중 예외 에러 발생: {str(e)}")
        return False


# 3. 🛡️ [고안정성 네이티브 분기점 통제부]
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
