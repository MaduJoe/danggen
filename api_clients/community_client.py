"""
커뮤니티 관리 API 클라이언트

동네생활 게시글 및 댓글 관련 API 메서드 구현
"""

from typing import Optional, List, Dict, Any
import requests
import structlog
from pydantic import ValidationError
import time

from config.api_config import get_config
from .auth_manager import get_auth_manager, AuthenticationError
from .models import (
    CommunityPost, CommunityPostCreate, CommunityPostUpdate,
    CommunityComment, CommunityCommentCreate, 
    CommunityPostSearchParams, CommunityPostListResponse, CommunityCommentListResponse,
    CommunityCategory, Location, APIResponse, ErrorResponse
)
from .base_client import BaseAPIClient

logger = structlog.get_logger(__name__)


class CommunityAPIClient(BaseAPIClient):
    """커뮤니티 관리 API 클라이언트"""
    
    def __init__(self):
        super().__init__()
        self.auth_manager = get_auth_manager()
        self.base_url = f"{self.config.base_url}/api/v1/community"
    
    def create_community_post(self, user_id: str, post_data: CommunityPostCreate) -> CommunityPost:
        """
        커뮤니티 게시글 생성
        
        Args:
            user_id: 작성자 사용자 ID
            post_data: 게시글 생성 데이터
            
        Returns:
            CommunityPost: 생성된 게시글 정보
            
        Raises:
            APIError: API 호출 실패
            ValidationError: 데이터 검증 실패
        """
        url = f"{self.base_url}/posts"
        
        try:
            logger.info("커뮤니티 게시글 생성 요청", 
                       user_id=user_id, title=post_data.title[:30])
            
            # 요청 데이터 준비
            data = post_data.model_dump()
            data["author_id"] = user_id
            
            response = self._make_request(
                method="POST",
                url=url,
                json=data,
                user_id=user_id
            )
            
            if response.status_code == 201:
                post_data = response.json()
                post = CommunityPost(**post_data)
                
                logger.info("커뮤니티 게시글 생성 성공", 
                           post_id=post.post_id, user_id=user_id)
                return post
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("커뮤니티 게시글 생성 데이터 검증 실패", 
                        user_id=user_id, error=str(e))
            raise
        except Exception as e:
            logger.error("커뮤니티 게시글 생성 실패", 
                        user_id=user_id, error=str(e))
            raise
    
    def get_community_posts(self, search_params: Optional[CommunityPostSearchParams] = None) -> CommunityPostListResponse:
        """
        커뮤니티 게시글 목록 조회
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            CommunityPostListResponse: 게시글 목록 응답
        """
        url = f"{self.base_url}/posts"
        
        try:
            params = {}
            if search_params:
                params = search_params.model_dump(exclude_none=True)
            
            logger.info("커뮤니티 게시글 목록 조회", params=params)
            
            response = self._make_request(
                method="GET",
                url=url,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                post_list = CommunityPostListResponse(**data)
                
                logger.info("커뮤니티 게시글 목록 조회 성공", count=len(post_list.posts))
                return post_list
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("커뮤니티 게시글 목록 응답 데이터 검증 실패", error=str(e))
            raise
        except Exception as e:
            logger.error("커뮤니티 게시글 목록 조회 실패", error=str(e))
            raise
    
    def get_community_post(self, post_id: str) -> Optional[CommunityPost]:
        """
        특정 커뮤니티 게시글 조회
        
        Args:
            post_id: 게시글 ID
            
        Returns:
            Optional[CommunityPost]: 게시글 정보 (없으면 None)
        """
        url = f"{self.base_url}/posts/{post_id}"
        
        try:
            logger.info("커뮤니티 게시글 조회", post_id=post_id)
            
            response = self._make_request(
                method="GET",
                url=url
            )
            
            if response.status_code == 200:
                data = response.json()
                post = CommunityPost(**data)
                
                logger.info("커뮤니티 게시글 조회 성공", post_id=post_id)
                return post
            
            elif response.status_code == 404:
                logger.warning("커뮤니티 게시글을 찾을 수 없음", post_id=post_id)
                return None
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("커뮤니티 게시글 응답 데이터 검증 실패", 
                        post_id=post_id, error=str(e))
            raise
        except Exception as e:
            logger.error("커뮤니티 게시글 조회 실패", 
                        post_id=post_id, error=str(e))
            raise
    
    def update_community_post(self, user_id: str, post_id: str, 
                            update_data: CommunityPostUpdate) -> Optional[CommunityPost]:
        """
        커뮤니티 게시글 수정
        
        Args:
            user_id: 사용자 ID
            post_id: 게시글 ID
            update_data: 수정 데이터
            
        Returns:
            Optional[CommunityPost]: 수정된 게시글 정보
        """
        url = f"{self.base_url}/posts/{post_id}"
        
        try:
            logger.info("커뮤니티 게시글 수정", post_id=post_id, user_id=user_id)
            
            data = update_data.model_dump(exclude_none=True)
            
            response = self._make_request(
                method="PUT",
                url=url,
                json=data,
                user_id=user_id
            )
            
            if response.status_code == 200:
                data = response.json()
                post = CommunityPost(**data)
                
                logger.info("커뮤니티 게시글 수정 성공", post_id=post_id)
                return post
            
            else:
                self._handle_error_response(response)
                return None
                
        except Exception as e:
            logger.error("커뮤니티 게시글 수정 실패", 
                        post_id=post_id, user_id=user_id, error=str(e))
            raise
    
    def delete_community_post(self, user_id: str, post_id: str) -> bool:
        """
        커뮤니티 게시글 삭제
        
        Args:
            user_id: 사용자 ID
            post_id: 게시글 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        url = f"{self.base_url}/posts/{post_id}"
        
        try:
            logger.info("커뮤니티 게시글 삭제", post_id=post_id, user_id=user_id)
            
            response = self._make_request(
                method="DELETE",
                url=url,
                user_id=user_id
            )
            
            if response.status_code == 204:
                logger.info("커뮤니티 게시글 삭제 성공", post_id=post_id)
                return True
            
            else:
                self._handle_error_response(response)
                return False
                
        except Exception as e:
            logger.error("커뮤니티 게시글 삭제 실패", 
                        post_id=post_id, user_id=user_id, error=str(e))
            raise
    
    def create_comment(self, user_id: str, post_id: str, 
                      comment_data: CommunityCommentCreate) -> CommunityComment:
        """
        댓글 생성
        
        Args:
            user_id: 작성자 사용자 ID
            post_id: 게시글 ID
            comment_data: 댓글 생성 데이터
            
        Returns:
            CommunityComment: 생성된 댓글 정보
        """
        url = f"{self.base_url}/posts/{post_id}/comments"
        
        try:
            logger.info("댓글 생성 요청", 
                       post_id=post_id, user_id=user_id, 
                       content=comment_data.content[:30])
            
            data = comment_data.model_dump()
            data["author_id"] = user_id
            
            response = self._make_request(
                method="POST",
                url=url,
                json=data,
                user_id=user_id
            )
            
            if response.status_code == 201:
                comment_data = response.json()
                comment = CommunityComment(**comment_data)
                
                logger.info("댓글 생성 성공", 
                           comment_id=comment.comment_id, post_id=post_id)
                return comment
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("댓글 생성 데이터 검증 실패", 
                        post_id=post_id, user_id=user_id, error=str(e))
            raise
        except Exception as e:
            logger.error("댓글 생성 실패", 
                        post_id=post_id, user_id=user_id, error=str(e))
            raise
    
    def get_comments(self, post_id: str, limit: int = 50, offset: int = 0) -> CommunityCommentListResponse:
        """
        댓글 목록 조회
        
        Args:
            post_id: 게시글 ID
            limit: 조회할 댓글 수
            offset: 시작 위치
            
        Returns:
            CommunityCommentListResponse: 댓글 목록 응답
        """
        url = f"{self.base_url}/posts/{post_id}/comments"
        
        try:
            params = {"limit": limit, "offset": offset}
            
            logger.info("댓글 목록 조회", post_id=post_id, params=params)
            
            response = self._make_request(
                method="GET",
                url=url,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                comment_list = CommunityCommentListResponse(**data)
                
                logger.info("댓글 목록 조회 성공", 
                           post_id=post_id, count=len(comment_list.comments))
                return comment_list
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("댓글 목록 응답 데이터 검증 실패", 
                        post_id=post_id, error=str(e))
            raise
        except Exception as e:
            logger.error("댓글 목록 조회 실패", 
                        post_id=post_id, error=str(e))
            raise
    
    def delete_comment(self, user_id: str, post_id: str, comment_id: str) -> bool:
        """
        댓글 삭제
        
        Args:
            user_id: 사용자 ID
            post_id: 게시글 ID
            comment_id: 댓글 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        url = f"{self.base_url}/posts/{post_id}/comments/{comment_id}"
        
        try:
            logger.info("댓글 삭제", post_id=post_id, comment_id=comment_id, user_id=user_id)
            
            response = self._make_request(
                method="DELETE",
                url=url,
                user_id=user_id
            )
            
            if response.status_code == 204:
                logger.info("댓글 삭제 성공", comment_id=comment_id)
                return True
            
            else:
                self._handle_error_response(response)
                return False
                
        except Exception as e:
            logger.error("댓글 삭제 실패", 
                        post_id=post_id, comment_id=comment_id, error=str(e))
            raise
    
    def find_posts_by_location(self, district: str, neighborhood: str, 
                              category: Optional[CommunityCategory] = None,
                              limit: int = 20) -> List[CommunityPost]:
        """
        위치별 게시글 조회
        
        Args:
            district: 구/군
            neighborhood: 동/읍/면
            category: 카테고리 (선택사항)
            limit: 조회할 게시글 수
            
        Returns:
            List[CommunityPost]: 게시글 목록
        """
        try:
            search_params = CommunityPostSearchParams(
                district=district,
                neighborhood=neighborhood,
                category=category,
                limit=limit
            )
            
            logger.info("위치별 게시글 조회", 
                       district=district, neighborhood=neighborhood, category=category)
            
            result = self.get_community_posts(search_params)
            return result.posts
            
        except Exception as e:
            logger.error("위치별 게시글 조회 실패", 
                        district=district, neighborhood=neighborhood, error=str(e))
            raise
    
    def find_posts_by_author(self, author_id: str, limit: int = 20) -> List[CommunityPost]:
        """
        작성자별 게시글 조회
        
        Args:
            author_id: 작성자 ID
            limit: 조회할 게시글 수
            
        Returns:
            List[CommunityPost]: 게시글 목록
        """
        try:
            search_params = CommunityPostSearchParams(
                author_id=author_id,
                limit=limit
            )
            
            logger.info("작성자별 게시글 조회", author_id=author_id)
            
            result = self.get_community_posts(search_params)
            return result.posts
            
        except Exception as e:
            logger.error("작성자별 게시글 조회 실패", 
                        author_id=author_id, error=str(e))
            raise
    
    def cleanup_test_posts(self, author_id: str) -> bool:
        """
        테스트 게시글 정리 (특정 작성자의 모든 게시글 삭제)
        
        Args:
            author_id: 작성자 ID
            
        Returns:
            bool: 정리 성공 여부
        """
        try:
            logger.info("테스트 게시글 정리 시작", author_id=author_id)
            
            # 해당 작성자의 모든 게시글 조회
            posts = self.find_posts_by_author(author_id, limit=100)
            
            deleted_count = 0
            for post in posts:
                try:
                    if self.delete_community_post(author_id, post.post_id):
                        deleted_count += 1
                        time.sleep(0.1)  # API 호출 간격 조절
                except Exception as e:
                    logger.warning("게시글 삭제 실패", 
                                  post_id=post.post_id, error=str(e))
                    continue
            
            logger.info("테스트 게시글 정리 완료", 
                       author_id=author_id, deleted_count=deleted_count)
            return True
            
        except Exception as e:
            logger.error("테스트 게시글 정리 실패", 
                        author_id=author_id, error=str(e))
            return False


# 테스트 호환성을 위한 별칭
CommunityClient = CommunityAPIClient
