import argparse, math, sys, time, threading, subprocess
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Pool


def leibniz_term(k):
    return ((-1) ** k) / (2 * k + 1)


def compute_segment(start, count):
    s = 0.0
    for k in range(start, start + count):
        s += leibniz_term(k)
    return s


def mode_gil(segments):
    results = [0] * len(segments)

    def worker(i, seg):
        results[i] = compute_segment(*seg)

    threads = []
    for i, seg in enumerate(segments):
        t = threading.Thread(target=worker, args=(i, seg))
        threads.append(t);
        t.start()
    for t in threads: t.join()
    return sum(results)


def mode_threadpool(segments):
    with ThreadPoolExecutor() as ex:
        parts = list(ex.map(lambda sc: compute_segment(*sc), segments))
    return sum(parts)


def mode_process(segments):
    manager = {}
    procs = []
    lock = threading.Lock()

    def worker(seg):
        nonlocal manager
        res = compute_segment(*seg)
        with lock:
            manager.setdefault('sum', 0.0)
            manager['sum'] += res

    for seg in segments:
        p = Process(target=worker, args=(seg,))
        procs.append(p);
        p.start()
    for p in procs: p.join()
    return manager.get('sum', 0.0)


def mode_pool(segments, n):
    with Pool(processes=n) as p:
        parts = p.map(lambda sc: compute_segment(*sc), segments)
    return sum(parts)


def mode_hosts(segments, hosts):
    procs = []
    results = [0] * len(segments)

    def ssh_worker(i, seg, host):
        start, count = seg
        cmd = [
            "ssh", host,
            sys.executable, __file__,
            "--internal", "--start", str(start),
            "--count", str(count)
        ]
        out = subprocess.check_output(cmd, text=True)
        results[i] = float(out.strip())

    threads = []
    for i, seg in enumerate(segments):
        host = hosts[i % len(hosts)]
        t = threading.Thread(target=ssh_worker, args=(i, seg, host))
        threads.append(t);
        t.start()
    for t in threads: t.join()
    return sum(results)


def main():
    p = argparse.ArgumentParser(description="π via Leibniz-Reihe parallel")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--with-gil", action="store_true")
    group.add_argument("--with-thread", action="store_true")
    group.add_argument("--with-proces", action="store_true")
    group.add_argument("--pool", type=int)
    group.add_argument("--hosts", type=lambda s: s.split(","))
    p.add_argument("--seg-size", type=int, default=1_000_000)
    # internale Flags für Hosts
    p.add_argument("--internal", action="store_true")
    p.add_argument("--start", type=int)
    p.add_argument("--count", type=int)
    args = p.parse_args()

    # Internal mode: nur ein Segment berechnen und ausgeben
    if args.internal:
        res = compute_segment(args.start, args.count)
        print(res)
        sys.exit(0)

    # Segmente bilden
    total_terms = args.seg_size * (len(args.hosts) if args.hosts else (
        args.pool or threading.active_count() if args.pool else
        (1 if args.with_gil or args.with_thread or args.with_proces else 1)
    ))
    segments = [
        (i * args.seg_size, args.seg_size)
        for i in range(total_terms // args.seg_size)
    ]

    start_time = time.perf_counter()
    if args.with_gil:
        part = mode_gil(segments)
    elif args.with_thread:
        part = mode_threadpool(segments)
    elif args.with_proces:
        part = mode_process(segments)
    elif args.pool:
        part = mode_pool(segments, args.pool)
    elif args.hosts:
        part = mode_hosts(segments, args.hosts)
    else:
        p.error("Kein Modus gewählt.")
    pi_est = part * 4
    elapsed = time.perf_counter() - start_time
    err = abs(math.pi - pi_est)
    print(f"π≈{pi_est:.12f}, Fehler={err:.3e}, Zeit={elapsed:.3f}s")


if __name__ == "__main__":
    main()
