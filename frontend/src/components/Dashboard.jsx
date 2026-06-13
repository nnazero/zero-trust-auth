import styles from "./Dashboard.module.css";

export default function Dashboard({ result }) {
  if (!result) return null;

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>📊 실시간 모니터링 대시보드</h2>

      {/* 인증 상태 */}
      <div className={styles.statusBox}>
        <div className={styles.statusTitle}>인증 상태</div>
        <div className={`${styles.statusValue} ${result.success ? styles.success : styles.fail}`}>
          {result.success ? "✅ 인증 성공" : "❌ 인증 실패"}
        </div>
        {result.success && (
          <div className={styles.token}>
            세션 토큰: {result.token}
          </div>
        )}
      </div>

      {/* 이중 잠금 */}
      <div className={styles.statusBox}>
        <div className={styles.statusTitle}>이중 잠금</div>
        <div className={`${styles.statusValue} ${result.success ? styles.success : styles.fail}`}>
          {result.success ? "🔒 통과" : "🔓 차단"}
        </div>
      </div>

      {/* PQC 서명 소요시간 */}
      {result.success && (
        <div className={styles.statusBox}>
          <div className={styles.statusTitle}>PQC 서명 소요시간</div>
          <div>
            <span className={styles.elapsed}>{result.elapsed}</span>
            <span className={styles.unit}>ms</span>
          </div>
        </div>
      )}

      {/* 로그 */}
      <div className={styles.statusBox}>
        <div className={styles.statusTitle}>인증 로그</div>
        <div className={styles.logBox}>
          {result.logs?.map((log, i) => (
            <div key={i} className={styles.logLine}>
              <span className={styles.time}>{log.time}</span> {log.msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}