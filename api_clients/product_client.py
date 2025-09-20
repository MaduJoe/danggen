"""
상품 관리 API 클라이언트

상품 등록, 삭제, 조회, 검색 등의 API 메서드 구현
"""

from typing import Optional, List, Dict, Any
import structlog
from pydantic import ValidationError

from .base_client import BaseAPIClient, APIError
from .models import Product, ProductCreate, ProductUpdate, ProductSearchParams

logger = structlog.get_logger(__name__)


class ProductAPIClient(BaseAPIClient):
    """상품 관리 API 클라이언트"""
    
    def __init__(self):
        super().__init__()
        self.base_url = self.config.endpoints.products_url
    
    def create_product(self, user_id: str, product_data: ProductCreate) -> Product:
        """상품 등록"""
        url = f"{self.base_url}"
        
        try:
            logger.info("상품 등록 요청", user_id=user_id, title=product_data.title)
            
            response = self._make_request(
                method="POST",
                url=url,
                json=product_data.dict(),
                user_id=user_id
            )
            
            if response.status_code == 201:
                product = Product(**response.json()["data"])
                logger.info("상품 등록 성공", product_id=product.product_id)
                return product
            
            else:
                self._handle_error_response(response)
                
        except Exception as e:
            logger.error("상품 등록 실패", user_id=user_id, error=str(e))
            raise
    
    def delete_product(self, user_id: str, product_id: str) -> bool:
        """상품 삭제"""
        url = f"{self.base_url}/{product_id}"
        
        try:
            response = self._make_request("DELETE", url, user_id=user_id)
            return response.status_code == 200
        except Exception as e:
            logger.error("상품 삭제 실패", product_id=product_id, error=str(e))
            raise
    
    def get_product_list(self, search_params: Optional[ProductSearchParams] = None) -> Dict[str, Any]:
        """상품 목록 조회"""
        url = f"{self.base_url}"
        
        params = {}
        if search_params:
            params = search_params.dict(exclude_unset=True)
        
        try:
            response = self._make_request("GET", url, params=params, require_auth=False)
            if response.status_code == 200:
                return response.json()["data"]
            else:
                self._handle_error_response(response)
        except Exception as e:
            logger.error("상품 목록 조회 실패", error=str(e))
            raise
    
    def get_product(self, product_id: str) -> Product:
        """상품 상세 조회"""
        url = f"{self.base_url}/{product_id}"
        
        try:
            response = self._make_request("GET", url, require_auth=False)
            if response.status_code == 200:
                return Product(**response.json()["data"])
            else:
                self._handle_error_response(response)
        except Exception as e:
            logger.error("상품 조회 실패", product_id=product_id, error=str(e))
            raise


# 테스트 호환성을 위한 별칭
ProductClient = ProductAPIClient