import time
import os
import random
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 설정 ---
# Railway와 같은 배포 환경에서는 환경 변수를 사용하여 쿠키와 API 키를 설정합니다.
T_ANO = os.environ.get("T_ANO")
TISTORY_SESSION_COOKIE = os.environ.get("TISTORY_SESSION_COOKIE")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not T_ANO or not TISTORY_SESSION_COOKIE or not GEMINI_API_KEY:
    print("오류: T_ANO, TISTORY_SESSION_COOKIE, 또는 GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    print("스크립트를 종료합니다.")
    exit()

# Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 설정 끝 ---

def generate_text(prompt_text):
    """Gemini API를 사용하여 텍스트를 생성합니다."""
    print(f"Gemini API 호출: {prompt_text}")
    try:
        response = model.generate_content(prompt_text)
        generated_text = response.text.strip().replace('"', '')
        print(f"Gemini API 응답: {generated_text}")
        return generated_text
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        return None

def generate_title():
    """게시글 제목을 생성합니다."""
    prompt = "당신은 경제 정보 블로그의 마케터입니다. '맞구독' 키워드를 필수로 포함하여, 모든 문자(띄어쓰기, 특수문자 포함)를 합쳐 28자 이하의 매력적인 블로그 소개글 제목을 1개 생성해주세요."
    title = generate_text(prompt)
    return title if title else "경제 정보 블로그, 맞구독 해요!"

def generate_content():
    """게시글 본문을 생성합니다."""
    prompt = "당신은 경제 정보 블로그의 운영자입니다. '경제 관련 지식을 공유하는 블로그를 운영하고 있으며, 맞구독하면 저도 방문하겠습니다'라는 의미를 담아, 친근한 어조로 2문장의 소개글을 작성해주세요."
    content = generate_text(prompt)
    return content if content else "경제 지식을 나누는 블로그입니다. 맞구독 해주시면 저도 꼭 찾아갈게요!"

def generate_comment():
    """댓글 내용을 생성합니다."""
    prompt = "당신은 경제 정보 블로그의 방문자입니다. '경제 초보를 위한 기본 지식을 전달하는 글을 쓰고 있습니다. 맞구독하고 유용한 정보를 함께 나눠요'라는 의미를 담아, 정중하고 친근한 어조로 2문장의 댓글을 작성해주세요."
    comment = generate_text(prompt)
    return comment if comment else "경제 초보를 위한 지식을 공유하고 있어요. 맞구독하고 좋은 정보 나눠요~"


def setup_driver():
    """셀레니움 웹드라이버를 설정하고 반환합니다."""
    print("Chromedriver를 자동으로 설정합니다...")
    try:
        print("헤드리스 모드로 드라이버를 설정합니다.")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)


        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        print("Chromedriver 설정 완료. (헤드리스 모드)")
        return driver
    except Exception as e:
        print(f"Chromedriver 설정 중 오류 발생: {e}")
        print("스크립트를 종료합니다.")
        exit()


def login_tistory(driver, t_ano, tistory_session):
    """쿠키를 사용하여 티스토리 로그인을 수행합니다."""
    print("쿠키를 사용하여 티스토리 로그인을 시작합니다...")
    try:
        # 쿠키를 설정하기 위해 먼저 해당 도메인으로 이동해야 합니다.
        driver.get("https://www.tistory.com")
        
        # 기존 쿠키를 삭제하여 깨끗한 상태에서 시작
        driver.delete_all_cookies()

        # 환경 변수에서 가져온 쿠키 추가
        print("로그인 쿠키를 추가합니다.")
        driver.add_cookie({"name": "_T_ANO", "value": t_ano})
        driver.add_cookie({"name": "TISTORY_SESSION", "value": tistory_session})
        
        # 쿠키가 적용되도록 페이지를 새로고침
        print("페이지를 새로고침하여 로그인 상태를 적용합니다.")
        driver.refresh()
        
        # 로그인 완료 확인 (내 블로그 아이콘이 나타나는지 확인)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.link_profile"))
        )
        print("쿠키를 이용한 로그인 성공!")
        return True
    except Exception as e:
        print(f"쿠키를 이용한 로그인 실패: {e}")
        return False

def create_forum_post(driver):
    """티스토리 포럼에 새로운 '맞구독' 요청 게시글을 작성합니다."""
    print("\n티스토리 포럼에 '맞구독' 요청 게시글 작성을 시작합니다.")
    forum_url = "https://www.tistory.com/community/forum"
    driver.get(forum_url)
    time.sleep(3)

    try:
        title_input = driver.find_element(By.CSS_SELECTOR, "input#title")
        content_textarea = driver.find_element(By.CSS_SELECTOR, "textarea#text.textarea_form")
        
        driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
        time.sleep(1)

        # ElementClickInterceptedException 방지를 위해 JavaScript 클릭 사용
        print("게시글 분류를 '블로그 소개'로 선택합니다.")
        blog_intro_category = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='inp02']"))
        )
        driver.execute_script("arguments[0].click();", blog_intro_category)
        print("게시글 분류를 '블로그 소개'로 선택했습니다.")
        time.sleep(1)

        title_text = generate_title()
        print(f"제목을 입력합니다: {title_text}")
        title_input.send_keys(title_text)
        time.sleep(1)

        content_text = generate_content()
        print(f"본문을 입력합니다: {content_text}")
        content_textarea.send_keys(content_text)
        time.sleep(1)

        submit_button = driver.find_element(By.CSS_SELECTOR, "button.btn_tistory_type5[type='submit']")
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(submit_button))
        print("등록 버튼을 클릭합니다.")
        submit_button.click()
        
        time.sleep(5)
        print("게시글을 성공적으로 등록했습니다.")
        
        # 글 작성 후 랜덤 대기
        wait_time = random.randint(10, 180)
        print(f"게시글 작성 완료. {wait_time}초 동안 대기합니다...")
        time.sleep(wait_time)
        
        return True

    except Exception as e:
        print(f"포럼 게시글 작성 중 오류 발생: {e}")
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
        for i, post in enumerate(posts):
            try:
                author_link = post.find_element(By.CSS_SELECTOR, "a.txt_id")
                if author_link.get_attribute('href') == blog_url_to_find:
                    driver.execute_script("arguments[0].scrollIntoView(true);", post)
                    time.sleep(1)
                    
                    expand_button = post.find_element(By.CSS_SELECTOR, "button.btn_explain")
                    expand_button.click()
                    print(f"댓글을 남길 게시글을 찾고 펼쳤습니다: {blog_url_to_find}")
                    time.sleep(2)

                    fresh_post = driver.find_elements(By.CSS_SELECTOR, "ul.list_tistory > li")[i]
                    
                    comment_textarea = fresh_post.find_element(By.CSS_SELECTOR, "textarea.textarea_form")
                    print(f'댓글을 입력합니다: "{comment_text}"')
                    comment_textarea.send_keys(comment_text)
                    time.sleep(1)

                    submit_button = fresh_post.find_element(By.CSS_SELECTOR, "button.btn_tistory_type1[type='submit']")
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(submit_button))
                    submit_button.click()
                    print("댓글을 성공적으로 등록했습니다.")
                    
                    # 댓글 작성 후 랜덤 대기
                    wait_time = random.randint(10, 180)
                    print(f"댓글 작성 완료. 다음 작업을 위해 {wait_time}초 동안 대기합니다...")
                    time.sleep(wait_time)
                    
                    return

            except Exception as e:
                print(f"포스트 처리 중 내부 오류: {e}")
                continue

        print("오류: 댓글을 남길 게시글을 다시 찾지 못했습니다.")

    except Exception as e:
        print(f"댓글 작성 중 오류 발생: {e}")

def process_forum_posts(driver):
    """티스토리 포럼 최신 글을 확인하고, '맞구독' 요청 시 구독하고 댓글을 남깁니다."""
    print("\n다른 사람의 '맞구독' 게시글 확인 및 구독/댓글 작업을 시작합니다.")
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
                    
                    if blog_url and "optimistic-mind" not in blog_url and blog_url not in blogs_to_process:
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
    
    for blog_url in blogs_to_process:
        was_successful = subscribe_to_blog(driver, blog_url)
        if was_successful:
            # 각 댓글마다 새로 생성
            comment_text = generate_comment()
            leave_comment(driver, blog_url, comment_text)
        else:
            print(f"{blog_url} 블로그는 이미 구독중이므로 댓글을 남기지 않습니다.")


if __name__ == "__main__":
    driver = setup_driver()

    if login_tistory(driver, T_ANO, TISTORY_SESSION_COOKIE):
        create_forum_post(driver)
        process_forum_posts(driver)

    print("\n모든 자동화 작업이 완료되었습니다. 브라우저를 종료합니다.")
    driver.quit()
