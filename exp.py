import requests

resp = requests.post(
    #"https://reagan.mjsec.kr/api/analysis-requests/",
    "http://127.0.0.1:8000/api/analysis-requests/",
<<<<<<< HEAD
    json={"site_url": "https://www.youtube.com/shorts/dV0l-K1Ogwk"}
=======
    json={"site_url": "https://2captcha.com/ko/demo/normal"}
>>>>>>> e218d30 ([update] capcha)
)
print(resp.status_code)   # 201
print(resp.json())        # 위 예시와 유사한 JSON 출력
