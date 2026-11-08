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
        return (Status::Unknown, "Versi kernel tidak terbaca".into());
    }
    if cpu.bore_detected {
        return (
            Status::Pass,
            format!("Penanda BORE pada {}", cpu.kernel_release),
        );
    }
    (
        Status::Warn,
        format!("Penanda BORE tidak ditemukan pada {}", cpu.kernel_release),
    )
}

fn check_zram(collector: &Collector) -> Check {
    let swaps = match fs::read_to_string(collector.proc_path.join("swaps")) {
        Ok(swaps) => swaps,
        Err(error) => {
            return (
                Status::Unknown,
                format!("Gagal membaca /proc/swaps ({error})"),
            )
        }
    };
    let mut lines = swaps.lines();
    if lines.next().and_then(|line| line.split_whitespace().next()) != Some("Filename") {
        return (Status::Unknown, "Format /proc/swaps tidak dikenali".into());
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
            "Tidak ada perangkat ZRAM aktif sebagai swap".into(),
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
                format!("Gagal menjalankan systemctl ({error})"),
            )
        }
    };
    if !output.status.success() {
        return (
            Status::Unknown,
            format!("systemctl gagal ({})", output.status),
        );
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let units: Vec<_> = stdout
        .lines()
        .filter_map(|line| line.split_whitespace().next())
        .collect();
    if units.is_empty() {
        return (Status::Pass, "0 unit gagal".into());
    }
    (
        Status::Fail,
        format!("{} unit gagal ({})", units.len(), units.join(", ")),
    )
}

fn check_snapper() -> Check {
    match fs::metadata("/etc/snapper/configs/root") {
        Ok(metadata) if metadata.is_file() => {
            (Status::Pass, "Berkas konfigurasi root tersedia".into())
        }
        Ok(_) => (Status::Fail, "Path konfigurasi root bukan berkas".into()),
        Err(error) if error.kind() == ErrorKind::NotFound => (
            Status::Fail,
            "Berkas konfigurasi root tidak ditemukan".into(),
        ),
        Err(error) => (
            Status::Unknown,
            format!("Konfigurasi root tidak bisa diperiksa ({error})"),
        ),
    }
}

pub fn run() -> i32 {
    println!("ConstOS Doctor");
    let collector = Collector::default();
    let checks = [
        ("Kernel", check_kernel(&collector)),
        ("Swap ZRAM", check_zram(&collector)),
        ("Layanan systemd", check_systemd()),
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
