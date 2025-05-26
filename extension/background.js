chrome.runtime.onInstalled.addListener(() => {
    console.log("차단 페이지로 이동됨.");
});

// 사이트 요청 가로채서 백엔드 분석 결과에 따라 차단 여부 결정
chrome.webRequest.onBeforeRequest.addListener(
  async (details) => {
    const url = details.url;

    try {
      const response = await fetch("백엔드 서버 주소 넣기/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });

      const result = await response.json();
      console.log("[REAGAN] 분석 결과:", result);

      if (result.phishing === true) {
        console.warn("[REAGAN] 차단됨:", url);
        return { cancel: true }; // 탐지된 피싱 사이트는 차단
      }
    } catch (e) {
      console.error("[REAGAN] 분석 중 오류:", e);
    }

    return { cancel: false }; // 탐지 실패 또는 정상: 접속 허용
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);