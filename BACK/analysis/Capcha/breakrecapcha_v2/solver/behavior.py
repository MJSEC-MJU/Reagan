# solver/behavior.py

import random
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException


def human_like_move_and_click(driver, element, duration: float = 0.5):
    """
    요소의 “정확한 화면 좌표”를 계산해서, 그 지점으로 마우스를 부드럽게 이동한 뒤 클릭합니다.

    1) 요소를 화면 중앙에 스크롤(스크롤한 뒤 짧게 대기)
    2) element.rect 를 사용해 “뷰포트 내 실제 좌표(x_abs, y_abs)” 계산
    3) ActionChains 를 통해 move_by_offset → 클릭
    4) 클릭 후 짧은 딜레이
    """
    # 1) 요소를 화면 중앙에 스크롤
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
    except Exception:
        pass

    # 스크롤 후 DOM/렌더링이 안정될 때까지 잠시 대기
    time.sleep(0.3 + random.uniform(0, 0.1))

    # 2) 화면 내 절대 좌표 계산
    # element.rect 은 브라우저 뷰포트 기준으로 (x, y, width, height)를 리턴
    rect = element.rect
    x_center = rect['x'] + rect['width'] / 2
    y_center = rect['y'] + rect['height'] / 2

    # 3) ActionChains 를 통해 move_by_offset
    action = ActionChains(driver)

    # 현재 마우스 커서 위치를 “(0, 0)”이라고 가정하고 움직인다고 가정
    # 실제는 브라우저가 내부적으로 px 단위로 처리하므로, 아래 move_by_offset 은 
    # (뷰포트 좌측 상단 기준) mouse가 이동해야 할 거리로 이해하시면 됩니다.
    try:
        # 몇 단계로 나눠서 이동할지 계산 (너무 빠르게 움직이면 봇으로 보일 수 있으므로 여러 스텝)
        steps = int(max(abs(x_center), abs(y_center)) / 100) + 1
        dx = x_center / steps
        dy = y_center / steps

        current_x, current_y = 0, 0
        for _ in range(steps):
            # 각 스텝마다 살짝 랜덤을 섞어서 자연스러운 움직임처럼 보이게 함
            move_x = dx + random.uniform(-3, 3)
            move_y = dy + random.uniform(-3, 3)
            current_x += move_x
            current_y += move_y
            action.move_by_offset(move_x, move_y)
            action.pause(duration / steps + random.uniform(0, 0.01))

        action.click().perform()

    except MoveTargetOutOfBoundsException:
        # move_target 이 뷰포트 밖이라 오류가 난다면, fallback 으로 단순 element.click()
        try:
            element.click()
        except Exception:
            pass

    except Exception:
        # 그 외 예외 발생 시에도 fallback 으로 단순 element.click()
        try:
            element.click()
        except Exception:
            pass

    # 4) 클릭 후 짧은 랜덤 대기
    time.sleep(0.2 + random.uniform(0, 0.2))
