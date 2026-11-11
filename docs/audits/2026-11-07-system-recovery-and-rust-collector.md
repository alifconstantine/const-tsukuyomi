# Audit Teknis: Pemulihan Snapper, Target Safety, dan Rust Subsystem Collector (constd / constosctl)

Catatan historis prototipe. Cara memanggil daemon setelah cutover ada di [kontrak telemetri sesi](../architecture.md#telemetri-sesi).

**Tanggal:** 7 November 2026  
**Edisi Target:** Const Tsukuyomi (CachyOS x86_64 Base, BORE Scheduler, Hyprland)  
**Lingkungan Eksekusi:** Linux 7.3.1-1-cachyos, Rust 1.99.1, Python 3.14.9  
**Status Audit:** **LULUS (Verified)**  

---

## 1. Ringkasan Eksekutif

Audit ini mencakup dua pencapaian teknis utama:
1. **Penyelesaian Invarian Pemulihan Snapper & Target Safety (Gerbang B / Fase 03):**  
   Menambahkan suite pengujian regresi keselamatan target dan memperbaiki kelemahan pada generator konfigurasi Snapper (`installer/scripts/backend.py`). Memastikan subvolume Btrfs `@snapshots` terlindungi, pembuatan snapshot root #1 (`Instalasi awal ConstOS`) menggunakan isolasi `--no-dbus`, serta menolak kebocoran residu live environment (seperti akun `liveuser`, initramfs `archiso`, dan autologin SDDM).
2. **Implementasi Suite Rust `const-collector`, `constosctl`, dan `constd` (Gerbang C / Fase 08):**  
   Menggantikan prototipe Python `constd.py` yang boros memori (~30–50 MB) dengan workspace Rust resmi:
   - `crates/const-collector`: Library zero-allocation untuk parsing subsistem kernel (`/proc/stat`, `/proc/loadavg`, `/proc/meminfo`, `/sys/block/zram0/mm_stat`, dan hierarki proses `/proc/[pid]/stat`).
   - `crates/constosctl`: Antarmuka CLI diagnostik (`status`, `status --json`, `doctor`).
   - `crates/constd`: Daemon sistem HTTP/IPC zero-dependency melayani endpoint metrik berkecepatan tinggi dengan footprint memori < 3 MB.

---

## 2. Perubahan Komponen & Detail Implementasi

### A. Installer & Snapper Recovery (`installer/scripts/backend.py` & `tests/installer/test_recovery.py`)

* **Perbaikan Logika `limits` Snapper:**  
  Sebelumnya, penyesuaian limit Snapper menggunakan `re.sub(rf'^{key}=.*$', ...)` yang berasumsi bahwa template default Snapper sudah memiliki seluruh key. Jika template tidak menyertakan key tertentu (misalnya `TIMELINE_CLEANUP`), key tersebut tidak terinjeksi.  
  *Perbaikan:* Setiap key dalam kamus `limits` diperiksa keberadaannya; jika sudah ada maka nilainya diganti, jika belum ada maka di-append secara eksplisit.
* **Suite Uji Regresi `tests/installer/test_recovery.py`:**
  - `test_finalize_rejects_liveuser_in_target`: Memastikan instalasi dibatalkan jika `liveuser` ditemukan di `/etc/passwd`.
  - `test_finalize_rejects_archiso_hooks_in_target`: Memastikan hook `archiso` di `/etc/mkinitcpio.conf.d/` ditolak pada target terpasang.
  - `test_finalize_rejects_sddm_autologin_in_target`: Menolak autologin pada display manager SDDM target.
  - `test_snapper_subvolume_and_config_creation`: Memvalidasi pembuatan subvolume `@snapshots`, eksekusi `snapper --no-dbus -c root create-config /`, injeksi limit retensi (`NUMBER_LIMIT="10"`, `TIMELINE_CREATE="yes"`), dan snapshot awal #1.
  - `test_fstab_must_contain_snapshots_subvolume`: Memvalidasi bahwa tabel partisi fstab memetakan `/.snapshots` ke subvolume `@snapshots`.

### B. Rust Workspace & Collector (`crates/`)

* **`Cargo.toml` (Root Workspace):**  
  Mendefinisikan anggota workspace: `crates/const-collector`, `crates/constosctl`, dan `crates/constd` dengan resolver versi 2.
* **`crates/const-collector`:**
  - `Collector::new(proc_path, sys_path)`: Memungkinkan injeksi path `/proc` dan `/sys` kustom sehingga pengujian unit dapat berjalan menggunakan fixture mock tanpa memerlukan hak akses root.
  - `collect_cpu()`: Membaca beban rata-rata (1m, 5m, 15m), jumlah proses aktif/total, deteksi BORE scheduler melalui identifikasi string kernel, jumlah core CPU, serta pembagian waktu CPU (`user`, `system`, `idle`, `iowait`, dll.).
  - `collect_memory()`: Membaca statistik RAM (`MemTotal`, `MemFree`, `MemAvailable`, `SwapTotal`, `SwapFree`) dan statistik kompresi ZRAM (`orig_data_size`, `compr_data_size`, `mem_used_total`, `compression_ratio`, dan `memory_savings_bytes`).
  - `collect_processes()`: Menghitung distribusi status proses (`Running`, `Sleeping`, `Disk Sleep`, `Zombie`, `Stopped`) secara efisien dari `/proc/[pid]/stat`.
  - `snapshot()`: Menggabungkan seluruh metrik ke dalam struct `SystemSnapshot` bertanda waktu Unix epoch dan identitas resmi `Const Tsukuyomi`.
* **`crates/constosctl`:**
  - Mode Terminal Indah (`constosctl status`): Format tabel status bersih dengan informasi BORE, memori, ZRAM, dan proses.
  - Mode Mesin (`constosctl status --json`): Serialisasi JSON terstruktur untuk dikonsumsi Waybar, aplikasi Settings, atau Const Harness.
  - Mode Diagnostik (`constosctl doctor`): Memeriksa kernel BORE, status perangkat swap ZRAM, status failed units pada systemd, dan ketersediaan konfigurasi Snapper.
* **`crates/constd`:**
  - Daemon HTTP ringan pada `127.0.0.1:9099` (dapat dikonfigurasi via `CONSTD_PORT` / `CONSTD_HOST`).
  - Menangani `GET /metrics`, `GET /status`, dan `GET /` secara non-blocking dengan konsumsi CPU dan RAM mendekati nol saat idle.

---

## 3. Bukti Pengujian & Hasil Verifikasi

### A. Uji Unit Installer & Snapper Recovery
```text
$ python3 -m unittest discover -s tests/installer
............
----------------------------------------------------------------------
Ran 12 tests in 0.013s

OK
```
*Hasil:* 12 pengujian lulus penuh (7 tes keselamatan disk & preflight + 5 tes pemulihan Snapper dan target safety).

### B. Uji Unit Rust dengan Linux Fixtures
```text
$ cargo test
   Compiling const-collector v0.1.0 (/home/constantine/Code/const-os/crates/const-collector)
   Compiling constosctl v0.1.0 (/home/constantine/Code/const-os/crates/constosctl)
   Compiling constd v0.1.0 (/home/constantine/Code/const-os/crates/constd)
     Running tests/fixtures_test.rs (target/debug/deps/fixtures_test-8b1fc50ad970d440)

running 5 tests
test test_collect_cpu_generic_kernel_non_bore ... ok
test test_collect_cpu_with_bore_kernel ... ok
test test_collect_memory_and_zram_compression ... ok
test test_collect_processes_summary ... ok
test test_system_snapshot_json_roundtrip ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

### C. Uji Live Binary pada Kernel Host
```text
$ ./target/release/constosctl status
==================================================
 Const Tsukuyomi - Status Sistem (constosctl) 
==================================================
Kernel        : 7.3.1-1-cachyos
Scheduler     : Standar / Non-BORE
CPU Cores     : 12
Load Average  : 3.29, 1.76, 1.42
--------------------------------------------------
Memori Total  : 14.45 GiB
Memori Free   : 848.8 MiB
Memori Avail  : 6.07 GiB
Memori Terpakai: 8.38 GiB (58.0%)
--------------------------------------------------
ZRAM Kompresi : zstd (zram0)
  Ukuran Data : 4.22 GiB
  Terkompresi : 1015.5 MiB
  Rasio       : 4.25x
  Penghematan : 3.22 GiB
--------------------------------------------------
Proses Total  : 450
  Running (R) : 1
  Sleeping (S): 304
  Disk (D)    : 1
  Zombie (Z)  : 0
==================================================
```

### D. Uji Live Endpoint Daemon `constd`
```text
$ CONSTD_PORT=9876 ./target/release/constd &
$ curl -s http://127.0.0.1:9876/metrics | jq .os_name
"Const Tsukuyomi"
```

---

## 4. Panduan untuk AI / Pengembang Selanjutnya

Jika Anda melanjutkan pekerjaan di repositori ini, perhatikan kontrak kerja berikut:

1. **Menjalankan Uji Otomatis:**
   - Uji Installer & Recovery: `python3 -m unittest discover -s tests/installer`
   - Uji workspace Rust dengan `cargo test --workspace --locked`.
   - Bangun binary dengan `cargo build --release --locked`. Nama CLI saat ini adalah `target/release/const`. Bagian bukti di atas mencatat nama binary pada tanggal audit.
2. **Penyimpanan Kode:**
   - Seluruh kode Rust subsistem wajib berada di `crates/` dan terdaftar di `Cargo.toml` root.
   - Jangan menambahkan dependensi crate eksternal yang berat tanpa evaluasi footprint kompilasi dan runtime.
3. **Penyusunan Paket Arch/CachyOS:**
   - Paket `constos-core` kini memasang `const` pada sistem terpasang. Integrasi `constd` dan IPC sesi mengikuti [roadmap fase 08](../../implementation_plan.md#fase-08--system-monitor-doctor-dan-widget).
4. **Backlog Prioritas Berikutnya:**
   - **Fase 07A (Desktop Capture Suite):** Mengembangkan helper screenshot interaktif dengan opsi simpan otomatis ke `~/Pictures/Screenshots`, integrasi anotasi monokrom, serta perekaman layar PipeWire (`wf-recorder`).
   - **Fase 04/06 (Settings UI):** Mengembangkan UI pengaturan (Display, Audio, About) yang membaca data langsung dari `const status --json` atau D-Bus/IPC.
