use std::fs;
use std::path::Path;
use const_collector::{Collector, CpuTimes, ZramStats};

fn setup_mock_proc_sys(base: &Path) {
    let proc_dir = base.join("proc");
    let sys_dir = base.join("sys");
    fs::create_dir_all(&proc_dir).unwrap();
    fs::create_dir_all(&sys_dir).unwrap();

    // 1. /proc/loadavg
    fs::write(
        proc_dir.join("loadavg"),
        "0.42 0.35 0.28 3/892 34567\n",
    ).unwrap();

    // 2. /proc/sys/kernel/osrelease
    let osrelease_dir = proc_dir.join("sys/kernel");
    fs::create_dir_all(&osrelease_dir).unwrap();
    fs::write(
        osrelease_dir.join("osrelease"),
        "7.3.1-1-cachyos-bore\n",
    ).unwrap();

    // 3. /proc/stat
    fs::write(
        proc_dir.join("stat"),
        "cpu  1000 200 300 4000 50 10 20 5 0 0\n\
         cpu0 500 100 150 2000 25 5 10 2 0 0\n\
         cpu1 500 100 150 2000 25 5 10 3 0 0\n\
         intr 1234567\n",
    ).unwrap();

    // 4. /proc/meminfo
    fs::write(
        proc_dir.join("meminfo"),
        "MemTotal:       16384000 kB\n\
         MemFree:         4096000 kB\n\
         MemAvailable:   10240000 kB\n\
         SwapTotal:       8192000 kB\n\
         SwapFree:        6144000 kB\n",
    ).unwrap();

    // 5. /sys/block/zram0/mm_stat
    let zram_dir = sys_dir.join("block/zram0");
    fs::create_dir_all(&zram_dir).unwrap();
    fs::write(
        zram_dir.join("mm_stat"),
        "4000000000 1000000000 1100000000 0 1200000000 45000 12000\n",
    ).unwrap();

    // 6. /proc/[pid]/stat
    let pids = [
        ("1", "(systemd) S 0 1 1 0 -1 4194560"),
        ("100", "(kthreadd) S 2 0 0 0 -1 2162944"),
        ("200", "(constd) R 1000 200 200 0 -1 4194304"),
        ("300", "(disk-io) D 1000 300 300 0 -1 4194304"),
        ("400", "(zombie-proc) Z 1000 400 400 0 -1 4194304"),
        ("500", "(stopped-proc) T 1000 500 500 0 -1 4194304"),
    ];

    for (pid, stat_line) in pids {
        let pid_dir = proc_dir.join(pid);
        fs::create_dir_all(&pid_dir).unwrap();
        fs::write(pid_dir.join("stat"), format!("{} {}\n", pid, stat_line)).unwrap();
    }
}

#[test]
fn test_collect_cpu_with_bore_kernel() {
    let tmp = tempfile::tempdir().unwrap();
    setup_mock_proc_sys(tmp.path());

    let collector = Collector::new(tmp.path().join("proc"), tmp.path().join("sys"));
    let cpu = collector.collect_cpu();

    assert_eq!(cpu.load_avg, (0.42, 0.35, 0.28));
    assert_eq!(cpu.running_processes, 3);
    assert_eq!(cpu.total_processes, 892);
    assert!(cpu.bore_detected, "BORE scheduler should be detected");
    assert_eq!(cpu.kernel_release, "7.3.1-1-cachyos-bore");
    assert_eq!(cpu.cpu_cores, 2);

    let times = cpu.cpu_times.expect("CpuTimes should be parsed");
    assert_eq!(
        times,
        CpuTimes {
            user: 1000,
            nice: 200,
            system: 300,
            idle: 4000,
            iowait: 50,
            irq: 10,
            softirq: 20,
            steal: 5,
        }
    );
}

#[test]
fn test_collect_cpu_generic_kernel_non_bore() {
    let tmp = tempfile::tempdir().unwrap();
    let proc_dir = tmp.path().join("proc");
    fs::create_dir_all(proc_dir.join("sys/kernel")).unwrap();
    fs::write(
        proc_dir.join("sys/kernel/osrelease"),
        "6.6.10-arch1-1-generic\n",
    ).unwrap();

    let collector = Collector::new(&proc_dir, tmp.path().join("sys"));
    let cpu = collector.collect_cpu();

    assert!(!cpu.bore_detected, "Generic kernel should not be detected as BORE");
    assert_eq!(cpu.kernel_release, "6.6.10-arch1-1-generic");
}

#[test]
fn test_collect_memory_and_zram_compression() {
    let tmp = tempfile::tempdir().unwrap();
    setup_mock_proc_sys(tmp.path());

    let collector = Collector::new(tmp.path().join("proc"), tmp.path().join("sys"));
    let mem = collector.collect_memory();

    assert_eq!(mem.mem_total_kb, 16384000);
    assert_eq!(mem.mem_free_kb, 4096000);
    assert_eq!(mem.mem_available_kb, 10240000);
    assert_eq!(mem.swap_total_kb, 8192000);
    assert_eq!(mem.swap_free_kb, 6144000);

    let zram = mem.zram.expect("ZRAM should be parsed from fixture");
    assert_eq!(
        zram,
        ZramStats {
            orig_data_size_bytes: 4000000000,
            compr_data_size_bytes: 1000000000,
            mem_used_total_bytes: 1100000000,
            compression_ratio: 4.0,
            memory_savings_bytes: 3000000000,
        }
    );
}

#[test]
fn test_collect_processes_summary() {
    let tmp = tempfile::tempdir().unwrap();
    setup_mock_proc_sys(tmp.path());

    let collector = Collector::new(tmp.path().join("proc"), tmp.path().join("sys"));
    let procs = collector.collect_processes();

    assert_eq!(procs.total, 6);
    assert_eq!(procs.running, 1);
    assert_eq!(procs.sleeping, 2);
    assert_eq!(procs.disk_sleep, 1);
    assert_eq!(procs.zombie, 1);
    assert_eq!(procs.stopped, 1);
}

#[test]
fn test_system_snapshot_json_roundtrip() {
    let tmp = tempfile::tempdir().unwrap();
    setup_mock_proc_sys(tmp.path());

    let collector = Collector::new(tmp.path().join("proc"), tmp.path().join("sys"));
    let snapshot = collector.snapshot();

    let json_str = serde_json::to_string(&snapshot).expect("Should serialize snapshot to JSON");
    assert!(json_str.contains("\"os_name\":\"Const Tsukuyomi\""));
    assert!(json_str.contains("\"bore_detected\":true"));

    let deserialized: const_collector::SystemSnapshot =
        serde_json::from_str(&json_str).expect("Should deserialize JSON back to SystemSnapshot");
    assert_eq!(snapshot, deserialized);
}
