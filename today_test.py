import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from agent.main import process_and_update

# 오늘자 신규 3개 - 네 data.json 포맷에 맞게 변환 완료
today_3 = [
  {
    "name": "Bitdeer AI A202 AI Cloud Facility",
    "lat": 1.4927,
    "lng": 103.7414,
    "type": "AIDC",
    "load": "65.1 MW",
    "source": "10-year data center services agreement, Johor Bahru Malaysia Campus, NVIDIA Cloud Partner",
    "status": "planned",
    "carbon": "mid",
    "desc": "Bitdeer AI가 말레이시아 조호르바루 캠퍼스에 확보한 65.1MW 규모 AI 클라우드 데이터센터 A202. 기존 21.7MW A201과 같은 캠퍼스. 2027년 Q3 energization 예정. NVIDIA Cloud Partner 시설.",
    "architecture": "High-Density GPU AI Cloud Pod with NVIDIA Accelerated Computing"
  },
  {
    "name": "HyperVault Hyderabad AI Campus",
    "lat": 17.1012,
    "lng": 78.3930,
    "type": "AIDC",
    "load": "1000 MW",
    "source": "TCS subsidiary HyperVault 264-acre land secured, Telangana power grid",
    "status": "planned",
    "carbon": "low",
    "desc": "Tata Consultancy Services 자회사 HyperVault가 하이데라바드 남부 264에이커 부지에 조성하는 최대 1GW 규모 AI 데이터센터 캠퍼스. 최대 7000억 루피 투자, 단계별 구축. Amazon hyperscale 부지 인근.",
    "architecture": "Hyperscale AI Campus with High-Density GPU for Training & Inference"
  },
  {
    "name": "Firmus x OpenAI Malaysia AI Factory",
    "lat": 2.7456,
    "lng": 101.7072,
    "type": "AIDC",
    "load": "900 MW",
    "source": "Nvidia-backed Firmus contracted capacity, OpenAI anchor customer multi-year deal",
    "status": "planned",
    "carbon": "mid",
    "desc": "호주 Firmus가 말레이시아에 구축하는 2개 AI Factory 사이트에 OpenAI가 앵커 고객으로 컴퓨팅 용량을 확보. Firmus 전체 계약 용량 900MW 이상 돌파. Nvidia, Blackstone 등 투자.",
    "architecture": "Firmus AI Factory with Dedicated AI Compute for Frontier Models"
  }
]

added, updated = process_and_update(today_3)
print(f"\n결과: 신규 {added}개 추가, {updated}개 업데이트")
