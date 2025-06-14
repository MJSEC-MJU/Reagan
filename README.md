
<!-- PROJECT SHIELDS -->
<p align="center">
  <a href="https://github.com/ialleejy/reagan-backend/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/ialleejy/reagan-backend/docker-compose-ci.yml?branch=dev" alt="CI Status"/>
  </a>
  <a href="https://hub.docker.com/repository/docker/ialleejy/reagan-backend">
    <img src="https://img.shields.io/badge/Docker-Hub-blue.svg" alt="Docker Hub"/>
  </a>
  <a href="https://github.com/MJSEC-MJU/breakrecapcha_v2">
    <img src="https://img.shields.io/badge/Repo-breakrecapcha_v2-blue.svg" alt="breakrecapcha_v2"/>
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
  </a>
  <a href="https://Reagan.mjsec.kr">
    <img src="https://img.shields.io/badge/Website-Online-brightgreen.svg" alt="Website"/>
  </a>
</p>

---

# Reagan  
> **3단계 AI 파이프라인 기반 악성 URL 탐지 시스템**

---

## 🔗 목차

1. [소개](#소개)  
2. [파이프라인 구성](#파이프라인-구성)  
3. [시스템 아키텍처](#시스템-아키텍처)  
4. [설치 및 실행](#설치-및-실행)  
5. [CI/CD 파이프라인](#cicd-파이프라인)  
6. [진행 현황](#진행-현황)  
7. [평가지표](#평가지표)  
8. [참고 논문](#참고-논문)  
9. [기여자](#기여자)  

---

## 📖 소개
Reagan은 **URL Detection AI**, **Packet Analysis AI**, **Break_Captcha_AI**로 구성된 3단계 파이프라인을 통해 악성 URL을 자동 식별하고,  
필요 시 자동 크롤링을 이어가기 위해 reCAPTCHA V2를 우회합니다.

- **URL Detection AI**: 텍스트·메타데이터 기반 1차 필터링  
- **Packet Analysis AI**: 네트워크 패킷 레벨 심층 분석  
- **Break_Captcha_AI**: reCAPTCHA V2 이미지 챌린지 자동 우회 (GitHub: [MJSEC-MJU/breakrecapcha_v2](https://github.com/MJSEC-MJU/breakrecapcha_v2))  

---

## 🛠️ 파이프라인 구성

```mermaid
flowchart TD
    A[URL 탐지 AI] --> B{CAPTCHA 존재?}
    B -->|Yes| C[Break_Captcha_AI]
    B -->|No| D[Packet Analysis AI]
    C --> D
    D --> E[최종 결과]
    
    E --> F[악성 URL 리포트]
    E --> G[크롤러 통합]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#ffccbc
    style D fill:#f3e5f5
    style E fill:#e8f5e8
    style F fill:#ffebee
    style G fill:#f1f8e9
````

1. **URL Detection AI**: 위험 URL 1차 탐지
2. **Break\_Captcha\_AI**: CAPTCHA 차단 시 자동 우회
3. **Packet Analysis AI**: 심층 패킷 분석 및 최종 악성 여부 판정

---

## 🏛 시스템 아키텍처

```mermaid
flowchart TB
    subgraph Client["클라이언트"]
        A[Chrome Extension]
    end
    
    subgraph Backend["백엔드 서비스"]
        A1[URL Detection AI]
        B[API Gateway]
        G{CAPTCHA 존재?}
        C[Packet Analysis AI]
        D[Break_Captcha_AI]
        H[결과 처리]
    end
    
    subgraph Infra["인프라스트럭처"]
        E[GCP VM]
        F[Nginx + Docker Compose]
    end
    
    A -->|URL 제출| A1
    A1 -->|의심 URL| B
    B --> G
    G -->|Yes| D
    G -->|No| C
    D --> C
    C --> H
    H -->|리포트| A
    
    E -.->|호스팅| F
    F -.->|서비스 제공| Backend
```

* HTTPS(443) 통신 암호화
* 방화벽: 80, 443, 8000 포트만 개방

---

## 🚀 설치 및 실행

```bash
# 1. 레포지토리 클론
git clone https://github.com/ialleejy/reagan-backend.git
cd reagan-backend

# 2. 환경 변수 설정
cp .env.example .env
# DOCKER_HUB_USERNAME, DB_*, SECRET_KEY 등을 .env에 설정

# 3. Docker로 빌드 & 실행
docker-compose up -d --build
```

> 웹 UI & API: [https://Reagan.mjsec.kr](https://Reagan.mjsec.kr)

---

## 🔄 CI/CD 파이프라인

1. **Push** → `dev` 브랜치
2. **빌드 & 테스트** (GitHub Actions / Docker Compose)
3. **Docker Hub**에 이미지 푸시
4. **자동 배포** → GCP VM (Nginx + Docker Compose)
5. **모니터링 & 알림** (이메일, Slack 등)

---

## 📈 진행 현황

* 서버 및 HTTPS 설정 완료
* 3단계 AI 파이프라인 개발 완료
* CI/CD 자동 배포 성공
* 초기 악성 URL 탐지 성공률: **95% 이상**

---

## 📊 평가지표

| 항목          | 목표치   |
| ----------- | ----- |
| 1차 필터링 정확도  | ≥ 90% |
| 심층 분석 탐지율   | ≥ 92% |
| 크롤러 연속성 유지율 | ≥ 90% |

---

## 📚 참고 논문

* **Breaking reCAPTCHAv2** (YOLO 기반 이미지 챌린지 자동화)
* **Understanding reCAPTCHAv2 via a Large-Scale Live User Study**

---

## 🤝 기여자

| 역할                           | 이름  |
| ---------------------------- | --- |
| Frontend & URL Detection AI  | 이주오 |
| Backend & Packet Analysis AI | 이윤태 |
| DevOps & Break\_Captcha\_AI  | 이종윤 |

---

© 2025 MJSEC & Myongji University · MIT License

```
```
