import hashlib
import base64
import json
from cryptography.fernet import Fernet
from pqc.sign import dilithium2 as pqc_sign

public_key, secret_key = pqc_sign.keypair()

hash_digest = hashlib.sha256(secret_key).digest()
fernet_key = base64.urlsafe_b64encode(hash_digest)
fernet = Fernet(fernet_key)

personal_data = {
    "name": "rose",
    "email": "user1@example.com",
    "phone": "010-1234-5678"
}

data_bytes = json.dumps(personal_data, ensure_ascii=False).encode()
encrypted = fernet.encrypt(data_bytes)

with open("backend/vault_user1.enc", "wb") as f:
    f.write(encrypted)

#결과화면
print("암호화 완료")
print(f"암호화된 데이터 크기: {len(encrypted)} bytes")

with open("backend/vault_user1.enc", "rb") as f:
    encrypted_loaded = f.read()

decrypted = fernet.decrypt(encrypted_loaded)
decrypted_data = json.loads(decrypted.decode())

print("복호화 결과:", decrypted_data)

print("\n공격자가 vault 파일을 탈취한 경우")
wrong_secret_key, _ = pqc_sign.keypair()
wrong_hash = hashlib.sha256(wrong_secret_key).digest()
wrong_fernet_key = base64.urlsafe_b64encode(wrong_hash)
wrong_fernet = Fernet(wrong_fernet_key)

try:
    wrong_fernet.decrypt(encrypted_loaded)
except Exception as e:
    print(f"복호화 실패: {type(e).__name__}")