"""
공통 테스트 픽스처 및 설정

모든 테스트에서 공통적으로 사용되는 픽스처들을 정의합니다.
"""

import os
import pytest
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Generator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    세션 범위 테스트 설정 픽스처
    
    Returns:
        Dict[str, Any]: 테스트 실행에 필요한 기본 설정
    """
    config = {
        "app_package": "com.towneers.www",
        "app_activity": ".SplashActivity",
        "platform_name": "Android",
        "automation_name": "UiAutomator2",
        "device_name": "Android Emulator",
        "appium_server": "http://localhost:4723",
        "api_base_url": os.getenv("API_BASE_URL", "https://api.daangn.com"),
        "test_timeout": 30,
        "implicit_wait": 10,
        "screenshot_dir": "screenshots",
        "test_data_dir": "test_data",
        "reports_dir": "reports",
    }
    
    # 디렉토리 생성
    for dir_key in ["screenshot_dir", "test_data_dir", "reports_dir"]:
        Path(config[dir_key]).mkdir(exist_ok=True)
    
    logger.info(f"테스트 설정 초기화 완료: {config}")
    return config


@pytest.fixture(scope="function")
def cleanup_test_data(test_config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    테스트 데이터 정리 픽스처
    
    테스트 실행 전후로 테스트 데이터를 정리합니다.
    
    Args:
        test_config: 테스트 설정
        
    Yields:
        Dict[str, Any]: 정리할 데이터 리스트
    """
    # 테스트 시작 전
    cleanup_data = {
        "created_users": [],
        "created_products": [],
        "created_chats": [],
        "uploaded_files": [],
    }
    
    logger.info("테스트 데이터 정리 픽스처 시작")
    
    try:
        yield cleanup_data
    finally:
        # 테스트 완료 후 정리
        logger.info(f"테스트 데이터 정리 시작: {cleanup_data}")
        
        # 실제 정리 로직은 각 API 클라이언트에서 구현
        for data_type, items in cleanup_data.items():
            if items:
                logger.warning(f"정리되지 않은 {data_type}: {len(items)}개")


@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, str]:
    """
    테스트용 사용자 데이터 생성 픽스처
    
    Returns:
        Dict[str, str]: 테스트용 사용자 정보
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "username": f"test_user_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "phone": f"010-1234-{timestamp[-4:]}",
        "nickname": f"테스터_{timestamp[-4:]}",
        "location": "서울시 용산구",
        "password": "TestPassword123!",
    }


@pytest.fixture(scope="function")
def test_product_data() -> Dict[str, Any]:
    """
    테스트용 상품 데이터 생성 픽스처
    
    Returns:
        Dict[str, Any]: 테스트용 상품 정보
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "title": f"테스트 상품_{timestamp}",
        "description": f"자동화 테스트용 상품입니다. 생성시간: {timestamp}",
        "price": 50000,
        "category": "기타 중고물품",
        "location": "서울시 용산구",
        "images": [],  # 실제 테스트에서 이미지 경로 추가
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(test_config: Dict[str, Any]) -> None:
    """
    테스트 환경 자동 설정 픽스처
    
    Args:
        test_config: 테스트 설정
    """
    logger.info("테스트 환경 설정 시작")
    
    # 환경 변수 검증
    required_env_vars = ["ANDROID_HOME"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"누락된 환경 변수: {missing_vars}")
    
    # 테스트 실행 정보 로깅
    logger.info(f"테스트 실행 시작: {datetime.now()}")
    logger.info(f"Python 경로: {os.sys.executable}")
    logger.info(f"작업 디렉토리: {os.getcwd()}")


@pytest.fixture(scope="function")
def screenshot_on_failure(request, test_config: Dict[str, Any]):
    """
    테스트 실패 시 스크린샷 캡처 픽스처
    
    Args:
        request: pytest request 객체
        test_config: 테스트 설정
    """
    yield
    
    if request.node.rep_call.failed:
        # 실패한 테스트의 스크린샷 캡처
        test_name = request.node.name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{test_config['screenshot_dir']}/failed_{test_name}_{timestamp}.png"
        
        logger.error(f"테스트 실패로 인한 스크린샷 캡처: {screenshot_path}")
        # 실제 스크린샷 캡처는 드라이버가 있을 때 구현


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    테스트 실행 결과를 request 객체에 저장하는 훅
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


def pytest_configure(config):
    """
    pytest 설정 훅
    """
    logger.info("Pytest 설정 완료")


def pytest_collection_modifyitems(config, items):
    """
    테스트 수집 후 수정 훅
    """
    logger.info(f"수집된 테스트 개수: {len(items)}")


# 위치 기반 테스트를 위한 커스텀 마커 처리
def pytest_runtest_setup(item):
    """
    각 테스트 실행 전 설정 훅
    """
    # location 마커 처리
    location_marker = item.get_closest_marker("location")
    if location_marker:
        location = location_marker.args[0] if location_marker.args else "기본위치"
        logger.info(f"위치 기반 테스트 실행: {location}")


@pytest.fixture(scope="function")
def allure_environment_properties():
    """
    Allure 리포트용 환경 정보 픽스처
    """
    return {
        "Python.Version": f"{os.sys.version}",
        "Platform": f"{os.sys.platform}",
        "Test.Framework": "pytest",
    }
