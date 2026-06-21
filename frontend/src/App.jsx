import { useState } from "react";
import axios from "axios";
import RegisterPanel from "./components/RegisterPanel";
import LoginPanel from "./components/LoginPanel";
import VaultPanel from "./components/VaultPanel";
import Dashboard from "./components/Dashboard";
import styles from "./App.module.css";

const BASE_URL = "http://127.0.0.1:8002";

export default function App() {
  const [authResult, setAuthResult] = useState(null);
  const [session, setSession] = useState(null); // { userId, token }

  const handleAuthResult = (result) => {
    setAuthResult(result);
    if (result.success) {
      setSession({ userId: result.userId, token: result.token });
    }
  };

  const handleLogout = async () => {
    if (!session) return;

    try {
      await axios.post(`${BASE_URL}/logout`, {
        user_id: session.userId,
        session_token: session.token,
      });
    } catch {
      // 서버 응답과 무관하게 클라이언트 세션은 항상 정리
    } finally {
      setSession(null);
      setAuthResult(null);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🛡️ Zero Trust Auth</h1>
        <p>양자 내성 암호(ML-DSA) + 기기 컨텍스트 이중 잠금 + 데이터 보호 계층</p>
        {session && (
          <button className={styles.logoutButton} onClick={handleLogout}>
            로그아웃 ({session.userId})
          </button>
        )}
      </div>

      <div className={styles.panels}>
        <RegisterPanel />
        <LoginPanel onAuthResult={handleAuthResult} />
        <VaultPanel session={session} />
        <Dashboard result={authResult} />
      </div>
    </div>
  );
}