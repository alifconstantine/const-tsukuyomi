use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CpuTimes {
    pub user: u64,
    pub nice: u64,
    pub system: u64,
    pub idle: u64,
    pub iowait: u64,
    pub irq: u64,
    pub softirq: u64,
    pub steal: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CpuStats {
    pub load_avg: (f64, f64, f64),
    pub running_processes: u32,
    pub total_processes: u32,
    pub bore_detected: bool,
    pub kernel_release: String,
    pub cpu_cores: usize,
    pub cpu_times: Option<CpuTimes>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ZramStats {
    pub orig_data_size_bytes: u64,
    pub compr_data_size_bytes: u64,
    pub mem_used_total_bytes: u64,
    pub compression_ratio: f64,
    pub memory_savings_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MemoryStats {
    pub mem_total_kb: u64,
    pub mem_free_kb: u64,
    pub mem_available_kb: u64,
    pub swap_total_kb: u64,
    pub swap_free_kb: u64,
    pub zram: Option<ZramStats>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct ProcessSummary {
    pub total: u32,
    pub running: u32,
    pub sleeping: u32,
    pub disk_sleep: u32,
    pub zombie: u32,
    pub stopped: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SystemSnapshot {
    pub timestamp_epoch: u64,
    pub os_name: String,
    pub cpu: CpuStats,
    pub memory: MemoryStats,
    pub processes: ProcessSummary,
}

#[derive(Debug, Clone)]
pub struct Collector {
    pub proc_path: PathBuf,
    pub sys_path: PathBuf,
}

impl Default for Collector {
    fn default() -> Self {
        Self {
            proc_path: PathBuf::from("/proc"),
            sys_path: PathBuf::from("/sys"),
        }
    }
}

impl Collector {
    pub fn new<P: AsRef<Path>, S: AsRef<Path>>(proc_path: P, sys_path: S) -> Self {
        Self {
            proc_path: proc_path.as_ref().to_path_buf(),
            sys_path: sys_path.as_ref().to_path_buf(),
        }
    }

    pub fn collect_cpu(&self) -> CpuStats {
        let mut load1 = 0.0;
        let mut load5 = 0.0;
        let mut load15 = 0.0;
        let mut running = 0;
        let mut total = 0;

        let loadavg_path = self.proc_path.join("loadavg");
        if let Ok(content) = fs::read_to_string(&loadavg_path) {
            let parts: Vec<&str> = content.split_whitespace().collect();
            if parts.len() >= 4 {
                load1 = parts[0].parse().unwrap_or(0.0);
                load5 = parts[1].parse().unwrap_or(0.0);
                load15 = parts[2].parse().unwrap_or(0.0);
                let proc_parts: Vec<&str> = parts[3].split('/').collect();
                if proc_parts.len() == 2 {
                    running = proc_parts[0].parse().unwrap_or(0);
                    total = proc_parts[1].parse().unwrap_or(0);
                }
            }
        }

        let mut kernel_release = String::new();
        let osrelease_path = self.proc_path.join("sys/kernel/osrelease");
        if let Ok(content) = fs::read_to_string(&osrelease_path) {
            kernel_release = content.trim().to_string();
        } else {
            let version_path = self.proc_path.join("version");
            if let Ok(content) = fs::read_to_string(&version_path) {
                if let Some(first_line) = content.lines().next() {
                    kernel_release = first_line.to_string();
                }
            }
        }

        let bore_detected = kernel_release.to_lowercase().contains("bore");

        let mut cpu_cores = 0;
        let mut cpu_times = None;
        let stat_path = self.proc_path.join("stat");
        if let Ok(content) = fs::read_to_string(&stat_path) {
            for line in content.lines() {
                if line.starts_with("cpu ") {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    if parts.len() >= 9 {
                        cpu_times = Some(CpuTimes {
                            user: parts[1].parse().unwrap_or(0),
                            nice: parts[2].parse().unwrap_or(0),
                            system: parts[3].parse().unwrap_or(0),
                            idle: parts[4].parse().unwrap_or(0),
                            iowait: parts[5].parse().unwrap_or(0),
                            irq: parts[6].parse().unwrap_or(0),
                            softirq: parts[7].parse().unwrap_or(0),
                            steal: parts[8].parse().unwrap_or(0),
                        });
                    }
                } else if line.starts_with("cpu") && line[3..].chars().next().map_or(false, |c| c.is_ascii_digit()) {
                    cpu_cores += 1;
                }
            }
        }

        if cpu_cores == 0 {
            cpu_cores = 1;
        }

        CpuStats {
            load_avg: (load1, load5, load15),
            running_processes: running,
            total_processes: total,
            bore_detected,
            kernel_release,
            cpu_cores,
            cpu_times,
        }
    }

    pub fn collect_memory(&self) -> MemoryStats {
        let mut mem_info = HashMap::new();
        let meminfo_path = self.proc_path.join("meminfo");
        if let Ok(content) = fs::read_to_string(&meminfo_path) {
            for line in content.lines() {
                if let Some((k, v)) = line.split_once(':') {
                    let num: u64 = v.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
                    mem_info.insert(k.trim().to_string(), num);
                }
            }
        }

        let mem_total_kb = *mem_info.get("MemTotal").unwrap_or(&0);
        let mem_free_kb = *mem_info.get("MemFree").unwrap_or(&0);
        let mem_available_kb = *mem_info.get("MemAvailable").unwrap_or(&mem_free_kb);
        let swap_total_kb = *mem_info.get("SwapTotal").unwrap_or(&0);
        let swap_free_kb = *mem_info.get("SwapFree").unwrap_or(&0);

        let mut zram = None;
        let mm_stat_path = self.sys_path.join("block/zram0/mm_stat");
        if let Ok(content) = fs::read_to_string(&mm_stat_path) {
            let parts: Vec<&str> = content.split_whitespace().collect();
            if parts.len() >= 3 {
                let orig: u64 = parts[0].parse().unwrap_or(0);
                let compr: u64 = parts[1].parse().unwrap_or(0);
                let mem_used: u64 = parts[2].parse().unwrap_or(0);

                let ratio = if compr > 0 {
                    (orig as f64) / (compr as f64)
                } else {
                    1.0
                };

                let savings = orig.saturating_sub(compr);

                zram = Some(ZramStats {
                    orig_data_size_bytes: orig,
                    compr_data_size_bytes: compr,
                    mem_used_total_bytes: mem_used,
                    compression_ratio: (ratio * 100.0).round() / 100.0,
                    memory_savings_bytes: savings,
                });
            }
        }

        MemoryStats {
            mem_total_kb,
            mem_free_kb,
            mem_available_kb,
            swap_total_kb,
            swap_free_kb,
            zram,
        }
    }

    pub fn collect_processes(&self) -> ProcessSummary {
        let mut summary = ProcessSummary::default();

        if let Ok(entries) = fs::read_dir(&self.proc_path) {
            for entry in entries.flatten() {
                let name = entry.file_name();
                let name_str = name.to_string_lossy();
                if name_str.chars().all(|c| c.is_ascii_digit()) {
                    summary.total += 1;
                    let stat_file = entry.path().join("stat");
                    if let Ok(content) = fs::read_to_string(&stat_file) {
                        // The state character is immediately after the last ')' character
                        if let Some(idx) = content.rfind(')') {
                            let remainder = &content[idx + 1..];
                            if let Some(state_char) = remainder.split_whitespace().next().and_then(|s| s.chars().next()) {
                                match state_char {
                                    'R' => summary.running += 1,
                                    'S' => summary.sleeping += 1,
                                    'D' => summary.disk_sleep += 1,
                                    'Z' => summary.zombie += 1,
                                    'T' => summary.stopped += 1,
                                    _ => (),
                                }
                            }
                        }
                    }
                }
            }
        }

        summary
    }

    pub fn snapshot(&self) -> SystemSnapshot {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        SystemSnapshot {
            timestamp_epoch: now,
            os_name: "Const Tsukuyomi".to_string(),
            cpu: self.collect_cpu(),
            memory: self.collect_memory(),
            processes: self.collect_processes(),
        }
    }
}
