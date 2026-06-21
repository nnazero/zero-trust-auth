import { useState } from "react";
import axios from "axios";
import styles from "./VaultPanel.module.css";

const BASE_URL = "http://127.0.0.1:8002";

export default function VaultPanel({ session }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [dek, setDek] = useState(null);
  const [dekDisplay, setDekDisplay] = useState("");
  const [encrypted, setEncrypted] = useState(null);
  const [decrypted, setDecrypted] = useState(null);
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), msg }]);
  };

  //DEK 생성 (브라우저 전용, 서버로 전송 안 함)
  const generateDEK = async () => {
    const key = await window.crypto.subtle.generateKey(
      { name: "AES-GCM", length: 256 },
      true,
      ["encrypt", "decrypt"]
    );
    setDek(key);

    const raw = await window.crypto.subtle.exportKey("raw", key);
    const hex = Array.from(new Uint8Array(raw))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    setDekDisplay(hex.slice(0, 16) + "...");

    addLog("DEK 생성 완료 (Encryption Layer, 기기 전용)");
  };

  //개인정보 암호화
  const handleEncrypt = async () => {
    if (!dek) {
      addLog("먼저 DEK를 생성하세요");
      return;
    }

    const data = JSON.stringify({ name, email, phone });
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(data);

    const ciphertext = await window.crypto.subtle.encrypt(
      { name: "AES-GCM", iv },
      dek,
      encoded
    );

    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ciphertext), iv.length);

    const b64 = btoa(String.fromCharCode(...combined));
    setEncrypted(b64);
    setDecrypted(null);
    addLog(`암호화 완료, 서버 전송 가능 형태 (${b64.length} bytes)`);
  };

  //복호화 (본인 DEK로만 가능)
  const handleDecrypt = async () => {
    if (!dek || !encrypted) {
      addLog("암호화된 데이터가 없습니다");
      return;
    }

    const combined = Uint8Array.from(atob(encrypted), (c) => c.charCodeAt(0));
    const iv = combined.slice(0, 12);
    const ciphertext = combined.slice(12);

    try {
      const plain = await window.crypto.subtle.decrypt(
        { name: "AES-GCM", iv },
        dek,
        ciphertext
      );
      const json = new TextDecoder().decode(plain);
      setDecrypted(JSON.parse(json));
      addLog("복호화 성공 (Encryption Layer 키 일치)");
    } catch {
      addLog("복호화 실패");
    }
  };

  const sendToServer = async () => {
    if (!session) {
      addLog("로그인이 필요합니다");
      return;
    }
    if (!encrypted) {
      addLog("먼저 암호화를 진행하세요");
      return;
    }

    try {
      addLog("암호문에 대한 서명 요청 중...");
      const signRes = await axios.post(`${BASE_URL}/sign`, {
        user_id: session.userId,
        challenge: encrypted,
      });

      await axios.post(`${BASE_URL}/vault`, {
        user_id: session.userId,
        session_token: session.token,
        ciphertext: encrypted,
        signature: signRes.data.signature,
      });

      addLog("서버 저장 완료 (서명 검증만 수행, 메모리에만 보관)");
    } catch (err) {
      addLog(`전송 실패: ${err.response?.data?.detail || "알 수 없는 오류"}`);
    }
  };

  //서버에서 암호문 조회 (복호화 DEK)
  const loadFromServer = async () => {
    if (!session) {
      addLog("로그인이 필요합니다");
      return;
    }

    try {
      const res = await axios.get(`${BASE_URL}/vault/${session.userId}`, {
        params: { session_token: session.token },
      });
      setEncrypted(res.data.ciphertext);
      setDecrypted(null);
      addLog("서버에서 암호문 수신 (서버는 평문을 알 수 없음)");
    } catch (err) {
      addLog(`조회 실패: ${err.response?.data?.detail || "알 수 없는 오류"}`);
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>데이터 보호 계층 (Vault)</h2>
      <p className={styles.subtitle}>Encryption Layer - DEK 기반 개인정보 보호</p>

      <div className={styles.layerBox}>
        <div className={styles.layerLabel}>DEK (Encryption Layer, 기기 전용)</div>
        <div className={styles.layerValue}>{dekDisplay || "생성되지 않음"}</div>
        <button className={styles.smallButton} onClick={generateDEK}>
          DEK 생성
        </button>
      </div>

      <input
        className={styles.input}
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="이름"
      />
      <input
        className={styles.input}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="이메일"
      />
      <input
        className={styles.input}
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="전화번호"
      />

      <div className={styles.buttonRow}>
        <button className={styles.button} onClick={handleEncrypt}>
          암호화
        </button>
        <button className={styles.button} onClick={handleDecrypt}>
          복호화
        </button>
      </div>

      {!session && <div className={styles.notice}>로그인 후 서버 전송이 가능합니다</div>}

      <div className={styles.buttonRow}>
        <button className={styles.secondaryButton} onClick={sendToServer} disabled={!session}>
          서버로 전송
        </button>
        <button className={styles.secondaryButton} onClick={loadFromServer} disabled={!session}>
          서버에서 불러오기
        </button>
      </div>
      
      {encrypted && (
        <div className={styles.dataBox}>
          <div className={styles.layerLabel}>암호화된 Vault</div>
          <div className={styles.cipherText}>{encrypted}</div>
        </div>
      )}

      {decrypted && (
        <div className={styles.dataBox}>
          <div className={styles.layerLabel}>복호화 결과</div>
          <div>
            {decrypted.name} / {decrypted.email} / {decrypted.phone}
          </div>
        </div>
      )}

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