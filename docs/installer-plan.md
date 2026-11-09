# Spesifikasi installer dan desktop pertama ConstOS

Rancangan kerja 9 November 2026. Dokumen ini menjadi acuan alur, perilaku, dan pemilihan paket untuk perubahan installer. [Roadmap](../implementation_plan.md) menyimpan prioritas dan bukti per build. [Panduan penerimaan](acceptance-guide.md#installer-dan-reboot-tanpa-iso) menyimpan cara menjalankan uji. Gunakan bahasa Indonesia dalam dokumentasi dan bahasa Inggris pada antarmuka bawaan.

## Dasar keputusan

| Sumber | Yang dapat disimpulkan |
| --- | --- |
| 26 screenshot VM Ryoku edisi CachyOS, 9 November 2026 | Memperlihatkan menu boot, **Preparing installer**, Welcome, pemilih keyboard/locale/zona waktu, jaringan dengan paket offline, hardware dan profil, pilihan compositor/browser/shell/file manager, Rashin, Gaming, Apps & Tools, disk dan layout, pembuatan akun, enkripsi, Review, serta instalasi yang masih berjalan. Rail langkah, pilihan yang tampak langsung, petunjuk keyboard, ringkasan layout, dan progres per tahap dapat diadaptasi. Layar selesai, login, dan desktop tidak tercakup dalam kumpulan ini. |
| Ryoku v1.0.7, `f7197d72d` | Pemilihan disk kosong dapat dilanjutkan ke Review tanpa mengetik. Ryoku meminta `ERASE` untuk operasi yang menghapus partisi yang sudah ada. Progres berasal dari penanda tahap dan keluaran backend. Source juga mendokumentasikan langkah setelah instalasi. [Alur TUI](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/installation/tui/README.md#the-step-flow) · [Kode Review dan progres](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/installation/tui/main.go#L3535) |
| Situs Ryoku, **Everything, already installed** | Rujukan untuk mengelompokkan isi desktop pertama dan menjelaskan fungsi tiap kelompok. Pilihan paket, mode offline, jumlah paket, serta ukuran Ryoku tidak menjadi spesifikasi ConstOS. [Situs Ryoku](https://ryoku.dev/) · [Manifest terdokumentasi Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/docs/preinstalled.md) |
| ConstOS `001a1db` | Baseline memisahkan Cage/Calamares live dari target Hyprland. Wizard memakai Location, Keyboard, Users, Disk dengan pengetikan path, dan Summary. Hasil baseline serta revisi berikutnya dicatat di [roadmap](../implementation_plan.md). [Sumber wizard](../installer/settings.conf) · [Modul Disk](../packages/constos-calamares/constosdisk.cpp) |

Screenshot adalah referensi tampilan. Urutan dan akibat aksi Ryoku ditelusuri ke source yang dipatok di atas. Kumpulan gambar lokal dan data akun di dalamnya tidak disalin ke repositori.

## Alur utama yang dituju

1. **Boot dari ISO.** GRUB membuka **Install ConstOS** sebagai pilihan utama dan menyediakan **ConstOS Diagnostics** sebagai jalur konsol. Setelah pilihan utama, splash dan sesi Cage menunjukkan bahwa installer sedang disiapkan. Jika startup gagal, pengguna bisa melihat alasan dan mencapai diagnosis atau membuka installer lagi.
2. **Siapkan instalasi dalam satu wizard Calamares.** Bahasa awal antarmuka Inggris. Pengguna mengatur keyboard, locale, waktu, jaringan, browser, disk, dan akun. Setiap layar menunjukkan langkah aktif, pilihan sekarang, dan aksi **Back**, **Continue**, atau **Cancel** yang sesuai. **Review** menampilkan rencana sebelum ada perubahan pada disk.
3. **Jalankan instalasi.** **Install ConstOS** memulai preflight dan verifikasi arsip bertanda tangan. Partisi dibuat setelah tahap itu berhasil. Progres dan pesan kegagalan mengikuti status backend.
4. **Selesaikan dan boot dari disk.** Setelah backend selesai dan mount target dilepas, layar **Installation complete** menawarkan **Restart** dan menjelaskan agar media instalasi dilepas atau boot diarahkan ke disk terpasang. ISO dan target adalah dua sesi terpisah. Jika VM masih memilih ISO, perbaiki urutan boot atau lepas ISO sebelum menilai target.
5. **Login ke target.** Boot dari disk membuka SDDM tanpa autologin. Pilih akun yang dibuat saat instalasi. Untuk akun tunggal yang sudah dipilih, fokus awal ada pada kata sandi. Autentikasi yang berhasil membuka Hyprland dan aplikasi hari pertama.
6. **Welcome desktop.** Tur muncul satu kali per akun setelah sesi Hyprland siap. Pengguna bisa melewati, membuka ulang dari launcher, dan melihat **Recommended Apps**. Welcome ini memiliki state per pengguna dan terpisah dari halaman Welcome installer di ISO.

**Batas iterasi awal.** CachyOS x86_64, UEFI, Hyprland, disk kosong minimal 32 GiB, dan instalasi online. Pertahankan Cage dan Calamares beserta backend saat ini. Profil hardware manual, compositor alternatif, pilihan terminal/file manager, Gaming, dual boot, enkripsi, instalasi offline, pengaturan partisi manual, serta akun tambahan memiliki scope dan uji tersendiri. Installer awal menyediakan satu akun administrator. Foot, Bash, dan Thunar tetap menjadi pilihan awal desktop.

## Langkah wizard dan keputusan UI

| Langkah | Perilaku dan syarat penerimaan |
| --- | --- |
| Welcome | Jelaskan disk kosong, kebutuhan unduhan, dan bahwa Review adalah kesempatan terakhir sebelum **Install**. Tampilkan kendala yang relevan dan langkah pemulihannya. Pengguna bisa membuka wizard tanpa jaringan atau tanpa disk. Bedakan pembukaan wizard dari kesiapan memasang. |
| Keyboard → Language & Formats → Time Zone | Pilih layout sebelum akun, dengan input uji yang benar-benar memakai layout sesi. Default bahasa/format `en_US.UTF-8`, layout US, dan zona waktu awal `America/New_York` mengikuti baseline. Tampilkan default itu dan biarkan pengguna menggantinya. Pilihan zona waktu tidak otomatis mengganti bahasa UI. Pakai daftar berfilter untuk katalog panjang dan pilihan yang terlihat langsung untuk daftar pendek. |
| Network | Pakai status NetworkManager untuk Ethernet dan Wi-Fi. Tampilkan perangkat, koneksi aktif, aksi sambung/ulang, serta pesan gagal di langkah terkait. Pengguna dapat mengisi pilihan sambil offline. Review menunjukkan kendala jaringan yang diketahui. Preflight tetap menjadi sumber keputusan untuk unduhan dan verifikasi paket, dengan alasan yang bisa ditindaklanjuti bila gagal. |
| Browser | Tampilkan **Brave · Recommended**, **Firefox**, **Chromium**, dan **No browser**. Satu pilihan menghasilkan paling banyak satu browser dari wizard. Tampilkan yang akan dipasang dan perubahan default sebelum **Install**. Rincian pengiriman ada di [pilihan browser](#pilihan-browser). |
| Disk | Tampilkan nama/model jika tersedia, path, kapasitas, dan identitas tambahan untuk membedakan perangkat yang serupa. Target harus dipilih dengan sengaja, lalu **Continue** aktif tanpa pengetikan path. Perlihatkan ringkasan GPT, ESP FAT32 1 GiB, dan Btrfs dengan `@`, `@home`, serta `@snapshots`. Jika kosongnya daftar menghalangi lanjut, jelaskan syarat dan sediakan **Check again**. |
| Account | Buat satu administrator dengan username dan kata sandi, konfirmasi kata sandi, nama lengkap, dan hostname sesuai kebijakan backend. Target desain mengunci root dan memakai sudo dari akun administrator. Migrasikan [konfigurasi Users](../installer/modules-config/users.conf) yang sekarang mengaktifkan kata sandi root dengan opsi pakai ulang. Buktikan hasilnya pada target. Validasi langsung dan fokus ke field yang perlu diperbaiki. Kata sandi tidak tampil di Review, progres, atau log. |
| Review | Ringkas keyboard, locale, waktu, browser, identitas disk dan layout, username serta hostname. Tautan **Edit** kembali ke pilihan terkait dan perubahan tercermin saat kembali. Beri peringatan bahwa instalasi memakai seluruh disk yang ditampilkan. **Install ConstOS** adalah konfirmasi eksplisit terakhir. |
| Installing → Complete | Tampilkan tahap aktif, tahap yang sudah selesai, dan **Installation details** yang dapat dibuka. Gunakan penanda backend untuk mengecek disk, mengunduh dan memverifikasi paket, membuat storage, memasang sistem, konfigurasi akun/boot, dan unmount. Saat pekerjaan belum bisa dihitung, pakai indikator tak tentu. Kegagalan sebelum partisi dapat memberi **Retry** atau **Back to Review** jika state aman. Kegagalan setelah partisi menjelaskan tahap dan jalur diagnosis. |

Desain visual mengikuti [design.md](../design.md). Prototipe review memakai gaya Monochrome, daftar pilihan keyboard-friendly, dan progres simulasi. Untuk runtime, jangan memakai timer untuk mengklaim tahapan selesai atau menampilkan log contoh. Uji Tab, tombol panah, Enter, Back, Cancel, fokus setelah pesan gagal, teks panjang, dan skala kecil. Gaya dari Ryoku menjadi referensi hierarki dan interaksi. Identitas, aset, serta implementasi antarmuka milik ConstOS.

Kiosk kembali ke menu tindakan jika launcher keluar. Halaman **Installation complete** hanya diaktifkan pada antrean Calamares yang sukses, sesudah job unmount. **Restart** menjalankan perintah dari [konfigurasi Finished](../installer/modules-config/finished.conf). Cancel atau error kembali ke menu buka ulang; state sebelum partisi dan retry di wizard tetap memiliki gerbang penerimaan tersendiri.

### Placeholder Const Harness

Rashin memberi referensi letak pilihan agen. Jika dipakai untuk review, tampilkan **Const Harness** dengan pilihan **Yes/No** dan label yang menjelaskan bahwa itu simulasi. Kedua pilihan hanya mengubah tampilan pilihan pada prototipe. Hasil paket, layanan, pengaturan startup, izin, akun, dan transaksi installer identik. Wizard yang dikirim di ISO menyembunyikan pilihan tersebut sampai paket dan lifecycle Harness lulus penerimaan di fase 11. Desktop dasar tetap bisa dipakai tanpa Harness.

### Kontrak pemilihan disk

Pemilih mengirim identitas dari snapshot kandidat yang dibuat backend. UI dapat menampilkan path, tetapi teks bebas dari UI tidak menjadi target partisi. Penolakan media ISO, drive lepas-pasang, disk read-only, disk berpartisi atau bermount, dan disk dengan signature tetap berlaku. Backend memeriksa ulang identitas dan kelayakan saat preflight dan tepat sebelum operasi partisi. Jika perangkat berganti, hilang, atau berubah setelah Review, hentikan dan minta pengguna memilih lagi.

Cutover mengubah modul `constosdisk`, pengiriman data lewat GlobalStorage, job preflight, dan pengujian backend dalam satu perubahan. Pemeriksaan yang kini memerlukan teks path diganti dengan validasi pilihan dari snapshot dan tindakan **Install ConstOS** di Review. Pastikan modul lama atau nilai pilihan yang tertinggal tidak memberi jalan untuk mempartisi. Mode yang menghapus data dari disk terisi berada di luar dukungan iterasi ini.

## Pilihan browser

| Pilihan | Sumber yang dituju | Hasil pada instalasi baru |
| --- | --- | --- |
| **Brave · Recommended** | `brave-bin` dari repo generik `[cachyos]` x86_64. [Katalog CachyOS](https://packages.cachyos.org/package/cachyos/x86_64/brave-bin) | Pilihan awal. Brave terpasang, muncul di launcher, dan membuka URL serta HTML secara default setelah login. |
| **Firefox** | `firefox` dari `[extra]`. [Katalog Arch](https://archlinux.org/packages/extra/x86_64/firefox/) | Firefox menjadi browser terpilih dan default. |
| **Chromium** | `chromium` dari `[extra]`. [Katalog Arch](https://archlinux.org/packages/extra/x86_64/chromium/) | Chromium menjadi browser terpilih dan default. |
| **No browser** | Daftar paket browser kosong. | Wizard tidak memasang browser dan tidak membuat handler yang menunjuk executable yang tidak ada. Desktop inti tetap siap. |

Pemetaan ID pilihan ke paket dan desktop entry harus berasal dari satu allowlist. Sebelum menampilkan opsi sebagai siap, buktikan resolusi repo, signature, dependensi, dan desktop entry paket yang dipakai. Gunakan transaksi preflight yang sama dengan sistem dasar. Jika pilihan gagal diunduh atau diverifikasi, tampilkan error dan izinkan kembali untuk memilih opsi lain sebelum perubahan disk. Jangan menjalankan AUR helper atau skrip unduhan di installer. Rujukan upstream Brave menjelaskan jalur distribusi lain, sedangkan ConstOS memakai paket repo CachyOS yang ditetapkan di atas. [Distribusi Brave di Linux](https://brave.com/linux/)

Cutover memindahkan `firefox` dari [manifest target](../installer/target-packages.x86_64) dan dependensi wajib [`constos-desktop`](../packages/constos-desktop/PKGBUILD) ke pemilihan browser. Sesuaikan [default MIME Firefox saat ini](../desktop/mimeapps.list) bersama penerapan pilihan di target. Validasi handler HTTP, HTTPS, dan HTML memakai desktop entry dari paket yang benar, dengan uji launcher serta `xdg-open` sebagai akun baru. Update paket lewat pacman. Pertahankan browser yang sudah terpasang dan override pengguna pada upgrade. Evaluasi Zen setelah jalur repo, update, dan default MIME mempunyai bukti tersendiri.

## Isi desktop hari pertama

Tabel ini mengelompokkan pengalaman yang harus tersedia setelah login. Status **sumber saat ini** berarti ada di manifest atau paket yang dirujuk. Gerbang runtime mengikuti roadmap. Jangan menghitung paket dari situs Ryoku sebagai paket ConstOS.

| Kelompok | Sumber saat ini | Target rilis awal dan tindak lanjut |
| --- | --- | --- |
| Sistem dan boot | CachyOS BORE, firmware, GRUB, Plymouth, SDDM, Btrfs, Snapper, ZRAM, `const doctor` dan `const update`. | Instal, login, diagnosis, pembaruan, dan verifikasi snapshot dari disk. Ukur jejak target dari VM bersih setelah boot dan update. |
| Desktop dan grafik | Hyprland, Waybar, Wofi, Mako, Swaylock, portal Hyprland/GTK, dan tema ConstOS. | Launcher, workspace, notifikasi, lock/logout, dan izin portal dapat dipakai sebelum perluasan shell. Const Hub, Const Store, Dock, Island, dan widget mengikuti gerbang desktop. |
| Jaringan, Bluetooth, dan audio | NetworkManager, BlueZ/Blueman, PipeWire/WirePlumber, dan pavucontrol. | Pastikan koneksi dan output audio dapat dipakai setelah login. Uji pemasangan Wi-Fi dalam installer terpisah dari jaringan pada target. |
| Aplikasi harian | Firefox, Thunar, Mousepad, Ristretto, Evince, dan File Roller. | Browser mengikuti pilihan wizard. Pertahankan Thunar dan aplikasi inti untuk file, teks, gambar, PDF, dan arsip. Evaluasi `mpv` sebagai pemutar ringan setelah baseline, dengan tes playback dan MIME. |
| Terminal dan CLI | Foot, Bash, `btop`, `fastfetch`, `curl`, `wget`, `rsync`, dan `unzip`. | Pertahankan terminal dan CLI baseline. Usulan tambahan dev ringan `git`, `ripgrep`, dan `jq` perlu bukti penggunaan serta dampak ukuran sebelum masuk default. Toolchain Go, Node/npm, build tools, dan IDE masuk profil opsional setelah installer stabil. |
| Capture dan font | `constos-screenshot` dengan grim/slurp/clipboard, Noto Sans, Noto Emoji, JetBrains Mono Nerd Font, dan ikon Papirus/Adwaita. | Buktikan screenshot dan fallback font pada target. Recorder, OCR, dan alat media tambahan mengikuti roadmap masing-masing. |
| Aplikasi tambahan | Flatpak dan Recommended Apps dengan LibreOffice, VLC, LocalSend, dan KeePassXC. | Pengguna memilih unduhan dari desktop. Const Store kelak berbagi backend katalog yang sama. Gaming dan virtualisasi tidak masuk wizard awal. Harness serta Wine/Waydroid tetap jalur terpisah sesuai penerimaan masing-masing. |

Sumber inventaris yang diuji adalah [manifest target](../installer/target-packages.x86_64), [resep paket desktop](../packages/constos-desktop/PKGBUILD), serta [katalog Recommended Apps](../desktop/welcome/catalog.py). Saat menambah paket, catat pemilik, fungsi, scope live/target, sumber, jalur update, pengaruh pada ukuran, dan cara membuktikan aksi dari akun biasa.

## Urutan perubahan dan gerbang

| Urutan | Hasil yang perlu dibuktikan |
| --- | --- |
| 1. Reproduksi baseline | Gunakan ISO Linux yang SHA dan paketnya tercatat, serta disk VM kosong yang identitasnya diketahui. Jalankan GRUB → Cage → wizard → install → lepas ISO → login SDDM → Hyprland. Catat titik gagal aktual dari log dan tampilan. Bedakan kegagalan launcher, paket, boot target, autentikasi, dan startup sesi. |
| 2. Benahi satu irisan installer | Boot, Welcome, pilihan disk dan Review, progres nyata, lalu Finish/Restart. Pertahankan desktop dasar agar regressi mudah diisolasi. Buktikan penolakan disk yang berubah dan kegagalan unduh tanpa perubahan disk. Perbaiki handoff ke login sampai bisa diulang dari disk baru. |
| 3. Integrasikan pilihan | Uji Network, locale/keyboard, akun, browser yang dipilih, dan No browser. Setiap pilihan memiliki perilaku target yang terbukti. Pastikan login tanpa autologin, browser yang sesuai, file manager, terminal, audio, dan Welcome satu kali. |
| 4. Kembali ke roadmap desktop | Lanjutkan pekerjaan shell/Hub/Store dari target terpasang yang sudah dibuktikan. Poles tema, widget, Dock, Island, dan Harness sesuai dependensi gerbang berikutnya. |

Gerbang installer memerlukan build yang sama untuk seluruh alur utama dan bukti kegagalan yang ditargetkan pada VM terpisah. Smoke tanpa disk, screenshot Ryoku, dan prototipe browser menjadi bukti untuk bagiannya masing-masing. Simpan SHA, checksum ISO, versi paket, profil VM, dan hasil login/desktop tanpa memasukkan log atau media pribadi ke Git.
