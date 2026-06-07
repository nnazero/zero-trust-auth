from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from pydantic import BaseModel
import os, base64, json

app = FastAPI()

# React 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 DB (메모리) - user_id: 공개키
user_db = {}
# 임시 챌린지 저장소
challenge_store = {}

class RegisterRequest(BaseModel):
    user_id: str
    public_key: str  # PEM 형식

class AuthRequest(BaseModel):
    user_id: str
    signature: str  # base64 인코딩된 서명값

# 1. 사용자 등록 (공개키 저장)
@app.post("/register")
def register(req: RegisterRequest):
    user_db[req.user_id] = req.public_key
    return {"message": f"{req.user_id} 등록 완료"}

# 2. 챌린지 요청 (로그인 1단계)
@app.get("/challenge/{user_id}")
def get_challenge(user_id: str):
    if user_id not in user_db:
        raise HTTPException(status_code=404, detail="유저 없음")
    challenge = base64.b64encode(os.urandom(32)).decode()
    challenge_store[user_id] = challenge
    return {"challenge": challenge}

# 3. 서명 검증 (로그인 2단계)
@app.post("/verify")
def verify(req: AuthRequest):
    if req.user_id not in user_db:
        raise HTTPException(status_code=404, detail="유저 없음")
    
    challenge = challenge_store.get(req.user_id)
    if not challenge:
        raise HTTPException(status_code=400, detail="챌린지 없음, 먼저 /challenge 호출")
    
    try:
        public_key = serialization.load_pem_public_key(
            user_db[req.user_id].encode()
        )
        signature_bytes = base64.b64decode(req.signature)
        public_key.verify(signature_bytes, challenge.encode(), ec.ECDSA(hashes.SHA256()))
        del challenge_store[req.user_id]  # 사용한 챌린지 삭제
        return {"message": "인증 성공 ✅", "session_token": base64.b64encode(os.urandom(16)).decode()}
    except Exception:
        raise HTTPException(status_code=401, detail="서명 검증 실패 ❌")

@app.get("/")
def root():
    return {"message": "Zero Trust Auth Server 🚀"}