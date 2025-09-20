"""
샘플 테스트 파일

pytest 설정 및 픽스처가 정상 작동하는지 확인하기 위한 테스트입니다.
"""

import pytest
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TestPytestSetup:
    """pytest 설정 검증 테스트 클래스"""
    
    @pytest.mark.unit
    def test_basic_assertion(self):
        """기본 단언문 테스트"""
        assert True
        logger.info("기본 단언문 테스트 통과")
    
    @pytest.mark.unit
    def test_config_fixture(self, test_config: Dict[str, Any]):
        """설정 픽스처 테스트"""
        assert test_config is not None
        assert "app_package" in test_config
        assert "api_base_url" in test_config
        
        logger.info(f"설정 픽스처 테스트 통과: {test_config['app_package']}")
    
    @pytest.mark.unit
    def test_cleanup_fixture(self, cleanup_test_data: Dict[str, Any]):
        """정리 픽스처 테스트"""
        assert cleanup_test_data is not None
        assert "created_users" in cleanup_test_data
        
        # 테스트 데이터 추가 시뮬레이션
        cleanup_test_data["created_users"].append("test_user_001")
        
        logger.info("정리 픽스처 테스트 통과")
    
    @pytest.mark.unit
    def test_user_data_fixture(self, test_user_data: Dict[str, str]):
        """사용자 데이터 픽스처 테스트"""
        assert test_user_data is not None
        assert "username" in test_user_data
        assert "email" in test_user_data
        assert test_user_data["username"].startswith("test_user_")
        
        logger.info(f"사용자 데이터 픽스처 테스트 통과: {test_user_data['username']}")
    
    @pytest.mark.unit
    def test_product_data_fixture(self, test_product_data: Dict[str, Any]):
        """상품 데이터 픽스처 테스트"""
        assert test_product_data is not None
        assert "title" in test_product_data
        assert "price" in test_product_data
        assert test_product_data["title"].startswith("테스트 상품_")
        assert isinstance(test_product_data["price"], int)
        
        logger.info(f"상품 데이터 픽스처 테스트 통과: {test_product_data['title']}")


class TestCustomMarkers:
    """커스텀 마커 테스트 클래스"""
    
    @pytest.mark.location("Yongsan")
    @pytest.mark.unit
    def test_location_marker(self):
        """위치 마커 테스트"""
        logger.info("용산구 위치 기반 테스트 실행")
        assert True
    
    @pytest.mark.api
    def test_api_marker(self):
        """API 마커 테스트"""
        logger.info("API 테스트 마커 확인")
        assert True
    
    @pytest.mark.mobile
    def test_mobile_marker(self):
        """모바일 마커 테스트"""
        logger.info("모바일 테스트 마커 확인")
        assert True
    
    @pytest.mark.e2e
    def test_e2e_marker(self):
        """E2E 마커 테스트"""
        logger.info("E2E 테스트 마커 확인")
        assert True
    
    @pytest.mark.smoke
    def test_smoke_marker(self):
        """스모크 마커 테스트"""
        logger.info("스모크 테스트 마커 확인")
        assert True


class TestEnvironmentValidation:
    """환경 검증 테스트 클래스"""
    
    @pytest.mark.unit
    def test_python_version(self):
        """Python 버전 확인"""
        import sys
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 11
        
        logger.info(f"Python 버전 확인: {version.major}.{version.minor}")
    
    @pytest.mark.unit  
    def test_required_packages(self):
        """필수 패키지 설치 확인"""
        try:
            import pytest
            import requests
            import pydantic
            logger.info("필수 패키지 설치 확인 완료")
            assert True
        except ImportError as e:
            pytest.fail(f"필수 패키지 누락: {e}")
    
    @pytest.mark.unit
    def test_directory_structure(self):
        """프로젝트 디렉토리 구조 확인"""
        import os
        from pathlib import Path
        
        required_dirs = ["tests", "pages", "api_clients", "utils", "config", "reports"]
        project_root = Path(__file__).parent.parent
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"디렉토리 누락: {dir_name}"
            assert dir_path.is_dir(), f"파일이 디렉토리가 아님: {dir_name}"
        
        logger.info("프로젝트 디렉토리 구조 확인 완료")


# 매개변수화된 테스트 예시
@pytest.mark.parametrize("test_input,expected", [
    ("hello", 5),
    ("world", 5),
    ("pytest", 6),
])
@pytest.mark.unit
def test_string_length(test_input: str, expected: int):
    """매개변수화된 테스트 예시"""
    assert len(test_input) == expected
    logger.info(f"문자열 길이 테스트: '{test_input}' = {expected}")


# 조건부 스킵 테스트 예시
@pytest.mark.skipif(
    condition=not hasattr(pytest, "importorskip"),
    reason="pytest 버전이 너무 낮음"
)
@pytest.mark.unit
def test_conditional_skip():
    """조건부 스킵 테스트 예시"""
    logger.info("조건부 스킵 테스트 실행")
    assert True
