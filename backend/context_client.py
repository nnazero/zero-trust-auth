import requests
import base64
import socket
from pqc.sign import dilithium2 as pqc_sign

BASE_URL = "http://127.0.0.1:8002"
USER_ID = "nayoung"

# ===============================================
# 기기 상태 수집 (이중 잠금용)
# ===============================================
def collect_device_context():
    # 현재 기기 IP 수집
    client_ip = socket.gethostbyname(socket.gethostname())
    
    # 가상 보안 에이전트 실행 여부 확인
    # 실제로는 psutil로 프로세스 확인하지만
    # 여기서는 시뮬레이션으로 True 반환
    is_agent_safe = True  # 정상 상태 시뮬레이션

    print(f"📡 기기 상태 수집 완료")
    print(f"   IP: {client_ip}")
    print(f"   보안 에이전트: {'✅ 실행중' if is_agent_safe else '❌ 중지됨'}")

    return is_agent_safe, client_ip

# ===============================================
# 1단계: PQC 키 쌍 생성
# ===============================================
print("🔑 ML-DSA 키 쌍 생성 중...")
public_key, secret_key = pqc_sign.keypair()
public_key_b64 = base64.b64encode(public_key).decode()
print("✅ 키 생성 완료!")

# ===============================================
# 2단계: 서버에 공개키 등록
# ===============================================
print(f"\n📤 공개키 등록 중... (user_id: {USER_ID})")
res = requests.post(f"{BASE_URL}/register", json={
    "user_id": USER_ID,
    "public_key": public_key_b64
})
print(f"✅ {res.json()['message']}")

# ===============================================
# 3단계: 챌린지 요청
# ===============================================
print("\n📩 챌린지 요청 중...")
res = requests.get(f"{BASE_URL}/challenge/{USER_ID}")
challenge = res.json()["challenge"]
print(f"📩 챌린지 수신: {challenge[:20]}...")

# ===============================================
# 4단계: 서명 + 기기 상태 수집
# ===============================================
print("\n✍️  서명 중...")
signature = pqc_sign.sign(challenge.encode(), secret_key)
signature_b64 = base64.b64encode(signature).decode()
print("✅ 서명 완료!")

print("\n🔍 기기 상태 수집 중...")
is_agent_safe, client_ip = collect_device_context()

# ===============================================
# 5단계: 서명 + 기기 상태 전송 (이중 잠금)
# ===============================================
print("\n🔐 서버에 검증 요청 중... (서명 + 기기 상태)")
res = requests.post(f"{BASE_URL}/verify", json={
    "user_id": USER_ID,
    "signature": signature_b64,
    "is_agent_safe": is_agent_safe,
    "client_ip": client_ip
})

result = res.json()
if res.status_code == 200:
    print(f"\n🎉 인증 성공!")
    print(f"   {result['context_check']}")
    print(f"   세션 토큰: {result['session_token']}")
else:
    print(f"\n❌ 인증 실패: {result['detail']}")

# ===============================================
# 6단계: 이중 잠금 실패 시뮬레이션
# ===============================================
print("\n" + "="*50)
print("🧪 [테스트] 보안 에이전트 꺼진 상태로 로그인 시도")
print("="*50)

# 새 챌린지 요청
res = requests.get(f"{BASE_URL}/challenge/{USER_ID}")
challenge = res.json()["challenge"]
signature = pqc_sign.sign(challenge.encode(), secret_key)
signature_b64 = base64.b64encode(signature).decode()

# 에이전트 꺼진 상태 시뮬레이션
res = requests.post(f"{BASE_URL}/verify", json={
    "user_id": USER_ID,
    "signature": signature_b64,
    "is_agent_safe": False,  # ← 에이전트 꺼짐
    "client_ip": client_ip
})

result = res.json()
print(f"결과: {result['detail']}")