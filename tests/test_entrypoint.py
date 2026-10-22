"""Run the real renamed entry point and its Tk event loop on temporary settings."""
import os
import runpy
import sys
import tempfile
from pathlib import Path
import tkinter as tk

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
launcher = (root / 'Start.bat').read_text(encoding='utf-8')
assert 'python file_order.py' in launcher
assert (root / 'organizer_engine.py').is_file()
original_tk = tk.Tk
windows = []

class SmokeWindow(original_tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes('-alpha', 0.0)
        windows.append(self)
        self.after(250, self.close_after_startup)

    def close_after_startup(self):
        assert self.title().startswith('File Order')
        assert hasattr(self, 'file_order_app')
        self.destroy()

with tempfile.TemporaryDirectory() as temp:
    os.environ['LOCALAPPDATA'] = temp
    tk.Tk = SmokeWindow
    try:
        runpy.run_path(str(root / 'file_order.py'), run_name='__main__')
    finally:
        tk.Tk = original_tk
assert len(windows) == 1
print('PASS: renamed launcher, engine import, real application startup and event loop')
