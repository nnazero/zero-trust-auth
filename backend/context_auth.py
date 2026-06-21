from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, base64
from pqc.sign import dilithium2 as pqc_sign
from backend.database import SessionLocal, User, DeviceProfile

app = FastAPI(title="Zero Trust Context Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

challenge_store = {}
key_store = {}
session_store = {}
vault_store = {}

class RegisterRequest(BaseModel):
    user_id: str
    public_key: str
    trusted_ip: str   
    agent_required: bool = True  

class SignRequest(BaseModel):
    user_id: str
    challenge: str

class AuthRequest(BaseModel):
    user_id: str
    signature: str
    # 이중 잠금: 기기 상태 추가
    is_agent_safe: bool
    client_ip: str

class VaultStoreRequest(BaseModel):
    user_id: str
    session_token: str
    ciphertext: str 
    signature: str   

class LogoutRequest(BaseModel):
    user_id: str
    session_token: str

# 1. 사용자 등록
@app.post("/register")
def register(req: RegisterRequest):
    public_key, secret_key = pqc_sign.keypair()
    key_store[req.user_id] = secret_key

    db = SessionLocal()
    try:
        # 기존 계정 덮어쓰기
        db.query(User).filter(User.user_id == req.user_id).delete()
        db.query(DeviceProfile).filter(DeviceProfile.user_id == req.user_id).delete()

        db.add(User(
            user_id=req.user_id,
            public_key=base64.b64encode(public_key).decode()
        ))
        db.add(DeviceProfile(
            user_id=req.user_id,
            trusted_ip=req.trusted_ip,
            agent_required=req.agent_required
        ))
        db.commit()
    finally:
        db.close()

    return {"message": f"{req.user_id} 등록 완료 (기기 프로필 저장됨)"}


# 2. 챌린지 발급
@app.get("/challenge/{user_id}")
def get_challenge(user_id: str):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()
    db.close()

    if not user:
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
def check_context(user_id: str, is_agent_safe: bool, client_ip: str):
    db = SessionLocal()
    profile = db.query(DeviceProfile).filter(DeviceProfile.user_id == user_id).first()
    db.close()

    if not profile:
        raise HTTPException(status_code=404, detail="기기 프로필 없음")

    # 잠금 1: 보안 에이전트 요구사항 확인
    if profile.agent_required and not is_agent_safe:
        raise HTTPException(
            status_code=403,
            detail="이중 잠금 실패: 보안 에이전트가 실행중이지 않습니다"
        )

    # 잠금 2: 등록된 IP와 일치 여부 확인
    if client_ip != profile.trusted_ip:
        raise HTTPException(
            status_code=403,
            detail=f"이중 잠금 실패: 등록된 기기가 아닙니다 (등록IP: {profile.trusted_ip}, 현재IP: {client_ip})"
        )

# 4. 서명 + 이중 잠금 검증
@app.post("/verify")
def verify(req: AuthRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == req.user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="유저 없음")

    challenge = challenge_store.get(req.user_id)
    if not challenge:
        raise HTTPException(status_code=400, detail="챌린지 없음")

    check_context(req.user_id, req.is_agent_safe, req.client_ip)

    try:
        public_key = base64.b64decode(user.public_key)
        signature = base64.b64decode(req.signature)

        pqc_sign.verify(signature, challenge.encode(), public_key)

        del challenge_store[req.user_id]

        session_token = base64.b64encode(os.urandom(16)).decode()
        session_store[session_token] = req.user_id

        return {
            "message": "인증 성공",
            "context_check": "이중 잠금 통과",
            "session_token": session_token
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="서명 검증 실패")

@app.get("/")
def root():
    return {"message": "Zero Trust Context Auth Server 🚀"}

# 5. 세션 유효성 확인
def check_session(user_id: str, session_token: str):
    if session_store.get(session_token) != user_id:
        raise HTTPException(status_code=401, detail="세션이 유효하지 않습니다")


# 6. Vault 저장
@app.post("/vault")
def store_vault(req: VaultStoreRequest):
    check_session(req.user_id, req.session_token)

    db = SessionLocal()
    user = db.query(User).filter(User.user_id == req.user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="유저 없음")

    try:
        public_key = base64.b64decode(user.public_key)
        signature = base64.b64decode(req.signature)
        pqc_sign.verify(signature, req.ciphertext.encode(), public_key)
    except Exception:
        raise HTTPException(status_code=401, detail="서명 검증 실패")

    vault_store[req.user_id] = req.ciphertext
    return {"message": "Vault 저장 완료 (메모리, DB 미사용)"}


# 7. Vault 조회
@app.get("/vault/{user_id}")
def get_vault(user_id: str, session_token: str):
    check_session(user_id, session_token)

    ciphertext = vault_store.get(user_id)
    if ciphertext is None:
        raise HTTPException(status_code=404, detail="저장된 Vault 없음")

    return {"ciphertext": ciphertext}

# 8. 로그아웃
@app.post("/logout")
def logout(req: LogoutRequest):
    check_session(req.user_id, req.session_token)

    session_store.pop(req.session_token, None)
    vault_store.pop(req.user_id, None)
    challenge_store.pop(req.user_id, None)

    return {"message": "로그아웃 완료, 메모리에서 삭제됨"}