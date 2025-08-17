from PyQt6.QtCore import QTimer

def run(func, delay_before_secs=0, delay_after_secs=0, *args, **kwargs):
    delayed_call = lambda: func(*args, **kwargs)
    QTimer.singleShot(delay_before_secs*1000, delayed_call)