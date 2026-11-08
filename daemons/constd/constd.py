#!/usr/bin/env python3
"""
ConstOS - Kernel & Hardware Subsystem Monitor Daemon (constd)
OS-MCP Bridge for Const Harness Workbench

Membaca subsistem kernel (/proc dan /sys) untuk menyediakan status CPU scheduling (BORE),
Virtual Memory & ZRAM, serta hierarki proses ke Const Harness tanpa hak akses root penuh.
"""

import os
import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 9099

def get_cpu_scheduler_stats():
    """Membaca beban CPU dan scheduler dari /proc/loadavg dan /proc/stat"""
    load_avg = [0.0, 0.0, 0.0]
    running_processes = 0
    total_processes = 0

    if os.path.exists("/proc/loadavg"):
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
            if len(parts) >= 5:
                load_avg = [float(parts[0]), float(parts[1]), float(parts[2])]
                proc_parts = parts[3].split('/')
                if len(proc_parts) == 2:
                    running_processes = int(proc_parts[0])
                    total_processes = int(proc_parts[1])

    return {
        "scheduler": "BORE (Burst-Oriented Response Enhancer)",
        "load_1m": load_avg[0],
        "load_5m": load_avg[1],
        "load_15m": load_avg[2],
        "running_threads": running_processes,
        "total_threads": total_processes
    }

def get_memory_and_zram_stats():
    """Membaca penggunaan RAM dan alokasi kompresi ZRAM dari /proc/meminfo dan /sys/block/zram0"""
    mem_info = {}
    if os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    if val.isdigit():
                        mem_info[key] = int(val)

    mem_total_kb = mem_info.get("MemTotal", 0)
    mem_free_kb = mem_info.get("MemFree", 0)
    mem_available_kb = mem_info.get("MemAvailable", 0)
    swap_total_kb = mem_info.get("SwapTotal", 0)
    swap_free_kb = mem_info.get("SwapFree", 0)

    zram_stats = {
        "enabled": False,
        "orig_data_size_bytes": 0,
        "compr_data_size_bytes": 0,
        "compression_ratio": 1.0
    }

    zram_mm_stat = "/sys/block/zram0/mm_stat"
    if os.path.exists(zram_mm_stat):
        try:
            with open(zram_mm_stat, "r") as f:
                stats = f.read().split()
                if len(stats) >= 2:
                    orig_size = int(stats[0])
                    compr_size = int(stats[1])
                    ratio = (orig_size / compr_size) if compr_size > 0 else 1.0
                    zram_stats = {
                        "enabled": True,
                        "algorithm": "zstd",
                        "orig_data_size_bytes": orig_size,
                        "compr_data_size_bytes": compr_size,
                        "compression_ratio": round(ratio, 2)
                    }
        except Exception:
            pass

    return {
        "total_kb": mem_total_kb,
        "available_kb": mem_available_kb,
        "used_kb": max(0, mem_total_kb - mem_available_kb),
        "swap_total_kb": swap_total_kb,
        "swap_used_kb": max(0, swap_total_kb - swap_free_kb),
        "zram": zram_stats
    }

def get_process_states_summary():
    """Membaca status proses sistem (R: Running, S: Sleeping, Z: Zombie)"""
    state_counts = {"R": 0, "S": 0, "Z": 0, "D": 0, "Other": 0}
    top_processes = []

    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
        for pid in pids[:100]:
            status_path = f"/proc/{pid}/status"
            if os.path.exists(status_path):
                try:
                    name = ""
                    state = ""
                    vm_rss = 0
                    with open(status_path, "r") as f:
                        for line in f:
                            if line.startswith("Name:"):
                                name = line.split(":", 1)[1].strip()
                            elif line.startswith("State:"):
                                state = line.split(":", 1)[1].strip().split()[0]
                            elif line.startswith("VmRSS:"):
                                rss_val = line.split(":", 1)[1].strip().split()[0]
                                if rss_val.isdigit():
                                    vm_rss = int(rss_val)

                    code = state[0] if state else "Other"
                    if code in state_counts:
                        state_counts[code] += 1
                    else:
                        state_counts["Other"] += 1

                    if vm_rss > 50000:
                        top_processes.append({"pid": int(pid), "name": name, "rss_kb": vm_rss, "state": state})
                except (IOError, PermissionError):
                    continue
    except Exception:
        pass

    top_processes.sort(key=lambda x: x["rss_kb"], reverse=True)

    return {
        "state_counts": state_counts,
        "high_memory_processes": top_processes[:10]
    }

class ConstDHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/metrics":
            data = {
                "timestamp": time.time(),
                "distro": "ConstOS (Harness Edition)",
                "cpu_scheduler": get_cpu_scheduler_stats(),
                "memory_zram": get_memory_and_zram_stats(),
                "process_summary": get_process_states_summary()
            }
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "constd"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silent logger to prevent journal spam
        pass

def run():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, ConstDHandler)
    print(f"[constd] ConstOS System Monitor Daemon running on http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[constd] Shutting down.")
        httpd.server_close()

if __name__ == "__main__":
    run()
