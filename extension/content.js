(async () => {
    const html = document.documentElement.outerHTML;
    const scripts = Array.from(document.scripts).map(s => s.innerText).join("\n");

    const styles = Array.from(document.styleSheets)
        .map(sheet => {
            try {
                return Array.from(sheet.cssRules || []).map(rule => rule.cssText).join("\n");
            } catch (e) {
                return ""; // CORS 등 접근 불가 예외 무시,
            }
        })
        .join("\n");

    // data 객체로 묶어서 나중에 백으로 보내기
    const data = {
        url: window.location.href,
        html: html,
        scripts: scripts,
        styles: styles
    };

    // 백엔드 서버로 전송 JSON 형식
    fetch("여기에 백엔드 서버 주소 추가할 것 (까먹으면 클남)", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
        .then(res => res.json())
        .then(result => {
            console.log("[REAGAN] 분석 결과:", result);
            // 백 연동하면 저장된 결과값을 chrome.storage.local 에서 get 으로 받아오면 됨
            chrome.storage.local.set({ reagan_result: result });
        })
        .catch(err => console.error("[REAGAN] 전송 실패:", err));
})();