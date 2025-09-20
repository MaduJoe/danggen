"""
Appium 모바일 자동화 드라이버

Android 디바이스 대상 Appium 드라이버 설정 및 관리
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union
import structlog

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException
)

logger = structlog.get_logger(__name__)


class MobileDriverError(Exception):
    """모바일 드라이버 관련 예외"""
    pass


class MobileDriver:
    """Appium 모바일 드라이버 클래스"""
    
    def __init__(self, 
                 appium_server_url: Optional[str] = None,
                 device_name: Optional[str] = None,
                 platform_version: Optional[str] = None,
                 app_package: Optional[str] = None,
                 app_activity: Optional[str] = None,
                 app_path: Optional[str] = None):
        
        # 환경 변수에서 설정 로드
        self.appium_server_url = appium_server_url or os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")
        self.device_name = device_name or os.getenv("DEVICE_NAME", "Android Emulator")
        self.platform_version = platform_version or os.getenv("PLATFORM_VERSION", "11.0")
        self.app_package = app_package or os.getenv("APP_PACKAGE", "com.towneers.www")
        self.app_activity = app_activity or os.getenv("APP_ACTIVITY", ".SplashActivity")
        self.app_path = app_path or os.getenv("APP_PATH")
        
        # 드라이버 관련
        self.driver: Optional[webdriver.Remote] = None
        self.implicit_wait_time = 10
        self.explicit_wait_time = 30
        
        # 스크린샷 관련
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # 디바이스 정보
        self.device_info: Dict[str, Any] = {}
        
        logger.info("MobileDriver 초기화 완료", 
                   server_url=self.appium_server_url,
                   device_name=self.device_name)
    
    @property
    def desired_capabilities(self) -> Dict[str, Any]:
        """Android desired capabilities 설정"""
        caps = {
            # 플랫폼 설정
            "platformName": "Android",
            "deviceName": self.device_name,
            "platformVersion": self.platform_version,
            "automationName": "UiAutomator2",
            
            # 앱 설정
            "appPackage": self.app_package,
            "appActivity": self.app_activity,
            
            # 세션 설정
            "noReset": True,  # 앱 데이터 유지
            "fullReset": False,  # 앱 재설치 하지 않음
            "newCommandTimeout": 300,  # 5분 타임아웃
            
            # 성능 설정
            "skipDeviceInitialization": False,
            "skipServerInstallation": True,
            "ignoreHiddenApiPolicyError": True,
            
            # 위치 권한
            "autoGrantPermissions": True,
            "autoAcceptAlerts": True,
            
            # 네트워크 설정
            "networkSpeed": "full",
            
            # 로깅
            "enablePerformanceLogging": False,
        }
        
        # APK 파일 경로가 있으면 추가
        if self.app_path and os.path.exists(self.app_path):
            caps["app"] = self.app_path
            logger.info("APK 파일 경로 설정", app_path=self.app_path)
        
        # Android SDK 경로 설정
        android_home = os.getenv("ANDROID_HOME")
        if android_home:
            caps["androidDeviceReadyTimeout"] = 60
            caps["androidInstallTimeout"] = 90
        
        return caps
    
    def start_driver(self) -> webdriver.Remote:
        """드라이버 시작"""
        if self.driver:
            logger.warning("드라이버가 이미 실행 중입니다")
            return self.driver
        
        try:
            logger.info("Appium 드라이버 시작", server_url=self.appium_server_url)
            
            self.driver = webdriver.Remote(
                command_executor=self.appium_server_url,
                desired_capabilities=self.desired_capabilities
            )
            
            # 암시적 대기 시간 설정
            self.driver.implicitly_wait(self.implicit_wait_time)
            
            # 디바이스 정보 수집
            self._collect_device_info()
            
            logger.info("Appium 드라이버 시작 완료", 
                       session_id=self.driver.session_id)
            
            return self.driver
            
        except Exception as e:
            logger.error("Appium 드라이버 시작 실패", error=str(e))
            raise MobileDriverError(f"드라이버 시작 실패: {e}")
    
    def stop_driver(self) -> None:
        """드라이버 종료"""
        if self.driver:
            try:
                session_id = self.driver.session_id
                self.driver.quit()
                self.driver = None
                logger.info("Appium 드라이버 종료 완료", session_id=session_id)
            except Exception as e:
                logger.error("드라이버 종료 중 오류", error=str(e))
                self.driver = None
        else:
            logger.info("종료할 드라이버가 없습니다")
    
    def restart_driver(self) -> webdriver.Remote:
        """드라이버 재시작"""
        logger.info("Appium 드라이버 재시작")
        self.stop_driver()
        time.sleep(2)  # 잠시 대기
        return self.start_driver()
    
    def _collect_device_info(self) -> None:
        """디바이스 정보 수집"""
        if not self.driver:
            return
        
        try:
            self.device_info = {
                "platform_name": self.driver.capabilities.get("platformName"),
                "platform_version": self.driver.capabilities.get("platformVersion"),
                "device_name": self.driver.capabilities.get("deviceName"),
                "device_udid": self.driver.capabilities.get("udid"),
                "automation_name": self.driver.capabilities.get("automationName"),
                "app_package": self.driver.current_package,
                "app_activity": self.driver.current_activity,
                "screen_size": self.driver.get_window_size(),
            }
            
            logger.info("디바이스 정보 수집 완료", device_info=self.device_info)
            
        except Exception as e:
            logger.warning("디바이스 정보 수집 실패", error=str(e))
    
    def set_location(self, latitude: float, longitude: float, altitude: Optional[float] = None) -> bool:
        """위치 정보 설정 (모킹)"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        try:
            location_data = {
                "latitude": latitude,
                "longitude": longitude,
            }
            
            if altitude is not None:
                location_data["altitude"] = altitude
            
            self.driver.set_location(**location_data)
            
            logger.info("위치 정보 설정 완료", 
                       latitude=latitude, longitude=longitude)
            
            return True
            
        except Exception as e:
            logger.error("위치 정보 설정 실패", 
                        latitude=latitude, longitude=longitude, error=str(e))
            return False
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """스크린샷 캡처"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # 파일 확장자 확인
        if not filename.endswith('.png'):
            filename += '.png'
        
        screenshot_path = self.screenshot_dir / filename
        
        try:
            self.driver.save_screenshot(str(screenshot_path))
            logger.info("스크린샷 캡처 완료", path=str(screenshot_path))
            return str(screenshot_path)
            
        except Exception as e:
            logger.error("스크린샷 캡처 실패", error=str(e))
            raise MobileDriverError(f"스크린샷 캡처 실패: {e}")
    
    def wait_for_element(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> Any:
        """요소가 나타날 때까지 대기"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        timeout = timeout or self.explicit_wait_time
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            element = wait.until(EC.presence_of_element_located(locator))
            logger.debug("요소 찾기 성공", locator=locator)
            return element
            
        except TimeoutException:
            logger.error("요소 찾기 타임아웃", locator=locator, timeout=timeout)
            raise
    
    def wait_for_element_clickable(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> Any:
        """요소가 클릭 가능할 때까지 대기"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        timeout = timeout or self.explicit_wait_time
        wait = WebDriverWait(self.driver, timeout)
        
        try:
            element = wait.until(EC.element_to_be_clickable(locator))
            logger.debug("클릭 가능한 요소 찾기 성공", locator=locator)
            return element
            
        except TimeoutException:
            logger.error("클릭 가능한 요소 찾기 타임아웃", locator=locator, timeout=timeout)
            raise
    
    def find_element_safe(self, locator: Tuple[str, str]) -> Optional[Any]:
        """안전한 요소 찾기 (예외 발생하지 않음)"""
        if not self.driver:
            return None
        
        try:
            return self.driver.find_element(*locator)
        except NoSuchElementException:
            return None
        except Exception as e:
            logger.warning("요소 찾기 중 예외", locator=locator, error=str(e))
            return None
    
    def is_element_displayed(self, locator: Tuple[str, str]) -> bool:
        """요소가 화면에 표시되는지 확인"""
        element = self.find_element_safe(locator)
        if element:
            try:
                return element.is_displayed()
            except:
                return False
        return False
    
    def swipe_up(self, duration: int = 800) -> None:
        """위로 스와이프"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = size["height"] * 3 // 4
        end_x = start_x
        end_y = size["height"] // 4
        
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
        logger.debug("위로 스와이프 실행")
    
    def swipe_down(self, duration: int = 800) -> None:
        """아래로 스와이프"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = size["height"] // 4
        end_x = start_x
        end_y = size["height"] * 3 // 4
        
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
        logger.debug("아래로 스와이프 실행")
    
    def tap_coordinates(self, x: int, y: int) -> None:
        """좌표 탭"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        self.driver.tap([(x, y)])
        logger.debug("좌표 탭 실행", x=x, y=y)
    
    def go_back(self) -> None:
        """뒤로 가기"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        self.driver.back()
        logger.debug("뒤로 가기 실행")
    
    def get_current_activity(self) -> str:
        """현재 액티비티 반환"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        return self.driver.current_activity
    
    def get_current_package(self) -> str:
        """현재 패키지 반환"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        return self.driver.current_package
    
    def is_app_installed(self, package_name: Optional[str] = None) -> bool:
        """앱 설치 여부 확인"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        package = package_name or self.app_package
        return self.driver.is_app_installed(package)
    
    def terminate_app(self, package_name: Optional[str] = None) -> bool:
        """앱 종료"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        package = package_name or self.app_package
        return self.driver.terminate_app(package)
    
    def activate_app(self, package_name: Optional[str] = None) -> None:
        """앱 활성화"""
        if not self.driver:
            raise MobileDriverError("드라이버가 시작되지 않았습니다")
        
        package = package_name or self.app_package
        self.driver.activate_app(package)
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop_driver()


# 전역 드라이버 인스턴스
_mobile_driver = None


def get_mobile_driver() -> MobileDriver:
    """전역 모바일 드라이버 반환"""
    global _mobile_driver
    if _mobile_driver is None:
        _mobile_driver = MobileDriver()
    return _mobile_driver


def create_mobile_driver(**kwargs) -> MobileDriver:
    """새로운 모바일 드라이버 생성"""
    return MobileDriver(**kwargs)
