from unittest.mock import patch
import pytest
import subprocess
import pi
import math

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

def test_mode_gil(short_segments):
    result = pi.mode_gil(short_segments)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

def test_mode_threadpool(short_segments):
    result = pi.mode_threadpool(short_segments)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

def test_mode_process(short_segments):
    result = pi.mode_process(short_segments)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

def test_mode_pool(short_segments):
    result = pi.mode_pool(short_segments, n=2)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

# Producer-Consumer-Tests

def test_producer_consumer_basic(short_segments):
    result = pi.producer_consumer(short_segments, num_consumers=2)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

@pytest.mark.parametrize("num_consumers", [1, 2, 4])
def test_producer_consumer_variable_consumers(long_segments, num_consumers):
    result = pi.producer_consumer(long_segments, num_consumers=num_consumers)
    expected = sum(pi.compute_segment(*seg) for seg in long_segments)
    assert abs(result - expected) < 1e-10

def test_producer_consumer_empty_segments():
    assert pi.producer_consumer([], num_consumers=2) == 0.0


@pytest.mark.parametrize("mode", [pi.mode_gil, pi.mode_threadpool, pi.mode_process, pi.mode_pool])
@pytest.mark.parametrize("iterations, seg_size", [(1000, 100), (2000, 200)])
def test_pi_accuracy_modes(mode, iterations, seg_size):
    segments = [(i * seg_size, min(seg_size, iterations - i * seg_size))
                for i in range((iterations + seg_size - 1) // seg_size)]
    if mode == pi.mode_pool:
        result = mode(segments, n=4)
    else:
        result = mode(segments)
    pi_est = result * 4
    assert abs(math.pi - pi_est) < 0.01

# Main-Funktion-Tests (CLI-Parameter)

@pytest.mark.parametrize("args", [
    ["pi.py", "--with-gil", "-i", "1000", "--seg-size", "100"],
    ["pi.py", "--with-thread", "-i", "2000", "--seg-size", "200"],
    ["pi.py", "--with-proces", "-i", "3000", "--seg-size", "300"],
    ["pi.py", "--pool", "4", "-i", "4000", "--seg-size", "400"],
    ["pi.py", "--producer-consumer", "2", "-i", "5000", "--seg-size", "500"]
])
def test_main_valid_modes(args):
    with patch("sys.argv", args):
        pi.main()

@pytest.mark.parametrize("args", [
    ["pi.py", "-i", "1000"],
    ["pi.py", "--unknown-arg"],
    ["pi.py", "--with-gil", "--with-thread"]
])
def test_main_invalid_args(args):
    with pytest.raises(SystemExit):
        with patch("sys.argv", args):
            pi.main()

def test_internal_mode(capsys):
    args = ["pi.py", "--internal", "--start", "0", "--count", "10"]
    with patch("sys.argv", args):
        with pytest.raises(SystemExit) as excinfo:
            pi.main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    expected_output = str(pi.compute_segment(0, 10))
    assert captured.out.strip() == expected_output


def test_no_mode_provided():
    args = ["pi.py"]
    with pytest.raises(SystemExit):
        with patch("sys.argv", args):
            pi.main()

@pytest.fixture
def mock_hosts():
    return ["host1", "host2"]

def mock_subprocess_check_output(cmd, text, timeout):
    start = int(cmd[-3])
    count = int(cmd[-1])
    return str(pi.compute_segment(start, count))

@patch('subprocess.check_output', side_effect=mock_subprocess_check_output)
def test_mode_hosts_basic(mock_ssh, short_segments, mock_hosts):
    result = pi.mode_hosts(short_segments, mock_hosts, timeout=60)
    expected = sum(pi.compute_segment(*seg) for seg in short_segments)
    assert abs(result - expected) < 1e-10

@patch('subprocess.check_output', side_effect=subprocess.SubprocessError("SSH Error"))
def test_mode_hosts_ssh_failure(mock_ssh, short_segments, mock_hosts):
    assert pi.mode_hosts(short_segments, mock_hosts, timeout=60) == 0.0

@patch('subprocess.check_output', side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=60))
def test_mode_hosts_timeout(mock_ssh, short_segments, mock_hosts):
    assert pi.mode_hosts(short_segments, mock_hosts, timeout=60) == 0.0
