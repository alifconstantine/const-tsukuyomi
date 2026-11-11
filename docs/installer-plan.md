# Spesifikasi installer dan desktop pertama ConstOS

Rancangan kerja 11 November 2026. Dokumen ini menjadi acuan alur, perilaku, dan pemilihan paket untuk perubahan installer. [Roadmap](../implementation_plan.md) menyimpan prioritas dan bukti per build. [Panduan penerimaan](acceptance-guide.md#installer-dan-reboot-tanpa-iso) menyimpan cara menjalankan uji. Gunakan bahasa Indonesia dalam dokumentasi dan bahasa Inggris pada antarmuka bawaan.

## Dasar keputusan

| Sumber | Yang dapat disimpulkan |
| --- | --- |
| 26 screenshot VM Ryoku edisi CachyOS, 9 November 2026 | Memperlihatkan menu boot, **Preparing installer**, Welcome, pemilih keyboard/locale/zona waktu, jaringan dengan paket offline, hardware dan profil, pilihan compositor/browser/shell/file manager, Rashin, Gaming, Apps & Tools, disk dan layout, pembuatan akun, enkripsi, Review, serta instalasi yang masih berjalan. Rail langkah, pilihan yang tampak langsung, petunjuk keyboard, ringkasan layout, dan progres per tahap dapat diadaptasi. Layar selesai, login, dan desktop tidak tercakup dalam kumpulan ini. |
| Ryoku v1.0.7, `f7197d72d` | Pemilihan disk kosong dapat dilanjutkan ke Review tanpa mengetik. Ryoku meminta `ERASE` untuk operasi yang menghapus partisi yang sudah ada. Progres berasal dari penanda tahap dan keluaran backend. Source juga mendokumentasikan langkah setelah instalasi. [Alur TUI](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/installation/tui/README.md#the-step-flow) · [Kode Review dan progres](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/installation/tui/main.go#L3535) |
| Situs Ryoku, **Everything, already installed** | Rujukan untuk mengelompokkan isi desktop pertama dan menjelaskan fungsi tiap kelompok. Pilihan paket, mode offline, jumlah paket, serta ukuran Ryoku tidak menjadi spesifikasi ConstOS. [Situs Ryoku](https://ryoku.dev/) · [Manifest terdokumentasi Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/docs/preinstalled.md) |
| ConstOS `001a1db` | Baseline memisahkan Cage/Calamares live dari target Hyprland. Wizard memakai Location, Keyboard, Users, Disk dengan pengetikan path, dan Summary. Hasil baseline serta revisi berikutnya dicatat di [roadmap](../implementation_plan.md). [Sumber wizard awal](https://github.com/alifconstantine/const-tsukuyomi/tree/001a1db/installer) |

Screenshot adalah referensi tampilan. Urutan dan akibat aksi Ryoku ditelusuri ke source yang dipatok di atas. Kumpulan gambar lokal dan data akun di dalamnya tidak disalin ke repositori.

## Alur utama yang dituju

1. Boot **Install Tsukuyomi** dari GRUB. Plymouth menampilkan status boot. Entri **Tsukuyomi Diagnostics** membuka konsol.
2. Cage dan Foot menampilkan judul piksel **TSUKUYOMI**, bar animasi merah, dan status **Preparing installer**. Tekan tombol untuk melewati animasi atau tunggu sampai Welcome. Wizard TUI dari Ryoku v1.0.7 lalu membuka Keyboard, Locale, Time zone, Network, Browser, Target disk, Hostname, Administrator, dan Review.
3. Pilih **Yes** di Review untuk memeriksa ulang identitas disk, waktu, keyring, dan arsip bertanda tangan. Partisi dibuat setelah semua pemeriksaan lulus. UI menampilkan tahap aktif dan log proses.
4. Sesudah unmount, **Reboot now** memulai reboot. Lepas ISO atau pilih disk terpasang. SDDM Clockwork Orbital mengautentikasi akun baru sebelum Hyprland dan Dux mulai. Panduan shortcut Welcome berbasis QML tampil satu kali per akun, tanpa gambar.

**Batas iterasi awal.** CachyOS x86_64, UEFI, Hyprland, disk kosong minimal 32 GiB, dan instalasi online. TUI menjalankan alur tetap dengan satu akun administrator, Fish, Kitty, Nautilus, dan Dux Shell. Penggunaan disk terisi, dual boot, enkripsi, instalasi offline, dan akun tambahan memiliki scope serta penerimaan tersendiri.

## Langkah wizard dan keputusan UI

| Langkah | Perilaku dan syarat penerimaan |
| --- | --- |
| Welcome | Jelaskan kebutuhan disk kosong, akses jaringan, dan konfirmasi di Review. Ctrl+C membatalkan sebelum instalasi dan kembali ke kiosk. |
| Keyboard, Locale, Time zone | Gunakan daftar berfilter dari TUI Ryoku. Terapkan layout sebelum akun. Locale target terpisah dari bahasa Inggris pada TUI. |
| Network | Tampilkan status jaringan atau tawarkan pilihan Wi-Fi. Pemeriksaan unduhan bertanda tangan dilakukan saat preflight. |
| Browser | Pilih Firefox, Chromium, Zen, atau None. TUI menampilkan pilihan di Review. |
| Target disk | Backend hanya menawarkan disk kosong yang memenuhi syarat. Cocokkan path, kapasitas, dan serial. |
| Hostname dan Administrator | Buat satu akun dengan Fish, grup wheel, dan kata sandi. Hash dikirim lewat stdin bersama pilihan yang dikonfirmasi. |
| Review | Tampilkan identitas disk, layout, keyboard, locale, zona waktu, browser, desktop, hostname, dan akun. Gunakan angka di rail untuk meninjau ulang langkah. |
| Install dan Finish | Event proses menentukan tahap aktif. TUI menampilkan sebab, tahap, dan path log privat bila gagal. Retry hanya sebelum tahap storage; sesudahnya simpan log dan periksa disk. Layar sukses muncul setelah target dilepas. |

UI memakai komponen Ryoku dengan palet dark crimson Tsukuyomi serta tanpa logo. Geometri rail, kartu isi, dan footer ditentukan ukuran terminal, sehingga pergantian langkah tidak mengubah posisi kartu. Daftar panjang memakai viewport picker. Lihat [design.md](../design.md) untuk token visual.

### Placeholder Const Harness

Rashin memberi referensi letak pilihan agen. Jika dipakai untuk review, tampilkan **Const Harness** dengan pilihan **Yes/No** dan label yang menjelaskan bahwa itu simulasi. Kedua pilihan hanya mengubah tampilan pilihan pada prototipe. Hasil paket, layanan, pengaturan startup, izin, akun, dan transaksi installer identik. Wizard yang dikirim di ISO menyembunyikan pilihan tersebut sampai paket dan lifecycle Harness lulus penerimaan di fase 11. Desktop dasar tetap bisa dipakai tanpa Harness.

### Kontrak pemilihan disk

Pemilih mengirim identitas dari snapshot kandidat yang dibuat backend. UI dapat menampilkan path, tetapi teks bebas dari UI tidak menjadi target partisi. Penolakan media ISO, drive lepas-pasang, disk read-only, disk berpartisi atau bermount, dan disk dengan signature tetap berlaku. Backend memeriksa ulang identitas dan kelayakan saat preflight dan tepat sebelum operasi partisi. Jika perangkat berganti, hilang, atau berubah setelah Review, hentikan dan minta pengguna memilih lagi.

Cutover mengubah daftar disk dari `backend.py --list-disks`, pengiriman identitas melalui JSON, preflight, dan pengujian backend dalam satu perubahan. Backend hanya menerima identitas yang cocok dengan daftar kandidat dan memverifikasi ulang identitas pada tahap storage. Pastikan modul lama atau nilai pilihan yang tertinggal tidak memberi jalan untuk mempartisi. Mode yang menghapus data dari disk terisi berada di luar dukungan iterasi ini.

## Pilihan browser

| Pilihan | Sumber yang dituju | Hasil pada instalasi baru |
| --- | --- | --- |
| **Firefox · Recommended** | `firefox` | Default untuk HTTP, HTTPS, dan HTML. |
| **Chromium** | `chromium` | Default untuk HTTP, HTTPS, dan HTML. |
| **Zen Browser** | `zen-browser-bin` dari repo generik CachyOS | Default untuk HTTP, HTTPS, dan HTML. |
| **No browser** | Tanpa paket browser dari wizard | Sistem terpasang tidak menulis handler browser. |

[Konfigurasi Browser](../installer/browsers.json) menjadi sumber pilihan, nama paket, dan ID desktop. Backend menerima ID dari TUI dan memasukkan satu paket yang dipilih ke transaksi unduhan sebelum mempartisi disk. Sesudah paket dipasang, backend memeriksa desktop entry dan menulis handler awal di `/etc/skel` sebelum membuat akun. Firefox menjadi rekomendasi mengikuti [inventaris Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/docs/preinstalled.md#everyday-apps).

## Isi desktop hari pertama

Tabel ini mengelompokkan pengalaman yang harus tersedia setelah login. Status **sumber saat ini** berarti ada di manifest atau paket yang dirujuk. Gerbang runtime mengikuti roadmap. Jangan menghitung paket dari situs Ryoku sebagai paket ConstOS.

| Kelompok | Sumber saat ini | Target rilis awal dan tindak lanjut |
| --- | --- | --- |
| Sistem dan boot | CachyOS BORE, firmware, GRUB, Plymouth, SDDM, Btrfs, Snapper, ZRAM, `const doctor` dan `const update`. | Instal, login, diagnosis, pembaruan, dan verifikasi snapshot dari disk. Ukur jejak target dari VM bersih setelah boot dan update. |
| Desktop dan grafik | Hyprland dan Dux Shell dengan preset Const, portal Hyprland/GTK, serta Wofi sebagai launcher cadangan. | Uji launcher, workspace, notifikasi, lock/logout, dan izin portal pada target. |
| Jaringan, Bluetooth, dan audio | NetworkManager, BlueZ, PipeWire/WirePlumber, dan pavucontrol. Quick Settings Dux membuka kontrol jaringan, Bluetooth, dan audio. | Pastikan koneksi dan output audio dapat dipakai setelah login. Uji pemasangan Wi-Fi dalam installer terpisah dari jaringan pada target. |
| Aplikasi harian | Browser pilihan, Nautilus, Mousepad, Ristretto, Evince, File Roller, dan mpv dengan MPRIS. Konfigurasi awal mpv memilih render Wayland dengan fallback software untuk VM. | Verifikasi MIME, launcher, dan playback pada VM serta perangkat fisik. |
| Terminal dan CLI | Kitty, Fish, Fastfetch dengan simbol Const ASCII khusus terminal, btop, eza, bat, fd, ripgrep, fzf, zoxide, jq, curl, wget, rsync, dan unzip; yay, Git, serta base-devel untuk AUR. | Uji pintasan terminal dan shell akun baru. Toolchain pengembangan tetap opsional. |
| Capture dan font | `constos-screenshot` dengan grim/slurp/clipboard, Noto Sans, Noto Emoji, JetBrains Mono Nerd Font, dan ikon Papirus/Adwaita. | Buktikan screenshot dan fallback font pada target. Recorder, OCR, dan alat media tambahan mengikuti roadmap masing-masing. |
| Aplikasi tambahan | Flatpak dan Recommended Apps dengan LibreOffice, VLC, LocalSend, dan KeePassXC. | Pengguna memilih unduhan dari desktop. Const Store kelak berbagi backend katalog yang sama. Gaming dan virtualisasi tidak masuk wizard awal. Harness serta Wine/Waydroid tetap jalur terpisah sesuai penerimaan masing-masing. |

Sumber inventaris yang diuji adalah [manifest target](../installer/target-packages.x86_64), [resep paket desktop](../packages/constos-desktop/PKGBUILD), serta [katalog Recommended Apps](../desktop/welcome/catalog.py). Saat menambah paket, catat pemilik, fungsi, scope live/target, sumber, jalur update, pengaruh pada ukuran, dan cara membuktikan aksi dari akun biasa.

## Urutan perubahan dan gerbang

| Urutan | Hasil yang perlu dibuktikan |
| --- | --- |
| 1. Reproduksi baseline | Gunakan ISO Linux yang SHA dan paketnya tercatat, serta disk VM kosong yang identitasnya diketahui. Jalankan GRUB → Cage/Foot → wizard → install → lepas ISO → login SDDM → Hyprland. Catat titik gagal aktual dari log dan tampilan. Bedakan kegagalan launcher, paket, boot target, autentikasi, dan startup sesi. |
| 2. Benahi satu irisan installer | Boot, Welcome, pilihan disk dan Review, progres nyata, lalu Finish/Restart. Pertahankan desktop dasar agar regressi mudah diisolasi. Buktikan penolakan disk yang berubah dan kegagalan unduh tanpa perubahan disk. Perbaiki handoff ke login sampai bisa diulang dari disk baru. |
| 3. Integrasikan pilihan | Uji Network, locale/keyboard, akun, browser yang dipilih, dan No browser. Setiap pilihan memiliki perilaku target yang terbukti. Pastikan login tanpa autologin, browser yang sesuai, file manager, terminal, audio, dan Welcome satu kali. |
| 4. Kembali ke roadmap desktop | Lanjutkan pekerjaan shell/Hub/Store dari target terpasang yang sudah dibuktikan. Poles tema, widget, Dock, Island, dan Harness sesuai dependensi gerbang berikutnya. |

Gerbang installer memerlukan build yang sama untuk seluruh alur utama dan bukti kegagalan yang ditargetkan pada VM terpisah. Smoke tanpa disk, screenshot Ryoku, dan prototipe browser menjadi bukti untuk bagiannya masing-masing. Simpan SHA, checksum ISO, versi paket, profil VM, dan hasil login/desktop tanpa memasukkan log atau media pribadi ke Git.
