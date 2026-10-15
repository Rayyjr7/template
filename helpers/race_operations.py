"""Bounded polling and synchronized thread-race helpers."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Barrier


def poll(fetch, ready, timeout=15.0, interval=0.5):
    """Call fetch until ready(result) is true or timeout expires."""
    deadline = time.monotonic() + timeout
    while True:
        result = fetch()
        if ready(result):
            return result
        if time.monotonic() >= deadline:
            raise TimeoutError("result was not ready before the timeout")
        time.sleep(interval)


def run_parallel(call, inputs, *, workers=10):
    """Call call(value) concurrently and preserve input order in the result."""
    values = list(inputs)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(call, values))


def race(call, attempts=20, *, workers=None):
    """Release synchronized workers together and return completion-order results."""
    if attempts <= 0:
        raise ValueError("attempts must be positive")
    worker_count = attempts if workers is None else min(workers, attempts)
    if worker_count <= 0:
        raise ValueError("workers must be positive")

    results = []
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        for start in range(0, attempts, worker_count):
            batch = range(start, min(start + worker_count, attempts))
            barrier = Barrier(len(batch))

            def invoke(index):
                barrier.wait()
                return call(index)

            futures = [executor.submit(invoke, index) for index in batch]
            for future in as_completed(futures):
                results.append(future.result())
    return results
