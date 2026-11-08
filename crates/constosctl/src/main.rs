use std::env;
use std::process::exit;
use const_collector::Collector;

mod doctor;
mod update;

fn print_usage() {
    println!("ConstOS System Inspection CLI");
    println!();
    println!("USAGE:");
    println!("    const <COMMAND> [OPTIONS]");
    println!();
    println!("COMMANDS:");
    println!("    status [--json]    Tampilkan snapshot metrik CPU, memori, ZRAM, dan proses");
    println!("    doctor             Jalankan preflight diagnostik kesehatan sistem ConstOS");
    println!("    update             Perbarui sistem dan aplikasi dari repositori pacman");
    println!("    version            Tampilkan versi CLI ConstOS");
    println!("    help               Tampilkan bantuan ini");
}

fn format_bytes(bytes: u64) -> String {
    if bytes >= 1024 * 1024 * 1024 {
        format!("{:.2} GiB", bytes as f64 / (1024.0 * 1024.0 * 1024.0))
    } else if bytes >= 1024 * 1024 {
        format!("{:.1} MiB", bytes as f64 / (1024.0 * 1024.0))
    } else if bytes >= 1024 {
        format!("{:.1} KiB", bytes as f64 / 1024.0)
    } else {
        format!("{} B", bytes)
    }
}

fn format_kb(kb: u64) -> String {
    format_bytes(kb * 1024)
}

fn run_status(json_mode: bool) {
    let collector = Collector::default();
    let snapshot = collector.snapshot();

    if json_mode {
        match serde_json::to_string_pretty(&snapshot) {
            Ok(json) => println!("{}", json),
            Err(e) => {
                eprintln!("Error serializing JSON: {}", e);
                exit(1);
            }
        }
        return;
    }

    println!("==================================================");
    println!(" Const Tsukuyomi - Status Sistem ");
    println!("==================================================");
    println!("Kernel        : {}", snapshot.cpu.kernel_release);
    println!("Scheduler     : {}", if snapshot.cpu.bore_detected { "BORE (Burst-Oriented Response Enhancer) [AKTIF]" } else { "Standar / Non-BORE" });
    println!("CPU Cores     : {}", snapshot.cpu.cpu_cores);
    println!("Load Average  : {:.2}, {:.2}, {:.2}", snapshot.cpu.load_avg.0, snapshot.cpu.load_avg.1, snapshot.cpu.load_avg.2);
    println!("--------------------------------------------------");
    println!("Memori Total  : {}", format_kb(snapshot.memory.mem_total_kb));
    println!("Memori Free   : {}", format_kb(snapshot.memory.mem_free_kb));
    println!("Memori Avail  : {}", format_kb(snapshot.memory.mem_available_kb));
    let used_kb = snapshot.memory.mem_total_kb.saturating_sub(snapshot.memory.mem_available_kb);
    let used_pct = if snapshot.memory.mem_total_kb > 0 {
        (used_kb as f64 / snapshot.memory.mem_total_kb as f64) * 100.0
    } else {
        0.0
    };
    println!("Memori Terpakai: {} ({:.1}%)", format_kb(used_kb), used_pct);
    println!("--------------------------------------------------");
    if let Some(zram) = &snapshot.memory.zram {
        println!("ZRAM Kompresi : zstd (zram0)");
        println!("  Ukuran Data : {}", format_bytes(zram.orig_data_size_bytes));
        println!("  Terkompresi : {}", format_bytes(zram.compr_data_size_bytes));
        println!("  Rasio       : {:.2}x", zram.compression_ratio);
        println!("  Penghematan : {}", format_bytes(zram.memory_savings_bytes));
    } else {
        println!("ZRAM Kompresi : Tidak aktif atau tidak terdeteksi");
    }
    println!("--------------------------------------------------");
    println!("Proses Total  : {}", snapshot.processes.total);
    println!("  Running (R) : {}", snapshot.processes.running);
    println!("  Sleeping (S): {}", snapshot.processes.sleeping);
    println!("  Disk (D)    : {}", snapshot.processes.disk_sleep);
    println!("  Zombie (Z)  : {}", snapshot.processes.zombie);
    println!("==================================================");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        run_status(false);
        return;
    }

    match args[1].as_str() {
        "status" => {
            let json_mode = args.iter().any(|a| a == "--json");
            run_status(json_mode);
        }
        "doctor" => exit(doctor::run()),
        "update" if args.len() == 2 => exit(update::run()),
        "update" => {
            eprintln!("Penggunaan: const update");
            exit(2);
        }
        "version" | "-v" | "--version" => {
            println!("const {} (Const Tsukuyomi Edition)", env!("CARGO_PKG_VERSION"));
        }
        "help" | "-h" | "--help" => print_usage(),
        unknown => {
            eprintln!("Perintah tidak dikenal: '{}'", unknown);
            print_usage();
            exit(2);
        }
    }
}
