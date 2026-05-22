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
        .block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem;}
        iframe {display: block; width: 100%; border: none;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 📊 1) 글로벌 총합 메트릭 (Global Overview Widgets)
st.markdown("### 📊 Global AI Infra Real-time Overview")
col1, col2, col3 = st.columns(3)
col1.metric(label="⚡ Total Global IT Power Capacity", value="14.2 GW", delta="+.8 GW (MoM)")
col2.metric(label="🤖 Est. Global AI Compute Power", value="245.8 EFLOPS", delta="+12.4% (QoQ)")
col3.metric(label="💡 Avg. Compute-to-Power Efficiency", value="18.4 PFLOPS/MW", delta="Optimal", delta_color="normal")
st.markdown("---")

# 5. HTML 파일 로드 및 고안정성 주입 스크립트 빌드
html_path = os.path.join(os.path.dirname(__file__), "index.html")

if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    
    # 🌟 [완전 개조] 2) 지도 팝업 컨텐츠 직접 가로채기 및 사양 강제 인젝션 시스템
    # 특정 Form ID에 의존하지 않고, 지도 위에 생성되는 모든 팝업 컨테이너 및 사이드바 내의 
    # '효율성:' 텍스트 영역을 직접 추적하여 그 바로 아래에 Primary Architecture 레이어를 강제로 끼워 넣습니다.
    tooltip_extension_script = """
    <script>
    function injectArchitectureSpec() {
        // 1. Leaflet 기본 팝업 및 index.html 내 정보 표시 가능성이 높은 클래스/요소 동시 타겟팅
        const popupTargets = document.querySelectorAll('.leaflet-popup-content, .popup-content, #sidebar, .info-panel, document');
        
        popupTargets.forEach(container => {
            if (!container) return;
            
            // 효율성 텍스트가 존재하는지 확인하고, 이미 아키텍처 정보가 주입되었는지 체크 (중복 주입 방지)
            if (container.innerHTML.includes('효율성:') && !container.innerHTML.includes('Primary Architecture:')) {
                
                // 기존 HTML 구조를 유지하면서 '효율성:' 문장이 끝나는 줄 아래에 사양 텍스트 강제 결합
                // 텍스트 형태와 HTML 형태 둘 다 대응할 수 있도록 처리합니다.
                let currentHtml = container.innerHTML;
                
                // 효율성 표시 부분 뒤에 자연스럽게 삽입하기 위한 치환 로직
                const targetPattern = /(효율성:\\s*\\d+(?:\\.\\d+)?\\s*PFLOPS\\/MW)/i;
                if (targetPattern.test(currentHtml)) {
                    container.innerHTML = currentHtml.replace(targetPattern, `$1<br>• <b>Primary Architecture:</b> NVIDIA H100 / Blackwell Mixed`);
                } else {
                    // 대체 가이드 패턴 (PFLOPS/MW단어 뒤에 매핑이 안 되었을 경우 하단에 박음)
                    container.innerHTML += `<div style="margin-top: 2px;">• <b>Primary Architecture:</b> NVIDIA H100 / Blackwell Mixed</div>`;
                }
            }
        });
    }

    // DOM 변화를 상시 감시하여 팝업이 뜨는 순간 즉시 낚아챔
    const popupObserver = new MutationObserver((mutations) => {
        for (let mutation of mutations) {
            if (mutation.addedNodes.length) {
                injectArchitectureSpec();
            }
        }
    });

    popupObserver.observe(document.body, { childList: true, subtree: true });

    // 백업 인터랙션 트리거 (클릭/마우스 오버 시 동시 재검증 수행)
    window.addEventListener('click', function() {
        setTimeout(injectArchitectureSpec, 30);
        setTimeout(injectArchitectureSpec, 150);
    });
    window.addEventListener('mouseover', function(e) {
        if(e.target.tagName === 'path' || e.target.classList.contains('leaflet-marker-icon') || e.target.closest('.leaflet-popup')) {
            setTimeout(injectArchitectureSpec, 30);
        }
    });
    </script>
    """

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

    // 폼 제출 리스너 안정적 바인딩 시스템
    function bindFormSubmit() {
        const form = document.getElementById('proWaitlistForm');
        if (form) {
            form.removeEventListener('submit', handleFakeDoorSubmit); // 중복 방지
            form.addEventListener('submit', handleFakeDoorSubmit);
        }
    }

    // 팝업이 새로 뜰 때마다 폼 핸들러도 같이 결합되도록 감시망 연동
    window.addEventListener('click', function() {
        setTimeout(bindFormSubmit, 100);
    });

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
    
    # 툴팁 확장 스크립트와 기본 브릿지 스크립트를 body 종료 태그 직전에 함께 주입합니다.
    combined_scripts = f"{tooltip_extension_script}{bridge_script}</body>"
    html_code = html_code.replace("</body>", combined_scripts)

    # 6. 컴포넌트 실행 (상단 메트릭 아래에 조화롭게 안착)
    components.html(html_code, height=900, scrolling=True)

else:
    st.error("저장소 루트 디렉터리에서 index.html 파일을 찾을 수 없습니다, 형님.")
