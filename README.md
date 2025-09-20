# 🥕 당근마켓 E2E 테스트 자동화 프레임워크

> 하이퍼로컬 플랫폼 '당근' 애플리케이션을 위한 견고하고 확장 가능한 E2E 테스트 자동화 프레임워크

[![E2E 테스트](https://github.com/username/danggen-e2e-automation/workflows/E2E%20테스트%20자동화/badge.svg)](https://github.com/username/danggen-e2e-automation/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Appium](https://img.shields.io/badge/Appium-2.0+-orange.svg)](http://appium.io/)
[![Allure](https://img.shields.io/badge/Allure-Reports-yellow.svg)](https://allurereport.org/)

## 🎯 프로젝트 개요

당근마켓의 핵심 기능들을 포괄하는 완전한 E2E 테스트 자동화 솔루션입니다.

### ✨ 주요 기능

- **🛒 중고거래 플로우**: 판매자 물품 등록부터 구매자 채팅까지의 완전한 거래 시나리오
- **🏘️ 커뮤니티 참여**: 동네생활 게시글 작성, 댓글 상호작용, 지역 기반 필터링
- **🛡️ 예외 상황 처리**: 금지 물품, 위치 조작, 결제 실패, 네트워크 오류 등 엣지 케이스
- **📊 자동화된 CI/CD**: GitHub Actions 기반 자동 테스트 실행 및 리포트 생성
- **📈 포괄적인 리포팅**: Allure Framework 기반 상세한 테스트 결과 분석

### 🏗️ 아키텍처 특징

- **다층 모델 구조**: API, UI, 드라이버 계층 분리
- **페이지 객체 모델**: 재사용 가능한 UI 컴포넌트
- **하이브리드 테스트**: API + 모바일 앱 통합 검증
- **데이터 격리**: 테스트별 독립적인 데이터 생성/정리

## 📋 시스템 요구사항

### 기본 환경
- **Python**: 3.11 이상
- **Node.js**: 18 이상 (Appium 용)
- **Java**: JDK 17 (Android SDK 용)
- **Android SDK**: API Level 28-31
- **Git**: 버전 관리

### 하드웨어 요구사항
- **RAM**: 최소 8GB (권장 16GB)
- **저장 공간**: 10GB 이상
- **CPU**: Intel/AMD x64 또는 Apple Silicon

## 🚀 빠른 시작

### 1단계: 저장소 클론
```bash
git clone https://github.com/username/danggen-e2e-automation.git
cd danggen-e2e-automation
```

### 2단계: 환경 설정
```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# Python 의존성 설치
pip install -r requirements.txt
```

### 3단계: Appium 설치 및 설정
```bash
# Appium 설치
npm install -g appium@next
npm install -g @appium/doctor

# Android 드라이버 설치
appium driver install uiautomator2

# 환경 검증
appium-doctor --android
```

### 4단계: Android 환경 설정
```bash
# Android SDK 설치 (Android Studio 또는 command line tools)
# ANDROID_HOME 환경변수 설정
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/platform-tools

# 에뮬레이터 생성 (선택사항)
avdmanager create avd -n test_avd -k "system-images;android-29;google_apis;x86_64"
```

## 🏗️ 프로젝트 구조

```
danggen-e2e-automation/
├── 🧪 tests/                     # 테스트 케이스
│   ├── test_marketplace_flow.py   # 중고거래 E2E 테스트
│   ├── test_community_flow.py     # 커뮤니티 E2E 테스트
│   ├── test_edge_cases.py         # 예외 상황 테스트
│   └── conftest.py               # 공통 픽스처
├── 🖼️ pages/                     # 페이지 객체 모델 (POM)
│   ├── base_page.py              # 기본 페이지 클래스
│   ├── login_page.py             # 로그인 페이지
│   ├── home_page.py              # 홈 페이지
│   ├── community_page.py         # 커뮤니티 페이지
│   ├── product_detail_page.py    # 상품 상세 페이지
│   └── chat_page.py              # 채팅 페이지
├── 🔗 api_clients/               # API 클라이언트
│   ├── base_client.py            # 기본 API 클라이언트
│   ├── carrot_api.py             # 통합 API 클라이언트
│   ├── user_client.py            # 사용자 관리 API
│   ├── product_client.py         # 상품 관리 API
│   ├── community_client.py       # 커뮤니티 API
│   ├── chat_client.py            # 채팅 API
│   ├── auth_manager.py           # 인증 관리
│   └── models.py                 # 데이터 모델 (Pydantic)
├── 🛠️ utils/                     # 유틸리티 함수
│   └── mobile_driver.py          # 모바일 드라이버 관리
├── ⚙️ config/                    # 설정 파일
│   ├── api_config.py             # API 설정
│   └── env.example               # 환경변수 예시
├── 🤖 .github/                   # GitHub Actions
│   ├── workflows/
│   │   └── e2e-tests.yml         # CI/CD 파이프라인
│   └── dependabot.yml            # 의존성 자동 업데이트
├── 📊 reports/                   # 테스트 리포트 (자동 생성)
├── 📷 screenshots/               # 테스트 스크린샷 (자동 생성)
├── 📋 requirements.txt           # Python 의존성
├── 🔧 pyproject.toml             # 프로젝트 설정
├── 🧪 pytest.ini                # Pytest 설정
└── 📖 README.md                  # 프로젝트 문서
```

## 🧪 테스트 실행 방법

### 기본 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 병렬 실행 (속도 향상)
pytest -n auto

# 상세 출력
pytest -v

# 실패 시 즉시 중단
pytest -x
```

### 마커별 테스트 실행
```bash
# E2E 통합 테스트
pytest -m "e2e"

# API 테스트만
pytest -m "api"

# 모바일 UI 테스트만
pytest -m "mobile"

# 스모크 테스트 (핵심 기능만)
pytest -m "smoke"

# 커뮤니티 기능 테스트
pytest -m "community"

# 예외 상황 테스트
pytest -m "edge_case"
```

### Allure 리포트 생성
```bash
# Allure 결과 수집하며 테스트 실행
pytest --alluredir=reports/allure-results

# Allure 리포트 생성 및 서빙
allure serve reports/allure-results

# 정적 리포트 생성
allure generate reports/allure-results -o reports/allure-report --clean
```

### 특정 테스트 파일 실행
```bash
# 중고거래 플로우만
pytest tests/test_marketplace_flow.py

# 커뮤니티 기능만
pytest tests/test_community_flow.py

# 예외 상황만
pytest tests/test_edge_cases.py
```

## 🏷️ 테스트 마커

| 마커 | 설명 | 사용 예시 |
|------|------|-----------|
| `@pytest.mark.api` | API 전용 테스트 | `pytest -m "api"` |
| `@pytest.mark.mobile` | 모바일 UI 테스트 | `pytest -m "mobile"` |
| `@pytest.mark.e2e` | End-to-End 통합 테스트 | `pytest -m "e2e"` |
| `@pytest.mark.smoke` | 핵심 기능 스모크 테스트 | `pytest -m "smoke"` |
| `@pytest.mark.community` | 커뮤니티 기능 테스트 | `pytest -m "community"` |
| `@pytest.mark.edge_case` | 예외 상황 테스트 | `pytest -m "edge_case"` |
| `@pytest.mark.location` | 위치 기반 테스트 | `pytest -m "location"` |

## 📊 리포팅 시스템

### Allure 리포트
- **라이브 리포트**: `allure serve reports/allure-results`
- **정적 리포트**: `reports/allure-report/index.html`
- **GitHub Pages**: CI/CD를 통한 자동 배포

### 생성되는 리포트
```
reports/
├── allure-results/          # Allure 원본 데이터
├── allure-report/           # 생성된 HTML 리포트
├── junit-results.xml        # JUnit 형식 결과
└── pytest-html-report.html # Pytest HTML 리포트

screenshots/
├── test_failure_*.png       # 실패 시 자동 스크린샷
└── test_step_*.png         # 단계별 스크린샷
```

## 🤖 CI/CD 파이프라인

### GitHub Actions 워크플로우
- **트리거**: Push, Pull Request, 스케줄 실행
- **매트릭스 빌드**: 다중 Android API 레벨 (28, 29, 30)
- **자동 리포트**: GitHub Pages 배포
- **아티팩트**: 테스트 결과, 스크린샷, 로그

### 파이프라인 단계
1. **환경 설정**: Python, Node.js, Android SDK
2. **의존성 설치**: 프로젝트 요구사항
3. **에뮬레이터 시작**: Android 가상 디바이스
4. **Appium 서버**: 백그라운드 실행
5. **테스트 실행**: 병렬 처리
6. **리포트 생성**: Allure HTML
7. **배포**: GitHub Pages

## 🏗️ 아키텍처 상세

### 다층 모델 구조
```
📱 모바일 앱 (당근마켓)
    ↕️
🖼️ 페이지 객체 계층 (POM)
    ↕️
🧪 테스트 계층 (Pytest)
    ↕️
🔗 API 클라이언트 계층
    ↕️
⚙️ 설정 관리 계층
```

### 핵심 설계 원칙
- **단일 책임**: 각 클래스는 하나의 명확한 역할
- **느슨한 결합**: 계층 간 독립성 보장
- **높은 응집도**: 관련 기능들의 그룹화
- **재사용성**: 공통 컴포넌트의 모듈화
- **확장성**: 새로운 기능 추가 용이성

### 데이터 플로우
1. **테스트 시작**: 픽스처를 통한 환경 초기화
2. **사용자 생성**: API를 통한 테스트 데이터 준비
3. **모바일 액션**: 페이지 객체를 통한 UI 조작
4. **API 검증**: 백엔드 상태 확인
5. **결과 수집**: Allure를 통한 리포트 생성
6. **정리**: 테스트 데이터 자동 삭제

## 🔧 고급 설정

### 환경 변수 설정
```bash
# .env 파일 생성 (config/env.example 참고)
cp config/env.example .env

# 필수 환경 변수
export APPIUM_SERVER_URL="http://localhost:4723/wd/hub"
export ANDROID_DEVICE_NAME="test_avd"
export API_BASE_URL="https://api.carrot.com"
```

### 커스텀 설정
```python
# config/api_config.py 수정
API_ENDPOINTS = {
    "development": "https://dev-api.carrot.com",
    "staging": "https://staging-api.carrot.com",
    "production": "https://api.carrot.com"
}
```

## 🐛 문제 해결

### 일반적인 문제들

**Q: Appium 연결 실패**
```bash
# Appium 서버 상태 확인
appium doctor --android
# 포트 충돌 해결
lsof -ti:4723 | xargs kill -9
```

**Q: 에뮬레이터 시작 실패**
```bash
# AVD 목록 확인
emulator -list-avds
# 메모리 할당 증가
emulator -avd test_avd -memory 4096
```

**Q: 테스트 데이터 정리 안됨**
```bash
# 수동 정리 스크립트 실행
python -c "from api_clients.carrot_api import get_api_client; get_api_client().cleanup_all_test_data()"
```

## 📈 성능 최적화

### 테스트 실행 속도 향상
- **병렬 실행**: `pytest -n auto`
- **마커 사용**: 필요한 테스트만 실행
- **픽스처 스코프**: 세션/모듈 레벨 재사용
- **에뮬레이터 캐시**: CI/CD에서 이미지 재사용

### 리소스 관리
- **메모리 사용량**: 테스트 후 자동 정리
- **네트워크 효율성**: API 호출 최적화
- **스토리지**: 오래된 리포트 자동 삭제

## 🤝 기여 가이드라인

### 개발 워크플로우
1. **이슈 생성**: 버그 리포트 또는 기능 요청
2. **브랜치 생성**: `feature/기능명` 또는 `bugfix/버그명`
3. **개발**: 코드 작성 및 테스트 추가
4. **테스트**: 로컬에서 전체 테스트 실행
5. **Pull Request**: 코드 리뷰 요청
6. **CI/CD**: 자동 테스트 및 검증
7. **머지**: 승인 후 main 브랜치 통합

### 코딩 규칙
- **PEP 8**: Python 코드 스타일 가이드 준수
- **타입 힌트**: 모든 함수에 타입 어노테이션 추가
- **Docstring**: 클래스와 메서드에 설명 문서 작성
- **테스트 커버리지**: 새 기능에 대한 테스트 필수

### 커밋 메시지 규칙
```
type(scope): description

feat(api): add community post creation endpoint
fix(mobile): resolve screenshot capture issue  
test(e2e): add edge case for payment failure
docs(readme): update installation guide
```

## 📚 추가 리소스

- **Appium 문서**: [appium.io](http://appium.io/)
- **Pytest 가이드**: [pytest.org](https://pytest.org/)
- **Allure 리포트**: [allurereport.org](https://allurereport.org/)
- **Pydantic 모델**: [pydantic-docs.helpmanual.io](https://pydantic-docs.helpmanual.io/)

## 👥 팀

- **개발자**: E2E 테스트 자동화 전문가
- **기여자**: 오픈소스 커뮤니티
- **유지보수**: 지속적인 업데이트 및 개선

## 📞 지원

- **Issues**: [GitHub Issues](https://github.com/username/danggen-e2e-automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/danggen-e2e-automation/discussions)
- **Wiki**: [프로젝트 위키](https://github.com/username/danggen-e2e-automation/wiki)

## 📝 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

---

**Made with ❤️ for the E2E Testing Community**
