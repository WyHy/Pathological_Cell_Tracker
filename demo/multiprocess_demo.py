from concurrent.futures import ProcessPoolExecutor, as_completed
from time import sleep


# 测试方法
def test(a, b):
    """
    求和
    :param a: int
    :param b: int
    :return: sum
    """
    sleep(5)
    return a + b


if __name__ == '__main__':
    """
    多进程示例程序
    """

    MAX_WORKER_NUM = 2
    # 创建进程池
    executor = ProcessPoolExecutor(max_workers=MAX_WORKER_NUM)

    qua = [(1, 2), (2, 3), (3, 4), (4, 5), ]

    results = []
    for item in qua:
        results.append(executor.submit(test, item[0], item[1]))

    # 总进程数
    job_count = len(results)

    # 完成计数
    done_count = 0
    # 跟踪任务完成情况
    for future in as_completed(results):
        # 获取返回值
        val = future.result()
        done_count += 1

        print("%s， %s / %s" % (val, done_count, job_count))
