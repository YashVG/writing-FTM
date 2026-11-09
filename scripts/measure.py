"""Run a bounded child process and record process/system memory, time and output."""
import argparse, json, subprocess, time
from pathlib import Path
import psutil
p = argparse.ArgumentParser()
p.add_argument('name'); p.add_argument('--timeout', type=int, default=1200)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args(); command = a.command
if command and command[0] == '--': command = command[1:]
out = Path('runs/pilot'); out.mkdir(parents=True, exist_ok=True)
start = time.monotonic(); swap0 = psutil.swap_memory().used
peak_rss = 0; min_available = psutil.virtual_memory().available; max_swap = swap0
reason = None; low_count = 0
with (out / f'{a.name}.log').open('w') as log:
    child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    proc = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak_rss = max(peak_rss, proc.memory_info().rss)
        except psutil.NoSuchProcess:
            pass
        available = psutil.virtual_memory().available
        min_available = min(min_available, available)
        max_swap = max(max_swap, psutil.swap_memory().used)
        low_count = low_count + 1 if available < 1.5 * 1024**3 else 0
        if time.monotonic() - start > a.timeout or low_count >= 5 or max_swap - swap0 > 2 * 1024**3:
            reason = 'timeout' if time.monotonic() - start > a.timeout else 'memory guard'
            child.terminate()
            try: child.wait(timeout=10)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
            break
        time.sleep(1)
result = {'name': a.name, 'command': command, 'exit_code': child.returncode,
    'wall_seconds': time.monotonic()-start, 'peak_process_rss_gib': peak_rss / 1024**3,
    'min_system_available_gib': min_available / 1024**3,
    'system_swap_growth_gib': (max_swap-swap0) / 1024**3, 'stop_reason': reason}
(out / f'{a.name}.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2), flush=True)
raise SystemExit(child.returncode or (1 if reason else 0))
