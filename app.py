import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime

# 🚨 구글 시트 연동을 위한 라이브러리 (gspread가 없다면 requirements.txt에 추가 필요)
try:
    import gspread
except ImportError:
    st.error("❌ 'gspread' 라이브러리가 누락되었습니다. requirements.txt에 gspread를 추가해 주세요, 형님.")

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


# 2. 📊 구글 시트(거북목 AI 시트1 공유)에 리드를 추가하는 함수
def append_to_google_sheet(email, dc_name="미지정"):
    # 거북목 AI에서 쓰던 세팅값(gspread_credentials 혹은 secrets 구조)이 있는지 검증
    if "gspread_credentials" not in st.secrets:
        st.error("❌ Streamlit Secrets에 구글 시트 인증 정보('gspread_credentials')가 설정되지 않았습니다.")
        return False
        
    try:
        # 거북목 AI에서 인증하던 방식 그대로 서비스 계정 활성화
        credentials = st.secrets["gspread_credentials"]
        gc = gspread.service_account_from_dict(credentials)
        
        # 💡 [필수 수정 구역] 거북목 AI에서 사용 중인 '구글 시트 파일 이름'을 정확히 적어주세요.
        # 예: "거북목_AI_리드_수집_시트"
        sheet_name = "시트1" 
        
        sh = gc.open(sheet_name)
        worksheet = sh.sheet1  # '시트1' 지정
        
        # 현재 시간 기록 (한국 시간 기준 포맷팅)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 📝 기존 데이터 아랫줄에 추가할 레코드 배열 구성 
        # [시간, 이메일, 서비스명, 관심인프라] 형태로 들어가며, 기존 컬럼 수에 맞춰 유연하게 쌓입니다.
        row_data = [current_time, email, "InfraPulse", dc_name]
        worksheet.append_row(row_data)
        
        return True
    except Exception as e:
        st.error(f"❌ 구글 시트 데이터 전송 중 예외 에러 발생: {str(e)}")
        return False


# 3. 🛡️ [고안정성 네이티브 분기점 통제부]
query_params = st.query_params

if query_params.get("submit_lead") == "true" and query_params.get("email"):
    lead_email = query_params.get("email")
    lead_target = query_params.get("target", "일반 메인 대기")
    
    st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
    with st.spinner("🚀 거북목 AI 공유 시트로 리드를 안전하게 이관 중..."):
        success = append_to_google_sheet(lead_email, lead_target)
        
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
