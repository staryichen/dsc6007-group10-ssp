"""网格核对的公共路径、命令行参数和固定输入版本校验。"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='A 独立核对 C 的固定 E2 网格产物')
parser.add_argument('--c-source',required=True,type=Path,help='固定 C 提交的源码目录')
parser.add_argument('--output',type=Path,default=ROOT/'results',help='独立核对输出目录')
parser.add_argument('--tag',default='a_review_v1',help='重现图表版本，已有版本不会覆盖')
args=parser.parse_args()
SOURCE=args.c_source.resolve();OUT=args.output.resolve();TAG=args.tag
expected=json.loads((ROOT/'source_hashes.json').read_text())
for name,digest in expected['files'].items():
    p=SOURCE/name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('输入与已核对的 C 固定版本不同：'+name)
