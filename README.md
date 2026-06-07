# 🔐 Zero Trust Auth — 양자 내성 패스키 인증 시스템

> 기존 비밀번호·SMS 2차 인증의 한계를 넘어,  
> **양자 내성 암호(PQC) + 기기 무결성 검증**으로 구현한 차세대 Zero Trust 인증 시스템

---

## 💡 왜 만들었나요?

| 기존 방식 | 취약점 |
|-----------|--------|
| 비밀번호 | 서버 DB 탈취 시 전체 계정 노출 |
| SMS 2차 인증 | AiTM 피싱 공격으로 우회 가능 |
| RSA/ECC 암호 | 양자 컴퓨터 등장 시 해독 가능 |

→ **서버는 공개키만 저장, 개인키는 절대 서버에 전송하지 않는 구조**로 설계

---

## 🏗️ 시스템 아키텍처

```
[사용자 기기]                                        [서버]
     |                                                  |
     |── 1. 로그인 요청 (user_id) ───────────────────>  |
     |                                                  |── Challenge(난수) 생성
     |<── 2. Challenge 전송 ──────────────────────────  |
     |                                                  |
     |── 개인키로 Challenge 서명                        |
     |── 기기 상태 수집 (is_agent_safe, IP 등)          |
     |                                                  |
     |── 3. 서명값 + 기기 상태(is_agent_safe) ────────> |
                                                        |── 1) 기기 무결성 상태 체크 (이중 잠금)
                                                        |── 2) PQC 공개키로 서명 검증
                                                        |── 성공 → 세션 발급
```

---

## 🗺️ 개발 로드맵

- [x] **Phase 1-1** — FastAPI 챌린지-응답 인증 서버 구현
- [ ] **Phase 1-2** — 양자 내성 암호(PQC) 키 쌍으로 교체
- [ ] **Phase 1-3** — 기기 무결성 컨텍스트 이중 잠금 추가
- [ ] **Phase 1-4** — React 실시간 모니터링 대시보드
- [ ] **Phase 1-5** — 동시성 부하 테스트 및 ECC vs PQC 연산 오버헤드 정량 분석
- [ ] **Phase 2** — 서버 DB 다이어트 + 자기주권형 분산 데이터 구조

---

## 🛠️ 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, uvicorn |
| 암호화 | cryptography (ECC) → ML-KEM / ML-DSA (NIST 표준 PQC 알고리즘 이식 예정) |
| Frontend | React (예정) |
| 인증 방식 | Passwordless Challenge-Response + 기기 무결성 이중 잠금 |

---

## 🚀 로컬 실행 방법

```bash
# 1. 가상환경 활성화
source venv/Scripts/activate

# 2. 서버 실행
uvicorn backend.main:app --reload

# 3. API 문서 확인
# http://127.0.0.1:8000/docs
```