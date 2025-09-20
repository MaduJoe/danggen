"""
API 클라이언트 기본 클래스

모든 API 클라이언트가 상속받는 기본 클래스
"""

import time
from typing import Optional, Dict, Any, Union
import requests
import structlog
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.api_config import get_config
from .auth_manager import get_auth_manager, AuthenticationError

logger = structlog.get_logger(__name__)


class APIError(Exception):
    """API 호출 관련 예외"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class BaseAPIClient:
    """API 클라이언트 기본 클래스"""
    
    def __init__(self):
        self.config = get_config()
        self.auth_manager = get_auth_manager()
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """HTTP 세션 생성"""
        session = requests.Session()
        
        # 기본 헤더 설정
        session.headers.update(self.config.headers)
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self, user_id: Optional[str] = None, 
                    custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """요청 헤더 생성"""
        headers = self.config.headers.copy()
        
        # 사용자 인증 헤더 추가
        if user_id:
            try:
                auth_headers = self.auth_manager.get_auth_headers(user_id)
                headers.update(auth_headers)
            except AuthenticationError as e:
                logger.warning("인증 헤더 생성 실패", user_id=user_id, error=str(e))
                raise
        
        # 커스텀 헤더 추가
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def _make_request(self, 
                     method: str, 
                     url: str,
                     user_id: Optional[str] = None,
                     require_auth: bool = True,
                     **kwargs) -> requests.Response:
        """
        HTTP 요청 실행
        
        Args:
            method: HTTP 메서드
            url: 요청 URL
            user_id: 인증할 사용자 ID
            require_auth: 인증 필수 여부
            **kwargs: requests 라이브러리 파라미터
            
        Returns:
            requests.Response: HTTP 응답
            
        Raises:
            APIError: API 호출 실패
            AuthenticationError: 인증 실패
        """
        # URL 정규화
        if not url.startswith(('http://', 'https://')):
            url = self.config.get_full_url(url)
        
        # 헤더 설정
        if require_auth and not user_id:
            raise APIError("인증이 필요한 요청에 user_id가 없습니다")
        
        try:
            headers = self._get_headers(user_id, kwargs.pop('headers', None))
            kwargs['headers'] = headers
            
            # 타임아웃 설정
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.config.request_timeout
            
            # 요청 로깅
            if self.config.log_requests:
                log_data = {
                    "method": method,
                    "url": url,
                    "user_id": user_id,
                    "headers": {k: v for k, v in headers.items() 
                              if k.lower() not in ['authorization', 'x-api-key']}
                }
                if 'json' in kwargs:
                    log_data['json'] = kwargs['json']
                elif 'data' in kwargs:
                    log_data['data'] = str(kwargs['data'])[:200]
                
                logger.info("API 요청", **log_data)
            
            # 요청 실행
            start_time = time.time()
            response = self.session.request(method, url, **kwargs)
            elapsed_time = time.time() - start_time
            
            # 응답 로깅
            if self.config.log_responses or response.status_code >= 400:
                log_data = {
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "elapsed_time": f"{elapsed_time:.3f}s",
                    "response_size": len(response.content)
                }
                
                if self.config.log_responses and response.text:
                    try:
                        log_data['response'] = response.json()
                    except:
                        log_data['response'] = response.text[:500]
                
                if response.status_code >= 400:
                    logger.error("API 요청 실패", **log_data)
                else:
                    logger.info("API 응답", **log_data)
            
            return response
            
        except requests.RequestException as e:
            logger.error("HTTP 요청 실패", 
                        method=method, url=url, error=str(e))
            raise APIError(f"HTTP 요청 실패: {e}")
        
        except AuthenticationError:
            raise  # 인증 오류는 그대로 전파
        
        except Exception as e:
            logger.error("예상치 못한 오류", 
                        method=method, url=url, error=str(e))
            raise APIError(f"예상치 못한 오류: {e}")
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """오류 응답 처리"""
        try:
            error_data = response.json()
            error_message = error_data.get('error_description', 
                                         error_data.get('message', 
                                                       f"HTTP {response.status_code}"))
        except:
            error_message = f"HTTP {response.status_code}: {response.text[:200]}"
        
        logger.error("API 오류 응답", 
                    status_code=response.status_code,
                    error=error_message)
        
        # 특정 상태 코드별 처리
        if response.status_code == 401:
            raise AuthenticationError("인증이 필요하거나 토큰이 유효하지 않습니다")
        elif response.status_code == 403:
            raise APIError("접근 권한이 없습니다", response.status_code, error_data)
        elif response.status_code == 404:
            raise APIError("요청한 리소스를 찾을 수 없습니다", response.status_code, error_data)
        elif response.status_code == 429:
            raise APIError("요청 한도를 초과했습니다", response.status_code, error_data)
        elif response.status_code >= 500:
            raise APIError("서버 오류가 발생했습니다", response.status_code, error_data)
        else:
            raise APIError(error_message, response.status_code, error_data)
    
    def get(self, url: str, user_id: Optional[str] = None, **kwargs) -> requests.Response:
        """GET 요청"""
        return self._make_request("GET", url, user_id=user_id, **kwargs)
    
    def post(self, url: str, user_id: Optional[str] = None, **kwargs) -> requests.Response:
        """POST 요청"""
        return self._make_request("POST", url, user_id=user_id, **kwargs)
    
    def put(self, url: str, user_id: Optional[str] = None, **kwargs) -> requests.Response:
        """PUT 요청"""
        return self._make_request("PUT", url, user_id=user_id, **kwargs)
    
    def patch(self, url: str, user_id: Optional[str] = None, **kwargs) -> requests.Response:
        """PATCH 요청"""
        return self._make_request("PATCH", url, user_id=user_id, **kwargs)
    
    def delete(self, url: str, user_id: Optional[str] = None, **kwargs) -> requests.Response:
        """DELETE 요청"""
        return self._make_request("DELETE", url, user_id=user_id, **kwargs)
    
    def upload_file(self, url: str, file_path: str, 
                   user_id: Optional[str] = None,
                   field_name: str = "file",
                   additional_data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        파일 업로드
        
        Args:
            url: 업로드 URL
            file_path: 업로드할 파일 경로
            user_id: 인증할 사용자 ID
            field_name: 파일 필드명
            additional_data: 추가 데이터
            
        Returns:
            requests.Response: 업로드 응답
        """
        try:
            with open(file_path, 'rb') as f:
                files = {field_name: f}
                data = additional_data or {}
                
                # multipart/form-data를 위해 Content-Type 헤더 제거
                headers = self._get_headers(user_id)
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                
                return self._make_request(
                    "POST", url, 
                    user_id=user_id,
                    files=files,
                    data=data,
                    headers=headers
                )
                
        except FileNotFoundError:
            raise APIError(f"파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            raise APIError(f"파일 업로드 실패: {e}")
    
    def health_check(self) -> bool:
        """API 서버 상태 확인"""
        try:
            health_url = f"{self.config.endpoints.base_url}/health"
            response = self._make_request("GET", health_url, require_auth=False)
            return response.status_code == 200
        except:
            return False
