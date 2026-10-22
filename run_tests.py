import subprocess
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
for test in sorted((root / "tests").glob("test_*.py")):
    print(f"Running {test.name}", flush=True)
    env=dict(os.environ,FILE_ORDER_LANGUAGE='tr')
    subprocess.run([sys.executable, str(test)], cwd=root, check=True,env=env)
print("All tests passed.")
