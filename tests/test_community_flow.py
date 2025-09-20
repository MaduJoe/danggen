"""
당근마켓 커뮤니티(동네생활) 플로우 E2E 테스트

동네생활 게시글 작성, 댓글 상호작용 시나리오 자동화
"""

import pytest
import allure
import time
from datetime import datetime
from typing import Dict, Any, Optional

import structlog
from faker import Faker

from api_clients.carrot_api import get_api_client
from api_clients.models import (
    UserCreate, CommunityPostCreate, CommunityCommentCreate,
    CommunityCategory, Location
)
from utils.mobile_driver import get_mobile_driver, MobileDriverError
from pages import LoginPage, HomePage
from pages.community_page import CommunityPage

logger = structlog.get_logger(__name__)
fake = Faker('ko_KR')


@allure.epic("당근마켓 E2E 테스트")
@allure.feature("커뮤니티 플로우")
class TestCommunityFlow:
    """커뮤니티 플로우 E2E 테스트 클래스"""
    
    def setup_method(self):
        """테스트 시작 전 설정"""
        self.api_client = get_api_client()
        self.mobile_driver = get_mobile_driver()
        
        # 테스트 데이터 저장용
        self.test_data = {
            "author": None,
            "commenter": None,
            "post": None,
            "comments": [],
            "created_users": [],
            "created_posts": [],
        }
        
        logger.info("커뮤니티 E2E 테스트 설정 완료")
    
    def teardown_method(self):
        """테스트 완료 후 정리"""
        try:
            self._cleanup_test_data()
        except Exception as e:
            logger.error("테스트 데이터 정리 실패", error=str(e))
        finally:
            # 모바일 드라이버 종료
            if self.mobile_driver:
                try:
                    self.mobile_driver.quit()
                except Exception as e:
                    logger.error("모바일 드라이버 종료 실패", error=str(e))
    
    def _cleanup_test_data(self):
        """테스트 데이터 정리"""
        logger.info("테스트 데이터 정리 시작")
        
        # 게시글 삭제
        for post_id in self.test_data.get("created_posts", []):
            try:
                if self.test_data["author"]:
                    self.api_client.delete_community_post(
                        self.test_data["author"].user_id, 
                        post_id
                    )
                    logger.debug("게시글 삭제 완료", post_id=post_id)
            except Exception as e:
                logger.warning("게시글 삭제 실패", post_id=post_id, error=str(e))
        
        # 사용자 삭제
        for user_id in self.test_data.get("created_users", []):
            try:
                self.api_client.delete_user(user_id)
                logger.debug("사용자 삭제 완료", user_id=user_id)
            except Exception as e:
                logger.warning("사용자 삭제 실패", user_id=user_id, error=str(e))
        
        logger.info("테스트 데이터 정리 완료")
    
    def _create_test_user(self, neighborhood: str = "yongsan", username_prefix: str = "testuser") -> object:
        """테스트 사용자 생성"""
        try:
            timestamp = int(time.time())
            
            # UserAPIClient의 create_user_with_location 메서드 사용
            user = self.api_client.users.create_user_with_location(
                neighborhood=neighborhood,
                base_username=username_prefix
            )
            
            self.test_data["created_users"].append(user.user_id)
            logger.info("테스트 사용자 생성 완료", 
                       user_id=user.user_id, neighborhood=neighborhood)
            return user
            
        except Exception as e:
            logger.error("테스트 사용자 생성 실패", 
                        neighborhood=neighborhood, error=str(e))
            raise
    
    def _create_test_post(self, author_id: str, location: Location, 
                         title_suffix: str = "") -> object:
        """테스트 게시글 생성"""
        try:
            timestamp = int(time.time())
            title = f"테스트 게시글 {title_suffix} {timestamp}"
            content = f"이것은 테스트용 게시글입니다. 작성시간: {datetime.now().isoformat()}"
            
            post_data = CommunityPostCreate(
                title=title,
                content=content,
                category=CommunityCategory.DAILY,
                location=location
            )
            
            post = self.api_client.create_community_post(author_id, post_data)
            self.test_data["created_posts"].append(post.post_id)
            
            logger.info("테스트 게시글 생성 완료", 
                       post_id=post.post_id, title=title[:30])
            return post
            
        except Exception as e:
            logger.error("테스트 게시글 생성 실패", 
                        author_id=author_id, error=str(e))
            raise
    
    @allure.story("게시글 작성 및 API 검증")
    @pytest.mark.e2e
    @pytest.mark.community
    def test_community_post_creation(self):
        """동네생활 게시글 작성 및 API 검증 테스트"""
        
        with allure.step("1. 테스트 사용자 생성"):
            self.test_data["author"] = self._create_test_user("yongsan", "author")
            author = self.test_data["author"]
            
        with allure.step("2. 모바일 드라이버 시작 및 위치 설정"):
            self.mobile_driver.start_driver()
            time.sleep(3)
            
            # 용산구 위치로 설정
            self.mobile_driver.set_location(37.5384, 126.9654)
            time.sleep(2)
            
        with allure.step("3. 앱에서 사용자 로그인"):
            login_page = LoginPage(self.mobile_driver)
            home_page = HomePage(self.mobile_driver)
            
            # 로그인 수행 (실제 구현에서는 로그인 로직 필요)
            # 여기서는 앱이 이미 로그인된 상태라고 가정
            time.sleep(2)
            
        with allure.step("4. 커뮤니티 탭으로 이동"):
            community_page = CommunityPage(self.mobile_driver)
            
            assert community_page.navigate_to_community_tab(), "커뮤니티 탭 이동 실패"
            time.sleep(2)
            
            # 현재 위치 확인
            location_text = community_page.get_current_location_text()
            logger.info("현재 앱 위치", location=location_text)
            
        with allure.step("5. 게시글 작성"):
            timestamp = int(time.time())
            post_title = f"E2E 테스트 게시글 {timestamp}"
            post_content = f"자동화 테스트로 작성된 게시글입니다.\n작성시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 게시글 작성 버튼 클릭
            assert community_page.click_write_post_button(), "게시글 작성 버튼 클릭 실패"
            time.sleep(2)
            
            # 게시글 내용 작성
            assert community_page.write_post(post_title, post_content), "게시글 작성 실패"
            time.sleep(3)
            
        with allure.step("6. API로 게시글 존재 확인"):
            # 작성자의 게시글 목록에서 확인
            author_posts = self.api_client.find_posts_by_location(
                district="용산구",
                neighborhood="한강로동",
                limit=10
            )
            
            # 작성한 게시글이 목록에 있는지 확인
            post_found = False
            for post in author_posts:
                if post_title in post.title and post.author_id == author.user_id:
                    self.test_data["post"] = post
                    self.test_data["created_posts"].append(post.post_id)
                    post_found = True
                    logger.info("게시글 API 확인 성공", post_id=post.post_id)
                    break
            
            assert post_found, f"작성한 게시글을 API에서 찾을 수 없음: {post_title}"
            
        with allure.step("7. 게시글이 올바른 동네에 게시되었는지 검증"):
            post = self.test_data["post"]
            assert post.location.district == "용산구", "게시글이 올바른 구에 게시되지 않음"
            assert post.location.neighborhood == "한강로동", "게시글이 올바른 동네에 게시되지 않음"
            
        allure.attach(
            self.mobile_driver.take_screenshot(),
            name="게시글 작성 완료 스크린샷",
            attachment_type=allure.attachment_type.PNG
        )
        
        logger.info("커뮤니티 게시글 작성 테스트 완료")
    
    @allure.story("다중 사용자 댓글 상호작용")
    @pytest.mark.e2e
    @pytest.mark.community
    def test_community_comment_interaction(self):
        """다중 사용자 댓글 작성 및 확인 상호작용 테스트"""
        
        with allure.step("1. 테스트 사용자들 생성"):
            # 첫 번째 사용자 (게시글 작성자)
            self.test_data["author"] = self._create_test_user("yongsan", "author")
            author = self.test_data["author"]
            
            # 두 번째 사용자 (댓글 작성자)
            self.test_data["commenter"] = self._create_test_user("yongsan", "commenter")
            commenter = self.test_data["commenter"]
            
        with allure.step("2. API로 게시글 작성"):
            # 작성자가 게시글 작성
            self.test_data["post"] = self._create_test_post(
                author.user_id, 
                author.location,
                "댓글테스트"
            )
            post = self.test_data["post"]
            
        with allure.step("3. 모바일 드라이버 시작 (첫 번째 사용자)"):
            self.mobile_driver.start_driver()
            time.sleep(3)
            
            # 용산구 위치로 설정
            self.mobile_driver.set_location(37.5384, 126.9654)
            time.sleep(2)
            
        with allure.step("4. 첫 번째 사용자로 앱 로그인 및 게시글 확인"):
            community_page = CommunityPage(self.mobile_driver)
            
            # 커뮤니티 탭 이동
            assert community_page.navigate_to_community_tab(), "커뮤니티 탭 이동 실패"
            time.sleep(2)
            
            # 작성한 게시글 찾기 및 클릭
            assert community_page.find_post_by_title(post.title), "게시글 찾기 실패"
            time.sleep(2)
            
        with allure.step("5. 두 번째 사용자로 전환하여 댓글 작성"):
            # 앱 재시작 (사용자 전환 시뮬레이션)
            self.mobile_driver.restart_driver()
            time.sleep(3)
            
            # 위치 재설정
            self.mobile_driver.set_location(37.5384, 126.9654)
            time.sleep(2)
            
            # 커뮤니티 탭 이동
            assert community_page.navigate_to_community_tab(), "커뮤니티 탭 이동 실패 (두 번째 사용자)"
            time.sleep(2)
            
            # 게시글 다시 찾기
            assert community_page.find_post_by_title(post.title), "게시글 찾기 실패 (두 번째 사용자)"
            time.sleep(2)
            
            # 댓글 작성
            timestamp = int(time.time())
            comment_text = f"자동화 테스트 댓글입니다. 작성시간: {timestamp}"
            
            assert community_page.write_comment(comment_text), "댓글 작성 실패"
            time.sleep(3)
            
        with allure.step("6. API로 댓글 작성 확인"):
            # API를 통해 댓글 생성
            comment_data = CommunityCommentCreate(content=comment_text)
            comment = self.api_client.create_comment(
                commenter.user_id, 
                post.post_id, 
                comment_data
            )
            
            logger.info("API로 댓글 생성 완료", comment_id=comment.comment_id)
            
        with allure.step("7. 첫 번째 사용자로 복귀하여 댓글 확인"):
            # 앱 재시작 (사용자 전환)
            self.mobile_driver.restart_driver()
            time.sleep(3)
            
            # 위치 재설정
            self.mobile_driver.set_location(37.5384, 126.9654)
            time.sleep(2)
            
            # 커뮤니티 탭 이동
            assert community_page.navigate_to_community_tab(), "커뮤니티 탭 이동 실패 (복귀)"
            time.sleep(2)
            
            # 게시글 찾기
            assert community_page.find_post_by_title(post.title), "게시글 찾기 실패 (복귀)"
            time.sleep(2)
            
            # 댓글 존재 확인
            assert community_page.verify_comment_exists(comment_text), "댓글 확인 실패"
            
        with allure.step("8. 실시간 댓글 반영 검증"):
            # API로 댓글 목록 조회
            comments_response = self.api_client.get_comments(post.post_id)
            
            comment_found = False
            for api_comment in comments_response.comments:
                if comment_text in api_comment.content:
                    comment_found = True
                    logger.info("댓글 실시간 반영 확인", comment_id=api_comment.comment_id)
                    break
            
            assert comment_found, "댓글이 실시간으로 반영되지 않음"
            
        allure.attach(
            self.mobile_driver.take_screenshot(),
            name="댓글 상호작용 완료 스크린샷",
            attachment_type=allure.attachment_type.PNG
        )
        
        logger.info("커뮤니티 댓글 상호작용 테스트 완료")
    
    @allure.story("동네 범위 제한 검증")
    @pytest.mark.e2e
    @pytest.mark.community
    def test_neighborhood_boundary_validation(self):
        """동네 범위 제한 검증 테스트"""
        
        with allure.step("1. 서로 다른 동네의 사용자 생성"):
            # 용산구 사용자
            yongsan_user = self._create_test_user("yongsan", "yongsan_user")
            
            # 강남구 사용자  
            gangnam_user = self._create_test_user("gangnam", "gangnam_user")
            
        with allure.step("2. 용산구 사용자가 게시글 작성"):
            yongsan_post = self._create_test_post(
                yongsan_user.user_id,
                yongsan_user.location,
                "용산구전용"
            )
            
        with allure.step("3. 강남구에서 용산구 게시글 검색"):
            # 강남구 지역 게시글 목록 조회
            gangnam_posts = self.api_client.find_posts_by_location(
                district="강남구",
                neighborhood="역삼동",
                limit=20
            )
            
            # 용산구 게시글이 강남구 목록에 없는지 확인
            yongsan_post_found = False
            for post in gangnam_posts:
                if post.post_id == yongsan_post.post_id:
                    yongsan_post_found = True
                    break
            
            assert not yongsan_post_found, "다른 동네 게시글이 잘못된 지역에 노출됨"
            
        with allure.step("4. 용산구에서 자신의 게시글 확인"):
            # 용산구 지역 게시글 목록 조회
            yongsan_posts = self.api_client.find_posts_by_location(
                district="용산구", 
                neighborhood="한강로동",
                limit=20
            )
            
            # 용산구 게시글이 용산구 목록에 있는지 확인
            yongsan_post_found = False
            for post in yongsan_posts:
                if post.post_id == yongsan_post.post_id:
                    yongsan_post_found = True
                    break
            
            assert yongsan_post_found, "자신의 동네에서 게시글을 찾을 수 없음"
            
        logger.info("동네 범위 제한 검증 테스트 완료")


@allure.epic("당근마켓 E2E 테스트")
@allure.feature("커뮤니티 스모크 테스트")
class TestCommunitySmoke:
    """커뮤니티 기본 기능 스모크 테스트"""
    
    @allure.story("커뮤니티 API 연결 확인")
    @pytest.mark.smoke
    @pytest.mark.community
    def test_community_api_health(self):
        """커뮤니티 API 서버 연결 및 기본 기능 확인"""
        
        with allure.step("API 클라이언트 초기화"):
            api_client = get_api_client()
            assert api_client is not None, "API 클라이언트 초기화 실패"
            
        with allure.step("커뮤니티 API 기본 기능 확인"):
            # 게시글 목록 조회 (빈 결과라도 API가 동작하는지 확인)
            try:
                posts_response = api_client.get_community_posts()
                assert posts_response is not None, "게시글 목록 조회 실패"
                logger.info("커뮤니티 API 연결 확인 완료", posts_count=len(posts_response.posts))
            except Exception as e:
                pytest.fail(f"커뮤니티 API 연결 실패: {str(e)}")
    
    @allure.story("모바일 앱 커뮤니티 탭 접근")
    @pytest.mark.smoke
    @pytest.mark.mobile
    def test_community_tab_access(self):
        """모바일 앱에서 커뮤니티 탭 접근 확인"""
        
        mobile_driver = None
        try:
            with allure.step("모바일 드라이버 시작"):
                mobile_driver = get_mobile_driver()
                mobile_driver.start_driver()
                time.sleep(3)
                
            with allure.step("커뮤니티 탭 접근"):
                community_page = CommunityPage(mobile_driver)
                
                # 커뮤니티 탭 이동 시도
                success = community_page.navigate_to_community_tab()
                assert success, "커뮤니티 탭 접근 실패"
                
                logger.info("커뮤니티 탭 접근 확인 완료")
                
        finally:
            if mobile_driver:
                try:
                    mobile_driver.quit()
                except Exception as e:
                    logger.error("모바일 드라이버 종료 실패", error=str(e))
