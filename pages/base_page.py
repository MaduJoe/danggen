"""
기본 페이지 클래스

모든 페이지 객체가 상속받는 기본 클래스
"""

import time
from typing import Optional, List, Tuple, Any, Union
import structlog
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from appium.webdriver.common.appiumby import AppiumBy

from utils.mobile_driver import MobileDriver, MobileDriverError

logger = structlog.get_logger(__name__)


class PageError(Exception):
    """페이지 관련 예외"""
    pass


class BasePage:
    """기본 페이지 클래스"""
    
    def __init__(self, driver: MobileDriver):
        self.driver = driver
        self.wait_timeout = 30
        self.page_load_timeout = 20
        
        # 페이지별 고유 요소 (서브클래스에서 정의)
        self.page_identifier: Optional[Tuple[str, str]] = None
        
        logger.debug(f"{self.__class__.__name__} 페이지 객체 생성")
    
    @property
    def mobile_driver(self):
        """모바일 드라이버 반환"""
        if not self.driver.driver:
            raise PageError("모바일 드라이버가 시작되지 않았습니다")
        return self.driver.driver
    
    def wait_for_page_load(self, timeout: Optional[int] = None) -> bool:
        """페이지 로딩 대기"""
        if not self.page_identifier:
            logger.warning(f"{self.__class__.__name__}에 page_identifier가 정의되지 않음")
            return True
        
        timeout = timeout or self.page_load_timeout
        
        try:
            self.wait_for_element(self.page_identifier, timeout)
            logger.info(f"{self.__class__.__name__} 페이지 로딩 완료")
            return True
            
        except TimeoutException:
            logger.error(f"{self.__class__.__name__} 페이지 로딩 타임아웃")
            return False
    
    def is_page_loaded(self) -> bool:
        """페이지 로딩 상태 확인"""
        if not self.page_identifier:
            return True
        
        return self.is_element_displayed(self.page_identifier)
    
    def find_element(self, locator: Tuple[str, str]) -> Any:
        """요소 찾기"""
        try:
            return self.mobile_driver.find_element(*locator)
        except NoSuchElementException:
            logger.error("요소를 찾을 수 없음", locator=locator)
            raise PageError(f"요소를 찾을 수 없음: {locator}")
    
    def find_elements(self, locator: Tuple[str, str]) -> List[Any]:
        """여러 요소 찾기"""
        try:
            return self.mobile_driver.find_elements(*locator)
        except Exception as e:
            logger.error("요소들을 찾을 수 없음", locator=locator, error=str(e))
            return []
    
    def find_element_safe(self, locator: Tuple[str, str]) -> Optional[Any]:
        """안전한 요소 찾기 (예외 발생하지 않음)"""
        return self.driver.find_element_safe(locator)
    
    def wait_for_element(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> Any:
        """요소가 나타날 때까지 대기"""
        timeout = timeout or self.wait_timeout
        return self.driver.wait_for_element(locator, timeout)
    
    def wait_for_element_clickable(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> Any:
        """요소가 클릭 가능할 때까지 대기"""
        timeout = timeout or self.wait_timeout
        return self.driver.wait_for_element_clickable(locator, timeout)
    
    def is_element_displayed(self, locator: Tuple[str, str]) -> bool:
        """요소가 화면에 표시되는지 확인"""
        return self.driver.is_element_displayed(locator)
    
    def click_element(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> bool:
        """요소 클릭"""
        try:
            element = self.wait_for_element_clickable(locator, timeout)
            element.click()
            logger.debug("요소 클릭 성공", locator=locator)
            return True
            
        except TimeoutException:
            logger.error("요소 클릭 타임아웃", locator=locator)
            return False
        except Exception as e:
            logger.error("요소 클릭 실패", locator=locator, error=str(e))
            return False
    
    def input_text(self, locator: Tuple[str, str], text: str, clear: bool = True) -> bool:
        """텍스트 입력"""
        try:
            element = self.wait_for_element(locator)
            
            if clear:
                element.clear()
            
            element.send_keys(text)
            logger.debug("텍스트 입력 성공", locator=locator, text=text[:50])
            return True
            
        except Exception as e:
            logger.error("텍스트 입력 실패", locator=locator, error=str(e))
            return False
    
    def get_text(self, locator: Tuple[str, str]) -> str:
        """요소의 텍스트 가져오기"""
        try:
            element = self.find_element(locator)
            text = element.text
            logger.debug("텍스트 가져오기 성공", locator=locator, text=text[:50])
            return text
            
        except Exception as e:
            logger.error("텍스트 가져오기 실패", locator=locator, error=str(e))
            return ""
    
    def get_attribute(self, locator: Tuple[str, str], attribute: str) -> str:
        """요소의 속성 가져오기"""
        try:
            element = self.find_element(locator)
            value = element.get_attribute(attribute)
            logger.debug("속성 가져오기 성공", locator=locator, attribute=attribute)
            return value or ""
            
        except Exception as e:
            logger.error("속성 가져오기 실패", locator=locator, attribute=attribute, error=str(e))
            return ""
    
    def swipe_up(self, duration: int = 800) -> None:
        """위로 스와이프"""
        self.driver.swipe_up(duration)
        time.sleep(0.5)  # 스와이프 후 잠시 대기
    
    def swipe_down(self, duration: int = 800) -> None:
        """아래로 스와이프"""
        self.driver.swipe_down(duration)
        time.sleep(0.5)
    
    def scroll_to_element(self, locator: Tuple[str, str], max_scrolls: int = 5) -> bool:
        """요소가 보일 때까지 스크롤"""
        for i in range(max_scrolls):
            if self.is_element_displayed(locator):
                logger.debug("스크롤로 요소 찾기 성공", locator=locator, scrolls=i)
                return True
            
            self.swipe_up()
        
        logger.warning("스크롤해도 요소를 찾을 수 없음", locator=locator)
        return False
    
    def wait_and_click(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> bool:
        """대기 후 클릭"""
        return self.click_element(locator, timeout)
    
    def wait_and_input(self, locator: Tuple[str, str], text: str, timeout: Optional[int] = None) -> bool:
        """대기 후 텍스트 입력"""
        try:
            self.wait_for_element(locator, timeout)
            return self.input_text(locator, text)
        except:
            return False
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """스크린샷 캡처"""
        if not filename:
            page_name = self.__class__.__name__.lower()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{page_name}_{timestamp}.png"
        
        return self.driver.take_screenshot(filename)
    
    def go_back(self) -> None:
        """뒤로 가기"""
        self.driver.go_back()
        time.sleep(1)  # 뒤로 가기 후 잠시 대기
    
    def refresh_page(self) -> None:
        """페이지 새로고침 (당근마켓에서는 아래로 당기기)"""
        self.swipe_down(duration=1000)
        time.sleep(2)
    
    def hide_keyboard(self) -> bool:
        """키보드 숨기기"""
        try:
            self.mobile_driver.hide_keyboard()
            return True
        except:
            return False
    
    def tap_coordinates(self, x: int, y: int) -> None:
        """좌표 탭"""
        self.driver.tap_coordinates(x, y)
        time.sleep(0.5)
    
    def long_press_element(self, locator: Tuple[str, str], duration: int = 1000) -> bool:
        """요소 길게 누르기"""
        try:
            element = self.find_element(locator)
            self.mobile_driver.tap([(element.location['x'], element.location['y'])], duration)
            logger.debug("요소 길게 누르기 성공", locator=locator)
            return True
        except Exception as e:
            logger.error("요소 길게 누르기 실패", locator=locator, error=str(e))
            return False
    
    def wait_for_text_in_element(self, locator: Tuple[str, str], text: str, timeout: Optional[int] = None) -> bool:
        """요소에 특정 텍스트가 나타날 때까지 대기"""
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(self.mobile_driver, timeout)
        
        try:
            wait.until(EC.text_to_be_present_in_element(locator, text))
            return True
        except TimeoutException:
            logger.error("요소에 텍스트 나타나기 타임아웃", locator=locator, text=text)
            return False
    
    def get_page_source(self) -> str:
        """페이지 소스 가져오기"""
        try:
            return self.mobile_driver.page_source
        except Exception as e:
            logger.error("페이지 소스 가져오기 실패", error=str(e))
            return ""
    
    def is_element_enabled(self, locator: Tuple[str, str]) -> bool:
        """요소가 활성화되어 있는지 확인"""
        try:
            element = self.find_element(locator)
            return element.is_enabled()
        except:
            return False
    
    def get_element_size(self, locator: Tuple[str, str]) -> dict:
        """요소 크기 가져오기"""
        try:
            element = self.find_element(locator)
            return element.size
        except:
            return {"width": 0, "height": 0}
    
    def get_element_location(self, locator: Tuple[str, str]) -> dict:
        """요소 위치 가져오기"""
        try:
            element = self.find_element(locator)
            return element.location
        except:
            return {"x": 0, "y": 0}
