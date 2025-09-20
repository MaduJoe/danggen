"""
API 설정 모듈

환경별 API 엔드포인트 설정 및 관리
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

logger = structlog.get_logger(__name__)


class Environment(Enum):
    """환경 타입 열거형"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class APIEndpoints:
    """API 엔드포인트 설정"""
    base_url: str
    auth_url: str = field(init=False)
    users_url: str = field(init=False)
    products_url: str = field(init=False)
    chat_url: str = field(init=False)
    upload_url: str = field(init=False)
    
    def __post_init__(self):
        """엔드포인트 URL 자동 생성"""
        self.auth_url = f"{self.base_url}/auth"
        self.users_url = f"{self.base_url}/users"
        self.products_url = f"{self.base_url}/products"
        self.chat_url = f"{self.base_url}/chat"
        self.upload_url = f"{self.base_url}/upload"


@dataclass
class APIConfig:
    """API 클라이언트 설정"""
    
    # 환경 설정
    environment: Environment = field(default_factory=lambda: Environment(
        os.getenv("API_ENVIRONMENT", "development")
    ))
    
    # API 설정
    api_version: str = os.getenv("API_VERSION", "v1")
    request_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("API_MAX_RETRIES", "3"))
    retry_delay: float = float(os.getenv("API_RETRY_DELAY", "1.0"))
    
    # 인증 설정
    api_key: Optional[str] = os.getenv("DAANGN_API_KEY")
    client_id: Optional[str] = os.getenv("DAANGN_CLIENT_ID")
    client_secret: Optional[str] = os.getenv("DAANGN_CLIENT_SECRET")
    
    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_requests: bool = os.getenv("LOG_REQUESTS", "true").lower() == "true"
    log_responses: bool = os.getenv("LOG_RESPONSES", "false").lower() == "true"
    
    # 디버그 모드
    debug_mode: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # 엔드포인트 설정
    endpoints: APIEndpoints = field(init=False)
    
    def __post_init__(self):
        """설정 초기화 후 처리"""
        # 환경별 베이스 URL 설정
        base_urls = {
            Environment.DEVELOPMENT: "https://dev-api.daangn.com/api/v1",
            Environment.STAGING: "https://staging-api.daangn.com/api/v1", 
            Environment.PRODUCTION: "https://api.daangn.com/api/v1",
            Environment.LOCAL: "http://localhost:8000/api/v1",
        }
        
        # 환경 변수로 베이스 URL 오버라이드 가능
        base_url = os.getenv("API_BASE_URL") or base_urls[self.environment]
        self.endpoints = APIEndpoints(base_url=base_url)
        
        # 로깅 설정
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        logger.info("API 설정 초기화 완료", 
                   environment=self.environment.value,
                   base_url=self.endpoints.base_url,
                   debug_mode=self.debug_mode)
    
    @property
    def headers(self) -> Dict[str, str]:
        """기본 HTTP 헤더"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"DaangnE2ETest/{self.api_version}",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            
        return headers
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """인증용 헤더 (클라이언트 인증)"""
        headers = self.headers.copy()
        
        if self.client_id and self.client_secret:
            import base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
            
        return headers
    
    def get_full_url(self, endpoint: str) -> str:
        """전체 URL 생성"""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        base_url = self.endpoints.base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"
    
    def validate_config(self) -> bool:
        """설정 유효성 검증"""
        errors = []
        
        # 필수 설정 검증
        if not self.endpoints.base_url:
            errors.append("API base URL이 설정되지 않음")
            
        if self.environment == Environment.PRODUCTION:
            if not self.api_key:
                errors.append("프로덕션 환경에서 API 키가 필요함")
            if not self.client_id or not self.client_secret:
                errors.append("프로덕션 환경에서 클라이언트 인증 정보가 필요함")
        
        # 타임아웃 검증
        if self.request_timeout <= 0:
            errors.append("요청 타임아웃은 0보다 커야 함")
        
        if self.max_retries < 0:
            errors.append("최대 재시도 횟수는 0 이상이어야 함")
        
        if errors:
            logger.error("API 설정 유효성 검증 실패", errors=errors)
            return False
            
        logger.info("API 설정 유효성 검증 통과")
        return True


# 전역 설정 인스턴스
api_config = APIConfig()


def get_config() -> APIConfig:
    """전역 API 설정 반환"""
    return api_config


def update_config(**kwargs) -> None:
    """설정 업데이트"""
    global api_config
    
    for key, value in kwargs.items():
        if hasattr(api_config, key):
            setattr(api_config, key, value)
            logger.info(f"API 설정 업데이트: {key} = {value}")
        else:
            logger.warning(f"알 수 없는 설정 키: {key}")
    
    # 엔드포인트 재생성
    api_config.__post_init__()


def load_config_from_file(config_path: str) -> APIConfig:
    """파일에서 설정 로드"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"설정 파일이 존재하지 않음: {config_path}")
        return api_config
    
    try:
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 설정 업데이트
        update_config(**config_data)
        logger.info(f"설정 파일 로드 완료: {config_path}")
        
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}", config_path=config_path)
    
    return api_config


# 환경별 기본 설정 예시
ENVIRONMENT_CONFIGS = {
    Environment.DEVELOPMENT: {
        "debug_mode": True,
        "log_requests": True,
        "log_responses": True,
        "request_timeout": 60,
    },
    Environment.STAGING: {
        "debug_mode": True,
        "log_requests": True,
        "log_responses": False,
        "request_timeout": 30,
    },
    Environment.PRODUCTION: {
        "debug_mode": False,
        "log_requests": False,
        "log_responses": False,
        "request_timeout": 15,
    },
    Environment.LOCAL: {
        "debug_mode": True,
        "log_requests": True,
        "log_responses": True,
        "request_timeout": 120,
    }
}
