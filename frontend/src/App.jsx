import { useState } from "react";
import RegisterPanel from "./components/RegisterPanel";
import LoginPanel from "./components/LoginPanel";
import VaultPanel from "./components/VaultPanel";
import Dashboard from "./components/Dashboard";
import styles from "./App.module.css";

export default function App() {
  const [authResult, setAuthResult] = useState(null);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🛡️ Zero Trust Auth</h1>
        <p>양자 내성 암호(ML-DSA) + 기기 컨텍스트 이중 잠금 + 데이터 보호 계층</p>
      </div>

      <div className={styles.panels}>
        <RegisterPanel />
        <LoginPanel onAuthResult={setAuthResult} />
        <VaultPanel />
        <Dashboard result={authResult} />
      </div>
    </div>
  );
}