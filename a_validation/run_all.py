"""使用当前 Python 解释器运行 A 的本地复现检查。"""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
jobs=[
    root/"test_regressions.py",
    root/"exact.py",
    root/"verify_e1.py",
    root/"example2.py",
    root/"check_budget_dp.py",
]
(root/"results").mkdir(exist_ok=True)
for path in jobs:
    print(f"正在运行 {path.relative_to(root)}",flush=True)
    r=subprocess.run([sys.executable,str(path)],cwd=root,text=True,capture_output=True)
    log=root/"results"/(path.stem+"_run.log")
    log.write_text(r.stdout+r.stderr,encoding="utf-8")
    print(r.stdout+r.stderr,end="",flush=True)
    if r.returncode:
        raise SystemExit(r.returncode)
print("A 的本地检查完成；这不代表 C 的求解器或最终网格已验收。")
