"""
홈 페이지 객체
"""

from typing import List
from appium.webdriver.common.appiumby import AppiumBy
import structlog

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class HomePage(BasePage):
    """홈 페이지"""
    
    def __init__(self, driver):
        super().__init__(driver)
        
        # 페이지 식별 요소
        self.page_identifier = (AppiumBy.ID, "com.towneers.www:id/bottom_navigation")
        
        # 하단 네비게이션
        self.bottom_nav_home = (AppiumBy.ID, "com.towneers.www:id/nav_home")
        self.bottom_nav_community = (AppiumBy.ID, "com.towneers.www:id/nav_community")
        self.bottom_nav_around = (AppiumBy.ID, "com.towneers.www:id/nav_around")
        self.bottom_nav_chat = (AppiumBy.ID, "com.towneers.www:id/nav_chat")
        self.bottom_nav_profile = (AppiumBy.ID, "com.towneers.www:id/nav_profile")
        
        # 상단 영역
        self.location_button = (AppiumBy.ID, "com.towneers.www:id/btn_location")
        self.search_button = (AppiumBy.ID, "com.towneers.www:id/btn_search")
        self.notification_button = (AppiumBy.ID, "com.towneers.www:id/btn_notification")
        
        # 상품 목록
        self.product_list = (AppiumBy.ID, "com.towneers.www:id/recycler_products")
        self.product_items = (AppiumBy.ID, "com.towneers.www:id/item_product")
        
        # 플로팅 버튼
        self.fab_write = (AppiumBy.ID, "com.towneers.www:id/fab_write")
    
    def click_search(self) -> bool:
        """검색 버튼 클릭"""
        return self.click_element(self.search_button)
    
    def click_location(self) -> bool:
        """위치 설정 클릭"""
        return self.click_element(self.location_button)
    
    def navigate_to_community(self) -> bool:
        """동네생활 탭으로 이동"""
        return self.click_element(self.bottom_nav_community)
    
    def navigate_to_chat(self) -> bool:
        """채팅 탭으로 이동"""
        return self.click_element(self.bottom_nav_chat)
    
    def navigate_to_profile(self) -> bool:
        """프로필 탭으로 이동"""
        return self.click_element(self.bottom_nav_profile)
    
    def click_write_post(self) -> bool:
        """글쓰기 버튼 클릭"""
        return self.click_element(self.fab_write)
    
    def get_product_items(self) -> List:
        """상품 아이템 목록 가져오기"""
        return self.find_elements(self.product_items)
    
    def click_first_product(self) -> bool:
        """첫 번째 상품 클릭"""
        products = self.get_product_items()
        if products:
            products[0].click()
            return True
        return False
