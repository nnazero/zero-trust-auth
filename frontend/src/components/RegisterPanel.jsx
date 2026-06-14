import { useState } from "react";
import axios from "axios";
import styles from "./RegisterPanel.module.css";

const BASE_URL = "http://127.0.0.1:8002";

export default function RegisterPanel() {
  const [userId, setUserId] = useState("user1");
  const [trustedIp, setTrustedIp] = useState("127.0.0.1");
  const [agentRequired, setAgentRequired] = useState(true);
  const [status, setStatus] = useState("idle");
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg }]);
  };

  const handleRegister = async () => {
    setStatus("loading");
    setLogs([]);

    try {
      addLog(`계정 생성 요청: ${userId}`);

      const res = await axios.post(`${BASE_URL}/register`, {
        user_id: userId,
        public_key: "",
        trusted_ip: trustedIp,
        agent_required: agentRequired,
      });

      addLog(res.data.message);
      addLog(`기기 프로필 등록 - IP: ${trustedIp}, 에이전트 필수: ${agentRequired ? "예" : "아니오"}`);
      setStatus("success");
    } catch (err) {
      const msg = err.response?.data?.detail || "알 수 없는 오류";
      addLog(`실패: ${msg}`);
      setStatus("fail");
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>계정 생성 (기기 등록)</h2>
      <p className={styles.subtitle}>최초 로그인 시 사용할 기기를 등록합니다</p>

      <input
        className={styles.input}
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        placeholder="User ID"
      />

      <input
        className={styles.input}
        value={trustedIp}
        onChange={(e) => setTrustedIp(e.target.value)}
        placeholder="신뢰 IP (예: 127.0.0.1)"
      />

      <label className={styles.checkboxRow}>
        <input
          type="checkbox"
          checked={agentRequired}
          onChange={(e) => setAgentRequired(e.target.checked)}
        />
        보안 에이전트 필수
      </label>

      <button
        className={`${styles.button} ${status === "loading" ? styles.buttonLoading : ""}`}
        onClick={handleRegister}
        disabled={status === "loading"}
      >
        {status === "loading" ? "등록 중..." : "계정 생성"}
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