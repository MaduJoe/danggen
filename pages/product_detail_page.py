"""
상품 상세 페이지 객체
"""

from appium.webdriver.common.appiumby import AppiumBy
import structlog

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class ProductDetailPage(BasePage):
    """상품 상세 페이지"""
    
    def __init__(self, driver):
        super().__init__(driver)
        
        # 페이지 식별 요소
        self.page_identifier = (AppiumBy.ID, "com.towneers.www:id/layout_product_detail")
        
        # 상품 정보
        self.product_title = (AppiumBy.ID, "com.towneers.www:id/text_product_title")
        self.product_price = (AppiumBy.ID, "com.towneers.www:id/text_product_price")
        self.product_description = (AppiumBy.ID, "com.towneers.www:id/text_product_description")
        self.product_images = (AppiumBy.ID, "com.towneers.www:id/viewpager_images")
        
        # 판매자 정보
        self.seller_profile = (AppiumBy.ID, "com.towneers.www:id/layout_seller_info")
        self.seller_name = (AppiumBy.ID, "com.towneers.www:id/text_seller_name")
        self.seller_manner_temp = (AppiumBy.ID, "com.towneers.www:id/text_manner_temperature")
        
        # 액션 버튼들
        self.chat_button = (AppiumBy.ID, "com.towneers.www:id/btn_chat")
        self.like_button = (AppiumBy.ID, "com.towneers.www:id/btn_like")
        self.share_button = (AppiumBy.ID, "com.towneers.www:id/btn_share")
        self.report_button = (AppiumBy.ID, "com.towneers.www:id/btn_report")
        
        # 기타
        self.back_button = (AppiumBy.ID, "com.towneers.www:id/btn_back")
        self.more_button = (AppiumBy.ID, "com.towneers.www:id/btn_more")
    
    def get_product_title(self) -> str:
        """상품 제목 가져오기"""
        return self.get_text(self.product_title)
    
    def get_product_price(self) -> str:
        """상품 가격 가져오기"""
        return self.get_text(self.product_price)
    
    def get_product_description(self) -> str:
        """상품 설명 가져오기"""
        return self.get_text(self.product_description)
    
    def get_seller_name(self) -> str:
        """판매자 이름 가져오기"""
        return self.get_text(self.seller_name)
    
    def start_chat(self) -> bool:
        """채팅하기 버튼 클릭"""
        logger.info("채팅하기 버튼 클릭")
        return self.click_element(self.chat_button)
    
    def toggle_like(self) -> bool:
        """찜하기/찜해제"""
        return self.click_element(self.like_button)
    
    def share_product(self) -> bool:
        """상품 공유"""
        return self.click_element(self.share_button)
    
    def report_product(self) -> bool:
        """신고하기"""
        return self.click_element(self.report_button)
    
    def go_back(self) -> bool:
        """뒤로 가기"""
        return self.click_element(self.back_button)
