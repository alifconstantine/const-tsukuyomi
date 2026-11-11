# ConstOS · Roadmap Pengembangan

**Prioritas 10 November 2026** · CachyOS x86_64, UEFI, Hyprland/Wayland

ConstOS dikembangkan sebagai distro Linux untuk pengembangan perangkat lunak dan penggunaan desktop sehari-hari, dengan sistem yang bisa dipasang, diperbarui, dan dipulihkan serta antarmuka monokrom yang konsisten sejak boot. Const Harness menambah workbench dan akses lokal ke desktop dengan izin pengguna. Roadmap dimulai dari Boot UI dan berakhir saat artefak rilis, jalur update, dan recovery sudah teruji.

**P0 saat ini adalah jalur pemasangan sampai desktop.** Jalur disk kosong dan reboot sudah dijalankan di VM. Lengkapi variasi browser dan jaringan, lalu uji aplikasi harian pada sesi Dux. Implementasi installer mengikuti [spesifikasi installer](docs/installer-plan.md).

## Posisi sekarang

| Bagian | Yang sudah dikerjakan | Yang perlu dibuktikan atau dilengkapi |
| --- | --- | --- |
| Build ISO | Profil Archiso dengan tema boot/login, sesi desktop, paket lokal, dan installer berhasil dibangun di Linux. Wrapper build mencatat checkout bersih, checksum paket/sumber lokal, symlink staging, versi paket, log, dan checksum ISO. Runner Live UEFI telah lulus pada Linux/KVM dan Windows/WHPX. | Jalankan workflow pada runner GitHub tepercaya yang sudah dikonfigurasi. Uji boot pada perangkat fisik. |
| Sesi live | Cage dan Foot membuka TUI yang diimpor dari Ryoku. Kedua entri GRUB tersedia, dengan splash Plymouth dan tema GRUB yang diadaptasi. | Uji Wi-Fi dan tampilan wizard pada resolusi lain. |
| Sistem dan installer | Wizard menyediakan Network dan pilihan Firefox, Chromium, Zen, atau No browser. Backend memilih transaksi bertanda tangan sebelum partisi dan menulis MIME browser pada akun baru. Firefox dan No browser lulus instalasi pada kandidat Calamares sebelumnya. | Uji instalasi dan handler Chromium serta Zen. |
| Diagnosis, telemetri, dan AI | `constos-core` memasang CLI Rust `const` pada sistem terpasang. `const doctor` memeriksa kernel, swap ZRAM, unit systemd yang gagal, ruang tersedia di `/`, serta konfigurasi Snapper dan mount `/.snapshots`. Collector dan daemon Rust `constd` lulus uji host pada bukti di bawah. | Uji dua pemeriksaan storage pada target terpasang. Integrasikan daemon Rust dan sambungkan UI sesi ke kontrak IPC. Profil live saat ini tidak mewajibkan Harness atau Ollama. |
| Pembaruan | `const update` membuka transaksi penuh pacman dari terminal pada sistem terpasang. | Siapkan repo rilis ConstOS bertanda tangan dan tuntaskan skenario update, reboot, dan recovery pada kandidat rilis. |
| Capture desktop | Print, Alt+Print, dan launcher memanggil `constos-screenshot`. Bukti screenshot dari ISO antara tetap di bawah. | Ulangi screenshot, cancel, dan portal di sesi Dux. |
| Shell dan aplikasi target | Target menjalankan paket Dux resmi dengan preset Const. Kitty/Fish memakai Fastfetch dengan simbol Const ASCII khusus terminal. Launcher, Quick Settings, notifikasi, lock, dan Nautilus diuji pada kandidat desktop sebelumnya. MP4 dan keluaran audio virtual lulus pada revisi playback. | Uji default aplikasi lain, aksesibilitas, beberapa monitor, dan audio perangkat fisik. |

### Koreksi Tsukuyomi · 11 November 2026

Perubahan sumber: startup resmi `start-hyprland`, preset dark crimson, nama tampilan Tsukuyomi, ASCII khusus Fastfetch, `GRUB_DISABLE_BOOTNEXT`, yay/Git/base-devel pada target, serta Welcome QML dengan kartu shortcut Ryoku tanpa gambar. Geometri wizard ditentukan ukuran terminal agar rail/kartu/footer tetap di tempat antar langkah. Layar gagal menampilkan sebab dan log privat tanpa QR; retry sesudah storage ditolak.

Screenshot kegagalan pengguna hanya memperlihatkan bagian bantuan. Penyebab percobaan tersebut belum dapat disimpulkan tanpa log. Log kegagalan berada pada sesi live; simpan sebelum reboot.

Snapshot QA bersih `edd97e6db88afb7e7f0aad7381ca4d1f65679d34` menghasilkan ISO `constos-2026.11.11-x86_64.iso` dengan SHA-256 `ebeb59c1050f7805b9c7b58364bcd5ab1423c3d322c0e3ff3f935a23314466a1`. ISO, checksum, metadata, dan screenshot ada di `iso/out/tsukuyomi-20261111/`. Uji memakai QEMU/KVM 11.1.3, OVMF UEFI, 4 vCPU, RAM 6 GiB, serta output virtio 1280 × 800.

- **Live.** Kedua entri boot, Ctrl+C ke menu tindakan, dan Diagnostics lulus. Splash menunjukkan nama Tsukuyomi, unit systemd, dan persentase. Pada Keyboard, Locale, Network, Browser, Hostname, dan Review, tepi kartu tetap pada baris piksel 49 dan 670. Uji Go juga mencakup grid pendek dan penolakan konfirmasi saat Review tak terlihat.
- **Kegagalan dan Retry.** Link jaringan diputus sebelum konfirmasi pada disk VM kosong 40 GiB `TSUKUYOMI-QA-1111`. TUI menampilkan tahap unduhan, kegagalan DNS pacman, log privat, dan Retry tanpa QR. Statistik QMP mencatat 0 byte ditulis ke disk target. Setelah link dipulihkan, Retry mengunduh dan memverifikasi paket, menyelesaikan pemasangan Firefox serta zona Asia/Jakarta, dan menawarkan **Reboot now**.
- **Boot disk dan desktop.** Tanpa ISO, GRUB menampilkan Tsukuyomi Linux, submenu advanced, dan UEFI Firmware Settings. SDDM menolak kata sandi salah dan menerima kata sandi benar. Proses `start-hyprland --` berjalan; `hyprctl configerrors` kosong. Dux Shell `2.1.2-1` aktif, kartu Launcher di Welcome membuka Dux dengan Tab dan Enter, dan Fastfetch menampilkan simbol Const ASCII pada Kitty/Fish. Paket `yay 13.1.0-2` dan `base-devel` terpasang; `yay --version` berhasil sebagai akun biasa. Firefox membuka fixture HTTP lokal lewat `xdg-open`. Logout kembali ke SDDM; login berikutnya tidak membuka Welcome otomatis dan launcher dapat membuka panduan lagi. Database sinkronisasi pacman pada akun baru diisi saat `const update` pertama.

Bukti VM ini belum mencakup perangkat fisik, multi-monitor, Wi-Fi/Bluetooth, pemasangan paket AUR, Chromium/Zen, atau rollback. Hasil build 10 November di bawah tetap berlaku hanya pada artefaknya masing-masing.


**Pembuka installer bergaya piksel.** Snapshot QA `8c3a42821c0209576f4e7f9928f9b281cdaa7278` menghasilkan ISO SHA-256 `568e7f9b0b43997a2cb91f0b25bb8e55667f5605687e470bdf128916d082a5c4`. Di QEMU/KVM dengan OVMF dan resolusi 1280 × 800, judul **TSUKUYOMI**, bar merah, dan status **Preparing installer** terlihat di tengah. Dua percobaan membuktikan transisi otomatis ke Welcome dan transisi melalui Enter. Ctrl+C kembali ke menu tindakan dan jalur Diagnostics lulus pada ISO ini. Uji Go dan `go vet` lulus. ISO, checksum, ringkasan smoke, dan screenshot ada di `iso/out/tsukuyomi-intro-20261111/`. Bukti autentikasi dan desktop memakai uji instalasi pada build sebelumnya.

**Palet merah pekat.** Snapshot QA `b7fcf4a748b0edf13b6b63769365e77e40a53bdf` menghasilkan ISO SHA-256 `c14e6305d9c00579d3e6082ae291136fdd6a2d666e5d839136d5f15651f5c7a7`. Screenshot dari QEMU/KVM dan OVMF pada 1280 × 800 mengonfirmasi `#B83242` untuk judul dan bar aktif, `#260F17` untuk jalur bar, serta latar `#120E11`. Uji Go, Welcome, Ctrl+C, dan Diagnostics lulus. ISO, checksum, screenshot, dan ringkasan uji tersedia di `iso/out/tsukuyomi-dark-red-20261111/`.

### Impor tampilan Ryoku · 10 November 2026

TUI Go, Clockwork Orbital, Plymouth, dan tata letak GRUB diambil dari Ryoku v1.0.7 `f7197d72`. Tema GRUB memakai sumber edisi Fedora Ryoku. Backend ConstOS menerima disk, browser, wilayah, dan akun dari TUI, lalu menjalankan preflight serta pemasangan. Dux memakai paket upstream, dan Fastfetch menampilkan informasi sistem tanpa logo. Bukti kandidat Calamares di bawah berlaku pada artefaknya masing-masing.

- **Kandidat pertama.** Snapshot QA bersih `6e7ef463cd573545ab9de6114ecab3ea6a72a6aa` menghasilkan ISO SHA-256 `fd41f8601f7bfc8415eadbeaa9313e2615721130a54b89f9fd796db8634b3817`. VM QEMU/KVM dengan OVMF, 4 vCPU dan RAM 6 GiB membuka Welcome TUI, membatalkan lewat Ctrl+C, dan lulus pemeriksaan Diagnostics. Bukti ada di `iso/work/const-integration.5ft6an/ryoku-release-smoke/`.
- **Disk uji kandidat pertama.** Wizard menampilkan Firefox, zona waktu America/New_York, dan serial `CONST-RYOKU-RELEASE` pada disk kosong 40 GiB. VM boot dengan hanya disk target dan memuat `\\EFI\\ConstOS\\grubx64.efi`. Clockwork Orbital menolak kata sandi salah dan membuka desktop pada autentikasi yang benar. Dux `2.1.2-1` berjalan melalui `dms run --session`. Fastfetch tampil tanpa logo dan Firefox membuka fixture lokal melalui `xdg-open`. Bukti ada di `iso/work/const-integration.5ft6an/ryoku-release-vm/`.
- **Revisi layar pertama.** Snapshot QA `789d8f5c0dd7a74f3b9646f031d9b123b418d9fc` menghasilkan ISO SHA-256 `d2a958b52212ec0500d2da666e552a41b6a36c8de1d1a5d536ed06ea80e5c286`. Installer menulis penanda rilis yang dikenali Dux saat membuat akun agar kartu What's New tidak muncul otomatis pada login pertama. Kedua entri GRUB dan cancel lulus pada ISO ini. Pada VM tanpa disk, memilih German membuka ulang sesi dan input fisik Z mengetik y di filter locale. Bukti ada di `iso/work/const-integration.5ft6an/ryoku-no-changelog-smoke/` dan `ryoku-layout-vm/`.
- **Instalasi revisi.** Disk kosong 40 GiB berserial `CONST-RYOKU-CLEAN` menyelesaikan instalasi dengan Firefox. **Reboot now** mengakhiri VM live. Saat dijalankan dengan hanya disk target, UEFI memuat ConstOS, Clockwork Orbital menerima kata sandi akun baru, dan desktop menampilkan Welcome ConstOS dengan panel Dux aktif. Kartu DMS tidak muncul pada login pertama. Kitty membuka Fish dan Fastfetch tanpa logo, serta handler browser terdaftar sebagai `firefox.desktop`. Bukti ada di `iso/work/const-integration.5ft6an/ryoku-no-changelog-vm/`. ISO yang diverifikasi dan tangkapan layar ada di `iso/out/const-ryoku-20261110/`.

### Integrasi desktop Const · 10 November 2026

Build Linux x86_64 menghasilkan kandidat awal ISO `constos-2026.11.10-x86_64.iso` dari snapshot QA `a05531dbf1e4126294a79abe7ff16b7fa31dcb88` dengan SHA-256 `26bc49b9ccffdf055bfbfae41a1d26cb0733d0dc575cf4e1e1340f7a1052369d`. Bukti lokal berada di `iso/work/const-integration.5ft6an/`. Pengujian memakai QEMU `11.1.3` dengan KVM, OVMF UEFI, 4 vCPU, RAM 6 GiB, dan disk virtual 40 GiB untuk skenario instalasi.

- **Smoke kandidat.** Entri Install mencapai Welcome dan Cancel kembali ke kiosk. Entri Diagnostics membuka TTY dengan 18 pemeriksaan baseline lulus, termasuk DHCP, ZRAM, dan jurnal. Progres Plymouth bergaya terminal terlihat pada boot kandidat. Lihat `delivery-smoke/summary.json` dan `delivery-install-vm/current.png`.
- **Instalasi kandidat.** Wizard menampilkan empat pilihan browser dan **Review** menampilkan Firefox serta serial disk uji. Setelah verifikasi paket, instalasi selesai dan **Restart** mengakhiri sesi live. Cold boot tanpa ISO memakai `\EFI\ConstOS\grubx64.efi`. SDDM menolak kata sandi salah, lalu membuka Hyprland dan Welcome dengan kata sandi yang benar. `xdg-open` membuka halaman lokal di Firefox `159.0.1-1`. Dux dan Quick Settings tampil, dan `const doctor` melaporkan lima pemeriksaan lulus, termasuk konfigurasi Snapper dan mount `/.snapshots`. Lihat `delivery-install-vm/`.
- **No browser.** Build integrasi `8208514dde9d33a11fe241df535aa0cb08cd7245` dengan SHA-256 `4599c833b637c3863b29e6e89e4fab1ae78477edf6b829a1aec96162562aa119` menyelesaikan instalasi dan boot disk tanpa ISO. SDDM menolak kata sandi salah dan menerima kata sandi benar. Quickshell memuat QML dari paket Const, Fish tampil di Kitty dengan Fastfetch ASCII, dan Firefox, Chromium serta Zen tidak terpasang. Launcher, Quick Settings, notifikasi, dan Nautilus dibuka. Lihat `final-install-vm/`.
- **Percobaan Firefox awal.** Build `4988085a745086c1122a1fd6651f19dc278730d0` dengan SHA-256 `68e2d0eed947aef9565fac6e8b336ec00dfa65f6cdf74530142023e0ff6bce01` membuka editor NetworkManager, memasang Firefox, dan boot tanpa ISO. Firefox menjadi handler web dan membuka halaman lokal melalui `xdg-open`. Lock Dux juga menerima autentikasi PAM setelah paket desktop dimutakhirkan di guest. Lihat `install-vm/`.
- **Temuan pada kandidat awal.** ISO memakai Calamares `3.4.1-6`, dengan target `constos-desktop 0.1.0-4`, Dux `2.1.2-1`, dan Hyprland `0.57.2`. Entri kernel GRUB masih berlabel Arch Linux dan mpv gagal membuka MP4 pada VM tanpa akselerasi. Menambahkan konfigurasi Wayland dengan fallback shared memory pada akun uji memulihkan video. Nada 440 Hz dari MP4 sintetis terdeteksi pada keluaran PCM QEMU. Lihat `delivery-install-vm/mpv-native-success.png` dan `delivery-install-vm/audio-recheck.txt`.
- **Revisi playback dan boot.** Snapshot QA `d507b6dee5cfb266731442392feba9cf9153b01f` menghasilkan ISO SHA-256 `d11be216058061f5b18f23a776a78a90bd94a0a6d0936bc0524664bb2b2a37d2`. ISO dan checksum tersedia di `iso/out/const-desktop-20261110/`. Paket `constos-desktop 0.1.0-5` menyiapkan konfigurasi mpv bagi akun baru. Installer menulis `GRUB_DISTRIBUTOR=Const` sebelum membuat konfigurasi boot target. Kedua entri GRUB, Cancel ke kiosk, serta 18 pemeriksaan mode Diagnostics lulus pada revisi ini. Lihat `playback-final-smoke/summary.json`.
- **Instalasi revisi.** Disk kosong berserial `CONST-PLAYBACK-QA` menyelesaikan instalasi dengan Firefox. Sesudah **Restart**, VM boot tanpa ISO dan menampilkan **Const Linux** di GRUB, lalu SDDM membuka sesi Hyprland/Dux. Akun baru memuat konfigurasi mpv dari paket. `xdg-open` membuka halaman lokal di Firefox dan MP4 sintetis di mpv. Nada uji 440 Hz terdeteksi pada keluaran virtual. Lihat `playback-final-vm/`, terutama `grub-const-linux.png`, `firefox-opened.png`, `mpv-playback.png`, dan `audio-verification.txt`.
- **Batas bukti.** Hyprland masih menampilkan peringatan startup langsung sesaat setelah login. Nama Dux/DMS masih terlihat pada sebagian pengaturan lanjutan upstream. Chromium, Zen, Wi-Fi, beberapa monitor, dan perangkat fisik belum diuji pada integrasi ini. Di host Linux, 20 uji installer dan 6 uji desktop lulus.

Smoke manual pada 6 November memakai VM QEMU/OVMF dengan 4 vCPU dan 3 GiB RAM. Kernel `7.3.1-1-cachyos-bore` berjalan di sesi Wayland, `systemctl --failed` melaporkan 0 unit gagal, dan `journalctl` bisa dibuka dari console fallback. Nama host live masih `CachyOS`. Instalasi ke disk dan boot perangkat fisik masih perlu diuji. [Panduan build](docs/build-guide.md)

### Prioritas installer setelah review Ryoku · 9 November 2026

Sebanyak 26 screenshot Ryoku edisi CachyOS dan bagian **Everything, already installed** ditinjau bersama source Ryoku v1.0.7. Ini bukti desain referensi dari boot sampai progres, bukan hasil uji ConstOS. [Spesifikasi installer](docs/installer-plan.md) menetapkan wizard yang lebih ringkas, Brave sebagai rekomendasi, konfirmasi disk kosong di Review, dan isi desktop pertama. Skenario Gaming dikeluarkan dan pilihan Yes/No Const Harness dibatasi pada prototipe. Data layar selesai, SDDM, dan Hyprland untuk build ConstOS berikutnya masih harus diambil dari VM.

Audit revisi sebelumnya menemukan wizard dapat keluar sebelum Welcome ketika daftar disk kosong dan Welcome mewajibkan probe satu mirror. Perubahan sumber lokal memindahkan kendala disk ke wizard, memusatkan verifikasi jaringan di preflight, serta mengalihkan smoke grafis ke Welcome dan Cancel. Bukti Linux dan hasil kasus pengguna belum tercatat.

Pada host Windows, 17 uji installer dengan fixture lulus. Qt 6.9.2 offscreen memeriksa warna tombol utama/disabled dan shortcut Cancel pada widget contoh. Payload staging dan orkestrasi smoke dengan OCR/QMP simulasi juga diperiksa. Uji boot, ukuran layar, fokus, dan transaksi pada ISO aktual masih terbuka.

### Reproduksi installer dari `001a1db` · 9 November 2026

Build dari checkout bersih `001a1dbcc5faa136372be6eda048a42d45f95f3f` di Arch Linux x86_64 menghasilkan ISO SHA-256 `4a135a7370563de3c262b7995e0271df0929058e9e23083f26d25aa140d4f8ea`. Calamares `3.4.1-2` memakai Qt `6.12.0-3` dan Boost `1.92.0-1`. Target QEMU/WHPX memakai firmware EDK2 UEFI, 4 vCPU, RAM 7 GiB, dan qcow2 kosong 40 GiB. Serial `CONSTOS-P0-baseline` dicocokkan di wizard sebelum pemasangan. Metadata dan tangkapan layar berada di `iso/work/p0-installer-20261109T103501Z/baseline/`.

- GRUB membuka Cage/Calamares. Disk meminta pengetikan path dan Summary hanya merangkum lokasi, keyboard, dan disk. Selama unduhan cache sudah mencapai 790 MiB ketika UI masih menampilkan 0%. Proses kemudian menyelesaikan pemasangan dan melepas mount Btrfs serta ESP.
- Dalam percobaan dari Finish, wizard tertutup ke menu kiosk. Saat installer dibuka lagi pada disk yang sudah dipasang, launcher menampilkan **No eligible empty disk found** sebelum Welcome. Belum ada bukti yang mengaitkan hasil itu dengan laporan pengguna dari build lain.
- Reboot dari TTY dan cold boot QEMU dengan hanya disk membaca `\\EFI\\ConstOS\\grubx64.efi`. SDDM meminta kata sandi, dan akun uji masuk ke Hyprland dengan Waybar serta Welcome. Hyprland `0.57.1` menampilkan peringatan startup langsung tanpa `start-hyprland`.

### Revisi P0 Disk, Review, dan Finish · 9 November 2026

Sumber build memakai `001a1db` ditambah perubahan lokal yang direkam di `iso/work/p0-installer-20261109T103501Z/final/source.txt`. Builder Arch Linux x86_64 menghasilkan Calamares `3.4.1-3` dan ISO SHA-256 `0bfc8f89330169e069fc356226d9439d7df60dc9cb5cc003a1e31689c9fb37a7`. Bukti utama berada di subdirektori `final/`. VM utama memakai QEMU `11.1.0`/WHPX, EDK2 UEFI, 4 vCPU, RAM 7 GiB, dan qcow2 baru 40 GiB dengan serial `CONSTOS-P0-final`.

- Build awal revisi `264bba88…` berhenti di loader branding dengan `key not found: slideshow`. Descriptor kini menyertakan kunci itu. Build antara `33860d7e…` membuka wizard, tetapi menunjukkan layout kustom sebagai default Keyboard dan kontras judul Review rendah. Build final menampilkan English (US) dan Review yang terbaca. Pemilihan lewat keyboard, **Edit** dan **Check again** diuji sebelum **Install ConstOS**.
- Pada VM terpisah dengan build antara, jaringan dinonaktifkan sebelum **Install ConstOS**. Tahap unduhan gagal dengan detail log dan installer dapat dibuka kembali dari kiosk saat offline. `lsblk` dan `wipefs --json --no-act` menunjukkan disk 40 GiB tetap tanpa partisi, mount, atau signature. Bukti berada di subdirektori `revised/`.
- Build final menampilkan tahap unduhan, partisi, bootstrap, konfigurasi, dan unmount dari JobQueue. **Installation complete** tampil setelah ESP dan Btrfs dilepas. **Restart** mengakhiri VM live dengan `-no-reboot`. VM yang sama kemudian dijalankan dengan `-boot order=c` tanpa ISO, memuat GRUB dari ESP, lalu menampilkan SDDM. Kata sandi salah ditolak dan kata sandi benar membuka Hyprland, Waybar, dan Welcome pertama. Lihat `stage-complete.png`, `installed-serial.log`, `sddm-wrong-password.png`, dan `desktop-first-welcome.png` di `final/`.
- Pada target, Foot dan Thunar terbuka lewat pintasan. Foot menunjukkan sesi Wayland, target systemd pengguna aktif, Btrfs terpasang di `/`, `/home`, dan `/.snapshots`, serta ESP FAT32 di `/boot/efi`. `sudo -n` ditolak tanpa autentikasi dan `passwd -S root` melaporkan `L`. Setelah **Skip**, logout dan login kedua membuka desktop tanpa menampilkan Welcome otomatis. Welcome masih bisa dibuka dari Wofi. Hyprland masih menampilkan peringatan startup langsung. Bukti ada di `foot-system-checks.png`, `desktop-foot-thunar.png`, `desktop-second-login.png`, dan `desktop-welcome-reopened.png`.
- Smoke Live UEFI untuk SHA ISO yang sama lulus pada VM tanpa disk. Entri default membuka Welcome dan Cancel mengembalikan menu kiosk. Diagnostics mencapai TTY dengan 18 pemeriksaan baseline lulus. Ringkasan dan bukti ada di `final-smoke-pass/summary.json`.
- Sebanyak 19 uji backend lulus di Linux. Kandidat `cachyos/brave-bin` x86_64 versi `1:1.99.55-1` lulus verifikasi signature dan memuat `brave-browser.desktop` pada pemeriksaan arsip di builder. Launcher, MIME, dan pilihan browser di wizard masih menunggu integrasi. Bukti paket ada di `candidate/brave-signature.log` dalam direktori uji yang sama.

### Revisi alur installer · 8 November 2026

Laporan VM pengguna menunjukkan dialog pra-wizard yang menampilkan JSON identitas disk. Ryoku v1.0.7 menggunakan wizard layar penuh, pemilih disk dalam rangkaian langkah, serta Review sebagai titik aman terakhir. ConstOS memakai pola itu melalui halaman Disk bawaan paket Calamares lokal dan Summary. **Next** di halaman Disk memerlukan path yang cocok. **Install** pada Summary memulai preflight, lalu backend memvalidasi ulang identitas sebelum partisi. Default waktu memakai America/New_York agar format wilayah awal selaras dengan bahasa Inggris. Pilihan bahasa dan lokasi tetap tersedia di wizard. [Alur Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/installation/tui/README.md#the-step-flow)

Pada host Windows, 16 uji installer dengan fixture lulus. Modul lulus kompilasi sintaks dengan header Calamares terpin dan Qt 6.9.2. Uji komponen Qt offscreen dengan fixture disk dan pengganti GlobalStorage membuktikan pemilihan keyboard, penolakan path salah, reset saat mengganti target, dan ringkasan yang meng-escape metadata. Pemeriksaan staging memverifikasi payload dan permintaan symlink; symlink Linux dan runtime Cage/Calamares masih memerlukan build ISO dan [uji VM](docs/acceptance-guide.md#installer-dan-reboot-tanpa-iso).

### Bukti smoke otomatis · 7 November 2026

Pelaksana: agen pengembangan pada sesi ini. Dependensi: host Linux dengan Archiso/keyring siap, checkout Git bersih, QEMU/OVMF, modul virtio, Python, dan OCR. Implementasi berada di `tests/live/`, `.github/workflows/live-uefi.yml`, dan `.github/actionlint.yaml`; tidak ada perubahan pada overlay live, menu GRUB, atau konfigurasi desktop.

| Bukti | Hasil dan lokasi lokal |
| --- | --- |
| Sumber build | `f395e17064b5eacc5f9f0139f7362d1174c998c1`: commit snapshot QA bersih dari baseline repo `02ea3e4` ditambah implementasi smoke awal, **bukan commit pada branch pengguna**. Snapshot disimpan sebagai `iso/out/live-smoke-20261107/qa-source.bundle`; hash runner/probe yang dieksekusi dicatat terpisah dalam summary. |
| Build Linux | Arch Linux x86_64 dalam VM, kernel builder `7.2.14-arch1-1`, Archiso `92-1`; seluruh symlink overlay terlacak lolos staging dan build penuh exit 0. Metadata, versi paket, dan log ada di `iso/out/live-smoke-20261107/`. |
| Artefak | `constos-2026.11.07-x86_64.iso`, SHA-256 `5404cd4ea9978e82bd1c05a54cf1643123908f990d0999b8421d0d06d8f7c7f5`. Checksum dicocokkan dengan metadata sebelum boot. |
| Smoke QEMU/WHPX | Dua cold boot UEFI dengan 4 vCPU, 6 GiB RAM, grafis virtio, tanpa disk target: desktop dan console fallback lulus. Kernel live `7.3.1-1-cachyos-bore`; Foot, Wofi, Thunar, symlink systemd, nol unit gagal, DHCP, ZRAM `zstd`, dan pembacaan jurnal boot saat ini lulus. Bukti final di `iso/out/live-smoke-20261107/smoke-final/`; screenshot desktop, launcher, Thunar, dan TTY diperiksa. Input QMP memakai pasangan event tekan/lepas eksplisit, bukan timer pelepasan tombol virtual. |
| Penolakan | Checkout kotor ditolak dengan exit 1 dan metadata failure tanpa ISO; metadata dengan checksum ISO salah ditolak sebelum VM dijalankan. Bukti wrapper final ada di `iso/out/live-smoke-20261107/dirty-checkout-final.json`. |
| Native Linux/TCG — belum lulus | Builder tidak menyediakan akses `/dev/kvm`. QEMU Linux memerlukan modul virtio GPU dan VGA yang sudah ditambahkan ke prasyarat panduan. Percobaan TCG bertingkat terakhir berhenti sebelum probe setelah 900 detik; layar menunjukkan kegagalan `systemd-nsresourced`, `timesyncd`, dan job device node yang tidak selesai. Diagnostik ada di `iso/out/live-smoke-20261107/smoke-linux-input-events/`; ini bukan bukti kelulusan Linux/KVM atau masalah yang sudah diisolasi ke kode distro. |

Pada pengujian awal ini, workflow GitHub dan smoke Linux/KVM belum dieksekusi. Kelulusan Linux/KVM dicatat pada bukti integrasi berikutnya; workflow GitHub tetap memerlukan runner berlabel `constos-build`, keyring tepercaya, akses `/dev/kvm`, serta repository variables untuk pasangan firmware. Workflow menolak KVM yang tidak tersedia dan tidak beralih ke TCG. ShellCheck dan actionlint lulus pada konfigurasi runner awal yang terdaftar. Bukti awal tidak membuktikan perangkat fisik, audio, portal, lock/logout, screenshot pengguna, installer, atau seluruh gerbang Live Alpha. Prosedur pengulangan ada di [panduan build](docs/build-guide.md#build-tercatat-dan-smoke-live-uefi).

### Bukti integrasi Boot UI, desktop live, dan storage installer · 7 November 2026

Pelaksana: agen pengembangan pada sesi ini. Build dilakukan di VM builder Arch Linux x86_64 terisolasi (kernel `7.2.14-arch1-1`, Archiso `92-1`, keyring Arch dan CachyOS terverifikasi), lalu diuji pada host Linux CachyOS `7.3.1-1-cachyos` dengan akselerasi `/dev/kvm` dan OVMF non-Secure-Boot.

| Bukti | Hasil dan lokasi lokal |
| --- | --- |
| Sumber dan paket lokal | Snapshot QA bersih `82369b08258a8a4a9b9238546fb0abf474d4b3b9` disimpan sebagai `iso/out/integrated-20261107/qa-source.bundle` (**bukan commit pada branch pengguna**). `packages/build-local.sh` menghasilkan `constos-core-0.1.0-1-any.pkg.tar.zst` dan `constos-desktop-0.1.0-1-any.pkg.tar.zst` beserta `SHA256SUMS` dan `SOURCE_SHA256SUMS` (71 entri terverifikasi). |
| Build ISO penuh | `constos-2026.11.07-x86_64.iso`, SHA-256 `904474baa686417a959b5aaf35d11b41955420e3f575d2c5167b4b48f8171507`. Seluruh symlink overlay lolos staging, tidak ada konflik berkas paket, dan build penuh exit 0. Bukti di `iso/out/integrated-20261107/build/`. |
| Smoke Live UEFI (Linux/KVM) | `tests/live/uefi_smoke.py --accelerator kvm` lulus (`ok: true`): cold boot desktop (41,93 detik) dan console fallback (32,86 detik). Menu GRUB bertema ConstOS, autologin SDDM ke `constos.desktop`, Waybar/Foot/Wofi/Thunar bertema `design.md`, kernel `7.3.1-1-cachyos-bore`, nol unit gagal, DHCP, ZRAM `zstd`, dan pembacaan jurnal TTY1 lulus. Bukti dan screenshot di `iso/out/integrated-20261107/smoke-live/`. |
| Probe sesi, MIME, portal, dan screenshot | Dijalankan pada **ISO antara** SHA-256 `62fe8f2bb010f7b8122aa40770c0006d4021cc9ea6d1f4dd31c0c3bede405973`, bukan ISO final `904474...`: seluruh unit sesi dan PipeWire/WirePlumber aktif, MIME/GSettings sesuai, screenshot layar penuh menghasilkan PNG clipboard valid (19.582 byte), dan interface portal `FileChooser`, `ScreenCast`, `Screenshot`, serta `Settings` tersedia. Bukti di `iso/out/integrated-20261107/smoke-extended/extended-report.json`. Ini bukan bukti picker portal, kualitas isi gambar, atau kelulusan seleksi area/cancel interaktif. |
| Smoke storage installer | Juga memakai **ISO antara** `62fe8f...` pada VM KVM dengan disk kosong 32 GiB (`serial=CONSTOS-QA-EMPTY`): backend membuat GPT + ESP FAT32 + Btrfs `@`/`@home`/`@snapshots`, menghasilkan `fstab` UUID, menolak disk setelah tidak lagi kosong, dan melepas mount. Bukti di `iso/out/integrated-20261107/smoke-installer-storage/storage-report.json`. Instalasi paket, konfigurasi akhir, serta reboot target belum tercakup. |

Untuk installer, bukti artefak pada bagian ini berhenti di tahap storage. Lihat hasil instalasi penuh dan reboot pada build berikutnya di bawah. Skenario interaktif, recovery, dan rollback mengikuti [panduan pengujian terpadu](docs/acceptance-guide.md).

### Pembaruan logo Const · 7 November 2026

Pemilik perubahan: agen pengembangan, berdasarkan pilihan pengguna untuk memakai simbol Const dari README. Master `assets/const-logo.svg` berupa dua path vektor, menggantikan logo C geometris pada sumber boot/login. `assets/export-logo.py` menghasilkan PNG RGBA 160×160 untuk GRUB/Plymouth serta SVG hitam dan ikon badge; SDDM, README, installer, dan ikon hicolor memakai sumber yang sama. Asal dan audit izin redistribusi yang belum selesai tercatat di `assets/manifest.json`.

Pemeriksaan: render master/ekspor, regenerasi identik, paket lokal, staging profil live dan target, sintaks shell, `qmllint`, serta greeter SDDM nyata dalam test mode Xvfb 1280×800 lulus. Logo dan kontrol login terlihat tanpa clipping pada screenshot `iso/out/logo-20261107/greeter.png`; laporan staging dan hash ekspor ada di direktori yang sama. Tidak ada uji autentikasi atau boot ISO baru dalam pemeriksaan logo ini. ISO dengan checksum `904474...` di atas tetap memakai logo sebelumnya dan harus dibangun ulang sebelum menilai logo Const saat boot.

### Audit sebelum commit dan push · 7 November 2026

Audit read-only dibagi pada jalur installer/paket dan boot/desktop, kemudian perbaikan diintegrasikan oleh agen utama. Enam temuan kode diperbaiki: data override Calamares kini menyertakan branding/QML pada direktori yang sama; bootstrap memakai arsip transaksi preflight melalui `pacstrap -U` tanpa sinkronisasi repo baru; symlink identitas upstream yang belum dimiliki paket ditangani sebelum instalasi core; pesan pembatalan `selection cancelled` dari slurp dikenali; brightnessctl masuk paket desktop/manifest target; dan prefix staging installer dinormalisasi agar alias `/` ditolak.

Bukti di `iso/out/audit-5_jo_9qn/`: tujuh regresi keselamatan lulus, termasuk perubahan identitas disk dan perubahan byte arsip sebelum partisi. Kasus arsip berubah gagal pada sumber snapshot sebelumnya dan lulus setelah perbaikan. Smoke CLI dengan stderr pembatalan slurp yang sebenarnya membuktikan clipboard tetap utuh dan cancel tidak menjadi error; kegagalan koneksi compositor tetap dilaporkan. Resolver pacman aktual dari database lokal tanpa jaringan menghasilkan 602 nama arsip transaksi yang valid. Paket lokal dan staging data Calamares juga lulus. Pemeriksaan ini tidak membuktikan bootstrap penuh, autentikasi, atau reboot target.

**Blocker upstream yang dibuktikan:** `cachyos-calamares 3.4.2-4` serta `cachyos-calamares-next 3.4.2-13` meminta `libboost_python314.so.1.91.0`, sementara library/repo saat audit memakai 1.92. Smoke KVM terhadap ISO historis `904474...` dengan gate baru `installer_runtime` gagal secara benar pada `calamares --version` (exit 127); hasil ada di `live-runtime-gate/summary.json`. Kelulusan Live UEFI sebelumnya terjadi sebelum gate ini ditambahkan. Jangan menandai installer atau gerbang Live/Installable Alpha selesai berdasarkan bukti lama, membuat symlink lintas ABI, atau melakukan downgrade parsial untuk melewati kegagalan ini.

Regresi ada di `tests/installer/test_backend.py` dan dijalankan oleh workflow manual sebelum build paket. Audit ini tidak membangun ISO baru setelah pembaruan logo dan perbaikan sumber; seluruh penerimaan runtime perlu diulang pada artefak baru setelah blocker paket diselesaikan.

### Rebuild Calamares sesuai ABI repo · 7 November 2026

Pemilik: agen pengembangan. Builder disposable KVM memakai repo generik dengan urutan identik `iso/pacman.conf`, Boost `1.92.0-1`, Python `3.14.9-1`, Qt6 `6.12.0-3`, dan GCC `16.2.1`. `constos-calamares 3.4.1-1` dibangun dari commit CachyOS `199d71543db805fac2cc649ced72ad01dcb2c362` dengan checksum sumber terpin. Patch `qt-widgets.patch` menyatakan dependensi Qt Widgets yang hilang pada API Python fork tersebut; kompilasi sebelum patch gagal pada `qmessagebox.h`, sesudah patch lulus. Metadata paket memerlukan `libboost_python314.so=1.92.0-64` dan Python 3.14; `calamares --version` benar-benar berjalan di builder headless, tanpa symlink ABI/downgrade.

Snapshot QA bersih `bcfa77cbae41f39d0e7d39df76e3a4e0f348279c` berasal dari baseline `b945b7f` ditambah perubahan ini (**bukan commit pada branch pengguna**). Build penuh menghasilkan `constos-2026.11.07-x86_64.iso`, SHA-256 `25d571d2d3a4dabb5fb996ae6385d943538de7fd86c85e167a88a73fb429be07`. Paket lokal, bundle sumber, metadata build, serta log berada di `iso/out/installable-proof-yd8lkdgk/`.

Staging memakai arsip paket nyata; repo unsigned hasil build hanya tersedia bagi mkarchiso, bukan konfigurasi pacman live/target. Arsip berubah dan fingerprint sumber berubah masing-masing ditolak sebelum repo lokal dibuat. Tujuh regresi keselamatan installer, sintaks shell, YAML workflow, dan 38 tautan/anchor lokal pada enam dokumen lulus. Runtime ISO baru masih harus dibuktikan; hasil build ini belum mencentang gerbang Installable Alpha.

### Bukti penerimaan instalasi UEFI disk kosong dan reboot tanpa ISO · 7 November 2026

Pelaksana: agen pengembangan pada sesi ini. ISO final `constos-2026.11.07-x86_64.iso` dibangun dari sumber QA `eec441c2b940826f4785fec86a860a703f3d6b39` (**bukan commit pada branch pengguna**) dengan SHA-256 `64c26f4244d0fe4a4ce030bbbe153a8d0850c6e24bce4817241f10e437d9110f`. Seluruh verifikasi dijalankan di QEMU KVM dengan firmware OVMF x86_64 tanpa Secure Boot pada disk virtual terisolasi 40 GiB (`serial=CONSTOS-INSTALL-QA`), tanpa menyentuh disk fisik host.

| Tahap | Yang diperiksa | Hasil aktual dan bukti |
| --- | --- | --- |
| Preflight safety | Kegagalan koneksi/mirror selama unduhan 1,28 GiB sebelum partisi | Preflight menolak melanjutkan; disk diperiksa dengan `wipefs` dan `lsblk`, terbukti **nol signature, nol partisi, dan tidak ada mount** (`install-error-dialog.png`, `pacman.log`). |
| Cancel launcher | Pembatalan dialog disk dan penutupan wizard | Launcher membatalkan tanpa mengubah disk; `wipefs` dan marker mount bersih (`launcher-cancel.json`). |
| Wizard UI/UX | Welcome, Location, Keyboard, Users, Summary | Logo Const tampil tanpa clipping, locale Jakarta, model keyboard us, akun `qatester` tanpa autologin, summary tidak membocorkan password (`wizard-users.png`, `wizard-summary.png`). |
| Storage & Bootstrap | Pembuatan GPT, ESP 1 GiB FAT32, Btrfs subvolume `@`, `@home`, `@snapshots` | Mount aktif dengan kompresi `zstd:3` dan opsi `noatime`, paket dipasang melalui `pacstrap -U` dari arsip transaksi terverifikasi tanpa unduhan repo baru sesudah partisi (`storage-execution.json`). |
| Finalize & Recovery | SDDM session default, GRUB UEFI, mkinitcpio BORE, Snapper root config | Fallback removable GRUB terpasang, initramfs `7.3.1-1-cachyos-bore` dibuat, `09_constos_theme` diperbaiki (`set -e`), dan snapshot single #1 `Instalasi awal ConstOS` berhasil dibuat (`installed-system-acceptance.json`). |
| Reboot tanpa ISO | Cold boot VM dengan `-boot order=c` tanpa drive CDROM/ISO | UEFI membaca `\EFI\ConstOS\grubx64.efi` dari ESP, SDDM tampil dengan tema ConstOS dan form login akun `qatester` (`installed-boot-initial.png`, `installed-boot-screen-2.png`). |
| Login & Target State | Autentikasi akun baru, masuk desktop Hyprland, verifikasi sistem | Waybar, Foot, Wofi aktif (`installed-wofi-launcher.png`); `getent passwd liveuser` exit 2 (tidak ada akun live); `constos-calamares` tidak ada pada target (exit 1); `systemctl --failed` melaporkan 0 unit gagal; ZRAM dan NetworkManager aktif (`installed-verified-final.png`). |

Bukti lengkap, bundle QA sumber, log, dan rekaman screenshot tersimpan di `iso/out/installable-proof-yd8lkdgk/`. Batas bukti: belum menguji rollback bootloader Snapper, update transaksi penuh pada target terpasang, atau perangkat fisik (Wi-Fi/touchpad/baterai/brightness laptop).

### Bukti implementasi Rust collector (constd & constosctl) dan uji keselamatan Snapper · 7 November 2026

Pelaksana: agen pengembangan pada sesi ini. Audit terinci disimpan di `docs/audits/2026-11-07-system-recovery-and-rust-collector.md`.

| Komponen | Yang diperiksa | Hasil aktual dan bukti |
| --- | --- | --- |
| Invarian Snapper | Perlindungan subvolume `@snapshots`, pemanggilan `snapper --no-dbus -c root create-config /`, dan injeksi limit `NUMBER_LIMIT=10`, `TIMELINE_CREATE=yes`, `TIMELINE_CLEANUP=yes` | 12/12 uji unit `tests/installer/test_backend.py` dan `tests/installer/test_recovery.py` lulus (0,013s). Perbaikan pada `installer/scripts/backend.py` menjamin seluruh key limit selalu terinjeksi sekalipun template default upstream tidak menyertakannya. |
| Keselamatan Target | Penolakan kebocoran residu live environment pada target terpasang | Uji regresi membuktikan deteksi dan penolakan jika akun `liveuser` ditemukan di `/etc/passwd`, hook `archiso` di mkinitcpio, atau konfigurasi autologin di SDDM. |
| Rust Subsystem Collector | Parsing `/proc/stat`, `/proc/loadavg`, `/proc/meminfo`, `/sys/block/zram0/mm_stat`, dan `/proc/[pid]/stat` tanpa alokasi berat | Workspace `crates/const-collector` lulus 5 test suite lengkap dengan Linux fixture mock (`tests/fixtures_test.rs`, 0,00s). Deteksi kernel BORE, rasio kompresi ZRAM 4,0x, dan pembagian state proses terverifikasi. |
| CLI Diagnostik `constosctl` | Eksekusi mode tabel `constosctl status`, mode mesin `constosctl status --json`, dan `constosctl doctor` | Binary rilis berjalan langsung pada kernel host CachyOS: mendeteksi 12 CPU core, memori, ZRAM `zstd` rasio 4,25x (hemat 3,22 GiB), 0 failed systemd units, dan snapshot Snapper root aktif. |
| Daemon Sistem `constd` | Server HTTP zero-overhead melayani `GET /metrics` dan `GET /status` | Daemon terbukti melayani permintaan curl pada port uji dengan respons JSON `Const Tsukuyomi` berkecepatan mikrodetik dan memori < 3 MB. |

### Bukti ConstOS Doctor · 8 November 2026

Build lokal memakai checkout `9f66389` beserta perubahan Doctor dan Rust 1.99.1. Paket `constos-core-0.1.0-2-x86_64` memiliki SHA-256 `8428be6c5d29b39d6f12bbee5aefb1f2f17e92f9e08ee2c4fbe0da0506edcd68`. Checksum sumber dan log staging tersimpan di `iso/out/doctor-KzkwzHnR/`. Enam tes Rust dan 12 tes regresi installer lulus. Regresi Doctor membedakan systemd sehat, unit gagal, dan kueri systemd yang gagal dengan stdout kosong.

QEMU 11.1.3/KVM, OVMF x86_64, dan kernel guest `7.3.1-1-cachyos-bore` dipakai untuk boot dari salinan copy-on-write disk target QA 40 GiB tanpa ISO. Pacman memasang paket baru melalui `-U`, dan `/usr/bin/const` tercatat sebagai milik `constos-core`. Akun biasa memperoleh empat `PASS` dan exit `0` dari TTY serial. Unit uji yang sengaja gagal muncul dengan nama lengkap dan exit `1`. Hasil sehat juga tampil di Foot dalam sesi Hyprland. Bukti ada di `iso/out/doctor-KzkwzHnR/vm-retry/`. Pengujian ini membuktikan paket pada target terpasang. Staging diperiksa terpisah dari build ISO penuh dan instalasi baru.

### Bukti `const update` · 8 November 2026

Build memakai checkout `9f66389` beserta perubahan CLI, Rust 1.99.1, dan paket `constos-core-0.1.0-3-x86_64` dengan SHA-256 `ff3e5ffbbb2ac1f8a8c7bdf7ed7f2eb39b4becaa73c0377e4c89b0a1f240bc0e`. Delapan tes Rust, 12 tes installer, dan staging ISO lulus. Paket diuji pada salinan disk target QA 40 GiB di QEMU 11.1.3/KVM dan OVMF x86_64 tanpa ISO, melalui TTY dengan akun wheel dan autentikasi sudo. Guest memakai konfigurasi repo target dari checkout untuk percobaan online.

| Skenario | Hasil |
| --- | --- |
| Terminal noninteraktif, argumen tambahan, dan penanda live | CLI menolak sebelum menjalankan pembaruan. Penanda live disimulasikan pada target VM. |
| DNS gagal | Pacman gagal menyinkronkan repo, CLI meneruskan exit `1`, dan daftar paket terpasang tetap sama. |
| Batal pada konfirmasi | Menjawab `n` di konfirmasi instalasi menghasilkan exit `1` dan checksum daftar paket terpasang tetap sama. |
| Transaksi disetujui | Pacman memverifikasi paket dan mengganti `zlib` dengan `zlib-ng` serta `zlib-ng-compat` versi `2.3.3-2`. CLI meneruskan exit `0`. |
| Reboot dan sudah mutakhir | Cold boot dari disk yang diperbarui mencapai SDDM dan NetworkManager aktif. Doctor exit `0`. Pacman melaporkan tidak ada paket yang perlu diperbarui, dengan exit `0`. |

Build, checksum, log, dan ringkasan skenario ada di `iso/out/update-3nHlsQRA/`. Kernel `7.3.1-1-cachyos-bore` dan Firefox `159.0.1-1` sudah sesuai versi repo saat pengujian. Penerimaan upgrade kernel, kegagalan tanda tangan, disk penuh, dan rollback Snapper masih terbuka.

Audit sebelum push menemukan konfigurasi `makepkg` host memakai `target-cpu=native`. Resep `constos-core` kini menetapkan `target-cpu=x86-64`. Paket `constos-core-0.1.0-4-x86_64` (SHA-256 `61c4c7d61ecf6f52458daf05ca44ad48790ecf40269035bf682b7d86db61273f`) lulus build dan staging. Pada salinan target terpasang di QEMU/KVM dengan model CPU `qemu64` tanpa AVX, `const doctor` lulus dan `const update` melaporkan sudah mutakhir dengan exit `0`. Bukti ada di `iso/out/maintenance-audit-Fcogmel5/`.

## Target rilis

| Gerbang | Fase | Hasil yang bisa dipakai |
| --- | --- | --- |
| **A · Live Alpha** | 01 | ISO dari checkout bersih, sesi installer, dan konsol diagnostik bekerja di UEFI. |
| **B · Installable Alpha** | 02–05 | Satu build membuktikan wizard, instalasi disk kosong, reboot tanpa ISO, login SDDM dengan akun baru, sesi Hyprland, browser sesuai pilihan, aplikasi inti, dan snapshot awal Snapper. Bukti rollback dan perangkat fisik dicatat terpisah. |
| **C · Desktop Beta** | 06–10, termasuk 07A–07B | Shell minimalis dan Const Hub dengan aksi nyata, Const Store, dock dan Dynamic Island opsional, widget bawaan, capture pengguna, pemasangan aplikasi Windows teruji, serta hasil uji perangkat dan performa. Android mengikuti hasil penerimaan terpisah. |
| **D · Harness Beta** | 11–13 | Paket Linux Harness, draft widget dengan preview dan persetujuan, serta computer use lokal dengan scope, consent, Stop, dan batas kemampuan yang jelas. |
| **E · ConstOS 1.0** | 14–15 | Paket dan ISO bertanda tangan, update/rollback teruji, hardware yang didukung terdokumentasi, dan batas Harness dibuktikan di sesi Wayland nyata. |

Untuk 1.0, prioritaskan satu jalur resmi **UEFI x86_64 + Hyprland + CachyOS**. Jalur alpha memakai VM OVMF dan kemudian minimal satu laptop atau desktop fisik yang dicatat model GPU, storage, Wi-Fi, dan RAM-nya. Status NVIDIA, hybrid GPU, CPU lama, LUKS, dual boot, dan Secure Boot dilaporkan per skenario yang benar-benar lulus. Desktop dasar harus tetap bisa digunakan tanpa login Harness atau koneksi ke penyedia AI.

Nomor fase adalah urutan integrasi. Desain aset, prototipe shell, dan dokumen bisa berjalan bersamaan setelah fondasi yang dipakai masing-masing tersedia. Lakukan probe portal begitu sesi Wayland pertama bisa berjalan. Hasilnya menentukan scope Harness Beta sebelum tim mengerjakan UI izin dan kontrol input.

### Kontrak pelaksanaan

Setiap item yang mulai dikerjakan harus mencatat pemilik perubahan, dependensi, paket/file yang terdampak, bukti penerimaan, dan blocker. Centang berarti skenario penerimaan sudah dijalankan pada build yang dicatat; keberadaan konfigurasi atau paket saja belum cukup. Simpan SHA, versi paket, profil VM/perangkat, perintah/skenario, hasil, serta lokasi log atau media yang sudah diperiksa privasinya. Jangan masukkan ISO, model, atau rekaman mentah ke Git.

| Jalur | Dependensi dan prioritas |
| --- | --- |
| Live dan installer | P0 mencakup alur boot ISO, wizard, preflight, instalasi, reboot tanpa ISO, SDDM, dan Hyprland dari build yang sama. Tahapan, paket hari pertama, dan batas scope ada di [spesifikasi installer](docs/installer-plan.md). |
| Shell dan Const Hub | Buktikan launcher dan satu kontrol audio dengan provider bersama sebelum memperluas shell. Fase 04 menetapkan kontrak state, fase 06 menetapkan token, dan fase 07 mengganti satu permukaan pada satu waktu. Fase 08 memperluas collector untuk Monitor dan widget. |
| Welcome dan Const Store | Validasi Welcome pada target. Pakai katalog yang sama untuk Recommended Apps dan Const Store. Discovery dan transaksi milik Store, konfigurasi desktop milik Hub. |
| Capture pengguna | Screenshot dasar diuji di fase 02; fase 07A menyelesaikan UI serta rekaman video/audio sebelum Desktop Beta. Probe portal dilakukan lebih awal; fitur ini tidak menunggu Harness. |
| Kompatibilitas aplikasi | Fase 07B memakai installer target fase 03 dan launcher serta asosiasi file fase 02. Prioritaskan Windows, kemudian Waydroid opsional. |
| Dock, widget, dan Island | Dock memakai model aplikasi/jendela shell. Widget dan Island memakai sumber data fase 07–08. Dock dan Island dapat dimatikan secara independen. Indikator rekaman dan tombol Stop tersedia di luar Island. |
| Harness | Probe observasi/izin Wayland dapat dimulai saat sesi Hyprland target tersedia. Draft widget bergantung pada paket Harness dan schema widget, sehingga dapat dikirim terpisah dari computer use. Desktop, screenshot, dan recorder tetap bekerja tanpa agen. |

Arsitektur dan batas kepercayaan ada di [docs/architecture.md](docs/architecture.md). Kebijakan perubahan dokumen ada di [AGENTS.md](AGENTS.md); prosedur kerja tersedia melalui [SKILLS.md](SKILLS.md).

## Temuan dari Ryoku dan Const Harness

Referensi ini memakai Ryoku `v1.0.7` (`f7197d72d`) dan Const Harness dari monorepo `const` (`d77752fb`). Path di bawah relatif terhadap root repo masing-masing. [Audit desktop Ryoku](docs/audits/2026-11-08-ryoku-desktop.md) mencatat rujukan source, perbedaan dengan implementasi sekarang, dan pola yang dipilih untuk dock, Hub, Store, terminal, serta widget.

| Referensi yang dicek | Pola yang dipakai di ConstOS |
| --- | --- |
| Ryoku `installation/iso/build.sh`, `installation/tests/README.md`, `installation/backend/lib/filesystem.sh` dan `snapshots.sh` | Pisahkan staging, build ISO, dan instalasi target. Tes QEMU harus benar-benar melepas ISO, reboot, dan memeriksa filesystem, konfigurasi, serta paket hasil instalasi. |
| Ryoku `release/packages/ryoku-desktop/PKGBUILD`, `system/services/manifest.tsv`, `docs/updates.md` | Setiap default punya pemilik paket. Pengaturan pengguna diletakkan terpisah dari default paket. Enablement service, pengiriman konfigurasi, dan diagnosis drift memiliki alur yang bisa diuji. |
| Ryoku `ryoku/shell/plugin/systemmonitor.cpp` dan `docs/performance.md` | Pisahkan collector dari UI. Ukur PSS, CPU, wakeups, dan frame saat idle maupun saat panel terbuka sebelum menambah polling atau animasi. |
| Harness `apps/harness/desktop/package.json`, `apps/harness/DESIGN.md`, `apps/harness/UPDATES.md` | Desktop sekarang memakai Electron, React, TypeScript, Vite, dan `node-pty`. Build upstream punya target Linux pacman dan AppImage. Bawa style studio dan pola izin yang bisa dipahami, lalu buktikan paket Linux berisi runtime lengkap. Pada ConstOS, pacman menjadi pemilik update paket Harness. |
| Harness `apps/harness/desktop/native/README.md`, `native/computer-use-linux/runtime.py`, `electron/computer/computer-controller.ts` | Windows memakai PowerShell/Win32/UI Automation, macOS memakai Swift, dan Linux memakai Python/PyGObject/AT-SPI. Wayland saat ini mengiklankan aksi semantik terbatas. Pertahankan kontrak handshake, antrean request, lease, dan snapshot yang sudah ada saat menambahkan provider Wayland baru. |

## Pilihan arsitektur

**Pakai Rust untuk collector, CLI, dan helper computer use Linux.** Proses yang terpisah memberi tempat yang jelas untuk parsing bertipe, validasi request, pengelolaan file descriptor, dan lifecycle sesi. Izin Wayland ditentukan backend, compositor, dan consent. Performa diukur di fase 10. Konfigurasi Hyprland memakai Lua dan integrasi build memakai Archiso serta pacman.

| Keputusan | Arah yang dipakai untuk perencanaan | Cara menetapkan |
| --- | --- | --- |
| UI shell dan Settings | **Dux Shell** dengan preset Const dan UI QML yang dipatok. Wofi dapat membuka launcher cadangan saat IPC shell gagal. | Uji lifecycle, fokus, aksesibilitas, dan dua output. Kontrak Const Hub dan sinkronisasi Harness ditetapkan terpisah. |
| Sistem lokal | `const doctor` untuk diagnosis. Rust `constd` memakai collector bersama dan D-Bus sesi saat UI membutuhkan stream metrik. Jalankan collector sebagai user biasa. Beri aksi sistem yang perlu elevasi method bertipe dengan izin per operasi. | Kirim satu pembacaan dari CLI terlebih dahulu, lalu sambungkan UI ke kontrak yang sama. Definisikan versi schema, pemilik data, dan perilaku saat service mati. |
| Harness desktop | Paketkan Electron yang ada terlebih dahulu. Tambahkan adapter Rust Wayland melalui host lokal yang ada. Tauri dapat dievaluasi belakangan untuk mengganti host desktop sambil memakai UI React yang kompatibel. | Keputusan pindah host memakai hasil pembandingan PTY, browser pane, streaming chat, storage/session restore, plugin/MCP, packaging, aksesibilitas, dan footprint. WebView tetap perlu diuji pada setiap platform yang didukung. [Arsitektur Tauri](https://v2.tauri.app/concept/architecture/) |
| Paket dan konfigurasi | Konfigurasi vendor dipasang lewat paket. Preferensi per-user memakai XDG config dengan schema versi. Data aplikasi, state, dan runtime dipisahkan. | Pakai paket yang sama untuk file yang memang dibagikan live/installed. Seeder hanya membuat file awal yang belum ada. Uji upgrade dari versi lama, config rusak, dan reset satu kelompok preferensi. |
| Izin computer use | Harness membuka helper user-session yang ditentukan paket melalui inherited stdio. Helper menerima izin sementara dari UI/portal dan melakukan pemeriksaan scope untuk setiap aksi. | Validasi satu target app dan satu sesi per lease. Backend mendeteksi kemampuan aktual dan menyajikan opsi yang tersedia. Hak root, listener jaringan, dan akses input global tanpa consent berada di luar kontrak. [RemoteDesktop portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html) |

Batas proses, kepemilikan konfigurasi, dan pemisahan capture pengguna dari computer use dijelaskan di [arsitektur ConstOS](docs/architecture.md). Tabel di atas mencatat keputusan yang harus dibuktikan selama integrasi, bukan daftar fitur yang semuanya sudah tersedia.

Gunakan `iso/`, `installer/`, `desktop/`, dan `packages/` sesuai tanggung jawab saat ini; `tests/live/` menampung build tercatat dan smoke UEFI. Tambahkan `system/` untuk kebijakan target dan `crates/` untuk kode Rust ketika dibutuhkan. Sumber helper Linux diusulkan berada di ConstOS dan dikirim sebagai paket versi tersendiri. Monorepo Harness memiliki adapter konsumennya. Tetapkan satu artefak binary per versi untuk kedua repo.

## Fase 01 · Boot UI dan bukti live boot

Audit 8 November 2026 pada perubahan di atas `9f66389a2` menguji tema greeter QML dengan Qt 6.12 offscreen dan model SDDM simulasi pada host Windows. Enam skenario lulus, mencakup akun tunggal pada login pertama, riwayat valid atau usang, fokus/Enter/Tab, percobaan ulang, opsi masuk, dan kondisi tanpa sesi. Autentikasi PAM, boot ISO, serta login target dengan tema baru tetap menunggu VM Linux UEFI. Suite 13 uji installer dengan operasi sistem disimulasikan juga lulus, termasuk penolakan penyiapan Snapper ketika mountpoint yang dilepas masih berisi data.

Pemeriksaan lanjutan pada host Windows membuktikan pemisahan keluaran helper staging live dan installed, urutan impor environment sebelum aktivasi sesi, sintaks shell/Python, dan 19 uji unit installer serta katalog dengan backend sistem disimulasikan. Uji GTK 4.24.1 di Windows membuka halaman Welcome dan katalog, melewati tur, mencoba kembali pemasangan yang gagal, serta membuka kedua halaman secara manual. Transaksi Flatpak pada uji GTK disimulasikan. Seleksi tiga entri dan deteksi dialog installer diuji dengan masukan OCR simulasi. Build Linux, cold boot ISO baru, login PAM, dan pemasangan Flatpak nyata masih menjadi gerbang penerimaan.

Revisi kiosk di atas commit `bcd137b2` mengikuti laporan pengguna dari VM. Pada host Windows, staging helper memisahkan sesi Cage live dari Hyprland dan Welcome terpasang. Simulasi launcher membuktikan bahwa kegagalan installer kembali ke layar tindakan dan dapat dicoba ulang. Pemeriksaan sintaks shell, Python, dan Rust, 19 uji unit installer/katalog, enam skenario Qt greeter, serta interaksi Welcome berbahasa Inggris di GTK 4.24.1 lulus. Bukti runner baru sebatas seleksi dua entri dan deteksi teks dialog dengan OCR simulasi. Build Linux, uji boot Cage, dan instalasi UEFI dengan ISO revisi masih terbuka.

- [x] **Build baseline.** Build penuh di Linux menghasilkan ISO dengan checksum terverifikasi. Boot normal dan console fallback lulus di QEMU/OVMF.
- [x] **Runner smoke lokal.** Build tercatat dari checkout Linux bersih dan dua cold boot QEMU/OVMF menguji kernel, symlink systemd, SDDM, tiga shortcut, DHCP, ZRAM, serta jurnal TTY. Lihat bukti 7 November di atas; workflow GitHub dan hardware tetap belum lulus.
- [ ] **Tema GRUB.** Verifikasi dua entri bahasa Inggris, timeout, kontras, navigasi keyboard, logo, kernel/initramfs, dan fallback teks.
- [ ] **Boot langsung ke installer.** Pengguna melaporkan ISO sebelumnya membuka desktop di belakang installer. Sumber baru memakai **Install ConstOS** sebagai default dan menjalankan TUI dalam sesi Cage/Foot khusus. **ConstOS Diagnostics** membuka TTY. Pendekatan sesi installer mengikuti pemisahan yang ditinjau pada [Ryoku v1.0.7](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/installation/README.md). Uji cancel, buka ulang, kegagalan preflight, serta pemasangan sampai login dari disk.
- [ ] **Splash Plymouth.** Mulai dari satu logo dan indikator progres ringan. Integrasikan hook dan tema ke initramfs sesuai profil live serta preset target ketika installer tersedia. Pastikan log bisa dilihat, prompt disk terenkripsi tetap muncul saat fitur itu diaktifkan, dan perangkat tanpa grafis tetap memiliki jalur teks. [Plymouth](https://wiki.freedesktop.org/www/Software/Plymouth/) · [mkinitcpio](https://man.archlinux.org/man/mkinitcpio.8.en)
- [ ] **Greeter SDDM.** Jalur normal menampilkan akun tunggal atau akun terakhir yang masih tersedia, dengan fokus ke kata sandi. Pilihan akun, sesi, dan layout tersedia di **Sign-in options**. Jika belum ada pilihan akun yang jelas, tampilkan pemilih akun sejak awal. Uji password salah/benar, navigasi keyboard, power menu, dan tema stock pada target terpasang. Autologin `liveuser` hanya di ISO. [SDDM](https://github.com/sddm/sddm)
- [ ] **Boot asset kit pertama.** Mulai dari logo di `assets/` dan warna studio. Siapkan logo transparan kecil untuk initramfs, latar statis GRUB, dan latar greeter dengan crop untuk 16:9 serta layar lebih sempit. Jadikan generasi gambar sebagai tahap desain, lalu commit hanya ekspor yang dipakai dan manifest asalnya.

**Fase lulus jika** ISO dari checkout bersih membuka installer dalam sesi khusus dan **ConstOS Diagnostics** bisa membaca `journalctl -b`. Periksa bahasa Inggris pada boot, dialog installer, dan jalur login default. Simpan tangkapan layar per tahap serta catatan durasi. [Profil Archiso](https://github.com/archlinux/archiso/blob/master/docs/README.profile.rst)

## Fase 02 · Aplikasi bawaan dan layanan sesi

- [ ] Pisahkan manifest menjadi **live**, **installed core**, dan **opsional** saat installer mulai memakainya. Core live mengambil paket untuk sesi dan diagnosis. Installed core menambah kebutuhan harian yang dipilih. Toolchain pengembangan, Harness, model lokal, dan aplikasi besar memakai profil opsional dengan ukuran yang terlihat.

| Kelompok | Pilihan awal | Alur yang harus bekerja |
| --- | --- | --- |
| Desktop inti | Kitty, Fish, Nautilus, Dux Shell, Wofi cadangan | Buka terminal, file manager, launcher, notifikasi, dan lock/logout dari keyboard maupun mouse. |
| Harian | Firefox direkomendasikan, Chromium, Zen, atau No browser. Nautilus, Mousepad, Ristretto, Evince, File Roller, dan mpv tersedia di manifest. | Buktikan setiap pilihan browser, MIME, dan playback. |
| Integrasi perangkat | NetworkManager, BlueZ dengan UI pairing yang diuji, PipeWire/WirePlumber, pavucontrol, portal Hyprland/GTK | Wi-Fi, pairing yang didukung, pengalihan audio output, file chooser, screen share, dan clipboard Wayland. |
| Diagnostik | `btop`, `fastfetch`, utilitas disk, serta `const doctor` pada sistem terpasang | Lihat status hardware, kernel, memory, storage, dan log kegagalan dari TTY. |
| Opsional | Dev toolchain, editor IDE, aplikasi Flatpak pilihan, Const Harness, serta engine/model lokal | Satu jalur pemasangan per aplikasi, ukuran dan dependensi tercatat, dan ada jalur uninstall yang mempertahankan data pengguna. |

- [ ] Periksa launcher `.desktop`, nama icon, kategori, file yang dipasang, dan `mimeapps.list`. Pastikan setiap menu menunjuk ke executable yang benar. Pilih backend portal secara eksplisit per interface setelah menguji sesi yang diluncurkan SDDM. [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/) · [portals.conf](https://flatpak.github.io/xdg-desktop-portal/docs/portals.conf.html)
- [ ] Definisikan service system dan user yang perlu aktif. Pisahkan autostart compositor dari service yang butuh supervisi. Impor env Wayland dari sesi aktual, hindari asumsi `wayland-1`, dan uji logout/login berulang agar proses panel, tray, dan notifikasi tidak ganda.
- [ ] Uji screenshot `Print` dan aksi launcher: area yang dipilih sesuai hasil clipboard, Escape membatalkan tanpa menimpa clipboard, dan kegagalan tool terlihat. Catat perbedaan konfigurasi Lua yang di-stage dengan konfigurasi `.conf` lama; hanya jalur yang benar-benar dimuat boleh diklaim didukung.
- [ ] Uji input teks beraksen/non-Latin, font fallback, pemilihan layout, mount/eject media lepas-pasang, trash, secret agent, dan dialog otorisasi dari sesi SDDM. Pilih paket tambahan berdasarkan skenario yang didukung; jangan menganggap toolkit otomatis menyelesaikan integrasi sesi.

**Fase lulus jika** desktop terpasang pada VM bisa membuka halaman lokal dari browser yang dipilih, mengakses file dan arsip, menyalin teks/gambar, memindah audio output, dan menjalankan diagnosis dasar. Jalur **No browser** tetap bisa memakai desktop inti. Catat paket opsional dan pengaruhnya pada ukuran instalasi.

## Fase 03 · Installer, sistem terpasang, dan recovery

- [x] **Buktikan jalur utama di VM UEFI.** Build P0 9 November dan kandidat 10 November masing-masing mencakup Cage dan Calamares, pemilihan satu disk kosong, instalasi, unmount, **Restart**, boot tanpa ISO, dan login SDDM ke Hyprland.
- [ ] **Lengkapi penerimaan wizard.** Gunakan [urutan wizard](docs/installer-plan.md#langkah-wizard-dan-keputusan-ui) untuk Network, pemilih locale/zona waktu, pilihan browser, retry sebelum partisi, dan skenario dua disk. Pertahankan preflight jaringan, waktu, keyring, storage, dan sumber paket sebelum partisi.
- [ ] **Pisahkan live dan installed.** Target menggunakan manifest dan paket konfigurasi yang ditentukan installer. Hapus akun live, autologin, aturan sudo live, unit khusus ISO, serta repo file sementara dari target. Aktifkan NetworkManager, display manager, dan layanan sesi yang diperlukan lewat jalur instalasi yang sama di VM dan perangkat fisik.
- [ ] **Paket target dan browser.** Pilihan browser sudah masuk transaksi target. Firefox dan **No browser** lulus uji VM. Ulangi instalasi dan periksa handler pada akun baru untuk Chromium dan Zen. Fase 14 membawa jalur paket lokal ke penerbitan, penandatanganan, dan rotasi keyring.
- [ ] **Disk kosong dan Review.** Pindahkan konfirmasi akhir dari kolom path ke aksi **Install ConstOS** di Review sesuai [kontrak pemilihan disk](docs/installer-plan.md#kontrak-pemilihan-disk). Pertahankan GPT, ESP, Btrfs dengan `@`, `@home`, dan `@snapshots`. Buktikan penolakan saat identitas berubah serta verifikasi mount, UUID, `fstab`, initramfs, dan bootloader target.
- [ ] **Uji recovery.** Buat konfigurasi Snapper dan retensi yang terbatas. Uji restore satu file, lalu satu recovery sistem yang benar-benar bisa boot. Dokumentasikan batas snapshot untuk ESP, `/boot` terpisah, data pengguna, dan layanan dengan state eksternal. Simpan prosedur rescue dari ISO/TTY saat greeter atau compositor gagal.
- [ ] **Perluas mode satu per satu.** LUKS masuk setelah prompt unlock, suspend/reboot, dan recovery diuji. Offline install memakai snapshot paket dan keyring yang tersedia di ISO atau mekanisme lain yang dipilih dan diverifikasi. Dual boot masuk setelah uji OVMF dan disk dengan partisi yang harus dipertahankan.

**Fase lulus jika** tes QEMU melakukan instalasi, melepas ISO, reboot, login ke akun baru, dan memverifikasi kernel, jaringan, desktop, filesystem, ZRAM, serta update dari repo yang dipercaya. Simulasikan mirror gagal dan satu kegagalan instalasi yang dapat didiagnosis. Uji recovery hingga sistem masuk lagi.

## Fase 04 · Const Hub dan tindakan sistem

- [ ] Buat spike UI kecil untuk **Display**, **Audio**, dan **About**. Sambungkan masing-masing ke sumber data nyata. Tetapkan navigasi, pencarian Settings, error message, dan satu komponen form yang mendukung keyboard. Mulai About dari `os-release`, versi kernel/compositor, dan petunjuk diagnosis. Kaitkan ke Doctor lengkap pada fase 08.

| Halaman | Kontrol tahap pertama | Pemilik state atau aksi |
| --- | --- | --- |
| Display & Input | Scale, resolusi, refresh rate, posisi monitor, layout keyboard, touchpad, aksesibilitas | Hyprland dan konfigurasi per-user. Mode display disimpan setelah pengguna memilih **Keep** dalam countdown. Gagal atau timeout mengembalikan layout sebelumnya. |
| Audio & Perangkat | Volume, mute, input/output, brightness, Bluetooth status | PipeWire/WirePlumber, backlight yang tersedia, dan BlueZ. UI menampilkan perangkat yang hilang dan status izin. |
| Network | Wi-Fi, koneksi aktif, detail dasar, buka editor jaringan | NetworkManager. Kredensial dikelola oleh dialog/secret agent yang sesuai. |
| Appearance & Desktop | Tema, wallpaper, aksen, ukuran UI, reduced motion, panel, keybinds, widget, toggle Dock dan Dynamic Island | Default paket dan override pengguna mengikuti [design.md](design.md). Preview dapat dibatalkan. Konflik keybind terlihat sebelum Apply. |
| Terminal | Font dan ukuran, profil warna, bentuk kursor, dan riwayat scrollback Kitty | Default vendor dan override per-user. Fish menjadi login shell awal. |
| Power, Privacy & Session | Battery dan profil yang tersedia, idle/lock, notifikasi, akses computer use | UPower/logind, satu pengelola power profile, dan izin sesi Harness. Tombol Stop/revoke mengikuti status nyata. |
| System | About, status update, shortcut ke System Monitor dan Doctor, lokasi log | CLI `const`, sistem paket, dan service terkait. Kontrol sensitif dirilis setelah kebijakan serta pemulihannya lulus. |

- [ ] Buat kontrak bertipe untuk nilai, capability, perubahan, dan error. UI hanya menawarkan aksi yang valid untuk hardware dan sesi. Simpan user prefs dengan penulisan atomik dan migrasi schema yang bisa diuji ulang. Sediakan reset per bagian dan back up preferensi lama sebelum migrasi.
- [ ] Gunakan provider yang sudah menguasai subsistem melalui API atau adaptor sempit. Jalankan perubahan tingkat user dalam sesi. Untuk aksi sistem yang dipilih, pakai mekanisme otorisasi per operasi dan tampilkan kegagalan tanpa mengubah status UI menjadi sukses.
- [ ] Definisikan provider minimum dan schema state sebelum spike UI: capability, nilai aktual, aksi pending, error, dan resync. UI tidak membaca metrik hardcode atau menjalankan string shell dari input pengguna. Perluas kontrak ini di fase 08, bukan membuat collector kedua.
- [ ] **Migrasi preferensi.** Inventarisasi konfigurasi dari `/etc/skel` yang sudah disalin ke home pengguna. Buat cadangan dan migrasi idempoten untuk file yang mulai dikelola. Uji akun lama yang punya edit lokal, akun baru, dan reset dari Hub.

**Fase lulus jika** halaman Settings dapat apply/cancel dan mengembalikan layout display. Uji restart sesi, pengguna kedua, preferensi rusak, hardware hilang, dan perubahan dari luar UI. Pakai kontrak state yang sama untuk menu cepat ketika menu itu dihubungkan di fase 07.

## Fase 05 · Dokumentasi penggunaan dan pengembangan

- [ ] Perbarui README agar membedakan fitur yang sudah tersedia, diuji, dan direncanakan. Pertahankan `docs/build-guide.md` sebagai jalur build yang dapat direproduksi. Buat panduan install/first login, shortcuts, hardware/known issues, recovery, dan alur update ketika tiap fitur sudah bisa dijalankan.
- [ ] Buat panduan pengembangan untuk layout repo, pengiriman file via paket, pemisahan overlay live dan target, schema Settings, dan cara menjalankan tes VM. Simpan keputusan besar seperti pilihan shell, filesystem, dan provider computer use dengan pilihan, konsekuensi, dan hasil uji.
- [ ] Rapikan lisensi proyek dan inventaris komponen/aset. Saat mengadaptasi kode atau tema dari Ryoku, CachyOS, atau repo lain, catat path sumber, commit/tag, notice, lisensi, dan perubahan yang dibuat. Catat juga asal serta izin redistribusi font, icon, wallpaper, dan binary yang dipaketkan.
- [ ] Sediakan panduan pengguna dan pengembang dalam bahasa Indonesia, serta English untuk antarmuka/help utama. Petakan dokumen dukungan ke log yang dibutuhkan dan cara meredaksi nama pengguna, token, SSID, dan path sensitif.
- [ ] Terapkan matriks sinkronisasi di [AGENTS.md](AGENTS.md) sejak perubahan pertama, bukan menunggu fase dokumentasi selesai. README menyimpan status pengguna, roadmap menyimpan pekerjaan/bukti, arsitektur menyimpan batas komponen, dan skill menyimpan prosedur. Perbarui hanya sumber yang terdampak dalam perubahan yang sama.

**Fase lulus jika** pengguna atau kontributor baru mengikuti panduan dari clone atau ISO baru hingga login dan bisa menemukan prosedur diagnosis/recovery. Catat langkah yang gagal dan perbaiki dokumentasinya sebelum memberi label Installable Alpha.

## Fase 06 · Desain menu, identitas, dan pipeline aset

Acuan awal tersedia di [design.md](design.md): identitas hitam/putih, aksen biru, token warna, tipografi, style komponen, serta kontrak preview dan tema adaptif dari wallpaper. Ini keputusan desain, bukan tema yang telah diterapkan atau kelulusan fase. Penyusunan desain dimulai sebelum integrasi fase 06 dan tidak menghambat installer.

- [ ] Implementasikan token pada [design.md](design.md) sebagai satu sumber versi. Review palet, tipografi, spacing, radius, fokus, motion, dan state pada prototype sebelum menerapkan adapter GTK, Qt, Kitty, SDDM, serta shell. Boot/greeter memakai palet vendor statis; preferensi sesi pengguna tidak dibaca sebelum login.
- [ ] Buat wireframe yang saling terhubung untuk **Launcher**, **Quick Settings**, **Notification Center**, **Workspace/Tray**, **Power/Session**, **Desktop Context Menu**, **Welcome**, **Const Hub**, **Const Store**, **Dock**, dan **Dynamic Island**. Bedakan permukaan yang selalu terlihat, yang muncul atas interaksi, dan yang boleh mengambil keyboard focus. Gunakan satu skala dan satu aturan closing lewat Escape atau klik luar.
- [ ] Pakai ImageGen nanti untuk eksplorasi wallpaper, tekstur, ilustrasi onboarding, dan latar boot/login. Simpan shortlist dan render final yang disetujui. Pakai vektor yang terbaca untuk ikon aksi serta logo, dengan raster fallback jika format boot membutuhkannya. Ekspor varian light/dark, crop untuk layar berbeda, dan ukuran yang sesuai target.
- [ ] Tetapkan manifest aset berisi ID stabil, pemilik paket, penggunaan, sumber/versi, lisensi/izin redistribusi, file editable, ekspor, dimensi, dan varian. Audit juga logo yang sudah ada; sumber yang belum diketahui dicatat sebagai blocker rilis, bukan diberi lisensi asumsi. Uji keterbacaan teks, kontras, font/cursor/icon fallback, ukuran initramfs, dan tampilan 100–200% scaling. Pastikan aset tersedia dalam paket serta initramfs yang memakainya.
- [ ] Buat katalog surface dan state untuk greeter, lockscreen, launcher, panel, Settings, dialog izin, capture toolbar/preview, recorder, pemilih widget, OSD volume/brightness, serta notifikasi. Catat aksi masuk/keluar, pemilik fokus, Escape/Back, tab order, state loading/error/denied, dan perilaku saat monitor hilang. Review alur lengkap, bukan hanya screenshot layar utama.
- [ ] Uji aksesibilitas spike QML sebelum mengunci toolkit: nama/role kontrol, fokus terlihat, keyboard-only, pembaca layar, kontras, ukuran teks besar, dan reduced motion. Jika jalur aksesibilitas gagal, evaluasi toolkit alternatif sebelum memperluas shell. String UI harus dapat diterjemahkan dan diuji dengan label panjang.
- [ ] Versikan token desain dan aturan ekspor. Paket memasang default vendor; wallpaper atau tema pilihan pengguna tidak ditimpa update. Build memakai ekspor yang dikomit dan tidak membutuhkan akun atau layanan generasi gambar.
- [ ] Implementasikan pilihan aksen Default, Manual, dan Wallpaper sesuai design.md melalui pemilik preferensi tema yang sama. Uji kontras palet hasil, preview/apply/cancel, persistensi, reset, gambar grayscale/rusak/hilang, sumber multi-monitor, dan kegagalan adapter. Pertahankan tema terakhir yang valid saat generasi gagal; mode manual tidak boleh berubah karena wallpaper. Catat toolkit yang membutuhkan reload atau tidak mendukung sinkronisasi.

**Fase lulus jika** review screenshot atau prototype mencakup boot, greeter, desktop, launcher, dan Settings dalam satu alur. Sediakan desain untuk state kosong, error, panjang teks terjemahan, keyboard-only, dan monitor kecil sebelum komponen dipoles.

## Fase 07 · Fungsi di balik menu dan shell

| Menu | Perilaku pertama yang dikirim |
| --- | --- |
| Launcher | Cari aplikasi, buka shortcut Settings dan Monitor, dukung riwayat/pinned items dan keyboard. Pakai mekanisme Desktop Entry untuk meluncurkan aplikasi. Sumber pencarian file/command dapat ditambahkan setelah ada opt-in dan batas direktori. |
| Quick Settings | Wi-Fi, Bluetooth, volume, brightness, Do Not Disturb, battery/power. Klik aksi memberi status pending lalu mengikuti state backend. Klik detail membuka halaman Settings terkait. |
| Notification Center | Tampilkan notifikasi, aksi asal, dismiss, dan DND. Pilih satu pemilik `org.freedesktop.Notifications` per sesi. Riwayat lokal punya batas dan dapat dihapus. |
| Workspace, tray, context | Pindah workspace, buka item tray, menu desktop untuk wallpaper/widgets/Settings, dan menu aplikasi dengan aksi yang didukung. Adapter Hyprland membaca event dan melakukan resync setelah compositor restart. |
| Power & Welcome | Lock, logout, suspend, reboot, shutdown dengan state capability dan konfirmasi yang sesuai. Welcome memperkenalkan pintasan dasar, bisa dilewati atau dibuka lagi, dan nantinya membuka rekomendasi di Const Store. |
| Dock aplikasi | Dock bawah opsional menampilkan pin, aplikasi yang berjalan, dan jendela yang dikelompokkan. Klik membuka atau memfokuskan aplikasi, keyboard dapat berpindah antarjendela, dan launcher tetap dapat dibuka saat dock dimatikan. |
| Const Store | Katalog, pencarian, dan Library untuk aplikasi Flathub terkurasi. Mulai dari daftar Recommended Apps. Tampilkan sumber, scope, progres, dan hasil transaksi. Pengaturan aplikasi maupun tampilan desktop tetap di Const Hub. |
| Clipboard dan OSD | Pilih/paste/hapus item teks atau gambar dari UI dengan batas riwayat, opsi menonaktifkan penyimpanan, dan clear. Jangan tampilkan riwayat di lockscreen. OSD volume, mute, dan brightness mengikuti state backend tanpa mencuri fokus. |
| Capture | Shortcut, launcher, dan panel membuka alur screenshot atau recorder yang sama. Panel menampilkan sumber, durasi, mute, dan Stop berdasarkan status nyata dari fase 07A. |

- [ ] Bagikan registry aksi dan state dengan Settings, keybind, widget, serta Island. Gunakan ID aksi dan parameter tervalidasi, dengan label terjemahan terpisah. Aksi UI memanggil adapter yang punya batas, agar string pencarian dan isi notifikasi tidak menjadi perintah shell.
- [ ] Uji perpindahan bar, launcher, dan notifikasi ke Dux dari satu sesi terpasang. Sediakan sesi fallback untuk pemulihan dari TTY. Pastikan applet tray, auth agent, dan notification daemon hanya dimulai sekali.
- [ ] **Onboarding target.** Sumber GTK dan paket sudah tersedia. Buktikan Welcome muncul satu kali per akun, bisa dibuka ulang, dan katalog Flathub memasang serta membuka aplikasi aktual. Jalankan skenario offline, retry, dan akun kedua sesuai [panduan penerimaan](docs/acceptance-guide.md#welcome-dan-recommended-apps).
- [ ] **Const Store.** Selaraskan scope, origin, dan ref antara daftar aplikasi terpasang dan aksi per-user. Pakai satu backend untuk halaman rekomendasi dan Library. Uji install, buka, update, hapus, offline/retry, serta aplikasi yang juga terpasang system-wide atau pada branch berbeda. Pacman dan `const update` tetap mengelola paket OS.
- [ ] **Dock aplikasi.** Mulai di monitor utama dengan pin per akun, satu tombol per aplikasi, dan pengelompokan jendela. Uji pencocokan Desktop Entry dengan app ID, pemindahan fokus, layar penuh, hotplug, serta pelepasan input mask dan reservasi tepi ketika dimatikan.

**Fase lulus jika** setiap item yang terlihat punya fungsi atau alasan disabled, hasilnya tampil kembali di UI, dan fokus pulih ke aplikasi sebelumnya setelah panel ditutup. Uji input cepat, monitor dicabut, daemon restart, izin ditolak, serta bahasa dengan label panjang.

## Fase 07A · Screenshot, rekaman video, dan rekaman audio

Ini fitur pengguna desktop, terpisah dari observasi agen di fase 12. Gunakan aplikasi/backend Wayland yang sudah tersedia sebelum menulis encoder atau layanan capture sendiri. `grim`/`slurp` adalah baseline screenshot saat ini; kandidat recorder dipilih setelah uji portal, audio, format, dan konsumsi resource pada build target. Tidak ada dukungan window/region, pause, encoder hardware, atau audio sistem yang diklaim hanya karena paket terpasang.

| Alur | Kontrak pengguna dan bukti penerimaan |
| --- | --- |
| Screenshot | Pilih layar, window, atau area sejauh backend mendukung; opsi cursor dan countdown; Escape membatalkan. Preview menyediakan copy, simpan PNG, buka folder, serta anotasi crop/panah/teks/redaksi melalui editor yang dipilih. Redaksi harus menjadi piksel pada berkas ekspor, bukan layer yang bisa dibuka lagi. Cocokkan isi/dimensi hasil dengan target, termasuk dua monitor, skala campuran, dan koordinat negatif. Mode tak didukung tidak ditawarkan. |
| Rekaman video | Pilih sumber dan kualitas/resolusi/FPS dari kemampuan aktual; tampilkan countdown, indikator aktif, durasi, dan Stop. Pause/resume hanya ditawarkan bila backend mendukung. Pilihan audio terpisah: tanpa audio, mikrofon, audio sistem, atau keduanya jika tersedia. Setelah Stop, tunggu finalisasi lalu buka hasil dari file manager dan putar video/audio untuk memeriksa durasi, frame, serta sinkronisasi A/V. |
| Rekaman audio | Alur audio-only tidak meminta izin layar. Pilih mikrofon atau sumber audio sistem yang tersedia, tampilkan level input, mute, durasi, dan Stop; kontrol gain memakai sumber perangkat yang sesuai. Pilih format ekspor serta sample rate/channel yang benar-benar didukung. Putar ulang hasil dan periksa channel, durasi, clipping, dan sumber yang direkam. |
| Penyimpanan dan berbagi | Gunakan direktori XDG Pictures/Videos/Music dengan subfolder ConstOS yang terlihat dan dapat diubah; jika belum dikonfigurasi, tawarkan lokasi simpan. Nama unik tanpa overwrite diam-diam, pratinjau lokasi, buka folder, dan copy sesuai tipe hasil. Hasil tetap lokal; upload dan pengiriman ke Harness membutuhkan tindakan serta izin terpisah. |

- [ ] Pilih satu jalur resmi untuk screenshot + editor, video recorder, dan audio recorder. Catat versi, paket, lisensi/codec, portal/direct-compositor access, dan alasan pilihan. Uji software encoding sebagai baseline; opsi hardware hanya masuk dukungan setelah diverifikasi. Jangan menambah dependensi aplikasi besar ke ISO tanpa mencatat ukurannya.
- [ ] Tetapkan pemilik sesi recorder dengan status `idle`, `selecting`, `countdown`, `recording`, `paused` bila didukung, `stopping`, `finalizing`, `completed`, `cancelled`, dan `failed`. Transisi mengikuti backend; Cancel tidak sama dengan sukses dan Stop belum berarti berkas siap. Batasi satu sesi rekaman yang dikelola UI per pengguna; percobaan kedua menawarkan kembali ke sesi aktif, bukan membuat proses tersembunyi.
- [ ] Pisahkan izin layar, mikrofon, audio sistem, dan akses berkas. Portal menampilkan picker untuk jalur yang memakainya; shortcut screenshot compositor harus dijelaskan sebagai akses sesi lokal, bukan dianggap dibatasi portal. Rekaman pengguna tidak memberi grant computer use kepada agen. Indikator/Stop harus tetap bisa dijangkau tanpa Island dan tanpa jendela recorder mendapat fokus.
- [ ] Saat lock atau logout dimulai, hentikan capture dan lepaskan akses sumber; finalisasi hasil yang sudah diperoleh jika memungkinkan. Revoke menghentikan sumber terkait; kehilangan sumber wajib menghentikan rekaman dengan alasan yang jelas. Jangan beralih ke mikrofon/output lain secara diam-diam dan jangan melanjutkan rekaman otomatis setelah unlock/relogin. Pada suspend atau crash, dokumentasikan apakah hasil parsial dapat dipulihkan.
- [ ] Tangani picker ditolak/dibatalkan, portal/encoder mati, device unplug, monitor dicabut, direktori tidak writable, disk penuh, dan kegagalan finalisasi. Jangan menampilkan notifikasi sukses sebelum berkas valid. Hapus sementara yang tidak diperlukan, tetapi jangan membuang hasil parsial yang bisa dipulihkan tanpa memberi pilihan. Stream/frame/audio mentah tidak masuk log diagnosis.
- [ ] Sambungkan shortcut yang tidak bentrok, launcher, panel, Settings capture, dan notifikasi hasil. Sembunyikan toolbar/preview dari hasil bila backend mendukung dan buktikan; jangan menjanjikan pembersihan notifikasi aplikasi lain dari frame. Screen sharing browser/meeting diuji terpisah dari rekaman berkas, termasuk pemakaian bersamaan dan konflik perangkat.

**Fase lulus jika** screenshot bisa disalin/disimpan/dianotasi, video tanpa audio dan setiap mode audio yang didukung dapat diputar ulang, dan audio-only merekam sumber yang dipilih tanpa izin layar. Uji izin ditolak, cancel, Stop, lock/logout, revoke, disk penuh, perangkat hilang, restart recorder, dua monitor, dan fractional scaling pada desktop terpasang. Desktop Beta memerlukan jalur screenshot, video, dan audio-only dasar yang teruji tanpa Harness.


## Fase 07B · Kompatibilitas aplikasi Windows dan Android

Riset dokumentasi upstream dan audit repositori selesai pada 8 November 2026. Desain, dependensi, jalur staging, dan skenario uji dirinci di [rancangan kompatibilitas aplikasi](docs/app-compatibility.md). Integrasi paket, handler file, dan pembuktian runtime masih terbuka.

- [ ] Masukkan Wine dan dependensi yang sudah diverifikasi ke transaksi target. Pasang handler EXE/MSI pada desktop terpasang, siapkan prefix saat diperlukan, dan daftarkan shortcut hanya setelah target aplikasi tersedia.
- [ ] Buktikan alur Windows pada instalasi bersih tanpa ISO dan dengan jaringan terputus sesudah pemasangan ConstOS. Uji MSI x64, installer EXE x86, program portabel, cancel/error, dan buka ulang dari launcher setelah reboot.
- [ ] Setelah jalur Windows terbukti, verifikasi sumber paket Waydroid, pasangan image x86_64, serta jalur pembaruannya. Tambahkan pilihan installer dan buktikan pemasangan APK serta jendela terpisah pada Hyprland. Catat batas kernel, GPU, dan ABI dari hasil uji.

**Gerbang Windows** tercapai ketika aplikasi yang diuji bisa dipasang dan dijalankan dari desktop tanpa terminal, konfigurasi manual, atau unduhan runtime setelah login. Dukungan Android mengikuti hasil pengujian tersendiri, termasuk saat inisialisasi atau pemasangan APK gagal.

## Fase 08 · System Monitor, Doctor, dan widget

- [x] Tulis collector Rust dengan fixture dari Linux dan output `const status --json` sebagai klien pertama. `crates/const-collector`, CLI Rust, dan `constd` selesai dibangun dan lulus 5 uji fixture serta pengujian host riil.
- [x] Kirim `const doctor` lewat `constos-core`. Uji sebagai akun biasa pada target VM dari desktop dan TTY, termasuk unit sistem yang sengaja gagal. Lihat bukti Doctor di atas.
- [ ] Setelah paket daemon Rust dan konsumennya siap, ganti dua salinan prototipe Python dan unit HTTP lama dengan satu sumber paket serta IPC sesi. Uji status pada akun biasa dan batasi respons pada metrik yang diperlukan UI.

| Metrik | Implementasi dan cara memeriksa |
| --- | --- |
| CPU dan scheduler | Hitung usage dari delta `/proc/stat` dan tampilkan load average terpisah. Tampilkan model, topology, frekuensi dan suhu bila tersedia. Bedakan kernel yang dikemas, mode scheduler yang dapat dideteksi, dan nilai yang tidak diketahui. Uji CPU hotplug, reboot counter, dan per-core saat ada beban. |
| Proses | Identitas proses memakai PID dan waktu mulai agar PID yang dipakai ulang tidak salah sasaran. Pindai sesuai izin, urutkan sebelum mengambil top-N, dan tangani proses yang keluar di tengah sampling. Tampilkan state dan RSS sesuai definisinya. |
| RAM dan paging | Gunakan `MemAvailable`, swap aktif, `/proc/pressure/memory`, dan statistik perangkat ZRAM. Baca algoritme yang aktif dan tunjukkan rasio kompresi terpisah dari biaya RAM perangkat. Tampilkan status unavailable jika file/fitur tidak ada. |
| Storage dan perangkat | Filesystem, mount, ruang bebas, I/O dari delta, status snapshot, GPU/suhu, battery, dan konektivitas sesuai capability. Bedakan perangkat fisik dan partisi agar I/O tidak terhitung dua kali. |

Sumber metrik dan batasnya dicatat bersama setiap collector. [Dokumentasi /proc](https://docs.kernel.org/filesystems/proc.html) · [Pressure Stall Information](https://docs.kernel.org/accounting/psi.html) · [ZRAM](https://docs.kernel.org/admin-guide/blockdev/zram.html) · [sched_ext](https://docs.kernel.org/scheduler/sched-ext.html)

- [ ] **Penerimaan diagnosis storage.** Cocokkan laporan ruang tersedia di `/` dan mount `/.snapshots` dengan `df` serta `findmnt` dari akun biasa pada target terpasang. Uji mount hilang dan disk penuh pada VM uji.
- [ ] **Perluasan Doctor.** Tambahkan diagnosis sesi, portal, audio, jaringan, dan status snapshot berdasarkan sumber yang dapat diperiksa. Diagnostic bundle harus bisa dipreview dan meredaksi data pribadi sebelum dibagikan.
- [ ] **Widget tahap pertama.** Jam/tanggal, battery, jaringan, media MPRIS, dan CPU/RAM/ZRAM. Tambah widget disk dan aktivitas Harness setelah sumber datanya tersedia. Satu collector/subscription melayani panel, widget, dan Monitor. Gunakan event jika tersedia, kurangi sampling saat tersembunyi, dan berhenti ketika widget dihapus.
- [ ] Simpan posisi, ukuran, visibility, dan output. Batasi drag/resize ke work area. Jika monitor dilepas, pindahkan widget ke fallback yang dapat dijangkau. Sediakan preview, undo/reset layout, dan kontrol keyboard. Data privat seperti judul media atau task bisa disembunyikan di layar terkunci atau saat berbagi layar.
- [ ] Tetapkan katalog widget bawaan: jam/tanggal, battery, jaringan, media, dan metrik sistem di atas. Tiap widget punya ID stabil, schema preferensi/versi, sumber data, aksi yang diizinkan, refresh policy, serta state unavailable/error. Kalender, timer, disk, dan aktivitas Harness hanya ditambahkan saat backend masing-masing tersedia; jangan membuat nilai contoh terlihat sebagai data pengguna.
- [ ] Sediakan pemilih widget dengan tambah/hapus, konfigurasi, reorder, resize bila didukung, preview, dan reset. Bedakan instance widget dari jenisnya. Migrasikan layout per-user tanpa duplikasi ketika output berubah, saat upgrade, atau saat konfigurasi rusak; pengguna kedua tidak mewarisi data pribadi pengguna pertama.
- [ ] Widget bawaan hanya memakai adapter yang ditentukan paket, bukan string perintah bebas. Konten widget bukan otorisasi aksi sistem. Kegagalan satu provider menampilkan error lokal tanpa menjatuhkan shell. Plugin pihak ketiga tidak masuk dukungan 1.0 sampai format, izin, kompatibilitas, dan isolasinya diputuskan.
- [ ] Siapkan schema draft deklaratif untuk menyusun komponen bawaan dari sumber data yang disetujui. Uji preview, batas ukuran dan refresh, validasi field, draft rusak, serta penolakan kode dan perintah bebas sebelum membuka jalur draft dari Harness.

**Fase lulus jika** metrik sesuai dengan `btop`, `free`, `zramctl`, `findmnt`, dan sumber kernel yang sesuai pada interval pengukuran yang dicatat. Uji data kosong, hardware yang tidak didukung, proses yang keluar, service mati, widget yang ditutup, dan reboot yang mempertahankan layout.

**Bukti diagnosis storage · 8 November 2026.** Dari `bcd137b` dengan perubahan ini, `cargo test --workspace --locked --offline` meluluskan 11 tes, termasuk disk penuh, hasil `df` yang tidak dapat dibaca, dan mount snapshot yang hilang pada fixture. Build lokal dengan Rust 1.99.1 menghasilkan `constos-core-0.1.0-5-x86_64` dengan SHA-256 `634240d46480703d0db3c53e56406ca6ac7d743129920096a02a37dde227683b`. Binary dari paket dijalankan tanpa `sudo` pada host Arch Linux x86_64 dengan kernel `7.3.1-1-cachyos`. Nilai 207,72 GiB cocok dengan `df`, `findmnt` mengonfirmasi `/.snapshots` ter-mount sebagai Btrfs, dan Doctor mengembalikan exit `0`. Penerimaan pada target VM masih terbuka.

Setelah perubahan digabungkan di atas `7d14cf9`, 11 tes Rust dan 19 tes Python lulus. Build menghasilkan `constos-core-0.1.0-6-x86_64` dengan SHA-256 `d8762e703052731b03a512c9c2b06b936be7d044ba8ae7866c32e5a09dabfd89`. Pada host yang sama, Doctor berbahasa Inggris melaporkan 207,61 GiB sesuai `df`, mount snapshot Btrfs sesuai `findmnt`, dan exit `0`.

## Fase 09 · Dynamic Island untuk Wayland

Mulai sebagai surface yang opsional dengan pola interaksi ConstOS. Saat referensi Windows diberikan, catat fitur yang menarik, perilaku saat hover/click, sumber event, dan ketentuan lisensi. Terjemahkan desain ke aturan Hyprland, termasuk work area, monitor, fokus, dan fullscreen.

| Bagian | Pilihan awal |
| --- | --- |
| Penempatan | Anchored di tengah atas monitor utama. **Floating** memakai zona non-eksklusif dan input mask. **Docked** mencadangkan strip atas yang tetap kecil. Reservasi berlaku pada tepi layar, sehingga ukuran panel yang membesar tidak dipakai untuk mengubah work area setiap frame. |
| State | **Idle** menampilkan waktu atau ringkasan kecil. **Peek** menunjukkan satu aktivitas singkat. **Expanded** membuka kontrol lengkap atas klik atau shortcut. **Hidden** mengikuti pengaturan, lock, dan fullscreen. Pemilihan konten dan animasi ditangani terpisah. |
| Prioritas | Kontrol capture dan Stop, peristiwa sistem penting, aktivitas Harness yang memang boleh ditampilkan, media, lalu waktu. Deduplikasi dengan Notification Center. Indikator computer use tetap tersedia lewat jalur terpisah jika Island mati atau tersembunyi. |
| Fokus dan input | Jangan ambil keyboard saat idle atau peek. Surface transparan hanya menerima input pada area yang terlihat/interaktif. Expanded dapat dibuka dengan shortcut, ditutup dengan Escape, lalu mengembalikan fokus. Sediakan alternatif klik untuk semua aksi hover. |
| Integrasi bar | Uji Island pada bar Dux. Tentukan satu pemilik reservasi top edge dan satu provider untuk setiap data widget. Gunakan konfigurasi per-monitor saat dock/undock serta perbedaan skala. |

- [ ] Buat prototipe Quickshell kecil berisi jam, media, dan satu event palsu dari fixture. Ukur ukuran surface, hit test, frame pacing, dan penggunaan CPU saat diam. Tetapkan mode floating/docked setelah mencobanya pada browser, terminal fullscreen, dan aplikasi dengan top chrome.
- [ ] Hubungkan data nyata dari fase 07–08. Tambahkan kalender ringkas, timer, progress transfer, atau aktivitas Harness lewat kontrak event yang sama jika sudah ada backend. Tombol Stop meminta penghentian sesi ke broker dan menunjukkan hasil yang dikonfirmasi.
- [ ] Uji 1 dan 2 monitor, scale campuran, display kecil, hotplug, fullscreen, screen share, reduced motion, dan perubahan fokus cepat. Minimalkan alokasi ketika hidden dan hentikan animasi/polling yang tidak terlihat.

**Fase lulus jika** area transparan meneruskan klik ke aplikasi di bawahnya, fullscreen mengikuti kebijakan yang dipilih, work area tetap stabil saat ekspansi, dan seluruh kontrol dapat dipakai dengan keyboard. [Protokol wlr-layer-shell](https://github.com/swaywm/wlr-protocols/blob/master/unstable/wlr-layer-shell-unstable-v1.xml) · [Quickshell PanelWindow](https://quickshell.org/docs/v0.3.2/types/Quickshell/PanelWindow/)

## Fase 10 · Optimasi sistem dan dukungan perangkat

- [ ] Buat baseline sebelum dan sesudah shell baru di perangkat yang sama. Rekam kernel, compositor, versi paket, mode power, driver, resolusi, dan profil VM. Ukur cold boot hingga desktop siap, PSS sesi idle, CPU dan wakeups, latency launcher/Settings, frame pacing Island, dan idle/suspend drain pada laptop. Ambil beberapa run dan catat median serta sebarannya.
- [ ] Bandingkan desktop fallback dengan shell baru, Harness aktif/nonaktif, serta idle/beban kompilasi/pressure memori. Tetapkan budget awal setelah ada hasil. Pisahkan biaya kompresi, sampling, animasi, dan proses Electron. Optimasi event subscription, wakeups, serta polling tersembunyi sebelum mengubah tuning kernel.
- [ ] Ukur screenshot serta rekaman video/audio sambil memakai desktop: CPU/GPU, memori, frame drop, sinkronisasi A/V, ukuran berkas per menit, dan respons Stop. Catat codec/resolusi/FPS/sumber audio dan driver; tentukan preset default dari hasil di hardware minimum. Widget tersembunyi dan rekaman yang sudah berhenti tidak boleh menyisakan polling atau proses encoder aktif.
- [ ] Uji ZRAM dan sysctl di VM dengan RAM terbatas dan satu perangkat fisik. Bandingkan pressure, jumlah swap, biaya RAM terkompresi, dan respons aplikasi. Catat nilai dari CachyOS dan override ConstOS yang betul-betul efektif. Terapkan tuning berbeda jika datanya mendukung perubahan itu.
- [ ] Kelola satu kebijakan power profile. Uji CPU governor yang disediakan perangkat, brightness, battery, idle, suspend/resume, audio setelah wake, display dan Wi-Fi. Untuk proses latar seperti Harness, evaluasi batas CPU/I/O/memori per unit user dengan cgroup v2 setelah ada beban nyata. Hindari pembatasan yang memutus kerja pengguna tanpa indikator. [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [ ] Pertahankan pemilihan kernel dan repo generik saat memvalidasi hardware. Tambahkan fallback kernel atau tier CPU melalui keputusan yang memeriksa dukungan instruksi, driver, initramfs, dan rollback. Dokumentasikan kombinasi GPU dan firmware yang diketahui bermasalah. [Varian kernel CachyOS](https://wiki.cachyos.org/features/kernel/)

**Fase lulus jika** tersedia laporan sebelum/sesudah dengan perangkat dan beban yang sama, regresi besar punya penyebab serta keputusan, dan desktop masih dapat digunakan ketika beban memori atau I/O tinggi.

## Fase 11 · Paket Linux Const Harness

Pilihan Yes/No yang ditinjau pada [prototipe installer](docs/installer-plan.md#placeholder-const-harness) tidak masuk transaksi rilis awal. Paket dan lifecycle diuji pada target terpasang di fase ini.

- [ ] Bangun upstream di Linux dengan `pnpm --filter @const/harness-desktop package:linux:pacman`. Periksa paket yang dihasilkan, executable, file `.desktop`, icon, resource native, dan dependensi `node-pty`. Pilih jalur konsumsi artefak paket yang sudah dapat diverifikasi atau PKGBUILD yang memasang artefak binary dengan checksum. Ganti resep lokal yang saat ini hanya membuat launcher ke `/opt/ConstHarness/const-harness-desktop`. [Resep paket saat ini](packages/const-harness/PKGBUILD)
- [ ] Uji instalasi dan upgrade pada target bersih. Dari launcher, cek startup di Wayland, PTY, pemilihan workspace, browser pane, clipboard, screen sharing aplikasi biasa, session restore, alur login/offline, serta data yang dipertahankan saat upgrade. Gunakan update pacman untuk edisi ConstOS dan sesuaikan perilaku update dalam aplikasi untuk paket distro.
- [ ] Jalankan Harness sebagai pengguna biasa dan sesuai sesi aktif. Jika pengguna memilih autostart, ikat lifecycle ke sesi dan impor variabel saat login. App tetap dapat digunakan ketika broker computer use tidak tersedia. Tampilkan kapabilitas berdasarkan hasil handshake dan izin runtime.
- [ ] Buat adapter Rust Linux dalam satu irisan kecil. Host Electron meluncurkan binary versi paket yang ditentukan dan membaca NDJSON dari inherited pipe. Pertahankan kontrak `ready`, `requestId`, handshake, error code, dan batas payload. Cocokkan perilaku dengan fixture yang sudah ada. Setelah host bisa memilih provider dengan aman, baru perluas kemampuan observasi.
- [ ] **Pembuatan widget lewat Harness.** Setelah schema fase 08 tersedia, kirim satu draft berisi komponen bawaan, misalnya jam dan CPU/RAM. Pengguna meninjau dan menambahkannya dari pemilih widget. Buktikan preview, tolak, simpan, dan hapus. Jalur ini tidak membutuhkan grant computer use.

**Fase lulus jika** paket bisa diinstal, dibuka, diperbarui, dan dihapus dari VM Linux dengan workspace yang tetap bisa diakses. Versi atau capability mismatch menghasilkan pesan yang dapat ditindaklanjuti. Workbench dan preview draft widget bekerja ketika computer use dinonaktifkan.

## Fase 12 · Native Computer Use, observasi lokal

Rust helper berjalan di sesi pengguna. Akses dibedakan per capability antara **melihat struktur aplikasi**, **menangkap gambar**, dan **mengirim input**. Jadikan izin sementara per target sebagai default, dengan pilihan menolak dan menghentikan sesi dari UI.

- [ ] **Spike kemampuan Wayland.** Dari ISO/instalasi target, catat versi Hyprland, XDPH, portal dan PipeWire. Probe apa yang benar-benar diiklankan lewat D-Bus. Uji ScreenCast dengan picker, scope window/output, serta apakah backend menyediakan RemoteDesktop dan `ConnectToEIS` atau metode input yang dibutuhkan. Dukungan protokol di spesifikasi perlu dibuktikan pada backend yang kita kirim. `InputCapture` menangkap input pengguna, sedangkan RemoteDesktop menyediakan jalur pengiriman input. [Pelacakan RemoteDesktop di XDPH](https://github.com/hyprwm/xdg-desktop-portal-hyprland/issues/252) · [RemoteDesktop](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html) · [InputCapture](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.InputCapture.html)
- [ ] **Observasi semantik.** Pakai AT-SPI dengan traversal berbatas, timeout, dan hasil per-app yang tervalidasi. Tangani aplikasi tanpa tree, role sensitif, ID window yang berubah, fokus, dan elemen yang hilang. Uji dengan fixture GTK/Qt serta satu aplikasi browser atau Electron. [Arsitektur AT-SPI](https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/architecture.html)
- [ ] **Observasi visual.** Prototype Rust dengan `ashpd` dan PipeWire. Buka picker melalui jalur portal, pilih target, batasi ukuran, jumlah frame, masa berlaku snapshot, dan memori. Tunjukkan bahwa capture aktif. Jika backend hanya menawarkan monitor, jelaskan scope itu kepada pengguna dan minta persetujuan terpisah sebelum menggunakannya. Meng-crop frame setelah diterima tidak mengurangi scope yang disetujui di portal. [ScreenCast portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html) · [Rust ashpd](https://docs.rs/ashpd/latest/ashpd/)
- [ ] **Privasi.** Default tanpa rekaman frame, teks yang diketik, clipboard, atau tree mentah pada log. Hasil pengamatan tetap lokal sampai pengguna memahami dan mengizinkan data yang dikirim ke model eksternal. Perlakukan teks di layar sebagai data yang bisa berisi instruksi asing. Tutup portal dan file descriptor saat pengguna menekan Stop, logout, lock, ganti target, atau proses induk putus.

**Fase lulus jika** target yang disetujui menghasilkan tree atau frame sesuai scope yang diberikan. Tolak, stop, revoke, dan hilangnya output menghentikan observasi dengan status yang jelas. Jika visual capture belum lolos, UI mengiklankan observasi semantik yang teruji.

## Fase 13 · Native Computer Use, aksi dengan izin dan sandbox

- [ ] **Aksi pertama melalui AT-SPI.** Uji klik semantik dan pengisian field pada aplikasi fixture. Setiap aksi memakai grant sementara dengan target, capability, sesi, expiry, dan aksi yang disetujui. Validasi ulang identitas window/elemen, status foreground saat relevan, koordinat, tipe input, serta snapshot terbaru sebelum pengiriman.
- [ ] **Input visual jika backend mendukung.** Uji klik, scroll, dan keyboard via RemoteDesktop/EIS atau jalur compositor yang bisa menegakkan scope dan consent. Catat transformasi koordinat antara stream, ukuran logis, scale, rotasi, dan target. Jika scope tidak bisa dijamin, batasi ke aksi semantik atau serahkan kontrol kepada pengguna. Akses root, `/dev/input`, dan `/dev/uinput` berada di luar jalur distribusi.
- [ ] **Lifecycle dan kontrol pengguna.** Satu lease aktif, antrean terserialisasi, deadline, pembatalan, rate limit, release tombol/modifier saat stop, serta pembacaan ulang state setelah aksi. Timeout setelah pengiriman menghasilkan status yang meminta observasi baru sebelum percobaan ulang. Sediakan Stop dengan shortcut dan kontrol UI yang tetap bekerja saat panel gagal.
- [ ] **Batas runtime.** Uji sandbox terminal Harness terpisah dari izin desktop. Ubah wrapper dari mount root luas menjadi daftar mount yang dibutuhkan, workspace terverifikasi, direktori sementara privat, kebijakan jaringan eksplisit, dan penolakan ketika isolasi tidak bisa diterapkan. Jalur sandbox tidak mendapat socket helper, file descriptor portal, agent SSH, keyring, atau data aplikasi secara otomatis. [Wrapper sekarang](iso/airootfs/usr/local/bin/const-sandbox)
- [ ] **Integrasi agen.** Tampilkan scope, status, dan perubahan di workbench. Untuk MCP, expose metrik baca-saja lebih dulu melalui adapter lokal yang benar-benar menjalankan handshake dan schema tool. Tool computer use lewat kebijakan broker yang sama. Nonaktifkan jalur remote/unattended untuk kontrol desktop pada rilis awal. Aksi destruktif, pembayaran, kredensial, sistem privilege, dan secure desktop berada di luar kapabilitas rilis awal.
- [ ] **Uji keselamatan.** Pakai aplikasi fixture dengan perubahan yang bisa diverifikasi. Uji salah target, popup asing, jendela pindah, multi-monitor skala campuran, izin ditolak, cancel saat aksi pending, timeout setelah aksi, aplikasi mati, dan sesi terkunci. Bukti keberhasilan berasal dari state aplikasi setelah aksi.

**Fase lulus jika** Harness menyelesaikan satu tugas lokal pada aplikasi fixture dan satu aplikasi sehari-hari yang tercatat didukung, dengan persetujuan, hasil terverifikasi, dan Stop efektif. Jika hanya aksi semantik yang lulus, cakupan itu menjadi dukungan resmi. Jalur input yang tidak bisa menegakkan scope atau consent tetap dinonaktifkan, bukan ditawarkan sebagai mode eksperimental.

## Fase 14 · Paket distribusi, update, dan rollback

- [ ] Finalisasi paket `constos-desktop`, `constos-core`, dan paket opsional Harness/helper yang dipakai di fase sebelumnya. Daftarkan kepemilikan file, dependensi, versi schema, script install, dan service. Installer memasang versi yang juga bisa di-upgrade lewat pacman. Gunakan default vendor yang dapat diidentifikasi dan simpan override di home pengguna.
- [ ] Hubungkan preflight staging dan tes VM dari fase 01–03 ke pipeline Linux yang juga mengompilasi Rust dengan lockfile, membangun paket, memvalidasi binary dan `.desktop`, lalu merakit ISO. Kaitkan SHA, versi repo/daftar paket, output hash, dan log CI. Tanda tangani rilis dari job tepercaya yang terpisah dari build PR. Uji keyring dan rotasinya sebelum membuka kanal stable. [Konfigurasi dan verifikasi paket pacman](https://man.archlinux.org/man/pacman.conf.5.en)
- [x] **CLI `const update`.** Uji transaksi pacman, pembatalan, status kegagalan DNS, cold boot sesudah transaksi, dan kondisi sudah mutakhir pada target VM. Lihat bukti `const update` di atas.
- [ ] **Penerimaan update rilis.** Uji paket ditolak karena tanda tangan, disk penuh, migrasi, dan reboot setelah update kernel. Paket ConstOS ikut setelah repo resmi bertanda tangan tersedia.
- [ ] **Integrasi update.** Welcome bisa menawarkan aksi update yang dipilih pengguna. Integrasi pengelola aplikasi lain, seperti Flatpak bila diadopsi, memakai langkah serta hasil tersendiri. Pastikan updater menunggu pekerjaan Harness yang relevan sebelum mengganti paket yang dipakai.
- [ ] Simpan satu kernel atau jalur boot pemulihan yang didukung serta riwayat artefak paket yang cocok. Latih downgrade paket ConstOS dan recovery sistem secara terpisah. Uji upgrade kernel yang menyentuh ESP atau `/boot`, lalu verifikasi versi modul, loader, dan initramfs setelah pemulihan. Tandai batas recovery data aplikasi dan snapshot di panduan.

**Fase lulus jika** kandidat rilis dapat diinstal, di-upgrade dari kandidat sebelumnya, dan dipulihkan. Bukti mencakup verifikasi tanda tangan, reboot sesudah update, preferensi pengguna yang bertahan, diagnosis kegagalan, dan satu rollback yang benar-benar boot.

## Fase 15 · Kualifikasi rilis dan ConstOS 1.0

| Pengujian rilis | Bukti minimum |
| --- | --- |
| Build dan boot | CI Linux menghasilkan ISO dari commit/tag, log tersimpan, SHA diverifikasi, UEFI VM dan satu perangkat fisik mencapai sesi, dan console recovery bekerja. |
| Install dan storage | Disk baru berhasil diinstal dan reboot tanpa ISO. Instalasi menyimpan akun dan layout yang benar. Snapshot, rollback, dan upgrade diuji. Skenario LUKS/offline/dual boot masuk daftar dukungan setelah memiliki bukti sendiri. |
| Desktop dan perangkat | Login/logout, launcher, semua aksi menu, display revert, file/MIME, audio, Wi-Fi, lock dan suspend diuji pada perangkat yang sesuai. Sertakan dua monitor, fractional scaling, keyboard-only, dan reduced motion untuk shell. |
| Capture dan privasi | Screenshot tersimpan/clipboard/anotasi benar, hasil rekaman video dan audio dapat diputar ulang, sumber serta sinkronisasi benar, dan Stop/lock/revoke melepas akses. Uji cancel/denied, disk penuh, device hilang, dua monitor, dan skala campuran; tidak ada upload otomatis. |
| UI, widget, dan aset | Alur capture/Settings/shell bisa dipakai dengan keyboard dan aksesibilitas yang didukung; widget bertahan setelah upgrade/hotplug tanpa kebocoran antar-user. Semua aset yang dipakai tersedia, punya asal/lisensi, dan lolos pemeriksaan kontras serta skala. |
| Metrik dan performa | Collector diverifikasi terhadap sumber kernel. Baseline mencakup boot, PSS/CPU idle, respons UI, pressure memori, dan beban kompilasi. Catat regresi serta hasil keputusan per build. |
| Harness dan izin | Paket berjalan di target. Demo memperlihatkan izin, observasi, aksi yang didukung, verifikasi hasil, Stop, dan penolakan di luar scope. Distro juga berfungsi saat Harness tidak dipasang. |
| Distribusi dan dukungan | ISO/paket bertanda tangan, checksum, release notes, known issues, hardware matrix, panduan install/update/recovery, inventaris lisensi, serta prosedur laporan bug dan keamanan tersedia. |

- [ ] Jalankan rilis kandidat di disk bersih dan pada versi sebelumnya. Bekukan perubahan UI selama verifikasi. Lakukan sign-off berdasarkan hasil tiap baris dan catat kegagalan penghalang rilis. Perbaiki kandidat, buat artefak baru, lalu ulangi tes yang terdampak.
- [ ] Tetapkan pemilik triage rilis dan jalur pelaporan bug/keamanan, masa dukungan artefak, retensi bukti uji, serta kebijakan refresh ISO pada basis rolling. Cocokkan README, roadmap, arsitektur, panduan, dan prosedur skill dengan perilaku kandidat. Dokumen yang kontradiktif atau klaim dukungan tanpa bukti memblokir publikasi.
- [ ] Verifikasi alur sistem pada kandidat rilis: monitor menampilkan state dan usage CPU nyata, ZRAM aktif dengan statistik aktual, recovery memulihkan perubahan dari snapshot, Monitor/Harness menerima data lokal, dan sandbox menolak operasi di luar izin. Pastikan sesi computer use berhenti setelah revoke. Catat hasil serta batas dukungannya dalam release notes.
- [ ] Publikasikan tag rilis, ISO, checksum/tanda tangan, paket, dan catatan rilis. Verifikasi download dari luar host build, instalasi baru, dan jalur update. Gunakan label dukungan yang sama di README, installer, dan Settings.

**ConstOS 1.0 siap ketika** seseorang di luar tim bisa mengunduh artefak, memverifikasi, memasang, login, menggunakan desktop sehari-hari, memperbarui, dan mengikuti recovery. Fitur Harness dipromosikan sesuai kapabilitas yang sudah lulus, dengan jalur penggunaan yang jelas ketika izin ditolak.

## Backlog pertama yang bisa dieksekusi

| Urutan | Perubahan | Bukti sebelum lanjut |
| --- | --- | --- |
| 1 | **Reproduksi baseline.** Build Linux baru dari SHA yang dicatat, lalu gunakan VM UEFI dengan disk uji. | Catat titik gagal aktual pada GRUB, Cage, TUI installer, reboot tanpa ISO, login SDDM, atau startup Hyprland sesuai [panduan pengujian terpadu](docs/acceptance-guide.md). |
| 2 | **Benahi installer sampai login.** Kerjakan alur, Review, progres, dan handoff sesuai [spesifikasi installer](docs/installer-plan.md#urutan-perubahan-dan-gerbang). | Instal ulang ke disk kosong, lepas ISO, login dengan akun baru dan buka desktop. Uji cancel, disk berubah, dan gagal unduh sebelum partisi. |
| 3 | **Pilihan installer dan desktop hari pertama.** Uji jaringan, akun, dan Firefox/Chromium/Zen/No browser. | Handler sesuai pilihan, SDDM meminta kata sandi, aplikasi inti terbuka, dan Welcome muncul sekali. |
| 4 | **Sesi Dux dan kontrol desktop.** Uji preset Const, launcher, notifikasi, lock, dan audio. | Keyboard, pemulihan fokus, skala, dua output, perubahan volume nyata, dan launcher cadangan. |
| 5 | **Desktop harian dan surface opsional.** Uji dock dan widget Dux. Evaluasi Const Store dan preferensi terminal di Hub sesudah baseline. | Transaksi Flatpak dari akun biasa, override bertahan, fullscreen, work area stabil, dan hotplug. |
| 6 | **Harness.** Paket Linux yang bisa dibuka, draft widget, lalu observasi dan aksi Wayland sesuai capability. Probe portal dapat dilakukan pada target Hyprland di langkah 2. | Draft ditinjau sebelum diterapkan. Buktikan penolakan, Stop, dan hasil aksi untuk setiap capability yang dipromosikan. |

Langkah 1–3 memulihkan fondasi sebelum backlog desktop dilanjutkan. Capture pengguna, Wine, recovery, serta pengujian hardware tetap mengikuti gerbang fase masing-masing. Bukti VM lama tetap tercatat pada bagian awal roadmap. Toolkit shell dan cakupan input Wayland ditetapkan dari hasil spike. Repo Dynamic Island Windows masuk review desain pada fase 09 setelah tautannya tersedia.
