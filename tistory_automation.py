import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 설정 ---
# Railway와 같은 배포 환경에서는 환경 변수를 사용하여 아이디와 비밀번호를 설정합니다.
# 로컬에서 테스트할 경우, 아래 주석 처리된 라인에 직접 값을 입력하고 사용할 수 있습니다.
TISTORY_ID = os.environ.get("TISTORY_ID")
TISTORY_PW = os.environ.get("TISTORY_PW")

# TISTORY_ID = "your_id@example.com" # 로컬 테스트용
# TISTORY_PW = "your_password"      # 로컬 테스트용

if not TISTORY_ID or not TISTORY_PW:
    print("오류: TISTORY_ID 또는 TISTORY_PW 환경 변수가 설정되지 않았습니다.")
    print("스크립트를 종료합니다.")
    exit()
# --- 설정 끝 ---


def setup_driver():
    """셀레니움 웹드라이버를 설정하고 반환합니다."""
    print("Chromedriver를 자동으로 설정합니다...")
    try:
        print("헤드리스 모드로 드라이버를 설정합니다.")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920x1080")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        print("Chromedriver 설정 완료. (헤드리스 모드)")
        return driver
    except Exception as e:
        print(f"Chromedriver 설정 중 오류 발생: {e}")
        print("스크립트를 종료합니다.")
        exit()


def login_tistory(driver, user_id, user_pw):
    """티스토리/카카오 계정 로그인을 수행합니다."""
    print("티스토리 로그인을 시작합니다...")
    driver.get("https://www.tistory.com/auth/login")
    
    try:
        # 1. '카카오계정으로 로그인' 버튼 클릭
        print("'카카오계정으로 로그인' 버튼을 클릭합니다.")
        kakao_login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.link_kakao_id"))
        )
        kakao_login_button.click()
        
        # 2. 이메일 입력
        print("이메일(카카오계정)을 입력합니다.")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
        )
        email_input.send_keys(user_id)
        
        # 3. 비밀번호 입력
        print("비밀번호를 입력합니다.")
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
        )
        password_input.send_keys(user_pw)
        
        # 4. '로그인' 버튼 클릭
        print("로그인 버튼을 클릭합니다.")
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # 5. 로그인 완료 확인 (내 블로그 아이콘이 나타나는지 확인)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.link_profile"))
        )
        print("로그인 성공!")
        return True
    except Exception as e:
        print(f"로그인 실패: {e}")
        return False

def subscribe_to_blog(driver, blog_url):
    """블로그 URL로 이동하여 구독 절차를 수행하고, 성공 여부를 반환합니다."""
    print(f"블로그 구독을 위해 {blog_url}로 이동합니다.")
    driver.get(blog_url)
    time.sleep(3)

    try:
        subscribe_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_subscription"))
        )
        
        button_text_element = subscribe_button.find_element(By.CSS_SELECTOR, "em.txt_state")
        if button_text_element.text != "구독하기":
            print("이미 구독중인 블로그입니다.")
            return False

        print("구독 버튼을 클릭합니다.")
        subscribe_button.click()
        
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".btn_subscription em.txt_state"), "구독중")
        )
        print("구독에 성공했습니다!")
        return True

    except Exception as e:
        print(f"구독 중 오류 발생: {e}")
        return False

def leave_comment(driver, blog_url_to_find, comment_text):
    """포럼 게시글에 댓글을 남깁니다."""
    print(f"게시글에 댓글을 남기기 위해 포럼으로 돌아갑니다...")
    forum_url = "https://www.tistory.com/community/forum"
    driver.get(forum_url)
    time.sleep(5)

    try:
        posts = driver.find_elements(By.CSS_SELECTOR, "ul.list_tistory > li")
        target_post = None
        for i, post in enumerate(posts):
            try:
                author_link = post.find_element(By.CSS_SELECTOR, "a.txt_id")
                if author_link.get_attribute('href') == blog_url_to_find:
                    # Javascript로 클릭하기 위해 스크롤
                    driver.execute_script("arguments[0].scrollIntoView(true);", post)
                    time.sleep(1)
                    
                    # '펼치기' 버튼 클릭
                    expand_button = post.find_element(By.CSS_SELECTOR, "button.btn_explain")
                    expand_button.click()
                    print(f"댓글을 남길 게시글을 찾고 펼쳤습니다: {blog_url_to_find}")
                    time.sleep(2) # 댓글 영역 로딩 대기

                    # 펼쳐진 post를 다시 찾아야 함 (DOM이 변경되었기 때문)
                    fresh_post = driver.find_elements(By.CSS_SELECTOR, "ul.list_tistory > li")[i]
                    
                    # 댓글 입력
                    comment_textarea = fresh_post.find_element(By.CSS_SELECTOR, "textarea.textarea_form")
                    print(f'댓글을 입력합니다: "{comment_text}"')
                    comment_textarea.send_keys(comment_text)
                    time.sleep(1)

                    # '완료' 버튼 클릭
                    submit_button = fresh_post.find_element(By.CSS_SELECTOR, "button.btn_tistory_type1[type='submit']")
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(submit_button))
                    submit_button.click()
                    print("댓글을 성공적으로 등록했습니다.")
                    time.sleep(3) # 등록 후 잠시 대기
                    return # 댓글 작성이 끝났으므로 함수 종료

            except Exception as e:
                print(f"포스트 처리 중 내부 오류: {e}")
                continue

        print("오류: 댓글을 남길 게시글을 다시 찾지 못했습니다.")

    except Exception as e:
        print(f"댓글 작성 중 오류 발생: {e}")

def process_forum_posts(driver):
    """티스토리 포럼 최신 글을 확인하고, '맞구독' 요청 시 구독하고 댓글을 남깁니다."""
    print("\n티스토리 포럼 자동화 작업을 시작합니다.")
    forum_url = "https://www.tistory.com/community/forum"
    driver.get(forum_url)
    time.sleep(5)

    blogs_to_process = []
    try:
        posts = driver.find_elements(By.CSS_SELECTOR, "ul.list_tistory > li")
        print(f"총 {len(posts)}개의 게시글을 찾았습니다.")

        for post in posts:
            try:
                title_element = post.find_element(By.CSS_SELECTOR, "span.inner_desc_tit")
                title = title_element.text

                if "맞구독" in title:
                    author_link_element = post.find_element(By.CSS_SELECTOR, "a.txt_id")
                    blog_url = author_link_element.get_attribute('href')
                    
                    if blog_url and blog_url not in [b[0] for b in blogs_to_process]:
                        print(f"\n처리할 '맞구독' 게시글을 찾았습니다: '{title}' ({blog_url})")
                        blogs_to_process.append(blog_url)

            except Exception as e:
                print(f"게시글 정보 수집 중 오류 발생: {e}")
                continue
    
    except Exception as e:
        print(f"포럼 게시글 목록을 가져오는 중 오류 발생: {e}")

    if not blogs_to_process:
        print("\n처리할 '맞구독' 게시글을 찾지 못했습니다.")
        return

    print(f"\n총 {len(blogs_to_process)}개의 블로그를 대상으로 구독 및 댓글 작업을 시작합니다.")
    comment_text = "경제 초보를 위한 기본 지식전달을 위한 글을 쓰고있습니다. 맞구독하고 많은 정보 얻어가세요 ~"

    for blog_url in blogs_to_process:
        was_successful = subscribe_to_blog(driver, blog_url)
        if was_successful:
            leave_comment(driver, blog_url, comment_text)
        else:
            print(f"{blog_url} 블로그는 이미 구독중이므로 댓글을 남기지 않습니다.")


if __name__ == "__main__":
    driver = setup_driver()

    if login_tistory(driver, TISTORY_ID, TISTORY_PW):
        process_forum_posts(driver)

    print("\n자동화 작업이 완료되었습니다. 브라우저를 종료합니다.")
    driver.quit()