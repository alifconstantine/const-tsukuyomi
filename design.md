# Desain ConstOS

Status: rancangan awal, 7 November 2026. Palet vendor statis sudah diterapkan pada sumber boot/greeter dan desktop fallback; pemilih aksen, generator wallpaper, serta Settings masih merupakan rancangan. Status implementasi dan bukti penerimaan tetap di [roadmap](implementation_plan.md); batas komponen di [arsitektur](docs/architecture.md).

## Arah visual

ConstOS memakai dasar hitam dan putih dengan biru sebagai aksen bawaan. Permukaan gelap bertingkat memisahkan konten; teks, jarak, dan garis memberi hierarki sebelum dekorasi. Gaya ini dipakai dari boot, login, desktop, hingga Settings dan capture.

- Tema gelap menjadi default pertama. Hitam murni dan putih murni tersedia untuk kebutuhan aset; area kerja memakai near-black dan off-white agar hierarki permukaan tetap terlihat.
- Aksen menunjukkan aksi utama, fokus, pilihan, dan kontrol aktif. Hindari memberi warna berbeda pada setiap metrik atau modul panel tanpa makna status.
- Pengguna dapat memilih aksen manual atau mengikuti wallpaper melalui Settings. Desktop dasar tidak membutuhkan Harness, akun, atau layanan daring.
- Gunakan surface solid sebagai baseline. Blur/transparansi hanya tambahan jika kontras dan performanya lulus; selalu ada tampilan solid yang bisa dipakai.
- Hindari neon, glow, gradien dekoratif, bayangan tebal, serta semua kontrol berbentuk pill. Logo bukan ornamen berulang pada setiap panel.

Ryoku menjadi referensi perilaku tema adaptif, bukan klaim kompatibilitas atau penyalinan implementasi. Adaptasi kode/aset memerlukan audit sumber dan lisensi tersendiri.

## Logo

Simbol resmi ConstOS adalah logo Const yang dipilih pengguna dari README, dengan master [assets/const-logo.svg](assets/const-logo.svg). Bentuk digambar ulang sebagai dua path vektor; tidak menyematkan PNG. Logo C geometris dengan kotak biru tidak lagi digunakan.

Gunakan simbol putih pada surface gelap dan hitam pada surface terang. Warna logo tidak mengikuti aksen pengguna atau wallpaper. Ikon aplikasi memakai badge gelap agar terbaca pada kedua tema; nama produknya tetap **ConstOS**.

README, SDDM, dan Calamares memakai SVG. GRUB dan Plymouth memakai satu ekspor PNG transparan 160×160 dari master yang sama. Ekspor serta status hak aset dicatat di [manifest](assets/manifest.json); logo sumber belum memiliki audit izin redistribusi yang lengkap. Regenerasi mengikuti [panduan build](docs/build-guide.md#ekspor-logo).


## Palet dan token warna

Nama token menyatakan peran, bukan nama warna. Komponen memakai token semantik; nilai hex berikut adalah baseline tema gelap, bukan warna yang boleh disalin bebas ke setiap toolkit.

| Token | Nilai awal | Penggunaan |
| --- | --- | --- |
| `canvas` | `#161616` | Latar dasar desktop dan jendela |
| `surface` | `#1E1E1E` | Panel, sidebar, kartu, dan menu |
| `surface-raised` | `#262626` | Dialog dan permukaan di atas panel |
| `surface-hover` | `#303030` | Hover pada kontrol netral |
| `border-subtle` | `#383838` | Pemisah dekoratif; bukan satu-satunya penanda kontrol |
| `control-border` | `#808080` | Batas kontrol saat diperlukan agar dapat dikenali |
| `text` | `#F5F5F5` | Teks utama dan ikon netral |
| `text-muted` | `#B0B0B0` | Deskripsi, metadata, placeholder |
| `accent` | `#60A5FA` | Aksi utama, fokus, dan kontrol aktif |
| `on-accent` | `#101010` | Label/ikon di atas isi aksen |
| `accent-surface` | `#20324A` | Latar pilihan dengan teks `text` |
| `success` | `#4ADE80` | Operasi selesai atau status sehat |
| `warning` | `#FBBF24` | Kondisi yang membutuhkan perhatian |
| `error` | `#F87171` | Kesalahan, penolakan, dan aksi destruktif |

Biru adalah aksen default, bukan warna wajib selamanya. Warna success/warning/error tidak mengikuti wallpaper atau aksen pilihan. Status juga memiliki label atau ikon agar makna tidak bergantung pada warna. Indikator rekaman dan akses computer use tetap eksplisit, dengan Stop yang terlihat.

Target kontras: teks biasa minimal 4,5:1; teks besar minimal 3:1; penanda fokus dan batas kontrol yang diperlukan minimal 3:1 terhadap permukaan yang berdampingan. Ukur setiap pasangan aktual, termasuk hover, selected, dan palet adaptif. `border-subtle` tidak memenuhi peran batas kontrol aksesibel. Disabled memakai label/state yang jelas, bukan sekadar menurunkan opacity seluruh komponen.

Perhitungan sRGB pada baseline menghasilkan kontras `text`/`surface-raised` 13,88:1, `text-muted`/`surface-raised` 6,98:1, dan `on-accent`/`accent` 7,48:1. Ini pemeriksaan nilai warna, bukan bukti hasil render atau kelulusan aksesibilitas seluruh UI.

## Tema adaptif dan Settings

### Pilihan aksen

| Mode | Perilaku rancangan |
| --- | --- |
| Default | Menggunakan biru dari palet vendor |
| Manual | Pengguna memilih preset atau warna kustom; mengganti wallpaper tidak mengganti aksen |
| Wallpaper | Mengambil kandidat warna dari wallpaper yang dipilih dan menurunkan aksen beserta token turunannya |

Mode Wallpaper menyesuaikan aksen, latar selected, hover beraksen, dan fokus. Canvas serta teks tetap netral pada tahap pertama agar foto yang sangat terang, gelap, atau berwarna kuat tidak mengubah keterbacaan seluruh desktop. Tema terang merupakan rancangan terpisah yang memerlukan palet dan verifikasi sendiri; wallpaper terang tidak otomatis mengaktifkannya.

### Aturan pembentukan palet

1. Ekstraksi dilakukan lokal dari berkas wallpaper yang dipilih; tidak mengunggah gambar atau memindai folder pribadi. Implementasi awal menargetkan gambar statis. Wallpaper bergerak tidak memicu ekstraksi per frame.
2. Pilih kandidat berwarna yang representatif, lalu sesuaikan luminansi/saturasi untuk kontras. `on-accent` dipilih dari pasangan terang/gelap yang memenuhi kontras; jangan mengasumsikan teks putih selalu terbaca.
3. Hasil harus deterministik untuk gambar, pengaturan, dan versi generator yang sama. Ekstraktor dan algoritme final dipilih setelah spike; dokumen ini tidak menetapkan dependensi baru.
4. Wallpaper grayscale atau kandidat yang tidak dapat memenuhi kontras memakai biru default dengan penjelasan di preview. Warna manual yang disesuaikan untuk kontras menampilkan warna masukan dan hasil efektif, bukan diam-diam menyimpan nilai berbeda.
5. Jika berkas hilang, rusak, atau generasi gagal, pertahankan tema terakhir yang valid dan tampilkan error. Jangan menandai penerapan baru sebagai sukses. Jika belum ada hasil valid, gunakan default vendor.
6. Untuk beberapa monitor, pengguna memilih wallpaper sumber tema; default-nya monitor utama. Satu palet berlaku untuk satu sesi. Fokus jendela atau perpindahan pointer tidak mengganti tema. Monitor sumber yang dicabut mempertahankan palet sampai pengguna memilih sumber lain.

### Alur Appearance

Halaman **Settings → Appearance** menyediakan pilihan wallpaper, mode aksen, pemilih warna manual, sumber wallpaper pada multi-monitor, ukuran teks/UI, reduced motion, dan reset tema.

- Preview menampilkan tombol utama, input dengan fokus, selected row, notifikasi, dan state error; bukan hanya kotak swatch.
- Apply menyimpan preferensi dan menerapkan hasil valid. Cancel atau Escape membuang preview dan mengembalikan tema sebelumnya.
- Saat mode Wallpaper aktif, penerapan wallpaper lewat Settings juga menerapkan paletnya. Perubahan wallpaper dari alat lain hanya diikuti jika adapter dapat mendeteksinya; jika belum tersedia, UI menjelaskan batas itu dan menyediakan regenerasi eksplisit.
- Tampilkan state pending dan kegagalan penerapan per adapter. Jangan mengklaim semua aplikasi berubah bila sebagian memerlukan reload atau tidak mendukung tema.
- Mode aktif menentukan sumber aksen; nilai manual tersimpan tidak menimpa mode Wallpaper. Reset mengembalikan pilihan tema vendor tanpa menghapus wallpaper pribadi, layout widget, atau data aplikasi.
- Pilihan pengguna bertahan setelah login ulang dan update. Pengguna kedua memiliki preferensi sendiri.

Pemilik preferensi, generasi token, dan batas live/installed mengikuti [kontrak tema](docs/architecture.md#ui-widget-dan-aset). Belum ada generator atau halaman Settings ini di profil live.

## Tipografi dan ikon

| Peran | Pilihan awal | Ukuran logis / bobot |
| --- | --- | --- |
| UI dan teks isi | Noto Sans, fallback sans-serif sistem | 14 px / 400 |
| Label kontrol dan navigasi | Noto Sans | 14 px / 500 |
| Judul bagian | Noto Sans | 18–20 px / 600 |
| Judul halaman | Noto Sans | 28 px / 600 |
| Caption dan metadata | Noto Sans | 12 px / 400 |
| Terminal, kode, dan nilai teknis | JetBrains Mono, fallback monospace | 13–14 px / 400 |

Ukuran adalah nilai awal pada skala 100%, bukan piksel fisik wajib. Gunakan line height sekitar 1,4 untuk teks isi, scaling toolkit, dan tinggi kontrol yang mengikuti ukuran teks. Jangan memakai bobot 800/900 untuk seluruh panel. Angka metrik memakai tabular numerals bila tersedia agar layout tidak bergeser.

Manifest live sudah mencantumkan `noto-fonts`, `noto-fonts-emoji`, dan `ttf-jetbrains-mono-nerd`; glyph aktual dan font fallback tetap perlu diperiksa pada target. Nerd Font hanya untuk konsumen yang membutuhkan glyph tersebut, bukan pengganti label aksesibel atau font UI umum. Uji teks Indonesia, English, non-Latin, emoji, dan label terjemahan panjang.

Ikon aksi memakai satu keluarga outline dengan ukuran awal 16, 20, dan 24 px. Gunakan ikon filled seperlunya untuk status aktif. Nama aksesibel wajib ada pada tombol ikon; tooltip tidak menjadi satu-satunya cara mengenali aksi. Papirus sudah ada dalam manifest untuk ikon aplikasi; set ikon aksi shell final beserta lisensinya belum dipilih.

## Bentuk, ukuran, dan gerak

- Spacing memakai kelipatan 4 px: 4, 8, 12, 16, 24, 32, 48. Padding kontrol awal 8–12 px; jarak antarbagian 24 px.
- Radius awal: kontrol 6 px, kartu/menu 10 px, dialog 14 px. Pill dipakai untuk badge atau switch, bukan seluruh permukaan.
- Border awal 1 px logis; fokus memakai ring 2 px yang tidak menggeser layout. Bedakan garis pemisah dekoratif dari batas kontrol.
- Tinggi kontrol awal 36 px, target sentuh minimal 44 px saat mode sentuh didukung. Jangan memotong teks pada ukuran font besar.
- Layout Settings memakai sidebar dan area konten; pada layar sempit navigasi dapat dipadatkan tanpa menghilangkan label/keyboard. Konten dialog dapat di-scroll dan aksi utama tetap terjangkau.
- Transisi awal 120–180 ms untuk hover/fokus dan 180–240 ms untuk membuka panel. Animasi tidak menunda aksi atau penutupan. Reduced motion menghilangkan perpindahan/resize dekoratif; state pending tetap dapat dikenali.
- Tidak ada animasi kontinu saat idle. Shadow ringan hanya untuk pemisahan lapisan; blur tidak menjadi syarat memahami hierarki.

## Komponen dan perilaku interaksi

| State | Aturan visual dan perilaku |
| --- | --- |
| Default / hover / pressed | Permukaan berubah secukupnya; label tidak berubah posisi |
| Focused | Ring jelas, urutan Tab masuk akal, aksi dapat dijalankan lewat keyboard |
| Selected / active | Aksen atau `accent-surface` disertai penanda pilihan; tidak disamakan dengan fokus |
| Pending | Tampilkan operasi berjalan; cegah pengiriman ganda untuk aksi yang sama |
| Disabled / unavailable | Jelaskan alasan atau capability yang hilang; jangan menampilkan aksi palsu |
| Error / denied | Pesan dekat sumber masalah, state lama tetap jujur, sediakan pemulihan yang relevan |
| Empty / offline | Tampilkan kondisi sebenarnya dan aksi yang masih tersedia, tanpa data contoh |

Tombol primary diisi aksen dan dibatasi satu aksi utama per kelompok. Tombol secondary memakai surface netral; aksi destruktif memakai label eksplisit serta token error. Input memiliki label tetap, bukan placeholder saja. Switch menggambarkan state backend aktual, termasuk pending dan kegagalan.

Escape menutup panel atau membatalkan preview yang bisa dibatalkan, lalu mengembalikan fokus. Klik luar boleh menutup menu ringan, tetapi tidak diam-diam membuang perubahan form atau menutup dialog consent penting. Dialog tidak mengambil fokus saat tidak diperlukan. Toast sukses hanya muncul setelah backend mengonfirmasi hasil.

## Penerapan lintas surface

| Surface | Pemakaian desain dan batas |
| --- | --- |
| GRUB dan Plymouth | Palet statis vendor, logo sederhana, kontras tinggi, navigasi/log teks tetap tersedia; tidak membaca wallpaper atau preferensi pribadi |
| SDDM | Identitas vendor yang sama, nama akun dan fokus ke kata sandi bila akun sudah dipilih. **Sign-in options** membuka pilihan akun, sesi, dan tata letak keyboard. Tema stock tersedia untuk recovery |
| Installer | Monochrome, rail langkah konsisten, pilihan yang terlihat atau dapat difilter, dan satu aksi utama. Welcome memakai nama ConstOS dan logo berukuran tetap. Fokus, alasan aksi nonaktif, dan pemulihan terlihat dekat langkah terkait. [Spesifikasi installer](docs/installer-plan.md#langkah-wizard-dan-keputusan-ui) |
| Lockscreen | Token sesi yang terakhir valid bila backend mendukung; autentikasi dan privasi lebih dahulu, tanpa riwayat clipboard/notifikasi sensitif |
| Shell dan Settings | Token semantik bersama; launcher, panel, Quick Settings, notifikasi, dan form memakai state yang sama |
| Capture dan izin | Sumber, status aktif, scope, durasi, cancel, dan Stop terbaca. Indikator tidak bergantung pada Island atau warna wallpaper |
| GTK, Qt, Foot, dan fallback | Adapter mengikuti kemampuan toolkit; aplikasi pihak ketiga tidak dijanjikan sepenuhnya mengikuti tema |
| Harness | Menjaga identitas studio yang selaras; sinkronisasi tema aplikasi belum diimplementasikan dan tidak menjadi dependensi desktop |

Jangan memakai wallpaper pribadi untuk boot/greeter global. Konfigurasi sesi live dan default target tetap terpisah sesuai arsitektur. Warna terminal ANSI mempertahankan makna serta kontrasnya; mengganti aksen shell tidak otomatis mengganti semua warna terminal.

## Arah Liquid Glass minimalis

Mulai dari satu launcher pada sesi Hyprland, dengan prototype Quickshell/QML. Gunakan kaca pada navigasi dan kontrol yang mengambang, dengan tint, blur bawaan compositor pada layer terpilih, batas tipis, dan aksen biru pada fokus atau pilihan aktif. Konten utama dan dialog penting memakai permukaan opak yang mudah dibaca. Sediakan **Reduce Transparency** dan **Reduce Motion**. Ukur kontras di wallpaper terang dan gelap, navigasi keyboard, skala, dan biaya render sebelum memperluas efek. [Apple HIG Materials](https://developer.apple.com/design/human-interface-guidelines/materials) · [Hyprland Layer Rules](https://wiki.hypr.land/configuring/core/rules/layer-rules/)

Desktop tetap lapang saat idle. Launcher dan menu sistem muncul saat diminta. Dock bawah berfungsi untuk pin dan berpindah antaraplikasi. Dynamic Island di tengah atas berfungsi untuk aktivitas yang sedang berlangsung. Uji keduanya sebagai opt-in pada beta, dengan toggle terpisah di **Const Hub → Appearance & Desktop**. Widget opsional memakai gaya yang sama. Const Hub dan Const Store memakai jendela berisi konten opak dengan material yang sama pada kontrol navigasinya.

Ryoku menjadi referensi untuk pemisahan installer dan desktop, token bersama, serta hit testing Kairos. Tetapkan token dan interaksi ConstOS sendiri sebelum meninjau adaptasi aset atau kode. Plugin refraksi dapat dinilai setelah blur bawaan dan fallback opak lolos pengujian. [Audit Ryoku](docs/audits/2026-11-08-ryoku-desktop.md)

## Kondisi awal dan keputusan yang belum selesai

Sumber tema boot/greeter serta Waybar/Wofi/Mako/Swaylock/Wlogout/Foot kini memakai palet vendor statis ini. `desktop/install.sh` memasang konfigurasi GTK/MIME/portal dan override default GSettings; `desktop/qt5ct/` dan `desktop/Kvantum/` masih belum dipasang oleh helper sehingga tidak diklaim aktif. Penerimaan visual setiap surface tetap menunggu pengujian pada build baru.

Keputusan dasar: dark-first, netral hitam/putih, aksen default biru, pilihan manual/wallpaper, Noto Sans untuk UI, dan token berbasis peran. Nilai ukuran, radius, dan durasi adalah baseline untuk prototype. Algoritme ekstraksi, set ikon shell, aset wallpaper/boot final, palet terang, serta pemetaan tiap toolkit masih memerlukan pilihan dan bukti uji. Toolkit shell tetap mengikuti spike pada roadmap.

## Review sebelum implementasi diperluas

Review pertama mengikuti GRUB → installer → Finish → boot dari disk → login SDDM → desktop sesuai [spesifikasi installer](docs/installer-plan.md#alur-utama-yang-dituju). Setelah alur tersebut terbukti, gunakan satu prototype Appearance dan review desktop → launcher → Settings. Tema menjaga jalur diagnosis tetap bisa diakses.

Review mencakup keyboard-only, kontras setiap state, pembaca layar pada toolkit yang dipilih, skala 100–200%, label panjang, layar kecil, dua monitor, dan reduced motion. Mode Wallpaper perlu gambar terang, gelap, grayscale, warna jenuh, berkas rusak/hilang, pergantian sumber monitor, serta pembuktian bahwa Cancel mengembalikan seluruh preview. Mode Manual harus bertahan saat wallpaper berubah.

Uji penerapan parsial/gagal, restart sesi, upgrade preferensi, dan pengguna kedua sebelum mengklaim tema adaptif didukung. Simpan identitas build dan screenshot surface aktual di bukti roadmap; jangan menyamakan preview desain, perhitungan warna, atau file token dengan UI yang telah lulus di Wayland.
