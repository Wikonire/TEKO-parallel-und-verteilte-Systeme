from unittest.mock import patch, MagicMock
import pytest
import subprocess
import pi
import math
import sys
import os

# Basis-Tests

def test_leibniz_term():
    assert pi.leibniz_term(0) == 1.0
    assert pi.leibniz_term(1) == -1/3
    assert pi.leibniz_term(2) == 1/5

def test_compute_segment():
    assert pi.compute_segment(0, 1) == 1.0
    assert pi.compute_segment(1, 2) == sum([pi.leibniz_term(1), pi.leibniz_term(2)])
    assert abs(pi.compute_segment(0, 10) - sum(pi.leibniz_term(k) for k in range(10))) < 1e-10

@pytest.fixture
def short_segments():
    return [(0, 10), (10, 10), (20, 10)]

@pytest.fixture
def long_segments():
    return [(0, 100), (100, 100), (200, 100)]

# Modus-Tests

@pytest.mark.parametrize("mode", [pi.mode_gil, pi.mode_threadpool, pi.mode_process])
def test_modes_basic(mode, short_segments):
    result = mode(short_segments)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

def test_mode_pool(short_segments):
    result = pi.mode_pool(short_segments, n=2)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

# Worker-Funktion Tests

def test_worker():
    seg, idx = (0, 10), 1
    mock_dict = MagicMock()
    with patch('pi.compute_segment', return_value=42):
        pi.worker(seg, idx, mock_dict)
    mock_dict.__setitem__.assert_called_once_with(idx, 42)

def test_pool_worker():
    seg = (0, 10)
    assert pi.pool_worker(seg) == pi.compute_segment(*seg)

# Producer-Consumer-Tests

@pytest.mark.parametrize("num_consumers", [1, 2, 4])
def test_producer_consumer(long_segments, num_consumers):
    result = pi.producer_consumer(long_segments, num_consumers=num_consumers)
    expected = sum(pi.compute_segment(*seg) for seg in long_segments)
    assert abs(result - expected) < 1e-10

def test_producer_consumer_empty():
    assert pi.producer_consumer([], num_consumers=2) == 0.0

# Genauigkeits-Test

@pytest.mark.parametrize("mode", [pi.mode_gil, pi.mode_threadpool, pi.mode_process, pi.mode_pool])
@pytest.mark.parametrize("iterations, seg_size", [(1000, 100), (2000, 200)])
def test_accuracy_modes(mode, iterations, seg_size):
    segments = [(i * seg_size, min(seg_size, iterations - i * seg_size))
                for i in range((iterations + seg_size - 1) // seg_size)]
    result = mode(segments, n=4) if mode == pi.mode_pool else mode(segments)
    assert abs(math.pi - result * 4) < 0.01

# CLI Tests

@pytest.mark.parametrize("args", [
    ["pi.py", "--with-gil", "-i", "1000"],
    ["pi.py", "--with-thread", "-i", "2000"],
    ["pi.py", "--with-proces", "-i", "3000"],
    ["pi.py", "--pool", "4", "-i", "4000"],
    ["pi.py", "--producer-consumer", "2", "-i", "5000"],
    ["pi.py", "--hosts", "host1,host2", "-i", "6000"]
])
def test_main_valid_modes(args):
    with patch("sys.argv", args):
        pi.main()

@pytest.mark.parametrize("args", [
    ["pi.py", "-i", "1000"],
    ["pi.py", "--unknown-arg"],
    ["pi.py", "--with-gil", "--with-thread"],
    ["pi.py", "--internal"],
    ["pi.py"]
])
def test_main_invalid_args(args):
    with pytest.raises(SystemExit):
        with patch("sys.argv", args):
            pi.main()

def test_parser_error_no_mode_selected():
    args = ["pi.py"]

    with patch("argparse.ArgumentParser.error") as mock_error:
        mock_error.side_effect = SystemExit(2)  # argparse.error wirft standardmäßig SystemExit(2)

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", args):
                pi.main()

        mock_error.assert_called_once_with("Kein Modus gewählt.")
        assert exc_info.value.code == 2

def test_main_no_mode_explicit():
    args = ["pi.py"]
    with pytest.raises(SystemExit) as excinfo:
        with patch("sys.argv", args):
            pi.main()
    assert excinfo.value.code != 0

def test_internal_mode(capsys):
    args = ["pi.py", "--internal", "--start", "0", "--count", "10"]
    with patch("sys.argv", args):
        with pytest.raises(SystemExit) as exinfo:
            pi.main()
        assert exinfo.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == str(pi.compute_segment(0, 10))

# SSH-Tests

@pytest.fixture
def mock_hosts():
    return ["host1", "host2"]

@patch('subprocess.check_output')
def test_mode_hosts_basic(mock_ssh, short_segments, mock_hosts):
    mock_ssh.side_effect = lambda cmd, text, timeout: str(pi.compute_segment(int(cmd[-3]), int(cmd[-1])))
    result = pi.mode_hosts(short_segments, mock_hosts, timeout=60)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

@patch('subprocess.check_output', side_effect=subprocess.SubprocessError("SSH Error"))
def test_mode_hosts_ssh_failure(mock_ssh, short_segments, mock_hosts):
    assert pi.mode_hosts(short_segments, mock_hosts, timeout=60) == 0.0

@patch('subprocess.check_output', side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=60))
def test_mode_hosts_timeout(mock_ssh, short_segments, mock_hosts):
    assert pi.mode_hosts(short_segments, mock_hosts, timeout=60) == 0.0

@patch('pi.subprocess.check_output', side_effect=subprocess.SubprocessError("SSH Fehler simuliert"))
@patch('pi.logging.error')
def test_ssh_worker_error(mock_log_err, mock_subproc):
    results = {}
    pi.ssh_worker(0, (0, 10), 'host1', results)
    mock_log_err.assert_called_once_with("SSH-Fehler auf host1: SSH Fehler simuliert")


def test_main_invocation_subprocess():
    script_path = os.path.join(os.path.dirname(__file__), "pi.py")
    result = subprocess.run(
        [sys.executable, script_path, "--with-gil", "-i", "10"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Error: {result.stderr}"
    assert "π≈" in result.stdout