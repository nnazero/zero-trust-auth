import requests
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

BASE_URL = "http://127.0.0.1:8000"
USER_ID = "user1"

# 1. 키 쌍 생성 (개인키 + 공개키)
print("🔑 키 쌍 생성 중...")
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# 공개키를 PEM 형식으로 변환
public_key_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# 2. 서버에 공개키 등록
print(f"📤 서버에 공개키 등록 중... (user_id: {USER_ID})")
res = requests.post(f"{BASE_URL}/register", json={
    "user_id": USER_ID,
    "public_key": public_key_pem
})
print(f"✅ 등록 완료: {res.json()['message']}")

# 3. 챌린지 요청
print("📩 챌린지 요청 중...")
res = requests.get(f"{BASE_URL}/challenge/{USER_ID}")
challenge = res.json()["challenge"]
print(f"📩 챌린지 수신: {challenge[:20]}...")

# 4. 개인키로 챌린지 서명
print("✍️  서명 중...")
signature = private_key.sign(
    challenge.encode(),
    ec.ECDSA(hashes.SHA256())
)
signature_b64 = base64.b64encode(signature).decode()

# 5. 서명값 서버에 전송 (검증 요청)
print("🔐 서버에 검증 요청 중...")
res = requests.post(f"{BASE_URL}/verify", json={
    "user_id": USER_ID,
    "signature": signature_b64
})

result = res.json()
if res.status_code == 200:
    print(f"🎉 인증 성공! 세션 토큰: {result['session_token']}")
else:
    print(f"❌ 인증 실패: {result['detail']}")