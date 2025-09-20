"""
로그인 페이지 객체
"""

from typing import Tuple
from appium.webdriver.common.appiumby import AppiumBy
import structlog

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class LoginPage(BasePage):
    """로그인 페이지"""
    
    def __init__(self, driver):
        super().__init__(driver)
        
        # 페이지 식별 요소
        self.page_identifier = (AppiumBy.ID, "com.towneers.www:id/login_title")
        
        # UI 요소 로케이터
        self.email_input = (AppiumBy.ID, "com.towneers.www:id/edit_email")
        self.password_input = (AppiumBy.ID, "com.towneers.www:id/edit_password")
        self.login_button = (AppiumBy.ID, "com.towneers.www:id/btn_login")
        self.signup_button = (AppiumBy.ID, "com.towneers.www:id/btn_signup")
        self.forgot_password_link = (AppiumBy.ID, "com.towneers.www:id/text_forgot_password")
        self.social_login_section = (AppiumBy.ID, "com.towneers.www:id/layout_social_login")
        self.kakao_login_button = (AppiumBy.ID, "com.towneers.www:id/btn_kakao_login")
        self.google_login_button = (AppiumBy.ID, "com.towneers.www:id/btn_google_login")
    
    def login_with_credentials(self, email: str, password: str) -> bool:
        """이메일/비밀번호로 로그인"""
        try:
            logger.info("로그인 시도", email=email)
            
            # 이메일 입력
            if not self.input_text(self.email_input, email):
                return False
            
            # 비밀번호 입력
            if not self.input_text(self.password_input, password):
                return False
            
            # 키보드 숨기기
            self.hide_keyboard()
            
            # 로그인 버튼 클릭
            if not self.click_element(self.login_button):
                return False
            
            logger.info("로그인 완료")
            return True
            
        except Exception as e:
            logger.error("로그인 실패", email=email, error=str(e))
            return False
    
    def click_signup(self) -> bool:
        """회원가입 버튼 클릭"""
        return self.click_element(self.signup_button)
    
    def click_forgot_password(self) -> bool:
        """비밀번호 찾기 클릭"""
        return self.click_element(self.forgot_password_link)
    
    def login_with_kakao(self) -> bool:
        """카카오 로그인"""
        return self.click_element(self.kakao_login_button)
    
    def login_with_google(self) -> bool:
        """구글 로그인"""
        return self.click_element(self.google_login_button)
