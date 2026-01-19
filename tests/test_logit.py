# import os
# import sys
import time
from typing import Callable, TypeVar, ParamSpec
# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(root_path)

from src.pyutilities.logit import pv, po, pe
from src.pyutilities.logit import time_calc, LogLevel, Logit, EmailLogit


# 定义参数规格变量（表示任意参数）
P = ParamSpec("P")
# 定义返回值类型变量（表示任意返回值）
R = TypeVar("R")

if __name__ == '__main__':

    @time_calc
    def add(a: int, b: int) -> int:
        """两数相加"""
        time.sleep(0.1)  # 模拟耗时操作
        return a + b

    # 接受任意函数，并保留其参数和返回值类型
    def run_func(func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """执行任意函数并返回其结果"""
        return func(*args, **kwargs)

    print("test po")
    a = 5
    po(f"a: {a}")
    po(f"a: {a}", "haha")

    print("\ntest pe")
    pe(run_func(add, 2, 3))
    pe(add(2, 3))
    pe([i*i for i in range(10)])

    arr = ["a", "", None, "d"]
    matrix = [["x", ""], [None, "y"]]
    d = {"": 100, None: 200, "key": 300}

    i = 0  # 空字符串的索引
    j = 1  # 第二个元素的索引
    empty_key = ""
    none_key = None

    pv(arr[i])
    pv(arr[j])
    pv(matrix[i][j])
    pv(d[empty_key])
    pv(d[none_key])
    pv(matrix[i+1][j-1])
    pv(arr[0] if i > 0 else arr[3])  # 复杂表达式测试

    import numpy as np
    # import numpy.typing as npt
    ary1 = np.linspace(0, 39, 4, dtype=np.float32)
    ary2 = [i for i in range(4)]

    for i in range(4):
        pv(ary1[i])
        pv(ary2[i])

    i = 1
    j = 2
    matij = np.random.randn(3, 3)
    pv(matij[i, j])
    pv(matij[i][j])

    print("\ntest Logit")
    logit = Logit(LogLevel.ERROR)
    logit.info("haha")
    logit.err("wahaha")

    @Logit()
    def say(something: str):
        print(f"say {something}!")

    say('hello')
