"""
채팅 관리 API 클라이언트

채팅방 생성, 메시지 전송, 히스토리 조회 등의 API 메서드 구현
"""

from typing import Optional, List, Dict, Any
import structlog

from .base_client import BaseAPIClient, APIError
from .models import ChatRoom, ChatRoomCreate, Message, MessageCreate

logger = structlog.get_logger(__name__)


class ChatAPIClient(BaseAPIClient):
    """채팅 관리 API 클라이언트"""
    
    def __init__(self):
        super().__init__()
        self.base_url = self.config.endpoints.chat_url
    
    def send_message(self, user_id: str, message_data: MessageCreate) -> Message:
        """메시지 전송"""
        url = f"{self.base_url}/messages"
        
        try:
            logger.info("메시지 전송", user_id=user_id, 
                       chat_room_id=message_data.chat_room_id)
            
            response = self._make_request(
                method="POST",
                url=url,
                json=message_data.dict(),
                user_id=user_id
            )
            
            if response.status_code == 201:
                message = Message(**response.json()["data"])
                logger.info("메시지 전송 성공", message_id=message.message_id)
                return message
            
            else:
                self._handle_error_response(response)
                
        except Exception as e:
            logger.error("메시지 전송 실패", user_id=user_id, error=str(e))
            raise
    
    def get_chat_history(self, user_id: str, chat_room_id: str, 
                        page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """채팅 히스토리 조회"""
        url = f"{self.base_url}/rooms/{chat_room_id}/messages"
        
        params = {"page": page, "page_size": page_size}
        
        try:
            response = self._make_request("GET", url, params=params, user_id=user_id)
            if response.status_code == 200:
                return response.json()["data"]
            else:
                self._handle_error_response(response)
        except Exception as e:
            logger.error("채팅 히스토리 조회 실패", 
                        chat_room_id=chat_room_id, error=str(e))
            raise
    
    def create_chat_room(self, user_id: str, room_data: ChatRoomCreate) -> ChatRoom:
        """채팅방 생성"""
        url = f"{self.base_url}/rooms"
        
        try:
            response = self._make_request(
                method="POST",
                url=url,
                json=room_data.dict(),
                user_id=user_id
            )
            
            if response.status_code == 201:
                return ChatRoom(**response.json()["data"])
            else:
                self._handle_error_response(response)
        except Exception as e:
            logger.error("채팅방 생성 실패", user_id=user_id, error=str(e))
            raise


# 테스트 호환성을 위한 별칭
ChatClient = ChatAPIClient