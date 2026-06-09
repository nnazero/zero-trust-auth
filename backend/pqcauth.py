from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pqc.sign import dilithium2 as pqc_sign
import os, base64

app = FastAPI(title="Zero Trust PQC Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 DB
user_db = {}
challenge_store = {}

class RegisterRequest(BaseModel):
    user_id: str
    public_key: str  # base64 인코딩된 PQC 공개키

class AuthRequest(BaseModel):
    user_id: str
    signature: str   # base64 인코딩된 PQC 서명값

# 1. 사용자 등록
@app.post("/register")
def register(req: RegisterRequest):
    user_db[req.user_id] = req.public_key
    return {"message": f"{req.user_id} 등록 완료", "algorithm": "ML-DSA (Dilithium2)"}

# 2. 챌린지 발급
@app.get("/challenge/{user_id}")
def get_challenge(user_id: str):
    if user_id not in user_db:
        raise HTTPException(status_code=404, detail="유저 없음")
    challenge = base64.b64encode(os.urandom(32)).decode()
    challenge_store[user_id] = challenge
    return {"challenge": challenge}

# 3. 서명 검증
@app.post("/verify")
def verify(req: AuthRequest):
    if req.user_id not in user_db:
        raise HTTPException(status_code=404, detail="유저 없음")

    challenge = challenge_store.get(req.user_id)
    if not challenge:
        raise HTTPException(status_code=400, detail="챌린지 없음")

    try:
        public_key = base64.b64decode(user_db[req.user_id])
        signature = base64.b64decode(req.signature)

        # PQC 서명 검증
        pqc_sign.verify(signature, challenge.encode(), public_key)

        del challenge_store[req.user_id]
        return {
            "message": "인증 성공 ✅",
            "algorithm": "ML-DSA (Dilithium2)",
            "session_token": base64.b64encode(os.urandom(16)).decode()
        }
    except Exception:
        raise HTTPException(status_code=401, detail="서명 검증 실패 ❌")

@app.get("/")
def root():
    return {"message": "Zero Trust PQC Auth Server 🚀", "algorithm": "ML-DSA (Dilithium2)"}