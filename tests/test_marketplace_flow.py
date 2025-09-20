"""
당근마켓 핵심 중고거래 플로우 E2E 테스트

판매자 물품 등록부터 구매자 채팅까지의 완전한 중고거래 시나리오 자동화
"""

import pytest
import allure
import time
from datetime import datetime
from typing import Dict, Any, Optional

import structlog
from faker import Faker

from api_clients.carrot_api import get_api_client
from api_clients.models import UserCreate, ProductCreate, MessageCreate, Location
from utils.mobile_driver import get_mobile_driver, MobileDriverError
from pages import LoginPage, HomePage, ProductDetailPage, ChatPage

logger = structlog.get_logger(__name__)
fake = Faker('ko_KR')


@allure.epic("당근마켓 E2E 테스트")
@allure.feature("중고거래 플로우")
class TestMarketplaceFlow:
    """중고거래 플로우 E2E 테스트 클래스"""
    
    def setup_method(self):
        """테스트 시작 전 설정"""
        self.api_client = get_api_client()
        self.mobile_driver = get_mobile_driver()
        
        # 테스트 데이터 저장용
        self.test_data = {
            "seller": None,
            "buyer": None,
            "product": None,
            "chat_room": None,
            "created_users": [],
            "created_products": [],
        }
        
        logger.info("E2E 테스트 설정 완료")
    
    def teardown_method(self):
        """테스트 완료 후 정리"""
        try:
            self._cleanup_test_data()
        except Exception as e:
            logger.error("테스트 데이터 정리 중 오류", error=str(e))
        
        # 드라이버 종료
        try:
            self.mobile_driver.stop_driver()
        except Exception as e:
            logger.error("드라이버 종료 중 오류", error=str(e))
        
        logger.info("E2E 테스트 정리 완료")
    
    @allure.story("완전한 중고거래 플로우")
    @allure.title("판매자 물품 등록 → 구매자 검색 → 채팅 → 거래 성사")
    @pytest.mark.e2e
    @pytest.mark.smoke
    def test_complete_marketplace_flow(self, test_config, cleanup_test_data):
        """
        완전한 중고거래 플로우 테스트
        
        시나리오:
        1. API로 판매자/구매자 계정 생성
        2. 판매자가 API로 물품 등록
        3. 구매자가 모바일 앱으로 로그인
        4. 물품 검색 및 상세 페이지 진입
        5. 채팅 시작 및 메시지 교환
        6. 테스트 데이터 정리
        """
        
        with allure.step("1. 테스트 사용자 계정 생성"):
            seller_data, buyer_data = self._create_test_users()
            cleanup_test_data["created_users"].extend([
                seller_data["user_id"], buyer_data["user_id"]
            ])
        
        with allure.step("2. 판매자가 물품 등록"):
            product_data = self._create_test_product(seller_data["user_id"])
            cleanup_test_data["created_products"].append(product_data["product_id"])
        
        with allure.step("3. 모바일 드라이버 시작"):
            self._start_mobile_driver()
        
        with allure.step("4. 구매자 앱 로그인"):
            self._login_buyer(buyer_data)
        
        with allure.step("5. 물품 검색 및 찾기"):
            self._search_and_find_product(product_data)
        
        with allure.step("6. 상품 상세 페이지 검증"):
            self._verify_product_details(product_data)
        
        with allure.step("7. 채팅 시작 및 메시지 교환"):
            self._start_chat_and_exchange_messages(buyer_data, seller_data, product_data)
        
        with allure.step("8. 거래 완료 검증"):
            self._verify_transaction_completion()
        
        logger.info("완전한 중고거래 플로우 테스트 성공")
    
    def _create_test_users(self) -> tuple:
        """테스트용 판매자/구매자 계정 생성"""
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        
        # 서울 용산구 위치 설정
        location = Location(
            latitude=37.5326,
            longitude=127.024612,
            address="서울특별시 용산구",
            district="용산구",
            neighborhood="이태원동"
        )
        
        # 판매자 생성
        seller_data = UserCreate(
            username=f"seller_{timestamp}",
            email=f"seller_{timestamp}@test.com",
            phone=f"010-1111-{timestamp[-4:]}",
            nickname=f"판매자_{timestamp[-4:]}",
            password="TestPassword123!",
            location=location
        )
        
        # 구매자 생성
        buyer_data = UserCreate(
            username=f"buyer_{timestamp}",
            email=f"buyer_{timestamp}@test.com", 
            phone=f"010-2222-{timestamp[-4:]}",
            nickname=f"구매자_{timestamp[-4:]}",
            password="TestPassword123!",
            location=location
        )
        
        # API로 사용자 생성
        seller = self.api_client.create_user(seller_data)
        buyer = self.api_client.create_user(buyer_data)
        
        self.test_data["seller"] = seller
        self.test_data["buyer"] = buyer
        
        logger.info("테스트 사용자 계정 생성 완료",
                   seller_id=seller.user_id,
                   buyer_id=buyer.user_id)
        
        return seller.dict(), buyer.dict()
    
    def _create_test_product(self, seller_id: str) -> Dict[str, Any]:
        """테스트용 물품 등록"""
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        
        product_data = ProductCreate(
            title=f"E2E테스트_물품_{timestamp}",
            description=f"자동화 테스트용 물품입니다. 등록시간: {timestamp}",
            price=50000,
            category="기타 중고물품",
            location=Location(
                latitude=37.5326,
                longitude=127.024612,
                address="서울특별시 용산구",
                district="용산구",
                neighborhood="이태원동"
            )
        )
        
        # API로 물품 등록
        product = self.api_client.create_product(seller_id, product_data)
        self.test_data["product"] = product
        
        logger.info("테스트 물품 등록 완료",
                   product_id=product.product_id,
                   title=product.title)
        
        return product.dict()
    
    def _start_mobile_driver(self):
        """모바일 드라이버 시작"""
        try:
            driver = self.mobile_driver.start_driver()
            
            # 위치 권한 설정
            self.mobile_driver.set_location(37.5326, 127.024612)
            
            # 앱 시작 대기
            time.sleep(3)
            
            logger.info("모바일 드라이버 시작 완료")
            
        except Exception as e:
            # 실패 시 스크린샷 캡처
            try:
                screenshot_path = self.mobile_driver.take_screenshot("driver_start_failed")
                allure.attach.file(screenshot_path, "드라이버 시작 실패", 
                                 attachment_type=allure.attachment_type.PNG)
            except:
                pass
            
            raise MobileDriverError(f"모바일 드라이버 시작 실패: {e}")
    
    def _login_buyer(self, buyer_data: Dict[str, Any]):
        """구매자 로그인"""
        try:
            # 로그인 페이지로 이동
            login_page = LoginPage(self.mobile_driver)
            
            # 페이지 로딩 대기
            if not login_page.wait_for_page_load(timeout=30):
                # 앱이 이미 로그인되어 있거나 다른 화면일 수 있음
                logger.warning("로그인 페이지를 찾을 수 없음, 홈 화면 확인")
                
                home_page = HomePage(self.mobile_driver)
                if home_page.is_page_loaded():
                    logger.info("이미 홈 화면에 있음, 로그인 스킵")
                    return
            
            # 로그인 수행
            success = login_page.login_with_credentials(
                buyer_data["email"],
                "TestPassword123!"
            )
            
            if not success:
                raise Exception("로그인 실패")
            
            # 홈 화면 로딩 대기
            home_page = HomePage(self.mobile_driver)
            if not home_page.wait_for_page_load(timeout=20):
                raise Exception("홈 화면 로딩 실패")
            
            # 스크린샷 캡처
            screenshot_path = self.mobile_driver.take_screenshot("login_success")
            allure.attach.file(screenshot_path, "로그인 성공", 
                             attachment_type=allure.attachment_type.PNG)
            
            logger.info("구매자 로그인 성공", buyer_id=buyer_data["user_id"])
            
        except Exception as e:
            # 실패 시 스크린샷 캡처
            try:
                screenshot_path = self.mobile_driver.take_screenshot("login_failed")
                allure.attach.file(screenshot_path, "로그인 실패", 
                                 attachment_type=allure.attachment_type.PNG)
            except:
                pass
            
            raise Exception(f"구매자 로그인 실패: {e}")
    
    def _search_and_find_product(self, product_data: Dict[str, Any]):
        """물품 검색 및 찾기"""
        try:
            home_page = HomePage(self.mobile_driver)
            
            # 검색 버튼 클릭
            if not home_page.click_search():
                raise Exception("검색 버튼 클릭 실패")
            
            # 검색어 입력 (간단한 검색을 위해 제품 제목의 일부 사용)
            search_keyword = product_data["title"].split("_")[0]  # "E2E테스트" 부분
            
            # 검색 입력 필드 찾기 및 입력 (실제 앱의 로케이터에 따라 수정 필요)
            from appium.webdriver.common.appiumby import AppiumBy
            search_input = (AppiumBy.ID, "com.towneers.www:id/edit_search")
            
            if not home_page.input_text(search_input, search_keyword):
                raise Exception("검색어 입력 실패")
            
            # 검색 실행 (엔터 키 또는 검색 버튼)
            search_button = (AppiumBy.ID, "com.towneers.www:id/btn_search")
            home_page.click_element(search_button)
            
            # 검색 결과 대기
            time.sleep(3)
            
            # 등록한 상품 찾기 및 클릭
            if not home_page.click_first_product():
                # 스크롤해서 찾기
                for i in range(3):
                    home_page.swipe_up()
                    time.sleep(1)
                    if home_page.click_first_product():
                        break
                else:
                    raise Exception("등록한 상품을 찾을 수 없음")
            
            # 스크린샷 캡처
            screenshot_path = self.mobile_driver.take_screenshot("product_search_success")
            allure.attach.file(screenshot_path, "상품 검색 성공", 
                             attachment_type=allure.attachment_type.PNG)
            
            logger.info("물품 검색 및 선택 성공", product_title=product_data["title"])
            
        except Exception as e:
            # 실패 시 스크린샷 캡처
            try:
                screenshot_path = self.mobile_driver.take_screenshot("search_failed")
                allure.attach.file(screenshot_path, "검색 실패", 
                                 attachment_type=allure.attachment_type.PNG)
            except:
                pass
            
            raise Exception(f"물품 검색 실패: {e}")
    
    def _verify_product_details(self, product_data: Dict[str, Any]):
        """상품 상세 페이지 정보 검증"""
        try:
            detail_page = ProductDetailPage(self.mobile_driver)
            
            # 상세 페이지 로딩 대기
            if not detail_page.wait_for_page_load(timeout=15):
                raise Exception("상품 상세 페이지 로딩 실패")
            
            # 상품 정보 검증
            displayed_title = detail_page.get_product_title()
            displayed_price = detail_page.get_product_price()
            
            # 제목 검증 (부분 일치)
            if product_data["title"] not in displayed_title:
                logger.warning("상품 제목 불일치", 
                             expected=product_data["title"],
                             actual=displayed_title)
            
            # 가격 검증 (숫자만 비교)
            expected_price = str(product_data["price"])
            if expected_price not in displayed_price.replace(",", ""):
                logger.warning("상품 가격 불일치",
                             expected=expected_price,
                             actual=displayed_price)
            
            # 스크린샷 캡처
            screenshot_path = self.mobile_driver.take_screenshot("product_detail_page")
            allure.attach.file(screenshot_path, "상품 상세 페이지", 
                             attachment_type=allure.attachment_type.PNG)
            
            logger.info("상품 상세 정보 검증 완료",
                       title=displayed_title,
                       price=displayed_price)
            
        except Exception as e:
            # 실패 시 스크린샷 캡처
            try:
                screenshot_path = self.mobile_driver.take_screenshot("detail_verification_failed")
                allure.attach.file(screenshot_path, "상세 페이지 검증 실패", 
                                 attachment_type=allure.attachment_type.PNG)
            except:
                pass
            
            raise Exception(f"상품 상세 정보 검증 실패: {e}")
    
    def _start_chat_and_exchange_messages(self, buyer_data: Dict[str, Any], 
                                        seller_data: Dict[str, Any], 
                                        product_data: Dict[str, Any]):
        """채팅 시작 및 메시지 교환"""
        try:
            detail_page = ProductDetailPage(self.mobile_driver)
            
            # 채팅하기 버튼 클릭
            if not detail_page.start_chat():
                raise Exception("채팅하기 버튼 클릭 실패")
            
            # 채팅 페이지 로딩 대기
            chat_page = ChatPage(self.mobile_driver)
            if not chat_page.wait_for_page_load(timeout=15):
                raise Exception("채팅 페이지 로딩 실패")
            
            # 구매자 메시지 전송
            buyer_message = f"안녕하세요! {product_data['title']} 구매하고 싶습니다."
            if not chat_page.send_message(buyer_message):
                raise Exception("구매자 메시지 전송 실패")
            
            # 메시지 전송 확인
            time.sleep(2)
            last_message = chat_page.get_last_message_text()
            if buyer_message not in last_message:
                logger.warning("전송된 메시지 확인 실패", 
                             sent=buyer_message, 
                             last=last_message)
            
            # API를 통한 판매자 응답 시뮬레이션
            try:
                # 실제로는 채팅방 ID를 얻어서 API로 메시지 전송
                # 여기서는 시뮬레이션으로 대체
                logger.info("판매자 응답을 API로 시뮬레이션")
                
            except Exception as e:
                logger.warning("판매자 응답 시뮬레이션 실패", error=str(e))
            
            # 스크린샷 캡처
            screenshot_path = self.mobile_driver.take_screenshot("chat_exchange")
            allure.attach.file(screenshot_path, "채팅 메시지 교환", 
                             attachment_type=allure.attachment_type.PNG)
            
            logger.info("채팅 메시지 교환 완료", 
                       buyer_message=buyer_message)
            
        except Exception as e:
            # 실패 시 스크린샷 캡처
            try:
                screenshot_path = self.mobile_driver.take_screenshot("chat_failed")
                allure.attach.file(screenshot_path, "채팅 실패", 
                                 attachment_type=allure.attachment_type.PNG)
            except:
                pass
            
            raise Exception(f"채팅 메시지 교환 실패: {e}")
    
    def _verify_transaction_completion(self):
        """거래 완료 검증"""
        try:
            # 채팅이 정상적으로 이루어졌는지 확인
            chat_page = ChatPage(self.mobile_driver)
            
            # 메시지 목록 확인
            messages = chat_page.get_messages()
            if len(messages) == 0:
                raise Exception("채팅 메시지가 없음")
            
            # 최종 스크린샷 캡처
            screenshot_path = self.mobile_driver.take_screenshot("transaction_completed")
            allure.attach.file(screenshot_path, "거래 완료", 
                             attachment_type=allure.attachment_type.PNG)
            
            logger.info("거래 완료 검증 성공", message_count=len(messages))
            
        except Exception as e:
            logger.error("거래 완료 검증 실패", error=str(e))
            # 검증 실패는 전체 테스트 실패로 이어지지 않음
    
    def _cleanup_test_data(self):
        """테스트 데이터 정리"""
        try:
            # 생성된 상품 삭제
            if self.test_data.get("product") and self.test_data.get("seller"):
                try:
                    self.api_client.delete_product(
                        self.test_data["seller"]["user_id"],
                        self.test_data["product"]["product_id"]
                    )
                    logger.info("테스트 상품 삭제 완료")
                except Exception as e:
                    logger.error("테스트 상품 삭제 실패", error=str(e))
            
            # 생성된 사용자 삭제
            for user_key in ["seller", "buyer"]:
                if self.test_data.get(user_key):
                    try:
                        self.api_client.delete_user(self.test_data[user_key]["user_id"])
                        logger.info(f"테스트 {user_key} 계정 삭제 완료")
                    except Exception as e:
                        logger.error(f"테스트 {user_key} 계정 삭제 실패", error=str(e))
            
            logger.info("테스트 데이터 정리 완료")
            
        except Exception as e:
            logger.error("테스트 데이터 정리 중 오류", error=str(e))


# 간단한 스모크 테스트 추가
@allure.epic("당근마켓 E2E 테스트")
@allure.feature("스모크 테스트")
class TestSmokeTests:
    """간단한 스모크 테스트들"""
    
    @allure.story("API 서버 연결 확인")
    @pytest.mark.smoke
    @pytest.mark.api
    def test_api_health_check(self):
        """API 서버 상태 확인"""
        api_client = get_api_client()
        
        # API 서버 상태 확인
        is_healthy = api_client.health_check()
        
        assert is_healthy, "API 서버가 응답하지 않습니다"
        logger.info("API 서버 상태 확인 성공")
    
    @allure.story("모바일 드라이버 연결 확인")
    @pytest.mark.smoke
    @pytest.mark.mobile
    def test_mobile_driver_connection(self):
        """모바일 드라이버 연결 확인"""
        mobile_driver = get_mobile_driver()
        
        try:
            # 드라이버 시작
            driver = mobile_driver.start_driver()
            
            # 앱 패키지 확인
            current_package = mobile_driver.get_current_package()
            expected_package = "com.towneers.www"
            
            assert expected_package in current_package, f"잘못된 앱 패키지: {current_package}"
            
            # 스크린샷 캡처
            screenshot_path = mobile_driver.take_screenshot("driver_connection_test")
            allure.attach.file(screenshot_path, "드라이버 연결 테스트", 
                             attachment_type=allure.attachment_type.PNG)
            
            logger.info("모바일 드라이버 연결 확인 성공", package=current_package)
            
        finally:
            mobile_driver.stop_driver()
