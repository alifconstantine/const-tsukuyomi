# Build dan uji ConstOS Live

Profil menargetkan **x86_64 UEFI** dengan GRUB dan kernel CachyOS BORE. ISO membuka TUI installer di Foot dan Cage, sedangkan target terpasang memakai Hyprland. Gunakan VM dengan Secure Boot dimatikan. Untuk membuktikan instalasi dan recovery, ikuti [pengujian terpadu](acceptance-guide.md) dan status di roadmap.

## Siapkan host build

Clone repo di filesystem Linux pada host CachyOS x86_64 agar symlink systemd ikut terpasang. Pasang perkakas dan siapkan kepercayaan paket sebelum build.

```bash
sudo pacman -Syu --needed archiso base-devel git python rust go make cachyos-keyring archlinux-keyring \
  grub squashfs-tools dosfstools mtools libisoburn
sudo pacman-key --populate archlinux cachyos
```

Paket diambil dari repositori CachyOS x86_64 generik dan repositori Arch. Untuk host Arch, siapkan keyring CachyOS melalui [petunjuk upstream](https://github.com/CachyOS/linux-cachyos#installation) sebelum memakai profil ini.

Paket installer dibangun dari sumber Go lokal di `installer/tui`. Builder memerlukan Go 1.26.5 atau lebih baru dan akses ke cache atau proxy modul Go. Di mode Diagnostics, periksa `constos-tui --version`.

## Rakit profil dan ISO

Jalankan dari root repo. Staging dapat diperiksa tanpa hak root.

```bash
# Semua paket dibuat sebagai user biasa sebelum build root.
packages="$PWD/iso/out/packages-$(date -u +%Y%m%dT%H%M%SZ)"
installer="${packages}-installer"
bash packages/build-local.sh "$packages"
bash packages/build-installer.sh "$installer"
bash iso/buildiso.sh --stage-only --packages-dir "$packages" --installer-dir "$installer"
sudo bash iso/buildiso.sh --packages-dir "$packages" --installer-dir "$installer" -v
```

Staging ISO memanggil `iso/install-boot.sh ROOT live` dan `installer/install.sh ROOT` untuk tema, backend installer, serta sesi Cage dan Foot yang dipilih SDDM. Paket target `constos-desktop` memanggil `desktop/install.sh ROOT` untuk Hyprland, Welcome, dan Recommended Apps. Dua paket target dan checksum disertakan di `/usr/share/constos/packages`. Binary TUI dan fingerprint sumber dibangun oleh `packages/build-installer.sh`. Staging memeriksa fingerprint dan memasang binary khusus pada profil live. `SHA256SUMS` memeriksa arsip dan `SOURCE_SHA256SUMS` mencocokkan sumber builder dengan checkout. Signature repo jaringan tetap diwajibkan. Setiap run memakai direktori kerja baru di `iso/work/`. `-w DIR`, `-o DIR`, `--packages-dir DIR`, dan `--installer-dir DIR` mengubah lokasi kerja, output, serta input paket. ISO muncul di `iso/out/constos-*.iso` secara default. Jalankan `makepkg` sebagai pengguna biasa.

`constos-core` mengompilasi CLI `const` dan daemon `constd` untuk x86_64 generik dengan `Cargo.lock`, termasuk saat host memakai flag CPU native. Build memerlukan `cargo`, `rustc`, dan dependensi Cargo yang sudah ada di cache atau dapat diunduh. Fingerprint paket lokal mencakup workspace Rust dan lockfile. Staging memakai `bsdtar` dari `libarchive` untuk mengambil `constd` dan berkas aktivasi sesi dari paket core yang sudah diverifikasi.

## Sumber tema dan shell

Preset Tsukuyomi memakai dark crimson pada GRUB/Plymouth, Clockwork Orbital, TUI, Dux, dan terminal. `desktop/welcome/qml` mengadaptasi kartu shortcut Ryoku; `guide.py` menyimpan state per akun. Regenerasi ASCII khusus Fastfetch: `python3 assets/export-ascii.py` (Pillow dan rsvg-convert). `yay`, Git, dan base-devel masuk manifest target dari repo bertanda tangan.

Desktop shell disediakan oleh paket `tsukuyomi-shell-git` (resep di `packages/tsukuyomi-shell/PKGBUILD`, fork dari `dux-shell`) atau fallback `extra/dux-shell`. Build paket memerlukan `go`, `make`, `git`, serta inisialisasi submodule `dux-qml-common` dan `dux-qt-base`. Unit pengguna menjalankan `/usr/bin/dms run --session --qs-child` dengan `DMS_QS_CHILD=1`, menggunakan runtime Quickshell upstream `/usr/bin/qs` dengan preset Const dari paket desktop. Untuk pengujian live QML saat pengembangan: `dms run --qs-child -c <path_ke_quickshell>`.

GRUB, Plymouth, dan Clockwork Orbital SDDM berasal dari Ryoku v1.0.7. Build mengambil sumber dari `iso/grub` dan `desktop/boot`, dengan palet Const dan tampilan tanpa logo. Atribusi ada di [COPYING.txt](../desktop/boot/COPYING.txt).

## Build tercatat dan smoke Live UEFI

Runner di `tests/live/` menguji ISO tanpa menambah service, SSH, atau konfigurasi khusus tes ke image. Host menjalankan QEMU sebagai user biasa, membuka dua VM tanpa disk terpasang, dan memilih entri GRUB melalui keyboard. Runner membaca layar TUI pada jalur grafis dan menjalankan probe dari TTY pada jalur Diagnostics. HTTP loopback host menyajikan probe dan menerima hasil melalui jaringan user-mode QEMU, lalu ditutup setelah tes.

Tambahkan perkakas pada host Linux yang sudah disiapkan di atas:

```bash
sudo pacman -Syu --needed git python qemu-system-x86 \
  qemu-hw-display-virtio-gpu qemu-hw-display-virtio-vga \
  edk2-ovmf tesseract tesseract-data-eng
```

Paket QEMU Arch bersifat modular: kedua modul virtio di atas diperlukan untuk profil grafis runner; `qemu-system-x86` saja tidak cukup.

Gunakan checkout Git bersih, termasuk tanpa berkas untracked di luar path ignored. Wrapper menolak checkout Windows yang kehilangan symlink; ia tidak merekonstruksi symlink atau mengubah konfigurasi Git global. Build memerlukan root, tetapi smoke tidak. Direktori output harus baru dan parent-nya sudah ada; artefak yang sudah ada tidak ditimpa.

```bash
mkdir -p iso/out
build="$PWD/iso/out/live-$(date -u +%Y%m%dT%H%M%SZ)"
packages="${build}-packages"
installer="${build}-installer"
bash packages/build-local.sh "$packages"
bash packages/build-installer.sh "$installer"
sudo -n bash tests/live/build.sh --output "$build" --packages-dir "$packages" --installer-dir "$installer"
iso=$(python3 -c 'import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print(p/json.loads((p/"build.json").read_text())["iso_filename"])' "$build")
python3 tests/live/uefi_smoke.py \
  --iso "$iso" --build-evidence "$build/build.json" \
  --ovmf-code /usr/share/edk2/x64/OVMF_CODE.4m.fd \
  --ovmf-vars /usr/share/edk2/x64/OVMF_VARS.4m.fd \
  --output "${build}-smoke"
```

Path firmware mengikuti [paket Arch edk2-ovmf](https://archlinux.org/packages/extra/any/edk2-ovmf/files/). Gunakan pasangan CODE/VARS non-Secure-Boot yang cocok dari host, bukan firmware `secboot`. Runner menyalin template VARS ke direktori bukti; template asli tidak ditulis. Default Linux mensyaratkan akses baca/tulis `/dev/kvm`; tidak ada fallback otomatis ke TCG. `--accelerator whpx` digunakan untuk smoke pada host Windows; `--accelerator tcg` menyediakan diagnosis emulasi eksplisit. TCG bertingkat belum lulus; lihat batas bukti di roadmap. Naikkan `--timeout` dari default 300 detik per cold boot bila diperlukan untuk diagnosis. VM memakai 4 vCPU, 6 GiB RAM, dan grafis virtio. Tesseract dengan model `eng` mengenali menu sebelum input keyboard; kegagalan OCR menggagalkan tes, bukan melewati GRUB.

### Pemeriksaan dan artefak

| Jalur | Bukti yang diperiksa |
| --- | --- |
| Build Linux | SHA checkout bersih sebelum/sesudah build, checksum paket lokal dan sumbernya, seluruh symlink overlay yang terlacak tetap symlink saat staging, versi paket host, log Archiso, satu ISO beserta SHA-256. |
| Install Tsukuyomi | VM smoke hanya membawa ISO dan firmware. Timeout GRUB membuka Welcome TUI berbahasa Inggris. Ctrl+C sebelum pemasangan kembali ke layar tindakan installer. Periksa screenshot Welcome dan menu tindakan. |
| Jaringan/ZRAM | NetworkManager aktif, IPv4 dan lease DHCP pada interface non-loopback, serta perangkat ZRAM aktif sebagai swap dengan algoritme `zstd`. Ini bukan uji internet atau Wi-Fi fisik. |
| Diagnostics | Cold boot entri terakhir dengan `systemd.unit=multi-user.target`, SDDM tidak aktif, controlling terminal `/dev/tty1`, dan `sudo -n journalctl -b` membaca entri dengan boot ID yang sesuai. Probe juga memeriksa kernel, symlink systemd, paket Cage, sesi installer, `constos-tui --version`, dan aktivasi `constd` sebagai `liveuser`. Probe membandingkan snapshot D-Bus dengan kernel dan `/proc/meminfo`. |

`build.json`, `build.log`, `staging.log`, `host-packages.txt`, checksum, dan ISO berada di direktori build. Direktori smoke menyimpan `summary.json`, report konsol, perintah/versi QEMU, hash firmware dan runner/probe, screenshot GRUB/dialog installer/layar tindakan/TTY, serta log kegagalan. Exit nonzero atau `ok: false` memblokir penerimaan. Pilih direktori baru untuk setiap percobaan.

Untuk menguji ISO yang sudah ada, jalankan runner tanpa `--build-evidence`. Hasilnya mencatat checksum tanpa klaim SHA sumber build. Untuk ISO historis sebelum migrasi `constd`, gunakan runner dari revisi build terkait agar pemeriksaan cocok dengan fitur ISO. Jika metadata diberikan, nama/checksum ISO, keberhasilan build, dan identitas checkout bersih harus cocok sebelum VM dijalankan.

Periksa screenshot secara visual sebelum mencentang acceptance. Runner belum menguji audio, portal, lock/logout, screenshot pengguna, instalasi, perangkat fisik, tema, atau kualitas render di berbagai skala. Simpan bukti hanya dari VM uji tanpa data pribadi; periksa dan redaksi sebelum membagikannya. Jangan commit ISO, salinan NVRAM, atau cache build.

### Workflow Linux tepercaya

`.github/workflows/live-uefi.yml` menyediakan `workflow_dispatch`, bukan eksekusi PR otomatis pada host berhak sudo. Siapkan runner khusus/sekali pakai berlabel `self-hosted`, `Linux`, `X64`, `constos-build` dengan prasyarat di panduan ini, keyring tepercaya, akses baca/tulis `/dev/kvm` untuk user runner, dan `sudo -n` untuk build. Jangan gunakan mesin kerja yang menyimpan data pribadi atau kredensial penandatanganan.

Isi repository variables `CONSTOS_OVMF_CODE` dan `CONSTOS_OVMF_VARS` dengan path firmware host. Jalankan workflow hanya pada ref yang sudah ditinjau. Checkout memakai `clean: true`; workspace runner bukan tempat menyimpan pekerjaan pengguna. Workflow membangun ISO, menjalankan smoke sebagai user biasa, dan mengunggah diagnostik selama 7 hari meskipun gagal; ISO, cache build, dan NVRAM tidak diunggah. Keberadaan workflow bukan bukti job GitHub sudah lulus; status eksekusi dicatat di roadmap.

## Pemeriksaan manual tambahan

Untuk diagnosis interaktif, boot **Tsukuyomi Diagnostics** dengan profil VM yang sama. Periksa `uname -r`, `systemctl --failed`, `nmcli general status`, `zramctl`, serta `journalctl -b`. Jalankan skenario shortcut, audio, file/MIME, lock/logout, screenshot, dan portal pada desktop yang sudah terpasang.

Regresi batas disk, arsip preflight, dan backend katalog dapat dijalankan sebagai pengguna biasa tanpa disk uji.

```bash
python3 -m unittest discover -s tests/installer -p 'test_*.py'
python3 -m unittest discover -s tests/desktop -p 'test_*.py'
```

Gunakan VM dengan disk virtual kosong terpisah untuk membuktikan seluruh wizard, penulisan disk, reboot, dan login. Smoke tanpa disk menguji jalur boot, Welcome, dan Cancel.

## Pengujian terpadu dan recovery tema

Gunakan [panduan pengujian terpadu](acceptance-guide.md) untuk tema GRUB/Plymouth/SDDM, screenshot/cancel, audio/portal, login ulang, serta instalasi pada disk virtual baru dan reboot tanpa ISO. Skenario itu tidak dicentang hanya karena runner baseline lulus.

Tema greeter dapat dipulihkan dari TTY dengan memasang konfigurasi stock yang disertakan sumber boot, lalu restart SDDM. Restart memutus sesi grafis: simpan pekerjaan terlebih dahulu. Palet boot/greeter statis dan tidak membaca wallpaper pengguna. Opsi aksen manual/adaptif pada Settings masih berupa rancangan di `design.md`, bukan bagian dari integrasi ini.
