document.addEventListener("DOMContentLoaded", () => {
    // 그냥 기본 표시
    icon.textContent = "WAIT";
    icon.className = "icon loading";
    label.textContent = "분석 중...";

    // 프론트 테스트용 코드 나중에 백엔드 연동 시 삭제 예정
    const result = {
        phishing: true, // ← false로 바꾸면 "SAFE" 뜸
        confidence: 0.97,
        reason: "의심스러운 URL이 감지되었습니다."
    };

    // 결과
    if (result.phishing === true) {
        icon.textContent = "DETECT";
        icon.className = "icon danger";
        label.textContent = "위험합니다.";
    } else if (result.phishing === false) {
        icon.textContent = "SAFE";
        icon.className = "icon safe";
        label.textContent = "안전합니다.";
    } else {
        icon.textContent = "FAIL";
        label.textContent = "판별 실패"; // 이건 그냥 넣어봄 근데 거의 뜰일 없을듯?
    }


    // 나중에 백엔드 완성되고 연동하면 아래 코드로 변경하기
    // 그냥 storage.local.get 으로 결과값만 저장해서 사용하는 코드임
    // chrome.storage.local.get("reagan_result", data => {
    //     const result = data.reagan_result;
    //     if (!result) return;

    //     if (result.phishing === true) {
    //         icon.textContent = "DETECT";
    //         icon.className = "icon danger";
    //         label.textContent = "위험합니다.";
    //     } else if (result.phishing === false) {
    //         icon.textContent = "SAFE";
    //         icon.className = "icon safe";
    //         label.textContent = "안전합니다.";
    //     } else {
    //         icon.textContent = "FAIL";
    //         label.textContent = "판별 실패";
    //     }
    // });
});