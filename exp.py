import requests

resp = requests.post(
    "http://127.0.0.1:8000/api/analysis-requests/",
    json={"site_url": "https://nid.naver.com/user2/help/naverProfile?m=viewModifyProfile&token_help=hIyVbsgTWvF2lrD3"}
)
print(resp.status_code)   # 201
print(resp.json())        # 위 예시와 유사한 JSON 출력
