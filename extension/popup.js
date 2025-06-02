// popup.js
document.addEventListener("DOMContentLoaded", () => {
  const icon  = document.getElementById("icon");
  const label = document.getElementById("label");

  // 1) content.js가 이미 chrome.storage.local.set({ reagan_result: siteTask.result })을
  //    수행해 두었다면, 여기서 바로 값을 가져와서 보여 주면 됩니다.
  chrome.storage.local.get("reagan_result", (data) => {
    const siteResult = data.reagan_result;
    console.log("[POPUP] storage 로부터 가져온 값:", siteResult);

    if (!siteResult) {
      icon.textContent   = "WAIT";
      icon.className     = "icon loading";
      label.textContent  = "분석 중...";
      return;
    }

    const isPhishing = siteResult.is_phishing === true;
    const confidence = siteResult.phishing_confidence ?? 0;

    // threshold를 정해서 아이콘/텍스트 분기
    if (isPhishing && confidence >= 0.5) {
      icon.textContent   = "DETECT";
      icon.className     = "icon danger";
      label.textContent  = `매우 위험 (확신도 ${confidence})`;
    } else {
      icon.textContent   = "SAFE";
      icon.className     = "icon safe";
      label.textContent  = "안전합니다";
    }
  });
});
