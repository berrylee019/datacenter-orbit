"""루트 진입점: CI에서 `python test_dedup.py` 한 줄로 중복 감지 테스트를 실행한다.

실제 테스트 코드는 utils/test_dedup.py 에 있고, 여기서는 그 모듈을
__main__ 으로 실행해 결과(assert 실패 시 exit code 1)를 그대로 전달한다.
워크플로(test-dedup.yml)는 이 파일을 실행하므로, 테스트 내용을 고칠 때는
utils/test_dedup.py 를 수정하면 된다.
"""

import os
import runpy
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if __name__ == "__main__":
    runpy.run_module("utils.test_dedup", run_name="__main__")
