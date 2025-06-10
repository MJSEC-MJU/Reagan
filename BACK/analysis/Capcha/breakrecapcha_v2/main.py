import os 
import time
import random
import io
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    TimeoutException,
)

# solver 모듈
from solver.behavior import human_like_move_and_click
from solver.image import ImageSolver

# utils 모듈
from utils.cookie import create_firefox_with_profile  # FIREFOX_PROFILE_PATH=None 으로 새 프로필 사용
from PIL import Image, ImageChops
# ============== 설정 파트 ==============

# 1) YOLOv8 모델 가중치 경로
YOLO_CLS_WEIGHTS = "weights/final.pt"
YOLO_SEG_WEIGHTS = "weights/yolo_seg.pt"

YOLO_SECOND_WEIGHTS="weights/yolo_cls.pt"

USE_SECONDARY = {"오토바이", "자전거", "motorcycle", "bicycle", "motorcycles", "bicycles"}
# 2) Firefox 프로필 경로
#    · None으로 설정하면 “완전 새 프로필” 사용 (쿠키·히스토리 없는 상태)
FIREFOX_PROFILE_PATH = None  

# 3) reCAPTCHA 데모 페이지 URL
RECAPTCHA_URL = "https://www.google.com/recaptcha/api2/demo"

# 4) 자동화 시도 횟수
NUM_TRIES = 5

def launch_browser_with_profile():
    """
    Firefox 브라우저를 새 프로필로 실행 → 최대화 시도
    """
    driver = create_firefox_with_profile(FIREFOX_PROFILE_PATH)
    try:
        driver.maximize_window()
        time.sleep(0.5)
    except Exception as e:
        print(f"  → [Warning] maximize_window() failed: {e}")
    return driver


def scroll_into_view(driver, element):
    """
    JavaScript로 요소를 화면 중앙에 스크롤
    """
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
     
    except Exception as e:
        print(f"    → [Warning] scrollIntoView failed: {e}")


def safe_click(driver, element):
    """
    human_like_move_and_click → MoveTargetOutOfBoundsException 시 element.click() 폴백
    """
    try:
        scroll_into_view(driver, element)
        human_like_move_and_click(driver, element, duration=0.4)
    except MoveTargetOutOfBoundsException:
        try:
            element.click()
        except Exception as e2:
            print(f"    → [Error] fallback click() failed: {e2}")
    except Exception:
        try:
            element.click()
        except Exception as e2:
            print(f"    → [Error] fallback click() failed: {e2}")
def click_recaptcha_checkbox(driver, wait):
    """
    reCAPTCHA 체크박스 클릭
    """
    try:
        iframe = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")))
        driver.switch_to.frame(iframe)
        print("  → [Info] reCAPTCHA checkbox converted to iframe")

        checkbox = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border")))
        safe_click(driver, checkbox)
        print("  → [Info] Checkbox clicked")

    except Exception as e:
        print(f"  → [Error] click_recaptcha_checkbox failed: {e}")
    finally:
        try:
            driver.switch_to.default_content()
            time.sleep(0.5)
        except Exception:
            pass

def solve_image_challenge_if_present(driver, wait, solver, solver_seg, max_image_attempts=3):
    """
    이미지 챌린지 풀이 시도. 성공 시 True, 아니면 False.
    """
    def enter_challenge_iframe():
        try:
            img_iframe = wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//iframe[contains(@title,'보안문자') or contains(@title,'challenge')]")))
            driver.switch_to.frame(img_iframe)
            print("  → [Info] Image challenge converted to iframe")
            return True
        except TimeoutException:
            print("  → [Info] Image Challenge iframe not found.")
            return False
    if not enter_challenge_iframe():
        return False
    while True:
        # 2) payload & 타일 수 확인
        payload = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.rc-imageselect-payload")))
        target_text = payload.find_element(By.TAG_NAME, "strong").text.strip()
        print(f"  → [Challenge] Target class: {target_text}")

        # 분기: secondary solver 사용 여부 결정
        if target_text in USE_SECONDARY:
            print("    ▶ [Info] secondary solver(segmentation) use")
            solver_to_use = solver_seg
        else:
            solver_to_use = solver
        print(f"  → [Info] Current model in use: {'secondary' if solver_to_use is solver_seg else 'primary'}")
        tile_elements = driver.find_elements(By.CSS_SELECTOR, "td.rc-imageselect-tile")
        num_tiles = len(tile_elements)
        print(f"  → [Info] {num_tiles}Tiles of were found")
        if num_tiles not in (9, 16):
            print("  → [Info] Not a 3×3 or 4×4 puzzle → End")
            driver.switch_to.default_content()
            return False
        

        grid_size = '3x3' if num_tiles == 9 else '4x4'
          # 이전 퍼즐판 이미지 저장용
        
        # 3) 이미지 챌린지 반복
        attempt=0
        while True:
            prev_puzzle_img = None
            attempt+=1
            print(f"    ▶ [Image Attempt {attempt}/{max_image_attempts}]")
            driver.switch_to.default_content()
            if not enter_challenge_iframe():
                return False
            payload = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.rc-imageselect-payload")))
            target_text = payload.find_element(By.TAG_NAME, "strong").text.strip()
            print(f"  → [Challenge Updated] Target Class: {target_text}")
            solver_to_use = solver_seg if target_text in USE_SECONDARY else solver
            print(f"  → [Info] Changed model: {'secondary' if solver_to_use is solver_seg else 'primary'}")
            # puzzle_root 재탐색
            tile_elements = driver.find_elements(By.CSS_SELECTOR, "td.rc-imageselect-tile")
            num_tiles = len(tile_elements)
            grid_size = '3x3' if num_tiles == 9 else '4x4'
            print(f"  → [Info] Updated Grid: {grid_size}, 타일 수: {num_tiles}")
            try:
                puzzle_root = driver.find_element(
                    By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]")
            except Exception:
                driver.switch_to.default_content()
                if not enter_challenge_iframe():
                    print("    → [Warn] New CAPTCHA iframe not found")
                    return False
                puzzle_root = driver.find_element(
                    By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]")

            #3*3 인 경우 
            if grid_size == '3x3':
                print("  → [Info] Calling solve_3x3()")
                clicked_indices = solver_to_use.solve_3x3(driver, puzzle_root)
                print(f"    • [Result] Clicked Index = {clicked_indices}")

                # === 여기에 삽입 ===
                # 한 번이라도 클릭했으면 모두 클릭할 때까지 반복 후 즉시 제출
                all_clicked = []
                if clicked_indices:
                    all_clicked = solver_to_use.solve_until_done(
                        driver, puzzle_root, grid_size='3x3', max_attempts=5
                    )
                if all_clicked:
                    verify_btn = wait.until(EC.element_to_be_clickable(
                        (By.ID, "recaptcha-verify-button")))
                    safe_click(driver, verify_btn)

                    print("  → [Info] Complete clicking all tiles, click Verify immediately")
                    time.sleep(1)
                    if check_recaptcha_solved(driver):
                        return True
        
                    if driver.find_elements(By.CSS_SELECTOR, ".rc-imageselect-error-select-more"):
                        print("    → [Info] Error message detected → Reload & retry")

                        # 이전 iframe/frame 빠져나와서 메인 컨텐트로
                        driver.switch_to.default_content()
                        enter_challenge_iframe()
                        # reload_and_reenter 헬퍼 호출 (리로드→대기→iframe 진입)
                        reload_btn = wait.until(
                                    EC.element_to_be_clickable((By.ID, "recaptcha-reload-button"))
                                )
                        
                        safe_click(driver, reload_btn)

                                # 기본 컨텍스트 복귀 및 iframe 재진입 준비
                        driver.switch_to.default_content()
                        prev_img = None  # 이미지 비교 초기화
                        puzzle_root = driver.find_element(
                            By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]"
                                )

                        continue
                    
                    else:
                        enter_challenge_iframe()
                        try:
                            # “더 많이 선택하세요” 또는 “죄송합니다. 다시 시도해 주세요” 에러 감지
                            if driver.find_elements(By.CSS_SELECTOR, ".rc-imageselect-error-select-more") or  driver.find_elements(By.CSS_SELECTOR, ".rc-imageselect-error-message"):
                                print("    → [Info] Error message detected → Reload & retry")
                                # Reload 버튼 클릭
                                enter_challenge_iframe()
                                reload_btn = wait.until(
                                    EC.element_to_be_clickable((By.ID, "recaptcha-reload-button"))
                                )
                        
                                safe_click(driver, reload_btn)
                            

                                # 기본 컨텍스트 복귀 및 iframe 재진입 준비
                                driver.switch_to.default_content()
                                prev_img = None  # 이미지 비교 초기화
                                puzzle_root = driver.find_element(
                                    By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]"
                                )
                                continue  # 다음 루프에서 다시 시도
                        except NoSuchElementException:
                            pass
                        print("Unsolved New puzzle created")
                        continue
                        
                # 4*4인 경운
            else:
                print("  → [Info] Call solve_4x4()")
                clicked_indices = solver_to_use.solve_4x4(driver, puzzle_root)
                   
                # 4×4 즉시 제출 분기
                 
                if clicked_indices:
                    print(f"    • [Result] Clicked index = {clicked_indices}")
                    verify_btn = wait.until(EC.element_to_be_clickable(
                    (By.ID, "recaptcha-verify-button")))
                    safe_click(driver, verify_btn)
                    print("  → [Info] Complete clicking on all 4×4 tiles, then click Verify immediately")
                    if check_recaptcha_solved(driver):
                        return True
                    else:
                        print("Unsolved New puzzle created")
                        continue
                        
                                
            if not clicked_indices:
                print("    → [Warn] No click target → Reload repeated attempts")
                for reload_try in range(1, 4):
                    try:
                        # 1) 이전 퍼즐판 테이블 요소를 미리 가져와 둡니다.
                        old_table = driver.find_element(
                            By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]"
                        )
                        # 2) Reload 버튼 클릭
                        reload_btn = wait.until(EC.element_to_be_clickable(
                            (By.ID, "recaptcha-reload-button")))
                        scroll_into_view(driver, reload_btn)
                        safe_click(driver, reload_btn)
                        print(f"    → [Info] Attempt to reload #{reload_try}")
                        # 3) 이전 테이블이 사라질 때까지 대기
                        wait.until(EC.staleness_of(old_table))
                        # 4) 메인 컨텍스트로 복귀
                        driver.switch_to.default_content()
                        # 5) 새 iframe 진입
                        if not enter_challenge_iframe():
                            print("    → [Warn] Failed to re-enter iframe")
                            continue
                        # 6) 새 퍼즐판 테이블이 로드될 때까지 대기
                        puzzle_root = wait.until(EC.presence_of_element_located(
                            (By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]")
                        ))
                        new_tiles = puzzle_root.find_elements(By.CSS_SELECTOR, "td.rc-imageselect-tile")
                        if new_tiles:
                            print("    → [Info] New puzzle board detected → Retry")
                            break
                        else:
                            print("    → [Warn] Puzzle board still missing → Reload")
                    except Exception as e:
                        print(f"    → [Error] Reload failed: {e}")
                        driver.switch_to.default_content()
                else:
                    # 3회 모두 실패했으면 종료
                    print("    → [Error] Puzzle board not found even after 3 reloads → End")
                    return False
            
                # Reload 후 재시도
                continue
        else:
            print(f"  → [Info] {attempt}번째 시도: solve_until_done() 재호출")
            clicked_indices = solver_to_use.solve_until_done(
                        driver, puzzle_root, max_attempts=5)
            print(f"    • [Result] 클릭된 인덱스 = {clicked_indices}")

# 체크박스가 성공했는지 여부
def check_recaptcha_solved(driver, wait=None):
    """
    reCAPTCHA 풀림 여부 확인
    - 먼저 메인 문서로 돌아간 뒤,
      체크박스 iframe으로 진입해서 'checked' 클래스를 검사합니다.
    - 실패 시 g-recaptcha-response 값도 확인합니다.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait as _W
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoSuchElementException, TimeoutException

    # 내부에서 wait 생성
    if wait is None:
        wait = _W(driver, 1)

    # 1) 메인 문서로 복귀
    driver.switch_to.default_content()

    # 2) 체크박스 iframe으로 진입
    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")))
    except TimeoutException:
        return False

    # 3) checked 상태 확인
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".recaptcha-checkbox-checked")))
        driver.switch_to.default_content()
        return True
    except TimeoutException:
        driver.switch_to.default_content()
        # 4) response textarea 확인
        try:
            resp = driver.find_element(By.CSS_SELECTOR, "textarea[name='g-recaptcha-response']")
            return bool(resp.get_attribute("value").strip())
        except NoSuchElementException:
            return False
                
def main():
    solver = ImageSolver(YOLO_CLS_WEIGHTS, YOLO_SEG_WEIGHTS)
    solver_seg = ImageSolver(YOLO_SECOND_WEIGHTS, YOLO_SEG_WEIGHTS) 
    for run_idx in range(1, NUM_TRIES + 1):
        print(f"\n=== Run #{run_idx} ===")
        driver = launch_browser_with_profile()
        wait = WebDriverWait(driver, 10)

        try:
            driver.get(RECAPTCHA_URL)
            print("  → [Info] Page load complete")
            driver.delete_all_cookies()
            time.sleep(1.0)
            driver.get(RECAPTCHA_URL)
            print("  → [Info] Reload after deleting cookies")

            click_recaptcha_checkbox(driver, wait)
            if check_recaptcha_solved(driver):
                print("[OK] Success with just a checkbox")
                driver.quit()
                break
            solve_image_challenge_if_present(driver, wait, solver, solver_seg)
            if check_recaptcha_solved(driver):
                print("[OK] recaptcha V2 bypass success")
                driver.quit()
                break
            else:
                print("[Fail]Unsolved")
                continue
            
        except Exception as e:
            print(f"[ERROR] Exception occurred: {e}")
        finally:
            driver.quit()
            print(f"[*] Run #{run_idx} Complete")
if __name__ == "__main__":
    main()