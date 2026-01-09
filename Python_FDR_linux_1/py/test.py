import time
from timeout_decorator import timeout

# 首先安装：pip install timeout-decorator

@timeout(20, use_signals=False)
def long_running_function():
    print("开始执行长时间运行的函数...")
    time.sleep(5)  # 尝试修改为小于20的数值测试正常执行
    print("函数执行完成")
    return "结果"

if __name__ == "__main__":
    try:
        result = long_running_function()
        print(f"函数成功执行，结果: {result}")
    except TimeoutError:
        print("函数执行超时（20秒），程序退出")
        exit(1)