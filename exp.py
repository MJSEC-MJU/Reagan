import requests

resp = requests.post(
    "http://127.0.0.1:8000/api/analysis-requests/",
    json={"site_url": "http://kimsignals.shop"}
)
print(resp.status_code)   # 201
print(resp.json())        # 위 예시와 유사한 JSON 출력
