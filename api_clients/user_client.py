"""
사용자 관리 API 클라이언트

사용자 생성, 삭제, 조회, 수정 등의 API 메서드 구현
"""

from typing import Optional, List, Dict, Any
import requests
import structlog
from pydantic import ValidationError
from datetime import datetime
import time

from config.api_config import get_config
from .auth_manager import get_auth_manager, AuthenticationError
from .models import (
    UserProfile, UserCreate, UserUpdate, APIResponse, 
    ErrorResponse, LoginRequest, LoginResponse, Location
)
from .base_client import BaseAPIClient

logger = structlog.get_logger(__name__)


class UserAPIClient(BaseAPIClient):
    """사용자 관리 API 클라이언트"""
    
    def __init__(self):
        super().__init__()
        self.auth_manager = get_auth_manager()
        self.base_url = self.config.endpoints.users_url
    
    def create_user(self, user_data: UserCreate) -> UserProfile:
        """
        사용자 생성
        
        Args:
            user_data: 사용자 생성 데이터
            
        Returns:
            UserProfile: 생성된 사용자 정보
            
        Raises:
            APIError: API 호출 실패
            ValidationError: 데이터 검증 실패
        """
        url = f"{self.base_url}/register"
        
        try:
            logger.info("사용자 생성 요청", username=user_data.username)
            
            # 데이터 검증
            user_dict = user_data.dict()
            
            response = self._make_request(
                method="POST",
                url=url,
                json=user_dict,
                headers=self.config.auth_headers,  # 클라이언트 인증
                require_auth=False  # 사용자 토큰 불필요
            )
            
            if response.status_code == 201:
                user_profile = UserProfile(**response.json()["data"])
                logger.info("사용자 생성 성공", 
                           username=user_data.username,
                           user_id=user_profile.user_id)
                return user_profile
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("사용자 데이터 검증 실패", errors=e.errors())
            raise
        
        except Exception as e:
            logger.error("사용자 생성 실패", 
                        username=user_data.username, error=str(e))
            raise
    
    def delete_user(self, user_id: str) -> bool:
        """
        사용자 삭제
        
        Args:
            user_id: 삭제할 사용자 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            APIError: API 호출 실패
            AuthenticationError: 인증 실패
        """
        url = f"{self.base_url}/{user_id}"
        
        try:
            logger.info("사용자 삭제 요청", user_id=user_id)
            
            response = self._make_request(
                method="DELETE",
                url=url,
                user_id=user_id  # 인증 필요
            )
            
            if response.status_code == 200:
                logger.info("사용자 삭제 성공", user_id=user_id)
                
                # 로컬 토큰도 삭제
                self.auth_manager.logout(user_id)
                
                return True
            
            else:
                self._handle_error_response(response)
                return False
                
        except Exception as e:
            logger.error("사용자 삭제 실패", user_id=user_id, error=str(e))
            raise
    
    def get_user(self, user_id: str, current_user_id: Optional[str] = None) -> UserProfile:
        """
        사용자 정보 조회
        
        Args:
            user_id: 조회할 사용자 ID
            current_user_id: 현재 사용자 ID (인증용, 없으면 공개 정보만)
            
        Returns:
            UserProfile: 사용자 정보
            
        Raises:
            APIError: API 호출 실패
        """
        url = f"{self.base_url}/{user_id}"
        
        try:
            logger.info("사용자 정보 조회", user_id=user_id)
            
            response = self._make_request(
                method="GET",
                url=url,
                user_id=current_user_id,  # 인증 선택적
                require_auth=False
            )
            
            if response.status_code == 200:
                user_profile = UserProfile(**response.json()["data"])
                logger.info("사용자 정보 조회 성공", user_id=user_id)
                return user_profile
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("사용자 정보 검증 실패", user_id=user_id, errors=e.errors())
            raise
        
        except Exception as e:
            logger.error("사용자 정보 조회 실패", user_id=user_id, error=str(e))
            raise
    
    def update_user(self, user_id: str, update_data: UserUpdate) -> UserProfile:
        """
        사용자 정보 수정
        
        Args:
            user_id: 수정할 사용자 ID
            update_data: 수정 데이터
            
        Returns:
            UserProfile: 수정된 사용자 정보
            
        Raises:
            APIError: API 호출 실패
            AuthenticationError: 인증 실패
        """
        url = f"{self.base_url}/{user_id}"
        
        try:
            logger.info("사용자 정보 수정 요청", user_id=user_id)
            
            # None이 아닌 필드만 전송
            update_dict = update_data.dict(exclude_unset=True)
            
            response = self._make_request(
                method="PUT",
                url=url,
                json=update_dict,
                user_id=user_id
            )
            
            if response.status_code == 200:
                user_profile = UserProfile(**response.json()["data"])
                logger.info("사용자 정보 수정 성공", user_id=user_id)
                return user_profile
            
            else:
                self._handle_error_response(response)
                
        except ValidationError as e:
            logger.error("수정 데이터 검증 실패", user_id=user_id, errors=e.errors())
            raise
        
        except Exception as e:
            logger.error("사용자 정보 수정 실패", user_id=user_id, error=str(e))
            raise
    
    def login(self, username: str, password: str) -> LoginResponse:
        """
        사용자 로그인
        
        Args:
            username: 사용자명 또는 이메일
            password: 비밀번호
            
        Returns:
            LoginResponse: 로그인 결과 (토큰 포함)
            
        Raises:
            AuthenticationError: 인증 실패
        """
        try:
            logger.info("사용자 로그인 시도", username=username)
            
            # 인증 매니저를 통한 로그인
            token_info = self.auth_manager.authenticate(username, password)
            
            # 사용자 정보 조회
            user_profile = self.get_user(username, username)
            
            login_response = LoginResponse(
                access_token=token_info.access_token,
                refresh_token=token_info.refresh_token,
                token_type=token_info.token_type,
                expires_in=token_info.expires_in,
                user=user_profile
            )
            
            logger.info("사용자 로그인 성공", username=username)
            return login_response
            
        except Exception as e:
            logger.error("사용자 로그인 실패", username=username, error=str(e))
            raise
    
    def logout(self, user_id: str) -> bool:
        """
        사용자 로그아웃
        
        Args:
            user_id: 로그아웃할 사용자 ID
            
        Returns:
            bool: 로그아웃 성공 여부
        """
        try:
            logger.info("사용자 로그아웃 시도", user_id=user_id)
            
            result = self.auth_manager.logout(user_id)
            
            if result:
                logger.info("사용자 로그아웃 성공", user_id=user_id)
            else:
                logger.warning("사용자 로그아웃 실패", user_id=user_id)
            
            return result
            
        except Exception as e:
            logger.error("사용자 로그아웃 실패", user_id=user_id, error=str(e))
            return False
    
    def search_users(self, 
                    keyword: Optional[str] = None,
                    location: Optional[str] = None,
                    page: int = 1,
                    page_size: int = 20) -> Dict[str, Any]:
        """
        사용자 검색
        
        Args:
            keyword: 검색 키워드 (닉네임, 사용자명)
            location: 위치 검색
            page: 페이지 번호
            page_size: 페이지 크기
            
        Returns:
            Dict: 페이지네이션된 사용자 목록
        """
        url = f"{self.base_url}/search"
        
        params = {
            "page": page,
            "page_size": page_size
        }
        
        if keyword:
            params["keyword"] = keyword
        if location:
            params["location"] = location
        
        try:
            logger.info("사용자 검색", keyword=keyword, location=location)
            
            response = self._make_request(
                method="GET",
                url=url,
                params=params,
                require_auth=False
            )
            
            if response.status_code == 200:
                result = response.json()["data"]
                logger.info("사용자 검색 성공", 
                           total=result.get("total", 0),
                           page=page)
                return result
            
            else:
                self._handle_error_response(response)
                
        except Exception as e:
            logger.error("사용자 검색 실패", keyword=keyword, error=str(e))
            raise
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 통계 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict: 사용자 통계 정보
        """
        url = f"{self.base_url}/{user_id}/stats"
        
        try:
            logger.info("사용자 통계 조회", user_id=user_id)
            
            response = self._make_request(
                method="GET",
                url=url,
                user_id=user_id
            )
            
            if response.status_code == 200:
                stats = response.json()["data"]
                logger.info("사용자 통계 조회 성공", user_id=user_id)
                return stats
            
            else:
                self._handle_error_response(response)
                
        except Exception as e:
            logger.error("사용자 통계 조회 실패", user_id=user_id, error=str(e))
            raise
    
    def change_password(self, user_id: str, 
                       current_password: str, 
                       new_password: str) -> bool:
        """
        비밀번호 변경
        
        Args:
            user_id: 사용자 ID
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            bool: 변경 성공 여부
        """
        url = f"{self.base_url}/{user_id}/password"
        
        data = {
            "current_password": current_password,
            "new_password": new_password
        }
        
        try:
            logger.info("비밀번호 변경 요청", user_id=user_id)
            
            response = self._make_request(
                method="PUT",
                url=url,
                json=data,
                user_id=user_id
            )
            
            if response.status_code == 200:
                logger.info("비밀번호 변경 성공", user_id=user_id)
                return True
            
            else:
                self._handle_error_response(response)
                return False
                
        except Exception as e:
            logger.error("비밀번호 변경 실패", user_id=user_id, error=str(e))
            raise

    # 커뮤니티 테스트를 위한 동네별 위치 데이터
    NEIGHBORHOOD_LOCATIONS = {
        "yongsan": Location(
            latitude=37.5384,
            longitude=126.9654,
            address="서울특별시 용산구 한강대로 405",
            district="용산구",
            neighborhood="한강로동"
        ),
        "gangnam": Location(
            latitude=37.4979,
            longitude=127.0276,
            address="서울특별시 강남구 테헤란로 152",
            district="강남구", 
            neighborhood="역삼동"
        ),
        "hongdae": Location(
            latitude=37.5563,
            longitude=126.9238,
            address="서울특별시 마포구 와우산로 94",
            district="마포구",
            neighborhood="서교동"
        ),
        "jamsil": Location(
            latitude=37.5125,
            longitude=127.1025,
            address="서울특별시 송파구 잠실동 19-9",
            district="송파구",
            neighborhood="잠실동"
        )
    }

    def create_user_with_location(self, neighborhood: str = "yongsan", 
                                  base_username: Optional[str] = None) -> UserProfile:
        """
        특정 동네 위치를 가진 테스트 사용자 생성
        
        Args:
            neighborhood: 동네 이름 (yongsan, gangnam, hongdae, jamsil)
            base_username: 기본 사용자명 (None이면 자동 생성)
            
        Returns:
            UserProfile: 생성된 사용자 정보
            
        Raises:
            ValueError: 지원하지 않는 동네
            APIError: API 호출 실패
        """
        if neighborhood not in self.NEIGHBORHOOD_LOCATIONS:
            raise ValueError(f"지원하지 않는 동네: {neighborhood}. "
                           f"가능한 값: {list(self.NEIGHBORHOOD_LOCATIONS.keys())}")
        
        # 고유한 사용자명 생성 (테스트 실행 시간 포함)
        timestamp = int(time.time())
        if base_username:
            username = f"{base_username}_{neighborhood}_{timestamp}"
        else:
            username = f"testuser_{neighborhood}_{timestamp}"
        
        nickname = f"테스트유저_{neighborhood}_{timestamp}"
        email = f"{username}@test.example.com"
        phone = f"010-{timestamp % 10000:04d}-{(timestamp // 10000) % 10000:04d}"
        
        # 사용자 생성 데이터
        user_data = UserCreate(
            username=username,
            email=email,
            phone=phone,
            nickname=nickname,
            password="testpass123!",
            location=self.NEIGHBORHOOD_LOCATIONS[neighborhood]
        )
        
        try:
            logger.info("동네별 사용자 생성 시작", 
                       neighborhood=neighborhood, username=username)
            
            # 사용자 생성
            user = self.create_user(user_data)
            
            # 생성된 사용자에 위치 정보 설정 (추가 확인)
            self._set_user_location(user.user_id, self.NEIGHBORHOOD_LOCATIONS[neighborhood])
            
            logger.info("동네별 사용자 생성 완료", 
                       user_id=user.user_id, neighborhood=neighborhood)
            
            return user
            
        except Exception as e:
            logger.error("동네별 사용자 생성 실패", 
                        neighborhood=neighborhood, error=str(e))
            raise

    def _set_user_location(self, user_id: str, location: Location) -> bool:
        """
        사용자 위치 정보 설정 (내부 메서드)
        
        Args:
            user_id: 사용자 ID
            location: 설정할 위치 정보
            
        Returns:
            bool: 성공 여부
        """
        url = f"{self.base_url}/{user_id}/location"
        
        try:
            logger.debug("사용자 위치 설정 요청", user_id=user_id, 
                        district=location.district, neighborhood=location.neighborhood)
            
            response = self._make_request(
                method="PUT",
                url=url,
                json=location.model_dump(),
                user_id=user_id
            )
            
            if response.status_code == 200:
                logger.debug("사용자 위치 설정 성공", user_id=user_id)
                return True
            else:
                logger.warning("사용자 위치 설정 실패", 
                             user_id=user_id, status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("사용자 위치 설정 오류", user_id=user_id, error=str(e))
            return False

    def get_neighborhood_users(self, neighborhood: str) -> List[UserProfile]:
        """
        특정 동네의 사용자 목록 조회
        
        Args:
            neighborhood: 동네 이름
            
        Returns:
            List[UserProfile]: 해당 동네 사용자 목록
        """
        if neighborhood not in self.NEIGHBORHOOD_LOCATIONS:
            raise ValueError(f"지원하지 않는 동네: {neighborhood}")
        
        location = self.NEIGHBORHOOD_LOCATIONS[neighborhood]
        
        try:
            logger.info("동네별 사용자 조회", neighborhood=neighborhood)
            
            # 실제 구현에서는 위치 기반 사용자 검색 API 호출
            # 여기서는 시뮬레이션
            url = f"{self.base_url}/search"
            params = {
                "district": location.district,
                "neighborhood": location.neighborhood,
                "limit": 100
            }
            
            response = self._make_request(
                method="GET",
                url=url,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                users = [UserProfile(**user_data) for user_data in data.get("users", [])]
                logger.info("동네별 사용자 조회 완료", 
                           neighborhood=neighborhood, count=len(users))
                return users
            else:
                self._handle_error_response(response)
                return []
                
        except Exception as e:
            logger.error("동네별 사용자 조회 실패", 
                        neighborhood=neighborhood, error=str(e))
            raise


# 테스트 호환성을 위한 별칭
UserClient = UserAPIClient