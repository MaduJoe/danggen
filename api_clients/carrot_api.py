"""
당근마켓 API 통합 클라이언트

모든 API 클라이언트를 통합한 메인 클라이언트
"""

import structlog
from typing import Optional, Dict, Any

from .user_client import UserAPIClient
from .product_client import ProductAPIClient
from .chat_client import ChatAPIClient
from .community_client import CommunityAPIClient
from .auth_manager import get_auth_manager
from .models import *

logger = structlog.get_logger(__name__)


class CarrotAPIClient:
    """당근마켓 API 통합 클라이언트"""
    
    def __init__(self):
        self.users = UserAPIClient()
        self.products = ProductAPIClient()
        self.chat = ChatAPIClient()
        self.community = CommunityAPIClient()
        self.auth_manager = get_auth_manager()
        
        logger.info("당근마켓 API 클라이언트 초기화 완료")
    
    # 편의 메서드들
    def create_user(self, user_data: UserCreate) -> UserProfile:
        """사용자 생성"""
        return self.users.create_user(user_data)
    
    def delete_user(self, user_id: str) -> bool:
        """사용자 삭제"""
        return self.users.delete_user(user_id)
    
    def create_product(self, user_id: str, product_data: ProductCreate) -> Product:
        """상품 등록"""
        return self.products.create_product(user_id, product_data)
    
    def delete_product(self, user_id: str, product_id: str) -> bool:
        """상품 삭제"""
        return self.products.delete_product(user_id, product_id)
    
    def get_product_list(self, search_params: Optional[ProductSearchParams] = None) -> Dict[str, Any]:
        """상품 목록 조회"""
        return self.products.get_product_list(search_params)
    
    def send_message(self, user_id: str, message_data: MessageCreate) -> Message:
        """메시지 전송"""
        return self.chat.send_message(user_id, message_data)
    
    def get_chat_history(self, user_id: str, chat_room_id: str) -> Dict[str, Any]:
        """채팅 히스토리 조회"""
        return self.chat.get_chat_history(user_id, chat_room_id)
    
    def login(self, username: str, password: str) -> LoginResponse:
        """로그인"""
        return self.users.login(username, password)
    
    def logout(self, user_id: str) -> bool:
        """로그아웃"""
        return self.users.logout(user_id)
    
    # 커뮤니티 관련 편의 메서드들
    def create_community_post(self, user_id: str, post_data: CommunityPostCreate) -> CommunityPost:
        """커뮤니티 게시글 생성"""
        return self.community.create_community_post(user_id, post_data)
    
    def get_community_posts(self, search_params: Optional[CommunityPostSearchParams] = None) -> CommunityPostListResponse:
        """커뮤니티 게시글 목록 조회"""
        return self.community.get_community_posts(search_params)
    
    def delete_community_post(self, user_id: str, post_id: str) -> bool:
        """커뮤니티 게시글 삭제"""
        return self.community.delete_community_post(user_id, post_id)
    
    def create_comment(self, user_id: str, post_id: str, comment_data: CommunityCommentCreate) -> CommunityComment:
        """댓글 생성"""
        return self.community.create_comment(user_id, post_id, comment_data)
    
    def get_comments(self, post_id: str, limit: int = 50, offset: int = 0) -> CommunityCommentListResponse:
        """댓글 목록 조회"""
        return self.community.get_comments(post_id, limit, offset)
    
    def find_posts_by_location(self, district: str, neighborhood: str, 
                              category: Optional[CommunityCategory] = None,
                              limit: int = 20) -> List[CommunityPost]:
        """위치별 게시글 조회"""
        return self.community.find_posts_by_location(district, neighborhood, category, limit)
    
    def cleanup_community_test_data(self, author_id: str) -> bool:
        """커뮤니티 테스트 데이터 정리"""
        return self.community.cleanup_test_posts(author_id)
    
    def health_check(self) -> bool:
        """API 서버 상태 확인"""
        return self.users.health_check()


# 전역 클라이언트 인스턴스
_api_client = None


def get_api_client() -> CarrotAPIClient:
    """전역 API 클라이언트 반환"""
    global _api_client
    if _api_client is None:
        _api_client = CarrotAPIClient()
    return _api_client


# 테스트 호환성을 위한 별칭
CarrotAPI = CarrotAPIClient