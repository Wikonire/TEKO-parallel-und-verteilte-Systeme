import argparse
import math
import sys
import time
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Pool, Manager
from queue import Queue
import logging
import functools

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])



def leibniz_term(k):
    return ((-1) ** k) / (2 * k + 1)


def compute_segment(start, count):
    return sum(leibniz_term(k) for k in range(start, start + count))

def run_internal_mode(start, count):
    result = compute_segment(start, count)
    print(result, flush=True)
    sys.exit(0)

def mode_gil(segments):
    results = [0] * len(segments)

    def worker(i, seg):
        results[i] = compute_segment(*seg)

    threads = [threading.Thread(target=worker, args=(i, seg)) for i, seg in enumerate(segments)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(results)


def mode_threadpool(segments):
    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda seg: compute_segment(*seg), segments)
    return sum(results)


def mode_process(segments):
    with Manager() as manager:
        result_dict = manager.dict()

        def worker(seg, idx):
            result_dict[idx] = compute_segment(*seg)

        processes = [Process(target=worker, args=(seg, idx)) for idx, seg in enumerate(segments)]
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        return sum(result_dict.values())


def pool_worker(seg):
    return compute_segment(*seg)


def mode_pool(segments, n):
    with Pool(processes=n) as pool:
        results = pool.map(pool_worker, segments)
    return sum(results)


def mode_hosts(segments, hosts, timeout):
    results = [0.0] * len(segments)

    def ssh_worker(i, seg, host):
        start, count = seg
        cmd = [
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            host, sys.executable, __file__,
            "--internal", "--start", str(start), "--count", str(count)
        ]
        try:
            logging.info(f"Segment {i} startet auf Host {host} ({start}, {count})")
            out = subprocess.check_output(cmd, text=True, timeout=60)
            results[i] = float(out.strip())
        except subprocess.SubprocessError as e:
            logging.error(f"SSH-Fehler auf {host}: {e}")

    threads = [threading.Thread(target=ssh_worker, args=(i, seg, hosts[i % len(hosts)]))
               for i, seg in enumerate(segments)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(results)


def producer_consumer(segments, num_consumers):
    q = Queue()
    results = [0.0] * len(segments)

    def producer():
        for idx, seg in enumerate(segments):
            q.put((idx, seg))
        for _ in range(num_consumers):
            q.put(None)

    def consumer():
        while True:
            item = q.get()
            if item is None:
                q.task_done()
                break
            idx, seg = item
            mapped = map(leibniz_term, range(seg[0], seg[0] + seg[1]))
            filtered = filter(lambda x: abs(x) > 1e-10, mapped)
            results[idx] = functools.reduce(lambda a, b: a + b, filtered, 0)
            q.task_done()

    prod_thread = threading.Thread(target=producer)
    consumers = [threading.Thread(target=consumer) for _ in range(num_consumers)]

    prod_thread.start()
    for c in consumers:
        c.start()

    prod_thread.join()
    q.join()
    for c in consumers:
        c.join()

    return sum(results)


def main():
    parser = argparse.ArgumentParser(description="π-Berechnung via Leibniz-Reihe parallel")

    parser.add_argument("--internal", action="store_true")
    parser.add_argument("--start", type=int)
    parser.add_argument("--count", type=int)

    # Interner Modus separat behandeln, bevor andere Argumente geprüft werden:
    args, remaining_args = parser.parse_known_args()

    if args.internal:
        if args.start is None or args.count is None:
            parser.error("--internal benötigt --start und --count.")
        run_internal_mode(args.start, args.count)

    # Für alle anderen Modi jetzt explizit die restlichen Argumente prüfen:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--with-gil", action="store_true")
    group.add_argument("--with-thread", action="store_true")
    group.add_argument("--with-proces", action="store_true")
    group.add_argument("--pool", type=int)
    group.add_argument("--hosts", type=lambda s: s.split(","))
    group.add_argument("--producer-consumer", type=int)

    parser.add_argument("-i", "--iterations", type=int, default=1_000_000)
    parser.add_argument("--seg-size", type=int, default=1_000_000)
    parser.add_argument("--timeout", type=int, default=60)

    args = parser.parse_args(remaining_args)

    total_terms = args.iterations
    segments = [
        (i * args.seg_size, min(args.seg_size, total_terms - i * args.seg_size))
        for i in range((total_terms + args.seg_size - 1) // args.seg_size)
    ]

    start_time = time.perf_counter()
    if args.with_gil:
        result = mode_gil(segments)
    elif args.with_thread:
        result = mode_threadpool(segments)
    elif args.with_proces:
        result = mode_process(segments)
    elif args.pool:
        result = mode_pool(segments, args.pool)
    elif args.hosts:
        result = mode_hosts(segments, args.hosts, args.timeout)
    elif args.producer_consumer:
        result = producer_consumer(segments, args.producer_consumer)
    else:
        parser.error("Kein Modus gewählt.")

    pi_est = result * 4
    elapsed = time.perf_counter() - start_time
    err = abs(math.pi - pi_est)

    logging.info(f"π≈{pi_est:.12f}, Fehler={err:.3e}, Zeit={elapsed:.3f}s")


if __name__ == "__main__":
    main()
