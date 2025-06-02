// content.js

(async () => {
  console.log("[REAGAN] content.js 시작:", window.location.href);

  // 1) 현재 페이지 URL을 data 형태로 백엔드에 보냄
  const data = { site_url: window.location.href };
  console.log("[REAGAN] 전송 데이터 확인:", data);

  try {
    // 2) 백엔드에 POST 요청 → analysis-requests에 저장
    const response = await fetch("http://localhost:8000/api/analysis-requests/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    console.log("[REAGAN] 백엔드 응답 status:", response.status);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    // 3) 분석 결과 전체 JSON
    const result = await response.json();
    console.log("[REAGAN] 분석 결과(원본):", result);

    // 4) tasks 배열에서 site Task만 골라냄
    const siteTask = Array.isArray(result.tasks)
      ? result.tasks.find(t => t.task_type === "site")
      : null;
    if (!siteTask) {
      console.warn("[REAGAN] site Task를 찾을 수 없음");
      return;
    }
    console.log("[REAGAN] siteTask 결과:", siteTask.result);

    // 5) siteTask.result안에 is_phishing: true/false 확인
    const isPhishing = siteTask.result?.is_phishing === true;
    const confidence = siteTask.result?.phishing_confidence ?? 0;
    console.log("[REAGAN] is_phishing:", isPhishing, "confidence:", confidence);

    // 6) 원하는 threshold 이상일 때만 강제 차단 화면으로 이동
    const CONF_THRESHOLD = 0.5;
    if (isPhishing && confidence >= CONF_THRESHOLD) {
      // 사용자에게 한번 더 묻고 싶으면 confirm을 쓰거나
      // 그냥 바로 강제 RDR(redirection) 시킬 수도 있습니다:

      // 6-1) 사용자가 이 페이지를 보려면 [확인] 버튼을 눌러야 계속
      const proceed = confirm(
        `이 사이트는 피싱으로 의심됩니다! (확신도 ${confidence})\n계속하시겠습니까?`
      );
      if (!proceed) {
        // 6-2) confirm에서 “취소”를 누르면 바로 blocked.html로 리디렉트
        window.location.replace(chrome.runtime.getURL("blocked.html"));
      }
      // 만약 “확인”을 누르면 그냥 페이지 계속 보여 줌
    }
  } catch (err) {
    console.error("[REAGAN] 전송 또는 분석 중 오류:", err);
    // 오류가 나도 페이지 자체는 차단하지 않고 그냥 떠 있게 둡니다.
  }
})();
