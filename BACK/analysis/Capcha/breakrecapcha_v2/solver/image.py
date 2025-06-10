import os
import re
import io
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from solver.behavior import human_like_move_and_click
from PIL import Image, ImageChops
import io

class ImageSolver:
    def __init__(self, cls_weights_path, seg_weights_path):
        # YOLOv8 모델 로드
        from ultralytics import YOLO
        self.cls_model = YOLO(cls_weights_path, verbose=False)
        self.seg_model = YOLO(seg_weights_path, verbose=False)

        # 한국어 → 영어 클래스 매핑
        self.class_map = {
            "cars":    "car",
            "bicycles": "bicycle",
            "자동차":        "car",
            "버스":          "bus",
            "오토바이":      "motorcycle",
            "교각":          "bridge",
            "소화전":        "hydrant",
            "자전거":        "bicycle",
            "화장실":        "toilet",
            "신호등":        "traffic light",
            "사람":          "person",
            "기차":          "train",
            "야자수":        "Palm",
            "횡단보도":      "crosswalk",
            "산 또는 언덕":   "mountain",
            "굴뚝":           "chimney"
        }
        plural_variants = {
            "cars":        "car",
            "buses":       "bus",
            "motorcycles": "motorcycle",
            "bridges":     "bridge",
            "fire hydrants":    "hydrant",
            "bicycles":    "bicycle",
            "toilets":     "toilet",
            "traffic lights": "traffic light",
            "people":      "person",
            "trains":      "train",
            "palms":       "Palm",
            "crosswalks":  "crosswalk",
            "mountains":   "mountain",
            "chimneys":    "chimney",
            "a fire hydrant": "hydrant"
        }
        self.class_map.update(plural_variants)
    def _parse_target(self, html_text: str) -> str:
        match = re.search(r"<strong[^>]*>([^<]+)</strong>", html_text)
        return match.group(1).strip() if match else ""

    def _get_target_text(self, driver):
        """
        화면 상의 <strong>…</strong> 세부 지시문(한국어)을 꺼내 리턴
        """
        selectors = [
            ".rc-imageselect-desc-no-canonical",
            ".rc-imageselect-desc",
            ".rc-imageselect-desc-canonical"
        ]
        for sel in selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                raw_html = elem.get_attribute("innerHTML")
                return self._parse_target(raw_html)
            except NoSuchElementException:
                continue
        return ""

    def _tile_to_pil(self, tile_element):
        """
        WebElement 타일을 screenshot_as_png로 받아 PIL.Image로 변환
        """
        try:
            png_bytes = tile_element.screenshot_as_png
        except StaleElementReferenceException:
            # 호출한 쪽에서 다시 찾아서 시도하도록 예외 전달
            raise
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")

    def solve_3x3(self, driver, puzzle_root):
        """
        3×3 퍼즐 한 판에서 정답 타일만 클릭.
        클릭된 인덱스를 리스트로 반환. 빈 리스트인 경우 → []
        """
        target_ko = self._get_target_text(driver)
        print(f"    • [Debug] solve_3x3: Parsed target (Korean) = '{target_ko}'")
        if not target_ko:
            return []

        target_en = self.class_map.get(target_ko)
        if target_en is None:
            return []
        print(f"    • [Info] Mapped YOLO class name (English) = '{target_en}'")

        # 최신 tile_wrappers 찾기
        try:
            tile_wrappers = puzzle_root.find_elements(By.CLASS_NAME, "rc-image-tile-wrapper")
        except StaleElementReferenceException:
            puzzle_root = driver.find_element(
                By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]"
            )
            tile_wrappers = puzzle_root.find_elements(By.CLASS_NAME, "rc-image-tile-wrapper")

        clicked_indices = []
        for idx, tile in enumerate(tile_wrappers):
            try:
                pil_img = self._tile_to_pil(tile)
            except StaleElementReferenceException:
                # 판이 바뀌었으면 다시 찾기
                tile_wrappers = puzzle_root.find_elements(By.CLASS_NAME, "rc-image-tile-wrapper")
                tile = tile_wrappers[idx]
                pil_img = self._tile_to_pil(tile)

            # 객체 검출
            results = self.cls_model.predict(source=pil_img, imgsz=256, conf=0.25)
            preds = results[0]
            names = preds.names
            cls_indices = preds.boxes.cls.cpu().numpy().astype(int)

            label = names[cls_indices[0]] if len(cls_indices) > 0 else "none"
            found = any(names[c] == target_en for c in cls_indices)
            if found:
                clicked_indices.append(idx)
            #print(f"      ▶ 타일 {idx}: 예측('{label}'), 목표('{target_en}') 여부: {found}")

        print(f"    • [Result] Index to click = {clicked_indices}")

        # 실제 클릭
        for idx in clicked_indices:
            try:
                human_like_move_and_click(driver, tile_wrappers[idx], duration=0.4)
                print(f"    • [Action] Tile {idx} clicked")
                time.sleep(0.4)
            except StaleElementReferenceException:
                # 재탐색 후 클릭
                tile_wrappers = puzzle_root.find_elements(By.CLASS_NAME, "rc-image-tile-wrapper")
                human_like_move_and_click(driver, tile_wrappers[idx], duration=0.4)
                print(f"    • [Fallback Action] Tile {idx} Clicked (Re-search)")
                time.sleep(0.4)
            except Exception as e:
                print(f"    • [Error] Tile {idx} click fail: {e}")
                try:
                    tile_wrappers[idx].click()
                except Exception as e2:
                    print(f"      → [Error] fallback click() fail: {e2}")

        return clicked_indices

    def solve_4x4(self, driver, puzzle_root):
        """
        4×4 퍼즐 한 판에서 정답 타일만 클릭.
        디버그용 이미지(debug_click_*.png)도 함께 저장합니다.
        """
        
        target_ko = self._get_target_text(driver)
        
        if not target_ko:
            return []
        target_en = self.class_map.get(target_ko)
        print(f"    • [Debug] solve_4x4: Parsed target (Korean) = '{target_ko}'")
        if target_en is None:
            return []
        print(f"    • [Info] Mapped YOLO class name (English) = '{target_en}'")
        # 1) 타일 래퍼 & PIL 이미지
        tile_wrappers = puzzle_root.find_elements(By.CLASS_NAME, "rc-image-tile-wrapper")
        pil_tiles = [self._tile_to_pil(t) for t in tile_wrappers]
        tile_w, tile_h = pil_tiles[0].size

        # 2) 전체 스티치 & 예측
        stitched = Image.new("RGB", (tile_w * 4, tile_h * 4))
        for i, img in enumerate(pil_tiles):
            stitched.paste(img, ((i % 4) * tile_w, (i // 4) * tile_h))
        results = self.cls_model.predict(source=stitched, imgsz=640, conf=0.15)[0]
        bboxes = results.boxes.xyxy.cpu().numpy().astype(int)
        class_ids = results.boxes.cls.cpu().numpy().astype(int)
        names = results.names

        # 3) 디버그용 그리기 준비
        #draw = ImageDraw.Draw(stitched)
        #font = ImageFont.load_default()
        # 그리드 선
        #for i in range(1, 4):
        #    draw.line([(i*tile_w, 0), (i*tile_w, tile_h*4)], fill="gray")
        #    draw.line([(0, i*tile_h), (tile_w*4, i*tile_h)], fill="gray")

        # 4) 겹침 기준으로 선택 및 시각화
        clicked_indices = []
        for i, bbox in enumerate(bboxes):
            if names[class_ids[i]] != target_en:
                continue

            x1, y1, x2, y2 = bbox
            # 빨간 박스: 2px 인셋
        #    draw.rectangle([x1+2, y1+2, x2-2, y2-2], outline="red", width=2)

            # 겹치는 타일 파란 박스 표시
            for idx in range(16):
                row, col = divmod(idx, 4)
                tx1, ty1 = col*tile_w, row*tile_h
                tx2, ty2 = tx1+tile_w, ty1+tile_h

                if not (x2 <= tx1 or x1 >= tx2 or y2 <= ty1 or y1 >= ty2):
                    if idx not in clicked_indices:
                        clicked_indices.append(idx)
                        # 파란 박스: 2px 인셋
            #            draw.rectangle([tx1+2, ty1+2, tx2-2, ty2-2], outline="blue", width=2)

        clicked_indices = sorted(clicked_indices)
        print(f"      ▶ [4×4] Tile index to click = {clicked_indices}")

        # 5) 디버그 이미지 저장
        #debug_path = f"debug_click_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        #stitched.save(debug_path)
        #print(f"    • [Debug] debug image saved to {debug_path}")

        # 6) 실제 클릭 수행 (타일 중앙에서 10% inset)
        from selenium.webdriver import ActionChains
        for idx in clicked_indices:
            el = tile_wrappers[idx]
            w, h = el.size['width'], el.size['height']
            # 중앙 위치 + 10% inset
            off_x = w*0.5 * 0.8
            off_y = h*0.5 * 0.8
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            ActionChains(driver) \
                .move_to_element_with_offset(el, off_x, off_y) \
                .click() \
                .perform()
            print(f"    • [Action] Tile {idx} clicked at offset ({off_x:.0f},{off_y:.0f})")
            time.sleep(0.3)

        return clicked_indices

    def solve_until_done(self, driver, puzzle_root, grid_size='3x3', max_attempts=10):
        """
        • grid_size == '4x4': 한 번만 solve_4x4() 호출 → 즉시 반환
        • grid_size == '3x3': 퍼즐판(타일)이 남아 있는 한 반복, 
          타일 요소가 더 이상 없을 때만 종료
        """
        # 4×4는 단일 호출
        if grid_size == '4x4':
            # 1) 4×4 퍼즐 한 판 풀기
            clicked = self.solve_4x4(driver, puzzle_root)
            print(f"    • [Result] 4×4 Clicked Index = {clicked}")

            # 2) 잠시 대기 → 새 퍼즐판(iframe) 나왔는지 확인
            time.sleep(1.5)
            driver.switch_to.default_content()
            new_tiles = driver.find_elements(By.CSS_SELECTOR, "td.rc-imageselect-tile")
            if new_tiles:
                print("    • [Info] New 4x4 puzzle detected → Try again")
                # 3) 새 퍼즐판 iframe으로 다시 진입해서 재귀 호출
                #    (혹은 while 루프라면 continue)
                return self.solve_until_done(driver, new_tiles[0].find_element(
                    By.XPATH, "./ancestor::table"), max_attempts= max_attempts-1)
            else:
                # 4) 더 이상 퍼즐판이 없으면 최종 반환
                return clicked

        # 3×3 퍼즐인 경우
        prev_img = None  
        all_clicked = []
        def enter_challenge_iframe():
            # solve_image_challenge_if_present 과 동일한 헬퍼
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                    "//iframe[contains(@title,'challenge') or contains(@title,'보안문자')]"))
            )
            driver.switch_to.frame(iframe)

        for attempt in range(1, max_attempts + 1):
            print(f"[Attempt {attempt}/{max_attempts}]")

            # 1) 클릭 전 스냅샷
            puzzle_root = driver.find_element(
                By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]"
            )
            prev_png = puzzle_root.screenshot_as_png
            prev_img = Image.open(io.BytesIO(prev_png)).convert('RGB')

            # 2) 실제 클릭 액션
            clicked = self.solve_3x3(driver, puzzle_root)
            if clicked:
                all_clicked.extend(clicked)
            else:
                print("    • [Info] There are no clickable targets on this board.")

            # 3) 조금 대기
            time.sleep(1.0)

            # 4) 메인 컨텐트로 복귀 후 iframe 재진입
            driver.switch_to.default_content()
            enter_challenge_iframe()
            # 5) 새 테이블이 로드될 때까지 대기
            puzzle_root = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@class,'rc-imageselect-table-')]")
                )
            )
            curr_img = Image.open(io.BytesIO(puzzle_root.screenshot_as_png)).convert('RGB')

            diff = ImageChops.difference(curr_img, prev_img)
            #prev_img.save("debug_prev.png")
            #curr_img.save("debug_curr.png")
            #diff.save("debug_diff.png")
            print("  → [Debug] Saved debug_prev.png, debug_curr.png, debug_diff.png")

            # 8) 보드 변경 없으면 반복 종료
            if diff.getbbox() is None:
                print("    • [Info] Puzzle board did not change → break")
                break

            # 없으면 다음 시도로 계속
            print("    • [Info] Puzzle board changed → next attempt")

            

        print(f"    • [Result] Total clicked index = {all_clicked}")
        return all_clicked
