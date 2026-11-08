use std::fs;
use std::io::ErrorKind;
use std::process::Command;

use const_collector::Collector;

#[derive(Debug)]
enum Status {
    Pass,
    Warn,
    Fail,
    Unknown,
}

type Check = (Status, String);

fn check_kernel(collector: &Collector) -> Check {
    let cpu = collector.collect_cpu();
    if cpu.kernel_release.is_empty() {
        return (Status::Unknown, "Could not read the kernel version".into());
    }
    if cpu.bore_detected {
        return (
            Status::Pass,
            format!("BORE marker found in {}", cpu.kernel_release),
        );
    }
    (
        Status::Warn,
        format!("BORE marker not found in {}", cpu.kernel_release),
    )
}

fn check_zram(collector: &Collector) -> Check {
    let swaps = match fs::read_to_string(collector.proc_path.join("swaps")) {
        Ok(swaps) => swaps,
        Err(error) => {
            return (
                Status::Unknown,
                format!("Could not read /proc/swaps ({error})"),
            )
        }
    };
    let mut lines = swaps.lines();
    if lines.next().and_then(|line| line.split_whitespace().next()) != Some("Filename") {
        return (Status::Unknown, "Unrecognized /proc/swaps format".into());
    }
    let devices: Vec<_> = lines
        .filter_map(|line| line.split_whitespace().next())
        .filter(|path| {
            path.strip_prefix("/dev/zram").is_some_and(|index| {
                !index.is_empty() && index.bytes().all(|byte| byte.is_ascii_digit())
            })
        })
        .collect();
    if devices.is_empty() {
        return (
            Status::Fail,
            "No ZRAM device is active as swap".into(),
        );
    }
    (Status::Pass, devices.join(", "))
}

fn check_systemd() -> Check {
    let output = match Command::new("systemctl")
        .args([
            "--system",
            "list-units",
            "--failed",
            "--plain",
            "--full",
            "--no-legend",
            "--no-pager",
        ])
        .output()
    {
        Ok(output) => output,
        Err(error) => {
            return (
                Status::Unknown,
                format!("Could not run systemctl ({error})"),
            )
        }
    };
    if !output.status.success() {
        return (
            Status::Unknown,
            format!("systemctl failed ({})", output.status),
        );
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let units: Vec<_> = stdout
        .lines()
        .filter_map(|line| line.split_whitespace().next())
        .collect();
    if units.is_empty() {
        return (Status::Pass, "No failed units".into());
    }
    (
        Status::Fail,
        format!("Failed units: {} ({})", units.len(), units.join(", ")),
    )
}

fn check_snapper() -> Check {
    match fs::metadata("/etc/snapper/configs/root") {
        Ok(metadata) if metadata.is_file() => {
            (Status::Pass, "Root configuration file is present".into())
        }
        Ok(_) => (Status::Fail, "Root configuration path is not a file".into()),
        Err(error) if error.kind() == ErrorKind::NotFound => (
            Status::Fail,
            "Root configuration file not found".into(),
        ),
        Err(error) => (
            Status::Unknown,
            format!("Could not inspect the root configuration ({error})"),
        ),
    }
}

pub fn run() -> i32 {
    println!("ConstOS Doctor");
    let collector = Collector::default();
    let checks = [
        ("Kernel", check_kernel(&collector)),
        ("ZRAM swap", check_zram(&collector)),
        ("systemd services", check_systemd()),
        ("Snapper", check_snapper()),
    ];
    let mut exit_code = 0;
    for (name, (status, detail)) in checks {
        let label = match status {
            Status::Pass => "PASS",
            Status::Warn => "WARN",
            Status::Fail => "FAIL",
            Status::Unknown => "UNKNOWN",
        };
        if matches!(status, Status::Fail | Status::Unknown) {
            exit_code = 1;
        }
        println!("[{label}] {name} · {detail}");
    }
    exit_code
}
