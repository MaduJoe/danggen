"""
커뮤니티(동네생활) 페이지 객체
"""

from typing import List, Optional
from appium.webdriver.common.appiumby import AppiumBy
import structlog
import time

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class CommunityPage(BasePage):
    """커뮤니티(동네생활) 페이지"""
    
    def __init__(self, driver):
        super().__init__(driver)
        
        # 페이지 식별 요소
        self.page_identifier = (AppiumBy.ID, "com.towneers.www:id/community_container")
        
        # 상단 영역
        self.community_title = (AppiumBy.ID, "com.towneers.www:id/title_community")
        self.location_text = (AppiumBy.ID, "com.towneers.www:id/text_location")
        self.search_button = (AppiumBy.ID, "com.towneers.www:id/btn_search_community")
        
        # 카테고리 탭
        self.tab_all = (AppiumBy.ID, "com.towneers.www:id/tab_all")
        self.tab_question = (AppiumBy.ID, "com.towneers.www:id/tab_question")
        self.tab_lost_found = (AppiumBy.ID, "com.towneers.www:id/tab_lost_found")
        self.tab_free_share = (AppiumBy.ID, "com.towneers.www:id/tab_free_share")
        
        # 게시글 목록
        self.post_list = (AppiumBy.ID, "com.towneers.www:id/recycler_community_posts")
        self.post_items = (AppiumBy.ID, "com.towneers.www:id/item_community_post")
        self.post_title = (AppiumBy.ID, "com.towneers.www:id/text_post_title")
        self.post_content = (AppiumBy.ID, "com.towneers.www:id/text_post_content")
        self.post_author = (AppiumBy.ID, "com.towneers.www:id/text_post_author")
        self.post_time = (AppiumBy.ID, "com.towneers.www:id/text_post_time")
        self.post_comments_count = (AppiumBy.ID, "com.towneers.www:id/text_comments_count")
        
        # 게시글 작성 버튼
        self.fab_write_post = (AppiumBy.ID, "com.towneers.www:id/fab_write_community")
        
        # 게시글 작성 화면
        self.write_post_container = (AppiumBy.ID, "com.towneers.www:id/write_post_container")
        self.input_post_title = (AppiumBy.ID, "com.towneers.www:id/edit_post_title")
        self.input_post_content = (AppiumBy.ID, "com.towneers.www:id/edit_post_content")
        self.btn_select_category = (AppiumBy.ID, "com.towneers.www:id/btn_select_category")
        self.btn_add_photo = (AppiumBy.ID, "com.towneers.www:id/btn_add_photo")
        self.btn_post_submit = (AppiumBy.ID, "com.towneers.www:id/btn_submit_post")
        self.btn_post_cancel = (AppiumBy.ID, "com.towneers.www:id/btn_cancel_post")
        
        # 게시글 상세 화면
        self.post_detail_container = (AppiumBy.ID, "com.towneers.www:id/post_detail_container")
        self.post_detail_title = (AppiumBy.ID, "com.towneers.www:id/detail_post_title")
        self.post_detail_content = (AppiumBy.ID, "com.towneers.www:id/detail_post_content")
        self.post_detail_author = (AppiumBy.ID, "com.towneers.www:id/detail_post_author")
        
        # 댓글 영역
        self.comments_list = (AppiumBy.ID, "com.towneers.www:id/recycler_comments")
        self.comment_items = (AppiumBy.ID, "com.towneers.www:id/item_comment")
        self.comment_text = (AppiumBy.ID, "com.towneers.www:id/text_comment_content")
        self.comment_author = (AppiumBy.ID, "com.towneers.www:id/text_comment_author")
        self.comment_time = (AppiumBy.ID, "com.towneers.www:id/text_comment_time")
        
        # 댓글 작성
        self.input_comment = (AppiumBy.ID, "com.towneers.www:id/edit_comment")
        self.btn_send_comment = (AppiumBy.ID, "com.towneers.www:id/btn_send_comment")
        
        # 네비게이션
        self.btn_back = (AppiumBy.ID, "com.towneers.www:id/btn_back")
        self.bottom_nav_community = (AppiumBy.ID, "com.towneers.www:id/nav_community")
    
    def navigate_to_community_tab(self) -> bool:
        """커뮤니티 탭으로 이동"""
        try:
            logger.info("커뮤니티 탭으로 이동")
            
            # 하단 네비게이션의 커뮤니티 탭 클릭
            if self.click_element(self.bottom_nav_community):
                # 페이지 로딩 대기
                time.sleep(2)
                return self.wait_for_page_load()
            
            return False
            
        except Exception as e:
            logger.error("커뮤니티 탭 이동 실패", error=str(e))
            return False
    
    def click_write_post_button(self) -> bool:
        """게시글 작성 버튼 클릭"""
        try:
            logger.info("게시글 작성 버튼 클릭")
            
            if self.click_element(self.fab_write_post):
                # 작성 화면 로딩 대기
                return self.wait_for_element(self.write_post_container, timeout=10)
            
            return False
            
        except Exception as e:
            logger.error("게시글 작성 버튼 클릭 실패", error=str(e))
            return False
    
    def write_post(self, title: str, content: str, category: Optional[str] = None) -> bool:
        """
        게시글 작성
        
        Args:
            title: 게시글 제목
            content: 게시글 내용
            category: 카테고리 (선택사항)
            
        Returns:
            bool: 작성 성공 여부
        """
        try:
            logger.info("게시글 작성 시작", title=title[:30])
            
            # 제목 입력
            if not self.input_text(self.input_post_title, title):
                logger.error("게시글 제목 입력 실패")
                return False
            
            # 내용 입력
            if not self.input_text(self.input_post_content, content):
                logger.error("게시글 내용 입력 실패")
                return False
            
            # 카테고리 선택 (선택사항)
            if category:
                self.click_element(self.btn_select_category)
                time.sleep(1)
                # 실제 구현에서는 카테고리 선택 로직 추가
                
            # 게시 버튼 클릭
            if self.click_element(self.btn_post_submit):
                # 게시 완료 대기
                time.sleep(3)
                logger.info("게시글 작성 완료", title=title[:30])
                return True
            
            return False
            
        except Exception as e:
            logger.error("게시글 작성 실패", title=title[:30], error=str(e))
            return False
    
    def find_post_by_title(self, title: str, max_scroll: int = 5) -> bool:
        """
        제목으로 게시글 찾기 및 클릭
        
        Args:
            title: 찾을 게시글 제목
            max_scroll: 최대 스크롤 횟수
            
        Returns:
            bool: 게시글 찾기 성공 여부
        """
        try:
            logger.info("게시글 검색 시작", title=title[:30])
            
            scroll_count = 0
            while scroll_count < max_scroll:
                # 현재 화면의 게시글 제목들 확인
                post_elements = self.find_elements(self.post_title)
                
                for post_element in post_elements:
                    try:
                        post_title_text = post_element.text
                        if title in post_title_text:
                            logger.info("게시글 발견, 클릭", title=title[:30])
                            post_element.click()
                            time.sleep(2)
                            return True
                    except Exception as e:
                        logger.debug("게시글 요소 접근 실패", error=str(e))
                        continue
                
                # 스크롤 다운
                if not self.scroll_down():
                    break
                    
                scroll_count += 1
                time.sleep(1)
            
            logger.warning("게시글을 찾을 수 없음", title=title[:30])
            return False
            
        except Exception as e:
            logger.error("게시글 검색 실패", title=title[:30], error=str(e))
            return False
    
    def write_comment(self, comment_text: str) -> bool:
        """
        댓글 작성
        
        Args:
            comment_text: 댓글 내용
            
        Returns:
            bool: 댓글 작성 성공 여부
        """
        try:
            logger.info("댓글 작성 시작", comment=comment_text[:30])
            
            # 댓글 입력 필드 클릭
            if not self.click_element(self.input_comment):
                logger.error("댓글 입력 필드 클릭 실패")
                return False
            
            # 댓글 내용 입력
            if not self.input_text(self.input_comment, comment_text):
                logger.error("댓글 내용 입력 실패")
                return False
            
            # 댓글 전송 버튼 클릭
            if self.click_element(self.btn_send_comment):
                time.sleep(2)  # 댓글 등록 대기
                logger.info("댓글 작성 완료", comment=comment_text[:30])
                return True
            
            return False
            
        except Exception as e:
            logger.error("댓글 작성 실패", comment=comment_text[:30], error=str(e))
            return False
    
    def get_comments(self) -> List[dict]:
        """
        댓글 목록 조회
        
        Returns:
            List[dict]: 댓글 정보 리스트
        """
        try:
            logger.info("댓글 목록 조회")
            
            comments = []
            comment_elements = self.find_elements(self.comment_items)
            
            for comment_element in comment_elements:
                try:
                    # 댓글 텍스트
                    comment_text_element = comment_element.find_element(*self.comment_text)
                    comment_text = comment_text_element.text if comment_text_element else ""
                    
                    # 작성자
                    author_element = comment_element.find_element(*self.comment_author)
                    author = author_element.text if author_element else ""
                    
                    # 작성 시간
                    time_element = comment_element.find_element(*self.comment_time)
                    comment_time = time_element.text if time_element else ""
                    
                    comments.append({
                        "text": comment_text,
                        "author": author,
                        "time": comment_time
                    })
                    
                except Exception as e:
                    logger.debug("댓글 요소 파싱 실패", error=str(e))
                    continue
            
            logger.info("댓글 목록 조회 완료", count=len(comments))
            return comments
            
        except Exception as e:
            logger.error("댓글 목록 조회 실패", error=str(e))
            return []
    
    def verify_comment_exists(self, comment_text: str) -> bool:
        """
        특정 댓글이 존재하는지 확인
        
        Args:
            comment_text: 확인할 댓글 내용
            
        Returns:
            bool: 댓글 존재 여부
        """
        try:
            comments = self.get_comments()
            for comment in comments:
                if comment_text in comment["text"]:
                    logger.info("댓글 존재 확인", comment=comment_text[:30])
                    return True
            
            logger.warning("댓글을 찾을 수 없음", comment=comment_text[:30])
            return False
            
        except Exception as e:
            logger.error("댓글 존재 확인 실패", comment=comment_text[:30], error=str(e))
            return False
    
    def go_back_to_community_list(self) -> bool:
        """커뮤니티 목록으로 돌아가기"""
        try:
            logger.info("커뮤니티 목록으로 돌아가기")
            
            if self.click_element(self.btn_back):
                time.sleep(2)
                return True
            
            return False
            
        except Exception as e:
            logger.error("커뮤니티 목록 돌아가기 실패", error=str(e))
            return False
    
    def get_current_location_text(self) -> Optional[str]:
        """현재 위치 텍스트 조회"""
        try:
            location_element = self.find_element(self.location_text)
            if location_element:
                location_text = location_element.text
                logger.debug("현재 위치 텍스트", location=location_text)
                return location_text
            
            return None
            
        except Exception as e:
            logger.error("위치 텍스트 조회 실패", error=str(e))
            return None
    
    def refresh_community_list(self) -> bool:
        """커뮤니티 목록 새로고침"""
        try:
            logger.info("커뮤니티 목록 새로고침")
            
            # 풀 투 리프레시 제스처
            return self.pull_to_refresh()
            
        except Exception as e:
            logger.error("커뮤니티 목록 새로고침 실패", error=str(e))
            return False
