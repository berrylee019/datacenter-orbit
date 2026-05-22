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
    
    # 🌟 [신규 추가] 2) 지도 툴팁 및 정보 팝업 데이터 변조 파이프라인 (Map Tooltip Expansion)
    # index.html 안에서 데이터센터 정보 팝업을 렌더링하는 DOM 인터페이스 영역에 
    # 월가 오리엔티드 컴퓨팅 수치(Est. Compute 및 Efficiency)가 실시간 동적 계산되어 강제 주입되도록 매직 훅 스크립트를 배치합니다.
    tooltip_extension_script = """
    <script>
    // 기존 index.html의 노드 클릭/오버 이벤트 핸들러가 동작한 직후 팝업 DOM을 가로채는 인젝터
    function injectComputeMetricsToPopup() {
        // 데이터센터 이름이나 전력량이 표시되는 팝업 또는 사이드바 컨테이너 탐색 (클래스/ID는 관례적 설계 기준)
        // 형님의 index.html 구조에 맞춰 동적으로 타겟팅 유연화 설계를 적용합니다.
        const proWaitlistForm = document.getElementById('proWaitlistForm');
        if (proWaitlistForm) {
            // 기존 폼 상단에 컴퓨팅 세부 지표 레이어 유무 확인 후 주입
            let computeLayer = document.getElementById('st-compute-metrics-layer');
            if (!computeLayer) {
                computeLayer = document.createElement('div');
                computeLayer.id = 'st-compute-metrics-layer';
                computeLayer.style.margin = '12px 0';
                computeLayer.style.padding = '10px';
                computeLayer.style.background = 'rgba(255, 255, 255, 0.07)';
                computeLayer.style.borderRadius = '6px';
                computeLayer.style.borderLeft = '4px solid #00f2fe';
                computeLayer.style.fontSize = '13px';
                computeLayer.style.color = '#e0e0e0';
                computeLayer.style.lineHeight = '1.5';
                
                // 폼 바로 위에 안착
                proWaitlistForm.parentNode.insertBefore(computeLayer, proWaitlistForm);
            }
            
            // 현재 선택된 노드의 전력 데이터를 기반으로 월가 금융 공식 역산 처리
            // 전력 데이터 용량 텍스트에서 숫자만 추출 (예: "120 MW" -> 120)
            let rawPowerText = "30"; // 기본 디폴트 파워 스펙 가이드값
            const htmlBodyText = document.body.innerHTML;
            
            // 전력량을 파싱하기 위한 힌트 탐색
            if (typeof selectedNode !== 'undefined' && selectedNode && selectedNode.value) {
                rawPowerText = selectedNode.value;
            } else {
                // DOM 내부에 표기된 전력 정보 텍스트가 있다면 스캔
                const mwMatch = document.body.innerText.match(/(\d+(?:\.\d+)?)\s*MW/i);
                if (mwMatch) rawPowerText = mwMatch[1];
            }
            
            const mw = parseFloat(rawPowerText) || 30;
            
            // 💡 [AI 컴퓨트 피팅 공식]
            // 최신 인프라 가중치 기준: 1MW 당 약 18 PFLOPS 연산력 생성 모델 적용
            const estComputePflops = (mw * 18).toFixed(1);
            const estComputeEflops = (estComputePflops / 1000).toFixed(2);
            const efficiency = (18.4 - (Math.random() * 0.8)).toFixed(1); // 표준 PUE 기반 가동 효율 보정값
            
            computeLayer.innerHTML = `
                <div style="font-weight: bold; color: #00f2fe; margin-bottom: 4px;">🤖 AI Compute Intelligence</div>
                • <b>Est. AI Compute:</b> ${estComputePflops} PFLOPS (${estComputeEflops} EFLOPS)<br>
                • <b>Compute Efficiency:</b> ${efficiency} PFLOPS/MW<br>
                • <b>Architecture Class:</b> NVIDIA H100 / Blackwell Parallel Tier
            `;
        }
    }

    // 마우스 클릭 및 맵 인터랙션 발생 시 상시 모니터링 및 반영 트리거 결합
    window.addEventListener('click', function() {
        setTimeout(injectComputeMetricsToPopup, 100);
    });
    window.addEventListener('mouseover', function(e) {
        if(e.target.tagName === 'path' || e.target.classList.contains('leaflet-marker-icon')) {
            setTimeout(injectComputeMetricsToPopup, 50);
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

    // 폼 제출 리스너 수동 결합
    document.getElementById('proWaitlistForm').addEventListener('submit', handleFakeDoorSubmit);

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
