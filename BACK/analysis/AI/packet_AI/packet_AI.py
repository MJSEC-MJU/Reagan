import time
import ssl
import socket
import json
import requests
import tldextract
import joblib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# 1) SSL/TLS 인증서 특징 추출
def get_tls_features(url: str) -> dict:
    """
    주어진 URL의 SSL/TLS 인증서 정보를 조회하여 특징 반환
    """
    features = {}
    parsed = urlparse(url)
    host = parsed.hostname
    port = 443 # https 기본포트
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(5)
            s.connect((host, port))
            cert = s.getpeercert()
    except Exception:
        # 실패 시 기본값
        return {
            'cert_valid_days': 0,
            'cert_days_to_expire': 0,
            'cert_issuer_len': 0,
            'cert_subject_cn_mismatch': 1
        }
    # 발급일/만료일
    not_before = ssl.cert_time_to_seconds(cert.get('notBefore', ''))
    not_after = ssl.cert_time_to_seconds(cert.get('notAfter', ''))
    now = time.time()
    valid_days = int((not_after - not_before) / 86400)
    days_to_expire = int((not_after - now) / 86400)
    # issuer 길이 (CA 정보 복잡도)
    issuer = cert.get('issuer', ())
    issuer_str = ''.join(x[0][1] for x in issuer) if issuer else ''
    issuer_len = len(issuer_str)
    # Common Name(CN)과 도메인 일치 여부
    subject = cert.get('subject', ())
    cn_list = [x[0][1] for x in subject if x[0][0]=='commonName']
    cn = cn_list[0] if cn_list else ''
    mismatch = int(cn.lower() != host.lower())
    # 결과
    features['cert_valid_days'] = valid_days
    features['cert_days_to_expire'] = days_to_expire
    features['cert_issuer_len'] = issuer_len
    features['cert_subject_cn_mismatch'] = mismatch
    return features

# 2) HTTP 응답 기반 특징 추출
def get_http_features(url: str) -> dict:
    """
    URL에 GET 요청을 보내고 응답 기반 특징 반환
    """
    features = {}
    session = requests.Session()
    start = time.time()
    try:
        resp = session.get(url, timeout=5, allow_redirects=True)
    except Exception:
        return {
            'status_code': 0,
            'resp_time_ms': 0,
            'redirect_count': 0,
            'final_url_mismatch': 1,
            'content_length': 0,
            'mime_type': ''
        }
    elapsed = int((time.time() - start)*1000)
    # 기본
    features['status_code'] = resp.status_code
    features['resp_time_ms'] = elapsed
    features['redirect_count'] = len(resp.history)
    # 최종 URL 도메인 비교
    orig = urlparse(url).hostname or ''
    final = urlparse(resp.url).hostname or ''
    features['final_url_mismatch'] = int(orig.lower()!=final.lower())
    # 콘텐츠 길이, MIME 타입
    features['content_length'] = len(resp.content or b'')
    content_type = resp.headers.get('Content-Type','')
    features['mime_type'] = content_type.split(';')[0]
    return features

# 3) HTML/JS 콘텐츠 기반 특징 추출
def get_html_js_features(url: str) -> dict:
    features = {}
    try:
        resp = requests.get(url, timeout=5)
        text = resp.text
    except Exception:
        # 실패 시 기본값 반환환
        return {
            'form_count': 0,
            'password_input_count': 0,
            'suspicious_js_calls': 0,
            'base64_count': 0,
            'external_link_count': 0,
            'external_resource_count': 0
        }
    soup = BeautifulSoup(text, 'html.parser')
    # (a) form 및 input
    forms = soup.find_all('form')
    features['form_count'] = len(forms)
    pwd_inputs = soup.find_all('input', attrs={'type':'password'})
    features['password_input_count'] = len(pwd_inputs)
    # (b) JS 패턴
    js_patterns = ['eval(', 'document.write', 'setTimeout(']
    suspicious = sum(text.count(p) for p in js_patterns)
    features['suspicious_js_calls'] = suspicious
    features['base64_count'] = text.lower().count('base64')
    # (c) 외부 링크 분석
    orig_domain = tldextract.extract(url).top_domain_under_public_suffix
    ext_links = 0
    for a in soup.find_all('a', href=True):
        link_dom = tldextract.extract(a['href']).top_domain_under_public_suffix
        if link_dom and link_dom != orig_domain:
            ext_links += 1
    features['external_link_count'] = ext_links
    # (d) 외부 리소스(script/img/link)
    resources = set()
    for tag, attr in [('script','src'),('img','src'),('link','href')]:
        for el in soup.find_all(tag, **{attr:True}):
            dom = tldextract.extract(el[attr]).top_domain_under_public_suffix
            if dom and dom != orig_domain:
                resources.add(dom)
    features['external_resource_count'] = len(resources)
    return features


# 통합 추출 함수 (url하나당 하나씩)
def extract_all_features(url: str) -> dict:
    f = {"url" : url}
    f.update(get_tls_features(url))
    f.update(get_http_features(url))
    f.update(get_html_js_features(url))
    print(f"{url} 삽입")
    if f['status_code'] == 0:
        return None
    return f


# 예시
if __name__ == '__main__':
    # CSV 로드
    df = pd.read_csv('dataComb.csv', encoding='cp949')
    nor_urls = df[df['type']==0]['url'].tolist()
    mal_urls = df[df['type']==1]['url'].tolist()
    # 특징 추출
    nor_feat = []
    for u in nor_urls:
        features = extract_all_features(u)
        if features:  # None 이 아니면 추가
            nor_feat.append(features)
        if len(nor_feat)==100:
            break

    mal_feat = []
    for u in mal_urls:
        features = extract_all_features(u)
        if features:
            mal_feat.append(features)
        if len(mal_feat)==100:
            break

    with open('normal_features.json', 'w', encoding='utf-8') as outfile:
        json.dump(nor_feat, outfile, indent=2, ensure_ascii=False)
    with open('malicious_features.json', 'w', encoding='utf-8') as outfile:
        json.dump(mal_feat, outfile, indent=2, ensure_ascii=False)
    print("Features saved to features.json")
    # 데이터프레임 생성
    data = nor_feat + mal_feat
    labels = [0]*len(nor_feat) + [1]*len(mal_feat)
    df_feat = pd.DataFrame(data)
    df_feat['label'] = labels
    # 전처리: URL 제거, 결측 0 처리, One-Hot 인코딩
    df_feat.drop(columns=['url'], inplace=True)
    df_feat.fillna(0, inplace=True)
    df_feat = pd.get_dummies(df_feat, columns=['mime_type'], prefix='mime')
    # 학습/테스트 분리
    X = df_feat.drop(columns=['label'])
    y = df_feat['label']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )
    # 모델 학습 및 평가
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print(df_feat.head())
    print(classification_report(y_test, y_pred))
    
    # ① 모델 저장
    joblib.dump(clf, "rf_model.pkl")

    # ② 학습에 사용한 입력 컬럼 순서도 같이 저장
    feature_cols = X_train.columns.tolist()
    with open("rf_columns.json", "w", encoding="utf-8") as f:
        json.dump(feature_cols, f, ensure_ascii=False)

