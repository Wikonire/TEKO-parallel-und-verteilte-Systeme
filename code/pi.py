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

"""
Calculate the k-th term of the Leibniz series for approximating π.

The Leibniz series for π is an infinite series that converges to π
when multiplied by 4. Each term in the series alternates in sign
and is formed based on the given input k.

:param k: int
    The non-negative integer index of the term in the Leibniz series.
:return: float
    The k-th term of the Leibniz series.
"""
def leibniz_term(k):

    return ((-1) ** k) / (2 * k + 1)

"""
    This function calculates the sum of a segment from the Leibniz series,
    starting from a specific index and extending a specific number of terms.
    The Leibniz series is an infinite series representation for approximating
    π (pi). Each term in the series is calculated using the `leibniz_term`
    function and is composed of reciprocals of odd numbers, alternating
    between addition and subtraction.

    :param start: The starting index of the segment in the Leibniz series.
                  The index must be a non-negative integer.
    :param count: The number of terms to include in the segment from the
                  starting index. This must be a non-negative integer.
    :return: The sum of the Leibniz series terms in the specified segment.
    :rtype: float
"""
def compute_segment(start, count):
    return sum(leibniz_term(k) for k in range(start, start + count))

"""
    Executes a segment computation in internal mode and terminates the program.

    This function computes a specific segment defined by the `start` and `count`
    parameters. The computed result is printed to standard output, and the program
    exits afterward.

    :param start: The starting index of the segment to compute.
    :type start: int
    :param count: The number of items to include in the segment computation.
    :type count: int
    :return: This function does not return a value as it exits the program
             after executing.
    :rtype: None
"""
def run_internal_mode(start, count):

    result = compute_segment(start, count)
    print(result, flush=True)
    sys.exit(0)

def worker(seg, idx, result_dict):
    result_dict[idx] = compute_segment(*seg)

def mode_gil(segments):
    results = [0] * len(segments)

    threads = [
        threading.Thread(target=worker, args=(seg, i, results))
        for i, seg in enumerate(segments)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(results)


"""
    Executes parallel computation on segments using ThreadPoolExecutor and computes 
    the sum of the results. Each segment is processed by the `compute_segment` 
    function, which is applied to the unpacked segment data.

    :param segments: A list of segment data tuples, where each tuple contains 
        the arguments to be passed to the `compute_segment` function.
    :type segments: list[tuple]

    :return: The sum of the results obtained by applying `compute_segment` on 
        all segments in the input list.
    :rtype: int
"""
def mode_threadpool(segments):

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda seg: compute_segment(*seg), segments)
    return sum(results)

def mode_process(segments, worker_func=worker):
    with Manager() as manager:
        result_dict = manager.dict()

        processes = [
            Process(target=worker_func, args=(seg, idx, result_dict))
            for idx, seg in enumerate(segments)
        ]

        for p in processes:
            p.start()
        for p in processes:
            p.join()

        return sum(result_dict.values())

# Berechnet die Teilsumme eines einzelnen Segments der Leibniz-Reihe
def pool_worker(seg):
    return compute_segment(*seg)


def mode_pool(segments, n):
    # Prozesspool erstellen
    with Pool(processes=n) as pool:
        # Segmente werden parallel verarbeitet
        results = pool.map(pool_worker, segments)
    # Summe wird erstellt, und Resultat zurückgegeben    
    return sum(results)


def ssh_worker(i, seg, host, results, timeout=60):
    start, count = seg
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        host, sys.executable, __file__,
        "--internal", "--start", str(start), "--count", str(count)
    ]
    try:
        logging.info(f"Segment {i} startet auf Host {host} ({start}, {count})")
        out = subprocess.check_output(cmd, text=True, timeout=timeout)
        results[i] = float(out.strip())
    except subprocess.SubprocessError as e:
        logging.error(f"SSH-Fehler auf {host}: {e}")


def mode_hosts(segments, hosts, timeout=60):
    results = [0.0] * len(segments)
    threads = [
        threading.Thread(target=ssh_worker, args=(i, seg, hosts[i % len(hosts)], results, timeout))
        for i, seg in enumerate(segments)
    ]

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
    parser = argparse.ArgumentParser(
        description="Parallelberechnung von π via Leibniz-Reihe.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--with-gil", action="store_true", help="Verwende Threads mit Global Interpreter Lock (GIL)")
    group.add_argument("--with-thread", action="store_true", help="Verwende ThreadPoolExecutor für parallele Ausführung")
    group.add_argument("--with-proces", action="store_true", help="Verwende Multiprocessing mit separaten Prozessen")
    group.add_argument("--pool", type=int, help="Verwende einen Prozesspool mit angegebener Anzahl Prozesse")
    group.add_argument("--hosts", type=lambda s: s.split(","), help="Verwende externe Hosts via SSH (kommagetrennt)")
    group.add_argument("--producer-consumer", type=int, help="Nutze das Producer-Consumer-Modell mit angegebener Anzahl Consumer-Threads")

    parser.add_argument("-i", "--iterations", type=int, default=1_000_000, help="Gesamtzahl der Iterationen zur π-Annäherung")
    parser.add_argument("--seg-size", type=int, default=1_000_000, help="Anzahl Terme pro Segment")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in Sekunden für SSH-Verbindungen")

    args = parser.parse_args()

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
        parser.error("Kein Berechnungsmodus gewählt. Nutze --help für verfügbare Optionen.")

    pi_test = result * 4
    elapsed = time.perf_counter() - start_time
    err = abs(math.pi - pi_test)

    logging.info(f"π≈{pi_test:.12f}, Fehler={err:.3e}, Zeit={elapsed:.3f}s")


if __name__ == "__main__":
    main()
