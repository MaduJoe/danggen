"""
채팅 페이지 객체
"""

from typing import List
from appium.webdriver.common.appiumby import AppiumBy
import structlog

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class ChatPage(BasePage):
    """채팅 페이지"""
    
    def __init__(self, driver):
        super().__init__(driver)
        
        # 페이지 식별 요소
        self.page_identifier = (AppiumBy.ID, "com.towneers.www:id/layout_chat")
        
        # 채팅 입력 영역
        self.message_input = (AppiumBy.ID, "com.towneers.www:id/edit_message")
        self.send_button = (AppiumBy.ID, "com.towneers.www:id/btn_send")
        self.attach_button = (AppiumBy.ID, "com.towneers.www:id/btn_attach")
        
        # 채팅 메시지 영역
        self.message_list = (AppiumBy.ID, "com.towneers.www:id/recycler_messages")
        self.message_items = (AppiumBy.ID, "com.towneers.www:id/item_message")
        self.my_message_items = (AppiumBy.ID, "com.towneers.www:id/item_my_message")
        self.other_message_items = (AppiumBy.ID, "com.towneers.www:id/item_other_message")
        
        # 상단 정보
        self.chat_title = (AppiumBy.ID, "com.towneers.www:id/text_chat_title")
        self.product_info = (AppiumBy.ID, "com.towneers.www:id/layout_product_info")
        
        # 뒤로가기
        self.back_button = (AppiumBy.ID, "com.towneers.www:id/btn_back")
    
    def send_message(self, message: str) -> bool:
        """메시지 전송"""
        try:
            logger.info("메시지 전송", message=message[:50])
            
            # 메시지 입력
            if not self.input_text(self.message_input, message):
                return False
            
            # 전송 버튼 클릭
            if not self.click_element(self.send_button):
                return False
            
            logger.info("메시지 전송 완료")
            return True
            
        except Exception as e:
            logger.error("메시지 전송 실패", error=str(e))
            return False
    
    def get_messages(self) -> List:
        """메시지 목록 가져오기"""
        return self.find_elements(self.message_items)
    
    def get_my_messages(self) -> List:
        """내 메시지 목록 가져오기"""
        return self.find_elements(self.my_message_items)
    
    def get_other_messages(self) -> List:
        """상대방 메시지 목록 가져오기"""
        return self.find_elements(self.other_message_items)
    
    def get_last_message_text(self) -> str:
        """마지막 메시지 텍스트 가져오기"""
        messages = self.get_messages()
        if messages:
            return messages[-1].text
        return ""
    
    def click_product_info(self) -> bool:
        """상품 정보 클릭"""
        return self.click_element(self.product_info)
    
    def go_back(self) -> bool:
        """뒤로 가기"""
        return self.click_element(self.back_button)
