/* background.js — MV3 service-worker */

const API_ENDPOINT   = "https://reagan.mjsec.kr/api/analysis-requests/";
const CONF_THRESHOLD = 0.5;
const CACHE_TTL      = 60 * 60 * 1e3; // 1h

let cache = {};          // URL → { ts, verdict, result }
let lastSiteResult = null;

chrome.runtime.onInstalled.addListener(() => {
  console.log("[REAGAN] 확장 설치/업데이트 완료");
});

/* ───────── ① onBeforeRequest: 페이지 로드 전 차단 ───────── */
chrome.webRequest.onBeforeRequest.addListener(
  (details) => decide(details.url)
                 .then(block => ({ cancel: block }))
                 .catch(()  => ({ cancel: false })),
  { urls: ["<all_urls>"] },
  ["blocking"]
);

/* ───────── ② content / popup 메시지 처리 ───────── */
chrome.runtime.onMessage.addListener((msg, _, reply) => {
  if (msg.type === "ANALYZE") {
    decide(msg.url)
      .then(block => reply({ ok: true, verdict: block, data: lastSiteResult }))
      .catch(err  => reply({ ok: false, error: err.toString() }));
    return true;       // async
  }

  if (msg.type === "GET_LAST_RESULT") {
    reply({ ok: !!lastSiteResult, data: lastSiteResult });
  }
});

/* 실제 판정 로직 */
async function decide(url) {
  // 1) 캐시
  if (cache[url] && Date.now() - cache[url].ts < CACHE_TTL) {
    return cache[url].verdict;
  }

  // 2) 백엔드 호출
  const res  = await fetch(API_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body:   JSON.stringify({ site_url: url })
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();

  const siteTask   = json.tasks?.find(t => t.task_type === "site");
  const siteResult = siteTask?.result || {};
  const block = siteResult.is_phishing === true &&
                (siteResult.phishing_confidence ?? 0) >= CONF_THRESHOLD;

  cache[url]     = { ts: Date.now(), verdict: block, result: siteResult };
  lastSiteResult = siteResult;
  chrome.storage.local.set({ reagan_result: siteResult });

  return block;
}
