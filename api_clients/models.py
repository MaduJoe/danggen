"""
API 데이터 모델 정의

Pydantic 모델을 사용한 API 응답 데이터 검증 및 타입 정의
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict
from pydantic.types import constr, conint


class UserStatus(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ProductStatus(str, Enum):
    """상품 상태"""
    SELLING = "selling"
    RESERVED = "reserved"
    SOLD = "sold"
    HIDDEN = "hidden"


class MessageType(str, Enum):
    """메시지 타입"""
    TEXT = "text"
    IMAGE = "image"
    STICKER = "sticker"
    SYSTEM = "system"


class ChatRoomStatus(str, Enum):
    """채팅방 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


# 기본 모델 클래스
class BaseAPIModel(BaseModel):
    """API 모델 기본 클래스"""
    
    model_config = ConfigDict(
        # 추가 필드 허용하지 않음
        extra="forbid",
        # datetime을 ISO 형식으로 직렬화
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        },
        # 스네이크 케이스 <-> 카멜 케이스 변환
        alias_generator=lambda field_name: ''.join(
            word.capitalize() if i > 0 else word 
            for i, word in enumerate(field_name.split('_'))
        )
    )


# 위치 관련 모델
class Location(BaseAPIModel):
    """위치 정보"""
    latitude: float = Field(..., ge=-90, le=90, description="위도")
    longitude: float = Field(..., ge=-180, le=180, description="경도")
    address: str = Field(..., min_length=1, max_length=200, description="주소")
    district: Optional[str] = Field(None, max_length=50, description="구/군")
    neighborhood: Optional[str] = Field(None, max_length=50, description="동/읍/면")


# 사용자 관련 모델
class UserProfile(BaseAPIModel):
    """사용자 프로필"""
    user_id: str = Field(..., min_length=1, max_length=50, description="사용자 ID")
    username: constr(min_length=3, max_length=30) = Field(..., description="사용자명")
    email: Optional[EmailStr] = Field(None, description="이메일")
    phone: Optional[constr(pattern=r"^010-\d{4}-\d{4}$")] = Field(None, description="전화번호")
    nickname: constr(min_length=2, max_length=20) = Field(..., description="닉네임")
    profile_image: Optional[str] = Field(None, description="프로필 이미지 URL")
    manner_temperature: Optional[float] = Field(None, ge=0, le=100, description="매너온도")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="사용자 상태")
    location: Optional[Location] = Field(None, description="위치 정보")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and not v.startswith('010'):
            raise ValueError('전화번호는 010으로 시작해야 합니다')
        return v
    
    @field_validator('manner_temperature')
    @classmethod
    def validate_manner_temperature(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('매너온도는 0-100 사이여야 합니다')
        return v


class UserCreate(BaseAPIModel):
    """사용자 생성 요청"""
    username: constr(min_length=3, max_length=30)
    email: EmailStr
    phone: constr(pattern=r"^010-\d{4}-\d{4}$")
    nickname: constr(min_length=2, max_length=20)
    password: constr(min_length=8, max_length=50)
    location: Location


class UserUpdate(BaseAPIModel):
    """사용자 정보 수정 요청"""
    nickname: Optional[constr(min_length=2, max_length=20)] = None
    profile_image: Optional[str] = None
    location: Optional[Location] = None


# UserProfile의 별칭 (테스트 호환성을 위해)
User = UserProfile


# 상품 관련 모델
class ProductImage(BaseAPIModel):
    """상품 이미지"""
    image_id: str = Field(..., description="이미지 ID")
    url: str = Field(..., description="이미지 URL")
    order: conint(ge=0) = Field(..., description="이미지 순서")
    is_primary: bool = Field(default=False, description="대표 이미지 여부")


class Product(BaseAPIModel):
    """상품 정보"""
    product_id: str = Field(..., description="상품 ID")
    title: constr(min_length=2, max_length=100) = Field(..., description="상품 제목")
    description: constr(max_length=2000) = Field(..., description="상품 설명")
    price: conint(ge=0) = Field(..., description="가격")
    category: str = Field(..., description="카테고리")
    status: ProductStatus = Field(default=ProductStatus.SELLING, description="상품 상태")
    seller_id: str = Field(..., description="판매자 ID")
    seller: Optional[UserProfile] = Field(None, description="판매자 정보")
    location: Location = Field(..., description="거래 위치")
    images: List[ProductImage] = Field(default_factory=list, description="상품 이미지")
    view_count: conint(ge=0) = Field(default=0, description="조회수")
    like_count: conint(ge=0) = Field(default=0, description="찜 수")
    chat_count: conint(ge=0) = Field(default=0, description="채팅 수")
    created_at: datetime = Field(..., description="등록일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('가격은 0 이상이어야 합니다')
        if v > 999999999:
            raise ValueError('가격이 너무 큽니다')
        return v


class ProductCreate(BaseAPIModel):
    """상품 등록 요청"""
    title: constr(min_length=2, max_length=100)
    description: constr(max_length=2000)
    price: conint(ge=0)
    category: str
    location: Location
    images: Optional[List[str]] = Field(default_factory=list, description="이미지 URL 목록")


class ProductUpdate(BaseAPIModel):
    """상품 수정 요청"""
    title: Optional[constr(min_length=2, max_length=100)] = None
    description: Optional[constr(max_length=2000)] = None
    price: Optional[conint(ge=0)] = None
    category: Optional[str] = None
    status: Optional[ProductStatus] = None
    location: Optional[Location] = None


class ProductSearchParams(BaseAPIModel):
    """상품 검색 파라미터"""
    keyword: Optional[str] = Field(None, max_length=100, description="검색 키워드")
    category: Optional[str] = Field(None, description="카테고리")
    min_price: Optional[conint(ge=0)] = Field(None, description="최소 가격")
    max_price: Optional[conint(ge=0)] = Field(None, description="최대 가격")
    location: Optional[Location] = Field(None, description="검색 위치")
    radius: Optional[conint(ge=1, le=50)] = Field(10, description="검색 반경(km)")
    status: Optional[ProductStatus] = Field(ProductStatus.SELLING, description="상품 상태")
    sort_by: Optional[str] = Field("created_at", description="정렬 기준")
    sort_order: Optional[str] = Field("desc", description="정렬 순서")
    page: Optional[conint(ge=1)] = Field(1, description="페이지 번호")
    page_size: Optional[conint(ge=1, le=100)] = Field(20, description="페이지 크기")
    
    @model_validator(mode='before')
    @classmethod
    def validate_price_range(cls, values):
        min_price = values.get('min_price')
        max_price = values.get('max_price')
        
        if min_price is not None and max_price is not None:
            if min_price > max_price:
                raise ValueError('최소 가격이 최대 가격보다 클 수 없습니다')
        
        return values


# 채팅 관련 모델
class Message(BaseAPIModel):
    """채팅 메시지"""
    message_id: str = Field(..., description="메시지 ID")
    chat_room_id: str = Field(..., description="채팅방 ID")
    sender_id: str = Field(..., description="발신자 ID")
    sender: Optional[UserProfile] = Field(None, description="발신자 정보")
    message_type: MessageType = Field(default=MessageType.TEXT, description="메시지 타입")
    content: str = Field(..., max_length=1000, description="메시지 내용")
    image_url: Optional[str] = Field(None, description="이미지 URL (이미지 메시지인 경우)")
    is_read: bool = Field(default=False, description="읽음 여부")
    created_at: datetime = Field(..., description="발송일시")


class MessageCreate(BaseAPIModel):
    """메시지 전송 요청"""
    chat_room_id: str
    message_type: MessageType = MessageType.TEXT
    content: constr(min_length=1, max_length=1000)
    image_url: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def validate_message_content(cls, values):
        message_type = values.get('message_type')
        content = values.get('content')
        image_url = values.get('image_url')
        
        if message_type == MessageType.IMAGE and not image_url:
            raise ValueError('이미지 메시지는 image_url이 필요합니다')
        
        if message_type == MessageType.TEXT and image_url:
            raise ValueError('텍스트 메시지에는 image_url이 필요하지 않습니다')
        
        return values


class ChatRoom(BaseAPIModel):
    """채팅방"""
    chat_room_id: str = Field(..., description="채팅방 ID")
    product_id: str = Field(..., description="상품 ID")
    product: Optional[Product] = Field(None, description="상품 정보")
    buyer_id: str = Field(..., description="구매자 ID")
    buyer: Optional[UserProfile] = Field(None, description="구매자 정보")
    seller_id: str = Field(..., description="판매자 ID")
    seller: Optional[UserProfile] = Field(None, description="판매자 정보")
    status: ChatRoomStatus = Field(default=ChatRoomStatus.ACTIVE, description="채팅방 상태")
    last_message: Optional[Message] = Field(None, description="마지막 메시지")
    unread_count: conint(ge=0) = Field(default=0, description="읽지 않은 메시지 수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")


class ChatRoomCreate(BaseAPIModel):
    """채팅방 생성 요청"""
    product_id: str


# API 응답 모델
class APIResponse(BaseAPIModel):
    """기본 API 응답"""
    success: bool = Field(..., description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")
    errors: Optional[List[str]] = Field(None, description="오류 목록")


class PaginatedResponse(BaseAPIModel):
    """페이지네이션 응답"""
    items: List[Dict[str, Any]] = Field(..., description="아이템 목록")
    total: conint(ge=0) = Field(..., description="전체 아이템 수")
    page: conint(ge=1) = Field(..., description="현재 페이지")
    page_size: conint(ge=1) = Field(..., description="페이지 크기")
    total_pages: conint(ge=0) = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")


# 인증 관련 모델
class LoginRequest(BaseAPIModel):
    """로그인 요청"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseAPIModel):
    """로그인 응답"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: Optional[str] = Field(None, description="리프레시 토큰")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: conint(gt=0) = Field(..., description="토큰 만료 시간(초)")
    user: UserProfile = Field(..., description="사용자 정보")


# 오류 응답 모델
class ErrorResponse(BaseAPIModel):
    """오류 응답"""
    error: str = Field(..., description="오류 코드")
    error_description: Optional[str] = Field(None, description="오류 설명")
    details: Optional[Dict[str, Any]] = Field(None, description="오류 상세 정보")


# 파일 업로드 관련 모델
class FileUploadResponse(BaseAPIModel):
    """파일 업로드 응답"""
    file_id: str = Field(..., description="파일 ID")
    file_name: str = Field(..., description="파일명")
    file_url: str = Field(..., description="파일 URL")
    file_size: conint(ge=0) = Field(..., description="파일 크기(바이트)")
    content_type: str = Field(..., description="파일 타입")
    uploaded_at: datetime = Field(..., description="업로드 일시")


# 통계 관련 모델
class ProductStats(BaseAPIModel):
    """상품 통계"""
    total_products: conint(ge=0) = Field(..., description="전체 상품 수")
    selling_products: conint(ge=0) = Field(..., description="판매 중 상품 수")
    sold_products: conint(ge=0) = Field(..., description="판매 완료 상품 수")
    total_views: conint(ge=0) = Field(..., description="전체 조회수")
    total_likes: conint(ge=0) = Field(..., description="전체 찜 수")


class UserStats(BaseAPIModel):
    """사용자 통계"""
    total_users: conint(ge=0) = Field(..., description="전체 사용자 수")
    active_users: conint(ge=0) = Field(..., description="활성 사용자 수")
    new_users_today: conint(ge=0) = Field(..., description="오늘 신규 가입자 수")


# 커뮤니티 관련 모델
class CommunityPostStatus(str, Enum):
    """커뮤니티 게시글 상태"""
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"
    REPORTED = "reported"


class CommunityCategory(str, Enum):
    """커뮤니티 카테고리"""
    ALL = "all"
    QUESTION = "question"
    LOST_FOUND = "lost_found"
    FREE_SHARE = "free_share"
    NEWS = "news"
    DAILY = "daily"


class CommunityPost(BaseAPIModel):
    """커뮤니티 게시글"""
    post_id: str = Field(..., description="게시글 ID")
    title: constr(min_length=1, max_length=100) = Field(..., description="제목")
    content: constr(min_length=1, max_length=2000) = Field(..., description="내용")
    category: CommunityCategory = Field(..., description="카테고리")
    author_id: str = Field(..., description="작성자 ID")
    author_nickname: str = Field(..., description="작성자 닉네임")
    location: Location = Field(..., description="작성 위치")
    status: CommunityPostStatus = Field(default=CommunityPostStatus.ACTIVE, description="게시글 상태")
    views_count: conint(ge=0) = Field(default=0, description="조회수")
    likes_count: conint(ge=0) = Field(default=0, description="좋아요 수")
    comments_count: conint(ge=0) = Field(default=0, description="댓글 수")
    images: Optional[List[str]] = Field(default=[], description="첨부 이미지 URL 목록")
    created_at: datetime = Field(..., description="작성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    

class CommunityPostCreate(BaseAPIModel):
    """커뮤니티 게시글 생성 요청"""
    title: constr(min_length=1, max_length=100)
    content: constr(min_length=1, max_length=2000)
    category: CommunityCategory
    location: Location
    images: Optional[List[str]] = Field(default=[], description="첨부 이미지 URL 목록")


class CommunityPostUpdate(BaseAPIModel):
    """커뮤니티 게시글 수정 요청"""
    title: Optional[constr(min_length=1, max_length=100)] = None
    content: Optional[constr(min_length=1, max_length=2000)] = None
    category: Optional[CommunityCategory] = None
    images: Optional[List[str]] = None


class CommunityComment(BaseAPIModel):
    """커뮤니티 댓글"""
    comment_id: str = Field(..., description="댓글 ID")
    post_id: str = Field(..., description="게시글 ID")
    content: constr(min_length=1, max_length=500) = Field(..., description="댓글 내용")
    author_id: str = Field(..., description="작성자 ID")
    author_nickname: str = Field(..., description="작성자 닉네임")
    parent_comment_id: Optional[str] = Field(None, description="부모 댓글 ID (대댓글인 경우)")
    likes_count: conint(ge=0) = Field(default=0, description="좋아요 수")
    created_at: datetime = Field(..., description="작성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")


class CommunityCommentCreate(BaseAPIModel):
    """커뮤니티 댓글 생성 요청"""
    content: constr(min_length=1, max_length=500)
    parent_comment_id: Optional[str] = None


class CommunityPostSearchParams(BaseAPIModel):
    """커뮤니티 게시글 검색 파라미터"""
    category: Optional[CommunityCategory] = None
    district: Optional[str] = None
    neighborhood: Optional[str] = None
    keyword: Optional[str] = None
    author_id: Optional[str] = None
    limit: conint(ge=1, le=100) = Field(default=20, description="페이지당 결과 수")
    offset: conint(ge=0) = Field(default=0, description="시작 위치")
    sort_by: Optional[str] = Field(default="created_at", description="정렬 기준")
    order: Optional[str] = Field(default="desc", description="정렬 순서")


class CommunityPostListResponse(BaseAPIModel):
    """커뮤니티 게시글 목록 응답"""
    posts: List[CommunityPost] = Field(..., description="게시글 목록")
    total: conint(ge=0) = Field(..., description="전체 게시글 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    page_info: Dict[str, Any] = Field(default_factory=dict, description="페이지 정보")


class CommunityCommentListResponse(BaseAPIModel):
    """커뮤니티 댓글 목록 응답"""
    comments: List[CommunityComment] = Field(..., description="댓글 목록")
    total: conint(ge=0) = Field(..., description="전체 댓글 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")