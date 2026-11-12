<div align="center">

# Const Tsukuyomi

**Distribusi Linux bertema gelap berbasis CachyOS dengan Hyprland**

[![Arch Linux](https://img.shields.io/badge/Base-CachyOS%20%28Arch%29-1793d1)](#)
[![Compositor](https://img.shields.io/badge/Compositor-Hyprland%20Wayland-00a8ff)](#)
[![Scheduler](https://img.shields.io/badge/Kernel-BORE%20Scheduler-ff4757)](#)
[![License](https://img.shields.io/badge/License-GPLv3-green)](#)

</div>

---

## Tentang ConstOS

ConstOS adalah distribusi Linux berbasis CachyOS untuk pengembangan perangkat lunak dan penggunaan desktop sehari-hari. ISO menargetkan x86_64 UEFI dengan kernel CachyOS BORE. Sesi installer membuka TUI Ryoku yang diadaptasi untuk ConstOS melalui Cage dan Foot. Sesi terpasang memakai Hyprland dengan Tsukuyomi Shell (fork kustom Dux Shell) berpreset Const. Const Harness adalah integrasi yang direncanakan untuk edisi berikutnya.

---

## Arsitektur dan status pengembangan

Arsitektur komponen, batas izin, dan pemisahan profil live dari sistem terpasang dijelaskan di [docs/architecture.md](docs/architecture.md). Status berikut membedakan konfigurasi yang tersedia dari integrasi yang masih perlu dibuktikan.

| Komponen | Status |
| :--- | :--- |
| Kernel | Manifest live memilih kernel CachyOS BORE. |
| Boot dan login | ISO membuka **Install Tsukuyomi** atau **Tsukuyomi Diagnostics** dari GRUB. Sesudah status boot Plymouth, sesi installer menampilkan judul piksel **TSUKUYOMI** dan **Preparing installer** sebelum Welcome. Pada sistem terpasang, boot langsung mengautentikasi akun ke sesi desktop Hyprland (tanpa layar login greeter), dengan penguncian layar dikelola langsung oleh Tsukuyomi Shell. |
| Memori dan ZRAM | Overlay live mengatur `zram-generator` dengan `zstd`, `vm.swappiness = 100`, dan `vm.vfs_cache_pressure = 50`. |
| Storage dan installer | TUI menampilkan disk kosong minimal 32 GiB. Konfirmasi di **Review** memulai pemeriksaan ulang disk dan unduhan paket bertanda tangan. Wizard menampilkan tahapan backend dan menawarkan **Reboot now** sesudah unmount. Rincian build dan batas uji ada di [roadmap](implementation_plan.md). |
| Diagnosis dan telemetri | Paket `constos-core` memasang CLI Rust `const` pada sistem terpasang. Jalankan `const doctor` tanpa `sudo` untuk memeriksa kernel, swap ZRAM, unit systemd yang gagal, ruang tersedia di `/`, serta konfigurasi Snapper dan mount `/.snapshots`. `const status --json` menyajikan snapshot metrik. Profil live dan paket core menyiapkan daemon Rust `constd` yang aktif saat diminta lewat D-Bus sesi. Integrasi Monitor, widget, dan Harness mengikuti roadmap. [Kontrak telemetri](docs/architecture.md#telemetri-sesi) |
| Pembaruan | Jalankan `const update` dari terminal pada sistem terpasang. Jika pembaruan tersedia, pacman menampilkan paket OS dan aplikasi dari repo yang dikonfigurasi untuk dikonfirmasi dalam satu transaksi. Lihat [panduan update dan recovery](docs/acceptance-guide.md#update-dan-recovery) untuk cakupan dan verifikasi. |
| Sandbox dan izin | Ada wrapper Bubblewrap yang menolak eksekusi saat `bwrap` tidak tersedia. Kebijakan akses dan integrasi agen masih perlu diuji. |
| Screenshot dan rekaman | Super+Shift+S membuka toolbar screenshot dan rekam audio. Print menyalin area dan Alt+Print menyalin layar. Toolbar menyediakan pratinjau, Save PNG, anotasi Satty, serta rekaman WAV dari mikrofon atau audio sistem. [Pemakaian dan rencana capture](docs/capture-plan.md) |
| Shell dan aplikasi harian | Tsukuyomi Shell (`tsukuyomi-shell-git`) menyediakan panel, launcher, Quick Settings, notifikasi, dan lock melalui runner `dms` dengan Quickshell upstream. Terminal Kitty membuka Fish dengan simbol Const ASCII pada Fastfetch. `yay`, Git, dan base-devel disertakan untuk penggunaan AUR sebagai pengguna biasa. Aplikasi inti mencakup Nautilus, mpv, Mousepad, Ristretto, Evince, dan File Roller. |
| Jaringan dan browser | Wizard menampilkan status NetworkManager dan dapat membuka pengaturan koneksi. Browser menawarkan Firefox sebagai rekomendasi, Chromium, Zen, dan No browser. Paket pilihan masuk transaksi unduhan sebelum perubahan disk. [Kontrak browser](docs/installer-plan.md#pilihan-browser) |
| Pengembangan shell | Integrasi khusus Const Hub, adapter palet Harness, dan draft widget mengikuti roadmap. |
| Welcome dan aplikasi opsional | Target membuka panduan shortcut QML pada login pertama, dengan kartu tindakan yang berasal dari Ryoku dan tanpa gambar. Welcome dan Recommended Apps bisa dibuka dari launcher. Katalog menawarkan LibreOffice, VLC, LocalSend, dan KeePassXC dari Flathub. Const Store direncanakan memakai katalog yang sama. |
| Aplikasi Windows dan Android | Direncanakan untuk sistem terpasang. Wine disiapkan oleh installer agar pengguna bisa memasang dan membuka aplikasi Windows dari desktop tanpa setup runtime manual. Waydroid menyusul sebagai pilihan untuk APK yang kompatibel. Lihat [rancangan kompatibilitas aplikasi](docs/app-compatibility.md). |

Gunakan Super+B untuk browser default, Super+Tab untuk overview Dux, dan Super+F untuk keluar dari fullscreen kembali ke tiling. [Daftar shortcut desktop](docs/desktop-shortcuts.md)

---

## Struktur Repositori

```text
ConstOS/
├── assets/                        # Logo dan aset visual ConstOS
├── crates/                        # Subsistem Rust (collector, constosctl, daemon constd)
├── docs/                          # Arsitektur distro & panduan teknis
│   ├── architecture.md            # Arsitektur, batas komponen, dan izin
│   ├── build-guide.md             # Build ISO di lingkungan Arch/CachyOS
│   └── acceptance-guide.md        # Uji terpadu boot, desktop, dan instalasi
├── iso/                           # Mesin build ISO (Archiso + CachyOS profile)
│   ├── buildiso.sh                # Skrip utama generator ISO
│   ├── profiledef.sh              # Metadata ISO ConstOS
│   ├── pacman.conf                # Repositori paket CachyOS dan Arch
│   ├── packages.x86_64            # Manifest paket sesi live
│   └── airootfs/                  # Root filesystem overlay
│       ├── etc/os-release         # Identitas resmi ConstOS
│       ├── etc/systemd/zram-generator.conf
│       ├── etc/sysctl.d/99-constos-memory.conf
│       └── usr/local/bin/const-sandbox
├── desktop/                       # Konfigurasi antarmuka Hyprland
│   ├── hypr/                      # Konfigurasi Hyprland
│   ├── dms/                       # Tema dan preset Const untuk Dux Shell
│   └── wofi/                      # Launcher cadangan
├── installer/                     # TUI, konfigurasi, dan backend pemasangan UEFI
└── packages/                      # Paket core/desktop dan resep Const Harness
```

---

## Cara Membangun ISO

Lihat panduan lengkap di [docs/build-guide.md](docs/build-guide.md).

```bash
packages="$PWD/iso/out/packages-$(date -u +%Y%m%dT%H%M%SZ)"
installer="${packages}-installer"
bash packages/build-local.sh "$packages"
bash packages/build-installer.sh "$installer"
bash iso/buildiso.sh --stage-only --packages-dir "$packages" --installer-dir "$installer"
sudo bash iso/buildiso.sh --packages-dir "$packages" --installer-dir "$installer" -v
```

---

## Pengembangan

ConstOS dikembangkan oleh Alif Constantine. Urutan integrasi, target rilis, dan kriteria verifikasi ada di [roadmap pengembangan](implementation_plan.md).

Urutan port backend dan TUI installer, probe live, serta katalog desktop ada di [rencana migrasi Rust](docs/rust-migration.md).

Arah visual ada di [design.md](design.md). Pemilih aksen, generator palet dari wallpaper, dan Const Hub masih direncanakan. [Audit desktop Ryoku](docs/audits/2026-11-08-ryoku-desktop.md) merekam perbandingan sebelum integrasi Dux.

Roadmap membedakan hasil uji kandidat Calamares sebelumnya dari pengujian jalur TUI Ryoku. Rincian artefak serta batas pengujian ada di [bukti Tsukuyomi](implementation_plan.md#koreksi-tsukuyomi--11-november-2026). Gunakan [panduan pengujian terpadu](docs/acceptance-guide.md) untuk mengulang alurnya.

Runner smoke Live UEFI dan workflow Linux manual mencakup dua entri GRUB, dialog dan layar tindakan installer pada VM tanpa disk target, jaringan, ZRAM, dan jurnal TTY. Cara menjalankan serta batas buktinya ada di [panduan build](docs/build-guide.md#build-tercatat-dan-smoke-live-uefi); hasil eksekusi dicatat di roadmap.

Panduan kontribusi agen ada di [AGENTS.md](AGENTS.md), dan prosedur kerja proyek diindeks di [SKILLS.md](SKILLS.md). Perubahan yang memengaruhi perilaku, arsitektur, atau cara kerja harus menyertakan pembaruan dokumen yang relevan; detail aturannya ada di AGENTS.md.

---

## Kredit

TUI installer, tema GRUB, dan Plymouth berasal dari Ryoku v1.0.7. Login memakai Clockwork Orbital karya Darkkal44 dari salinan qylock di Ryoku. Tsukuyomi memakai tema dark crimson dan menyesuaikan nama produk serta integrasi. Panduan shortcut mengadaptasi komponen Welcome Ryoku. Lisensi dan atribusi ikut dipaketkan. [Ryoku v1.0.7](https://github.com/Ryoku-dev/ryoku/tree/f7197d72de8a21e44b0bea922bdd915f28f6b327) · [qylock](https://github.com/Darkkal44/qylock)

Desktop menjalankan paket Tsukuyomi Shell (fork dari Dux Shell) dengan preset Const. [Tsukuyomi Shell](https://github.com/alifconstantine/tsukuyomi-shell) · [Dux Shell Upstream](https://github.com/duxlabs-dev/dux-shell)

## Lisensi

Proyek ini dirilis di bawah lisensi [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html). Komponen Const Harness dilisensikan secara terpisah.
