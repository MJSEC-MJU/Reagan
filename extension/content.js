(async () => {
    // data 객체로 묶어서 나중에 백으로 보내기
    const data = {
        site_url: window.location.href
    };

    console.log("[REAGAN] 전송 데이터 확인:", data);

    // 백엔드 서버로 전송 JSON 형식
    // 테스트를 위해 임시로 서버 주소 넣었음 나중에 바꿀것
    fetch("백엔드 서버 주소 넣기/api/analysis-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
        .then(res => res.json())
        .then(result => {
            console.log("[REAGAN] 분석 결과:", result);
            chrome.storage.local.set({ reagan_result: result });

            if (result.html_result?.phishing || result.url_result?.phishing) {
                const confirmBlock = confirm("이 사이트는 위험할 수 있습니다. 그래도 접속하시겠습니까?");
                if (!confirmBlock) {
                    const redirectUrl = chrome.runtime.getURL("blocked.html") + `?original=${encodeURIComponent(window.location.href)}`;
                    window.location.replace(redirectUrl);
                }
            }
        })
        .catch(err => console.error("[REAGAN] 전송 실패:", err));
})();