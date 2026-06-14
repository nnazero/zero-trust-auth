import requests
import base64
import time
from pqc.sign import dilithium2 as pqc_sign

BASE_URL = "http://127.0.0.1:8001"  # pqcauth.py는 8001 포트로 실행할 거예요
USER_ID = "user1"

# ===============================================
# 1단계: PQC 키 쌍 생성
# ===============================================
print("🔑 ML-DSA (Dilithium2) 키 쌍 생성 중...")

start = time.time()
public_key, secret_key = pqc_sign.keypair()
end = time.time()

print(f"✅ 키 생성 완료! 소요시간: {(end - start) * 1000:.2f}ms")
print(f"   공개키 크기: {len(public_key)} bytes")
print(f"   개인키 크기: {len(secret_key)} bytes")

# base64로 인코딩 (서버 전송용)
public_key_b64 = base64.b64encode(public_key).decode()

# ===============================================
# 2단계: 서버에 공개키 등록
# ===============================================
print(f"\n📤 서버에 공개키 등록 중... (user_id: {USER_ID})")
res = requests.post(f"{BASE_URL}/register", json={
    "user_id": USER_ID,
    "public_key": public_key_b64
})
print(f"✅ {res.json()['message']} | 알고리즘: {res.json()['algorithm']}")

# ===============================================
# 3단계: 챌린지 요청
# ===============================================
print("\n📩 챌린지 요청 중...")
res = requests.get(f"{BASE_URL}/challenge/{USER_ID}")
challenge = res.json()["challenge"]
print(f"📩 챌린지 수신: {challenge[:20]}...")

# ===============================================
# 4단계: PQC 개인키로 서명
# ===============================================
print("\n✍️  ML-DSA로 서명 중...")

start = time.time()
signature = pqc_sign.sign(challenge.encode(), secret_key)
end = time.time()

print(f"✅ 서명 완료! 소요시간: {(end - start) * 1000:.2f}ms")
print(f"   서명 크기: {len(signature)} bytes")

signature_b64 = base64.b64encode(signature).decode()

# ===============================================
# 5단계: 검증 요청
# ===============================================
print("\n🔐 서버에 검증 요청 중...")
res = requests.post(f"{BASE_URL}/verify", json={
    "user_id": USER_ID,
    "signature": signature_b64
})

result = res.json()
if res.status_code == 200:
    print(f"🎉 인증 성공! | 알고리즘: {result['algorithm']}")
    print(f"   세션 토큰: {result['session_token']}")
else:
    print(f"❌ 인증 실패: {result['detail']}")