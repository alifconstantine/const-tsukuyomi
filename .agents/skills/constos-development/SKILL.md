---
name: constos-development
description: Gunakan saat mengubah atau meninjau profil ISO, staging desktop, installer, capture, daemon, packaging, atau dokumentasi ConstOS untuk menentukan jalur implementasi, verifikasi, dan pembaruan dokumen yang relevan.
---

# Pengembangan ConstOS

## Konteks yang dibaca

Path kode di bawah relatif terhadap root repositori. Baca [AGENTS.md](../../../AGENTS.md), [roadmap](../../../implementation_plan.md), dan [arsitektur](../../../docs/architecture.md). Untuk build/live boot, baca [panduan build](../../../docs/build-guide.md). Jangan menduplikasi status fitur atau daftar perintah instalasi paket ke skill ini.

Untuk installer, browser, atau handoff ke desktop, baca [spesifikasi installer](../../../docs/installer-plan.md) sebelum mengubah kode. Saat reproduksi, catat batas antara kegagalan wizard, backend, boot disk, autentikasi, dan startup sesi. Uji handoff sampai login dari disk pada build yang sama sebelum melanjutkan pekerjaan shell.

## 1. Tentukan jalur efektif

- Untuk ISO, buka `iso/buildiso.sh`, profil, manifest, dan overlay yang terdampak. Cocokkan file sumber dengan hasil staging; jangan mengedit `iso/work/` atau `iso/out/` sebagai perbaikan permanen.
- Untuk sesi ISO, ikuti `installer/install.sh ROOT`, autologin SDDM khusus live, dan `installer/session/constos-installer.desktop` yang membuka Cage. Untuk desktop target, ikuti `desktop/install.sh ROOT` serta sesi `constos.desktop` → `constos-session` dengan `desktop/hypr/hyprland.lua`.
- Untuk boot/login, ikuti `iso/install-boot.sh ROOT live|installed` dan sumber `desktop/boot/`. Hook/preset Archiso serta autologin hanya untuk mode live; target memakai preset terpasang.
- Untuk identitas logo, ubah master `assets/const-logo.svg`, lalu regenerasikan ekspor sesuai [panduan build](../../../docs/build-guide.md#ekspor-logo). Periksa `assets/manifest.json`, `iso/install-boot.sh`, staging GRUB, dan `installer/install.sh`; jangan menambah salinan master atau mengasumsikan izin redistribusi raster sumber.
- Untuk installed target, ikuti `installer/install.sh`, manifest target, backend Calamares, serta paket `constos-core`/`constos-desktop`. Bangun paket lewat `packages/build-local.sh` sebagai user biasa sebelum build root; cocokkan checksum artefak dan sumbernya sesuai panduan build. Jangan menyalin seluruh overlay live ke disk.
- Untuk Calamares live, gunakan `packages/build-calamares.sh` dengan dependensi dan repo generik yang sama seperti ISO. Berikan hasilnya melalui `--calamares-dir DIR` ke staging/build tercatat; periksa fingerprint sumber, SONAME, `calamares --version`, dan wizard pada ISO baru. Repo lokal hasil build tidak boleh masuk konfigurasi pacman live/target. Jangan memperbaiki mismatch ABI dengan symlink library atau downgrade parsial.
- Untuk capture, periksa jalur screenshot, recorder, dan editor yang benar-benar terpasang; cocokkan kemampuan aktual dengan status serta acceptance di roadmap. Jangan memakai izin computer use sebagai jalan pintas.
- Untuk daemon dan packaging, temukan sumber serta konsumen yang benar-benar dipakai sebelum menambah protokol, menyalin collector, atau mengganti executable.

## 2. Pilih pemeriksaan yang sesuai

| Perubahan | Pemeriksaan minimum |
| --- | --- |
| Markdown saja | Tautan lokal/anchor, code fence, referensi lama, kesesuaian status/rencana, dan dampak dokumen menurut AGENTS.md. Tidak memerlukan build ISO. |
| Shell build/staging | Pemeriksaan sintaks shell yang diubah, jalankan staging, lalu periksa file/permission/symlink yang terdampak. Staging bukan bukti boot. |
| Manifest, kernel, initramfs, boot, atau service live | Build tercatat dan runner `tests/live/uefi_smoke.py` sesuai panduan build; periksa dua entri GRUB, layar installer, dan jalur diagnostik. Tambahkan pengujian hardware untuk klaim di luar VM. |
| UI, keybind, tema, widget, atau portal | Interaksi pada sesi Wayland target: fokus/keyboard, aksi nyata, cancel/error, dan monitor/scale yang relevan. Screenshot hasil render harus cocok dengan build yang diuji. |
| Screenshot atau recorder | Jalankan alur pengguna, periksa isi clipboard/hasil gambar, buka serta putar rekaman video/audio. Uji sumber, Stop/cancel/denied, dan kasus lifecycle/failure yang diubah sesuai fase 07A. |
| Installer, storage, update, atau recovery | Gunakan disk VM uji, instalasi/reboot tanpa ISO, periksa target, lalu jalankan update/recovery yang diubah. Pastikan identitas disk sebelum operasi destruktif. |
| Collector, IPC, helper, atau sandbox | Jalankan klien/skenario nyata dengan user biasa; cocokkan output dengan sumber sistem dan periksa batas izin. Uji penolakan serta penghentian akses yang terdampak. |

Gunakan command serta prasyarat build dari panduan, bukan salinan resep yang bisa tertinggal. Jangan mengklaim boot/hardware/codec/portal lulus berdasarkan manifest atau exit code saja. Jika runtime target tidak tersedia, selesaikan pemeriksaan yang mungkin dan sebutkan batasnya; jangan mencentang acceptance runtime.

Untuk baseline live, gunakan wrapper `tests/live/build.sh` dari checkout Linux bersih dan runner UEFI menurut panduan build. Jangan menyamakan smoke ISO lama tanpa metadata build dengan build dari SHA checkout saat ini. Workflow manual memerlukan runner tepercaya; jangan mengaktifkan PR tidak tepercaya pada host berhak sudo. Runner tidak menggantikan pengujian audio, portal, lock, capture, atau instalasi.

Gunakan [pengujian terpadu](../../../docs/acceptance-guide.md) untuk tema boot/greeter, lifecycle sesi, screenshot/cancel, portal/audio, dan instalasi. Installer awal hanya untuk disk UEFI kosong: identitas disk VM harus dicocokkan sebelum konfirmasi. Jangan mengganti penolakan preflight dengan bypass signature, penghapusan keyring, atau penghapusan partisi agar pengujian terlihat lulus.

## 3. Simpan bukti yang tepat

Catat identitas build, versi penting, profil VM/perangkat, skenario, hasil aktual, dan lokasi log/media yang sudah diperiksa privasinya. Pisahkan bukti live, installed, dan hardware fisik. Gunakan hasil baru untuk memperbarui status roadmap; jangan menghapus bukti lama hanya karena target desain berubah.

Bukti media untuk capture harus memperlihatkan sumber/isi yang benar serta hasil playback, bukan hanya ukuran berkas. Bukti UI harus mencakup aksi dan state setelah aksi. Jangan memasukkan media pribadi, clipboard, token, ISO, atau model ke Git.

## 4. Tutup perubahan beserta dokumennya

Ikuti matriks pembaruan di AGENTS.md. Perilaku publik masuk README/panduan, status dan bukti masuk roadmap, kontrak komponen masuk arsitektur, command build masuk panduan build, dan perubahan prosedur ini masuk skill. `SKILLS.md` berubah hanya jika katalog/trigger/lokasi skill berubah; AGENTS.md berubah jika aturan kerja berubah.

Periksa kembali tautan jika file dipindah, hapus instruksi lama yang sudah digantikan, dan sebutkan verifikasi yang benar-benar dijalankan. File skill bukan catatan progres dan bukan jaminan otomatisasi klien.
