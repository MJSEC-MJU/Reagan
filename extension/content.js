/* content.js */

(async () => {
  const pageUrl = window.location.href;
  console.log("[REAGAN] content.js 시작:", pageUrl);

  // background 에 분석 요청 → Promise 형태로 응답 받음
  const result = await chrome.runtime.sendMessage({
    type: "ANALYZE",
    url: pageUrl
  });

  if (!result.ok || !result.data) {
    console.warn("[REAGAN] 분석 실패 또는 결과 없음");
    return;
  }

  const { is_phishing, phishing_confidence: conf = 0 } = result.data;
  console.log("[REAGAN] 판정:", is_phishing, "confidence:", conf);

  const THRESHOLD = 0.5;
  if (is_phishing && conf >= THRESHOLD) {
    const proceed = confirm(
      `이 사이트는 피싱 의심 사이트입니다! (확신도 ${conf})\n계속하시겠습니까?`
    );
    if (!proceed) {
      // 확정 차단 – blocked.html 로 이동
      window.location.replace(chrome.runtime.getURL("blocked.html"));
    }
  }
})();
