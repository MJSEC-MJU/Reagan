import requests

resp = requests.post(
    "https://reagan.mjsec.kr/api/analysis-requests/",
<<<<<<< HEAD
    json={"site_url": "http://kimsignals.shop"}
=======
    #"http://127.0.0.1:8000/api/analysis-requests/",
    json={"site_url": "https://www.naver.com/"}
>>>>>>> 36d15183961e05c96d41916d499ac9d13d79dc60
)
print(resp.status_code)   # 201
print(resp.json())        # 위 예시와 유사한 JSON 출력
