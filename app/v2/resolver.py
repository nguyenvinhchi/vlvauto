
from concurrent.futures import ThreadPoolExecutor
import time

from app.log_factory import create_logger
from app.send_window_event import simulate_click, simulate_mouse_move_around


LOGGER = create_logger(name='DoLogin')


def await_execute(func, *args, **kwargs):
        """
        Runs any callable in a background thread and blocks until result is returned.
        """
        with ThreadPoolExecutor() as executor:
            future = executor.submit(func, *args, **kwargs)
            r = future.result()  # Blocks until done

def click_login_button( points: tuple, delay=5000):
    # Step 1: Click Login button
    simulate_click(*points[0])
    LOGGER.info("Clicked login button")


def click_server_icon(points: tuple, delay=5000):
    simulate_click(*points[1])
    LOGGER.info("Clicked server icon")

def double_click_avatar(points: tuple):
    simulate_click(*points[2], action='double_click')
    LOGGER.info("Double-clicked character avatar")

def close_login_warning_dialog(points: tuple):
    # 4rd point is confirm button which will close the warning
    simulate_click(*points[3])

def close_login_server_connect_warning_dialog(self, points: tuple):
    simulate_click(*points[0])

class Resolver:
    
    @staticmethod
    def do_single_click(points: tuple):
        await_execute(simulate_click, *points[0])

    @staticmethod
    def do_login_user_pass(points: tuple):
        await_execute(click_login_button, points)
        time.sleep(5)
        await_execute(click_server_icon, points)
        time.sleep(5)
        await_execute(double_click_avatar, points)

    @staticmethod
    def do_select_server(points: tuple):
        await_execute(click_server_icon, points)
        time.sleep(5)
        await_execute(double_click_avatar, points)

    @staticmethod
    def do_select_character(points: tuple):
        await_execute(double_click_avatar, points)

    @staticmethod
    def do_move_around(start_x, start_y):
        await_execute(simulate_mouse_move_around, start_x, start_y)


