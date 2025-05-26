document.addEventListener("DOMContentLoaded", () => {
    const icon = document.getElementById("icon");
    const label = document.getElementById("label");

    chrome.storage.local.get("reagan_result", data => {
        const result = data.reagan_result;

        if (!result) {
            icon.textContent = "WAIT";
            icon.className = "icon loading";
            label.textContent = "분석 중...";
            return;
        }

        if (result.phishing === true) {
            icon.textContent = "DETECT";
            icon.className = "icon danger";
            label.textContent = "매우 위험.";
        } else if (result.phishing === false) {
            icon.textContent = "SAFE";
            icon.className = "icon safe";
            label.textContent = "극히 안전.";
        } else {
            icon.textContent = "FAIL";
            icon.className = "icon";
            label.textContent = "판별 실패";
        }
    });
});