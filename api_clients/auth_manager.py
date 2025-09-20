"""
인증 토큰 관리 시스템

JWT 토큰 관리, 자동 갱신 로직 및 인증 헤더 처리
"""

import json
import time
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import jwt
import requests
import structlog

from config.api_config import get_config

logger = structlog.get_logger(__name__)


@dataclass
class TokenInfo:
    """토큰 정보 데이터 클래스"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600  # 기본 1시간
    expires_at: Optional[float] = None
    scope: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        """토큰 만료 시간 자동 계산"""
        if self.expires_at is None:
            self.expires_at = time.time() + self.expires_in
    
    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 확인 (30초 버퍼 포함)"""
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - 30)  # 30초 버퍼
    
    @property
    def expires_soon(self) -> bool:
        """토큰이 곧 만료되는지 확인 (5분 이내)"""
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - 300)  # 5분 버퍼
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenInfo':
        """딕셔너리에서 생성"""
        return cls(**data)


class TokenStorage:
    """토큰 저장소 (암호화 지원)"""
    
    def __init__(self, storage_path: Optional[str] = None, encrypt: bool = True):
        self.storage_path = Path(storage_path or "config/tokens.enc")
        self.encrypt = encrypt
        self._encryption_key = self._get_encryption_key()
        self._cipher = Fernet(self._encryption_key) if encrypt else None
        
        # 저장소 디렉토리 생성
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_encryption_key(self) -> bytes:
        """암호화 키 생성/로드"""
        key_file = self.storage_path.parent / ".token_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # 새 키 생성
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # 키 파일 권한 설정 (Unix 계열)
            try:
                key_file.chmod(0o600)
            except (OSError, AttributeError):
                pass  # Windows에서는 무시
            
            logger.info("새로운 토큰 암호화 키 생성됨")
            return key
    
    def save_token(self, user_id: str, token_info: TokenInfo) -> None:
        """토큰 저장"""
        try:
            # 기존 토큰들 로드
            tokens = self.load_all_tokens()
            
            # 새 토큰 추가
            tokens[user_id] = token_info.to_dict()
            
            # 암호화 및 저장
            data = json.dumps(tokens, indent=2)
            
            if self.encrypt and self._cipher:
                encrypted_data = self._cipher.encrypt(data.encode())
                with open(self.storage_path, 'wb') as f:
                    f.write(encrypted_data)
            else:
                with open(self.storage_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            
            logger.info("토큰 저장 완료", user_id=user_id, 
                       expires_at=token_info.expires_at)
                       
        except Exception as e:
            logger.error("토큰 저장 실패", user_id=user_id, error=str(e))
            raise
    
    def load_token(self, user_id: str) -> Optional[TokenInfo]:
        """특정 사용자 토큰 로드"""
        tokens = self.load_all_tokens()
        token_data = tokens.get(user_id)
        
        if token_data:
            return TokenInfo.from_dict(token_data)
        
        return None
    
    def load_all_tokens(self) -> Dict[str, Dict[str, Any]]:
        """모든 토큰 로드"""
        if not self.storage_path.exists():
            return {}
        
        try:
            if self.encrypt and self._cipher:
                with open(self.storage_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = decrypted_data.decode()
            else:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = f.read()
            
            return json.loads(data)
            
        except Exception as e:
            logger.error("토큰 로드 실패", error=str(e))
            return {}
    
    def delete_token(self, user_id: str) -> bool:
        """토큰 삭제"""
        try:
            tokens = self.load_all_tokens()
            
            if user_id in tokens:
                del tokens[user_id]
                
                # 업데이트된 토큰들 저장
                data = json.dumps(tokens, indent=2)
                
                if self.encrypt and self._cipher:
                    encrypted_data = self._cipher.encrypt(data.encode())
                    with open(self.storage_path, 'wb') as f:
                        f.write(encrypted_data)
                else:
                    with open(self.storage_path, 'w', encoding='utf-8') as f:
                        f.write(data)
                
                logger.info("토큰 삭제 완료", user_id=user_id)
                return True
                
        except Exception as e:
            logger.error("토큰 삭제 실패", user_id=user_id, error=str(e))
        
        return False
    
    def clear_all_tokens(self) -> None:
        """모든 토큰 삭제"""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            logger.info("모든 토큰 삭제 완료")
        except Exception as e:
            logger.error("토큰 전체 삭제 실패", error=str(e))


class AuthenticationManager:
    """인증 관리자"""
    
    def __init__(self, storage: Optional[TokenStorage] = None):
        self.config = get_config()
        self.storage = storage or TokenStorage()
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)
        
        # 재시도 설정
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def authenticate(self, username: str, password: str) -> TokenInfo:
        """사용자 인증"""
        auth_url = self.config.endpoints.auth_url + "/login"
        
        auth_data = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        
        headers = self.config.auth_headers.copy()
        
        try:
            logger.info("사용자 인증 시도", username=username)
            
            response = self.session.post(
                auth_url,
                json=auth_data,
                headers=headers,
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                token_info = TokenInfo(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in", 3600),
                    scope=token_data.get("scope"),
                    user_id=username
                )
                
                # 토큰 저장
                self.storage.save_token(username, token_info)
                
                logger.info("인증 성공", username=username, 
                           expires_at=token_info.expires_at)
                
                return token_info
                
            else:
                error_msg = f"인증 실패: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error_description', response.text)}"
                    except:
                        error_msg += f" - {response.text}"
                
                logger.error("인증 실패", username=username, 
                           status_code=response.status_code,
                           error=error_msg)
                
                raise AuthenticationError(error_msg)
                
        except requests.RequestException as e:
            logger.error("인증 요청 실패", username=username, error=str(e))
            raise AuthenticationError(f"인증 요청 실패: {e}")
    
    def refresh_token(self, token_info: TokenInfo) -> TokenInfo:
        """토큰 갱신"""
        if not token_info.refresh_token:
            raise AuthenticationError("리프레시 토큰이 없음")
        
        refresh_url = self.config.endpoints.auth_url + "/refresh"
        
        refresh_data = {
            "refresh_token": token_info.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            logger.info("토큰 갱신 시도", user_id=token_info.user_id)
            
            response = self.session.post(
                refresh_url,
                json=refresh_data,
                headers=self.config.auth_headers,
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # 새로운 토큰 정보 생성
                new_token_info = TokenInfo(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", token_info.refresh_token),
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in", 3600),
                    scope=token_data.get("scope"),
                    user_id=token_info.user_id
                )
                
                # 새 토큰 저장
                if token_info.user_id:
                    self.storage.save_token(token_info.user_id, new_token_info)
                
                logger.info("토큰 갱신 성공", user_id=token_info.user_id)
                
                return new_token_info
                
            else:
                logger.error("토큰 갱신 실패", 
                           user_id=token_info.user_id,
                           status_code=response.status_code)
                
                raise AuthenticationError(f"토큰 갱신 실패: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error("토큰 갱신 요청 실패", 
                        user_id=token_info.user_id, error=str(e))
            raise AuthenticationError(f"토큰 갱신 요청 실패: {e}")
    
    def get_valid_token(self, user_id: str) -> Optional[TokenInfo]:
        """유효한 토큰 반환 (자동 갱신 포함)"""
        token_info = self.storage.load_token(user_id)
        
        if not token_info:
            logger.warning("저장된 토큰이 없음", user_id=user_id)
            return None
        
        # 토큰이 만료되었으면 갱신 시도
        if token_info.is_expired:
            logger.info("토큰이 만료됨, 갱신 시도", user_id=user_id)
            try:
                return self.refresh_token(token_info)
            except AuthenticationError:
                logger.warning("토큰 갱신 실패, 재인증 필요", user_id=user_id)
                self.storage.delete_token(user_id)
                return None
        
        # 토큰이 곧 만료되면 미리 갱신
        elif token_info.expires_soon:
            logger.info("토큰이 곧 만료됨, 미리 갱신", user_id=user_id)
            try:
                return self.refresh_token(token_info)
            except AuthenticationError:
                logger.warning("사전 토큰 갱신 실패, 기존 토큰 사용", user_id=user_id)
                return token_info
        
        return token_info
    
    def get_auth_headers(self, user_id: str) -> Dict[str, str]:
        """인증 헤더 반환"""
        token_info = self.get_valid_token(user_id)
        
        if not token_info:
            raise AuthenticationError(f"유효한 토큰이 없음: {user_id}")
        
        headers = self.config.headers.copy()
        headers["Authorization"] = f"{token_info.token_type} {token_info.access_token}"
        
        return headers
    
    def logout(self, user_id: str) -> bool:
        """로그아웃 (토큰 무효화)"""
        token_info = self.storage.load_token(user_id)
        
        if not token_info:
            return True
        
        logout_url = self.config.endpoints.auth_url + "/logout"
        
        try:
            headers = self.get_auth_headers(user_id)
            
            response = self.session.post(
                logout_url,
                headers=headers,
                timeout=self.config.request_timeout
            )
            
            # 토큰 저장소에서 삭제
            self.storage.delete_token(user_id)
            
            logger.info("로그아웃 완료", user_id=user_id, 
                       status_code=response.status_code)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error("로그아웃 실패", user_id=user_id, error=str(e))
            # 실패해도 로컬 토큰은 삭제
            self.storage.delete_token(user_id)
            return False


class AuthenticationError(Exception):
    """인증 관련 예외"""
    pass


# 전역 인증 관리자 인스턴스
_auth_manager = None


def get_auth_manager() -> AuthenticationManager:
    """전역 인증 관리자 반환"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager


# Alias for backward compatibility
AuthManager = AuthenticationManager
