#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import re
import inspect
import time
from enum import IntEnum
from functools import wraps
# from functools import partial
from typing import override
from typing import Callable, TypeVar, ParamSpec
from typing import Optional, Dict


# 定义一个泛型类型变量，表示任意类型
T = TypeVar('T')


def po(*values: T, endstr: str = "\n") -> None:
    """
    打印变量值并附带调用位置信息（行号和文件名）
    
    Args:
        *values: 要打印的一个或多个值
        endstr: 输出结尾字符，默认为换行符
    """
    # 使用inspect模块的公共API获取调用帧信息（更规范）
    frame = inspect.currentframe()
    # 获取当前帧的上一帧（即调用者的帧）
    caller_frame = frame.f_back if frame else None
    
    filename: Optional[str] = None
    linenum: Optional[int] = None

    if caller_frame:
        filename = caller_frame.f_code.co_filename
        linenum = caller_frame.f_lineno
        # 帮助垃圾回收
        del caller_frame

    # 清理当前帧引用
    if frame:
        del frame

    # 处理无法获取位置信息的情况
    file_info = (f"{linenum}@{filename}" 
                 if (linenum is not None and filename is not None) 
                 else "unknown location")

    # 处理值的字符串转换
    try:
        outputstr = ", ".join(map(str, values))
    except (TypeError, ValueError, OverflowError) as e:
        # 捕获字符串转换中常见的特定异常：
        # TypeError - 类型不支持str()转换
        # ValueError - 转换过程中值无效
        # OverflowError - 数值过大无法转换
        outputstr = f"Error converting values to string: {e}"

    # 打印结果
    print(f"{file_info} ", end="")
    print(outputstr, end=endstr)


def pv(p: T, endstr: str = "\n") -> None:
    """
    打印变量及其名称（支持多层索引表达式）和调用位置信息，
    确保正确显示所有层级索引变量的值
    
    Args:
        p: 要打印的变量
        endstr: 输出结尾字符，默认为换行符
    """
    var_name = ""
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back if current_frame else None

    if caller_frame:
        # 获取调用者代码行并提取变量名
        caller_lines = inspect.getframeinfo(caller_frame)[3]
        if caller_lines:
            for line in caller_lines:
                # 移除注释和多余空格
                cleaned_line = re.sub(r"#.*$", "", line).strip()
                # 匹配pv(...)表达式，支持带空格的情况
                if match := re.search(r'\bpv\s*\(\s*(.+?)\s*(?:,|)\s*\)', cleaned_line):
                    var_name = match.group(1).split(", end")[0].strip()
                    break

        # 处理索引表达式（支持多层索引）
        # 先尝试匹配双层索引（如a[i][j]）
        double_index_match = re.search(
            r"^(.+?)\[([^\]]+)\]\[([^\]]+)\]$", 
            var_name
        )
        
        # 再尝试匹配逗号分隔索引（如a[i,j]）
        comma_index_match = re.search(
            r"^(.+?)\[([^\]]+),\s*([^\]]+)\]$", 
            var_name
        )
        
        # 最后尝试匹配单层索引（如a[i]）
        single_index_match = re.search(
            r"^(.+?)\[([^\]]+)\]$", 
            var_name
        )

        # 处理双层索引
        if double_index_match:
            base, idx1, idx2 = double_index_match.groups()
            resolved_idx1 = _resolve_index(idx1, caller_frame.f_locals)
            resolved_idx2 = _resolve_index(idx2, caller_frame.f_locals)
            var_name = f"{base}[{resolved_idx1}][{resolved_idx2}]"
        
        # 处理逗号分隔索引
        elif comma_index_match:
            base, idx1, idx2 = comma_index_match.groups()
            resolved_idx1 = _resolve_index(idx1, caller_frame.f_locals)
            resolved_idx2 = _resolve_index(idx2, caller_frame.f_locals)
            var_name = f"{base}[{resolved_idx1}, {resolved_idx2}]"
        
        # 处理单层索引
        elif single_index_match:
            base, idx = single_index_match.groups()
            resolved_idx = _resolve_index(idx, caller_frame.f_locals)
            var_name = f"{base}[{resolved_idx}]"

        # 清理帧引用
        del caller_frame

    # 清理当前帧引用
    if current_frame:
        del current_frame

    # 获取位置信息（行号和文件名）
    file_info = "unknown location"
    frame = inspect.currentframe()
    if frame and frame.f_back:
        back_frame = frame.f_back
        filename = back_frame.f_code.co_filename
        linenum = back_frame.f_lineno
        file_info = f"{linenum}@{filename}"
        del back_frame
    if frame:
        del frame

    # 打印结果
    print(f"{file_info} {var_name} = {p}", end=endstr)


V = TypeVar('V')  # 用于索引值的泛型
def _resolve_index(index_expr: str, locals_dict: Dict[str, V]) -> str:
    """解析索引表达式，将变量替换为实际值（处理空值）"""
    index_expr = index_expr.strip()
    
    # 检查是否是变量引用
    if index_expr in locals_dict:
        val = locals_dict[index_expr]
        if val is None:
            return "None"
        elif isinstance(val, str) and val.strip() == "":
            return '""'
        else:
            return str(val)
    
    # 检查是否是复杂表达式（尝试简单解析）
    try:
        # 尝试评估表达式（仅使用局部变量）
        # 注意：这有一定风险，仅用于调试场景
        return str(eval(index_expr, {}, locals_dict))
    except (NameError, TypeError, ValueError, SyntaxError) as e:
        # 明确捕获可能的异常类型：
        # NameError - 表达式中包含未定义的变量
        # TypeError - 表达式类型错误（如字符串与数字相加）
        # ValueError - 表达式值无效
        # SyntaxError - 表达式语法错误
        return index_expr


def pe(exp: T, end: str = "\n") -> None:
    """
    打印表达式及其运行结果（调试专用），支持嵌套函数调用等复杂表达式
    
    Args:
        exp: 任意表达式（会被求值）
        end: 输出结尾字符，默认为换行符
    """
    exp_name: Optional[str] = None
    # 先获取当前帧，添加空检查
    current_frame = inspect.currentframe()
    if current_frame is None:
        # 无法获取帧信息时直接使用默认名称
        exp_name = "expression"
    else:
        # 获取调用者帧，同样添加空检查
        caller_frame = current_frame.f_back
        if caller_frame:
            caller_lines = inspect.getframeinfo(caller_frame)[3]
            
            if caller_lines:
                # 改进的正则：使用平衡括号匹配来处理嵌套函数调用
                pattern = r"\bpe\s*\(([^()]*+(?:\([^()]*+\)[^()]*+)*+)\)"
                
                for line in caller_lines:
                    cleaned_line = re.sub(r"#.*$", "", line).strip()
                    match = re.search(pattern, cleaned_line)
                    
                    if match:
                        exp_name = match.group(1).rstrip(',').strip()
                        break
        
        # 显式删除帧引用，帮助垃圾回收
        del current_frame

    # 处理未匹配到表达式的情况
    if exp_name is None:
        exp_name = "expression"
    
    # 打印表达式和结果
    print(f"{exp_name} = {exp}", end=end)


# 定义参数规格变量（表示任意参数）
P = ParamSpec("P")
# 定义返回值类型变量（表示任意返回值）
R = TypeVar("R")
def time_calc(func: Callable[P, R]) -> Callable[P, R]:
    """装饰器：计算并打印函数的执行时间"""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()
        result = func(*args, **kwargs)  # 执行被装饰的函数
        exec_time = time.time() - start_time
        print(f"{func.__name__}花费的时间是：{exec_time:.6f}秒")
        return result
    return wrapper


class LogLevel(IntEnum):
    INFO = 1
    WARN = 2
    ERROR = 3


class Logit():
    def __init__(self, level: LogLevel = LogLevel.INFO, logfile: str = ""):
        self._level: LogLevel = level
        self._logfile: str = logfile

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]: # 接受函数
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # print(__name__)
            # fun_name = sys._getframe().f_code.co_name
            fun_name = func.__name__
            self._log(self._level, f"{fun_name}() was called")
            return func(*args, **kwargs)
        return wrapper  # 返回函数

    def _notify(self):
        pass

    def _log(self, level: LogLevel, msg: str):
        if level >= self._level:
            # print(__file__)
            # print(sys._getframe().f_lineno)
            timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            # filename = sys._getframe().f_code.co_filename
            filename: Optional[str] = None
            linenum: Optional[int] = None
            frame = inspect.currentframe()
            # 获取当前帧的上一帧（即调用者的帧）
            caller_frame = frame.f_back if frame else None
            if caller_frame:
                filename = caller_frame.f_code.co_filename
                linenum = caller_frame.f_lineno
                # 帮助垃圾回收
                del caller_frame

            # 清理当前帧引用
            if frame:
                del frame
            # linenum = sys._getframe().f_back.f_back.f_lineno
            # 处理无法获取位置信息的情况
            file_info = (f"{linenum:03d}@{filename}" 
                 if (linenum is not None and filename is not None) 
                 else "unknown location")
            logstring = f"{timestr} {file_info} [{level}]: {msg}"
            print(logstring)
            if self._logfile:
                with open(self._logfile, 'a', encoding='utf8') as opened_file:
                    _ = opened_file.write(logstring + '\n')
            self._notify()

    def info(self, msg: str):
        self._log(LogLevel.INFO, msg)

    def warn(self, msg: str):
        self._log(LogLevel.WARN, msg)

    def err(self, msg: str):
        self._log(LogLevel.ERROR, msg)


class EmailLogit(Logit):
    def __init__(self, email: str, level: LogLevel = LogLevel.INFO):
        self._email = email
        super().__init__(level, "")

    @override
    def _notify(self):
        # send a email to self._email
        pass


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
    ary1 = np.linspace(0, 39, 4)
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
