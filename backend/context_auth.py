from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pqc.sign import dilithium2 as pqc_sign
import os, base64, psutil
from pqc.sign import dilithium2 as pqc_sign

app = FastAPI(title="Zero Trust Context Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 DB
user_db = {}
challenge_store = {}
key_store = {}  # user_id: secret_key (임시저장)

# 허용된 IP 대역 (로컬 테스트용)
ALLOWED_IP_PREFIXES = ["127.0.0.1", "192.168."]

# 필수 보안 에이전트 프로세스 이름 (가상)
REQUIRED_AGENT = "zero_trust_agent"

class RegisterRequest(BaseModel):
    user_id: str
    public_key: str

class SignRequest(BaseModel):
    user_id: str
    challenge: str

class AuthRequest(BaseModel):
    user_id: str
    signature: str
    # 이중 잠금: 기기 상태 추가
    is_agent_safe: bool
    client_ip: str

# 1. 사용자 등록
@app.post("/register")
def register(req: RegisterRequest):
    # PQC 키 쌍 생성
    public_key, secret_key = pqc_sign.keypair()
    
    # 공개키는 DB에, 개인키는 임시 저장
    user_db[req.user_id] = base64.b64encode(public_key).decode()
    key_store[req.user_id] = secret_key
    
    return {"message": f"{req.user_id} 등록 완료"}


# 2. 챌린지 발급
@app.get("/challenge/{user_id}")
def get_challenge(user_id: str):
    if user_id not in user_db:
        raise HTTPException(status_code=404, detail="유저 없음")
    challenge = base64.b64encode(os.urandom(32)).decode()
    challenge_store[user_id] = challenge
    return {"challenge": challenge}

@app.post("/sign")
def sign(req: SignRequest):
    if req.user_id not in key_store:
        raise HTTPException(status_code=404, detail="키 없음, 먼저 /register 호출")
    
    secret_key = key_store[req.user_id]
    signature = pqc_sign.sign(req.challenge.encode(), secret_key)
    return {"signature": base64.b64encode(signature).decode()}


# 3. 이중 잠금 검증
def check_context(is_agent_safe: bool, client_ip: str):
    # 잠금 1: 보안 에이전트 상태 확인
    if not is_agent_safe:
        raise HTTPException(
            status_code=403,
            detail="❌ 이중 잠금 실패: 보안 에이전트가 실행중이지 않습니다"
        )

    # 잠금 2: IP 대역 확인
    if not any(client_ip.startswith(prefix) for prefix in ALLOWED_IP_PREFIXES):
        raise HTTPException(
            status_code=403,
            detail=f"❌ 이중 잠금 실패: 허용되지 않은 IP입니다 ({client_ip})"
        )

# 4. 서명 + 이중 잠금 검증
@app.post("/verify")
def verify(req: AuthRequest):
    if req.user_id not in user_db:
        raise HTTPException(status_code=404, detail="유저 없음")

    challenge = challenge_store.get(req.user_id)
    if not challenge:
        raise HTTPException(status_code=400, detail="챌린지 없음")

    # 이중 잠금 먼저 체크
    check_context(req.is_agent_safe, req.client_ip)

    try:
        public_key = base64.b64decode(user_db[req.user_id])
        signature = base64.b64decode(req.signature)

        # PQC 서명 검증
        pqc_sign.verify(signature, challenge.encode(), public_key)

        del challenge_store[req.user_id]
        return {
            "message": "인증 성공 ✅",
            "context_check": "이중 잠금 통과 🔒",
            "session_token": base64.b64encode(os.urandom(16)).decode()
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="서명 검증 실패 ❌")

@app.get("/")
def root():
    return {"message": "Zero Trust Context Auth Server 🚀"}