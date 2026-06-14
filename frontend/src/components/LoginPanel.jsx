import { useState } from "react";
import axios from "axios";
import styles from "./LoginPanel.module.css";

const BASE_URL = "http://127.0.0.1:8002";

export default function LoginPanel({ onAuthResult }) {
  const [userId, setUserId] = useState("user1");
  const [clientIp, setClientIp] = useState("127.0.0.1");
  const [isAgentSafe, setIsAgentSafe] = useState(true);
  const [status, setStatus] = useState("idle");
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg }]);
  };

  const handleLogin = async () => {
    setStatus("loading");
    setLogs([]);

    try {
      addLog("🔑 키 쌍 생성 중...");

      // 1. 등록 (서버에서 PQC 키 쌍 생성)
      await axios.post(`${BASE_URL}/register`, {
        user_id: userId,
        public_key: "",
      });
      addLog("✅ 공개키 등록 완료");

      // 2. 챌린지 요청
      const challengeRes = await axios.get(`${BASE_URL}/challenge/${userId}`);
      const challenge = challengeRes.data.challenge;
      addLog(`📩 챌린지 수신: ${challenge.slice(0, 15)}...`);

      // 3. 서버에서 서명값 받아오기
      addLog("✍️ ML-DSA 서명 중...");
      const start = performance.now();
      const signRes = await axios.post(`${BASE_URL}/sign`, {
        user_id: userId,
        challenge: challenge,
      });
      const signature = signRes.data.signature;
      const elapsed = (performance.now() - start).toFixed(2);
      addLog(`✅ 서명 완료! 소요시간: ${elapsed}ms`);

      // 4. 기기 상태 수집
      addLog(`📡 기기 상태: IP=${clientIp}, 에이전트=${isAgentSafe ? "✅" : "❌"}`);

      // 5. 검증 요청
      addLog("🔐 서버 검증 요청 중...");
      const verifyRes = await axios.post(`${BASE_URL}/verify`, {
        user_id: userId,
        signature: signature,
        is_agent_safe: isAgentSafe,
        client_ip: clientIp,
      });

      addLog(`🎉 인증 성공! 소요시간: ${elapsed}ms`);
      addLog(`🔒 ${verifyRes.data.context_check}`);
      setStatus("success");
      onAuthResult({
        success: true,
        logs,
        elapsed,
        token: verifyRes.data.session_token,
      });
    } catch (err) {
      const msg = err.response?.data?.detail || "알 수 없는 오류";
      addLog(`❌ 실패: ${msg}`);
      setStatus("fail");
      onAuthResult({ success: false, logs });
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>🔐 Zero Trust 패스키 로그인</h2>
      <p className={styles.subtitle}>ML-DSA(Dilithium2) + 기기 무결성 이중 잠금</p>

      <input
        className={styles.input}
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        placeholder="User ID"
      />

      <input
        className={styles.input}
        value={clientIp}
        onChange={(e) => setClientIp(e.target.value)}
        placeholder="현재 IP"
      />

      <label className={styles.checkboxRow}>
        <input
          type="checkbox"
          checked={isAgentSafe}
          onChange={(e) => setIsAgentSafe(e.target.checked)}
        />
        보안 에이전트 실행중
      </label>

      <button
        className={`${styles.button} ${status === "loading" ? styles.buttonLoading : ""}`}
        onClick={handleLogin}
        disabled={status === "loading"}
      >
        {status === "loading" ? "인증 중..." : "🚀 패스키 로그인"}
      </button>

      <div className={styles.logBox}>
        {logs.map((log, i) => (
          <div key={i} className={styles.logLine}>
            <span className={styles.time}>{log.time}</span> {log.msg}
          </div>
        ))}
      </div>
    </div>
  );
}