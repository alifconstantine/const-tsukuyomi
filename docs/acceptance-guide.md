# Pengujian terpadu boot, desktop, dan instalasi

Panduan ini mencakup GRUB, Plymouth, sesi installer Cage, dan desktop Hyprland terpasang pada UEFI. Skenario menjelaskan hasil yang harus dibuktikan. Build dan smoke otomatis mengikuti [panduan build](build-guide.md), sedangkan hasil aktual dicatat di [roadmap](../implementation_plan.md).

## Siapkan build dan disk uji

Gunakan ISO baru dari sumber yang diuji. Catat checksum, identitas sumber, versi paket, firmware, CPU/RAM VM, waktu, serta direktori bukti. ISO lama yang pernah boot tidak membuktikan perubahan tema atau installer baru. Jangan menguji installer pada disk host atau disk berisi data.

Smoke otomatis menguji dua entri GRUB pada VM tanpa disk target. Untuk pengujian installer manual, buat VM terpisah dengan **satu disk virtual baru**, minimal 32 GiB, RAM awal 8 GiB atau lebih, 4 vCPU, UEFI non-Secure-Boot, dan koneksi internet. Cache unduhan paket menggunakan ruang sesi live. Pemeriksaan installer harus gagal sebelum partisi jika sumber daya tidak cukup.

Contoh berikut dijalankan sebagai user biasa di host Linux yang sudah memenuhi prasyarat QEMU/OVMF. Sesuaikan path ISO dan firmware sesuai host. Direktori run harus baru; image/NVRAM lama tidak ditimpa.

```bash
iso=/path/ke/constos-build-yang-diuji.iso
run="$PWD/iso/out/install-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -- "$run"
qemu-img create -f qcow2 "$run/target.qcow2" 32G
cp -- /usr/share/edk2/x64/OVMF_VARS.4m.fd "$run/vars.fd"
vm() {
    qemu-system-x86_64 -name ConstOS-install-QA \
        -machine q35 -accel kvm -cpu host -smp 4 -m 8192 \
        -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.4m.fd \
        -drive "if=pflash,format=raw,unit=1,file=$run/vars.fd" \
        -drive "if=none,id=target,format=qcow2,file=$run/target.qcow2" \
        -device virtio-blk-pci,drive=target,serial=CONSTOS-QA-EMPTY \
        -device virtio-vga -nic user,model=virtio-net-pci "$@"
}
vm -drive "file=$iso,media=cdrom,format=raw,readonly=on" -boot order=d
```

Audio VM membutuhkan perangkat HDA dan backend audio QEMU yang tersedia di host; contoh di atas tidak mengaktifkan audio. Tambahkan backend/perangkat tersebut sebelum menguji playback. Jangan menyebut perangkat audio tidak ada sebagai kelulusan skenario audio.

Di guest, periksa `lsblk -d -o NAME,SIZE,MODEL,SERIAL,WWN`. Disk target harus cocok dengan serial `CONSTOS-QA-EMPTY` dan ukuran image baru. Bila tidak cocok, berhenti. Tidak ada disk fisik host, direktori home, atau perangkat blok host yang boleh diteruskan ke VM.

## Boot dan login

| Skenario | Hasil yang harus diamati |
| --- | --- |
| GRUB normal | Identitas ConstOS, warna dan teks terbaca, timeout bekerja, navigasi panah/Enter jelas; kernel serta initramfs yang benar terpilih |
| GRUB teks | Lewat console GRUB, `unset theme` lalu `terminal_output console`; kembali ke menu dan buktikan entri boot tetap bisa dipakai tanpa tema |
| Diagnostics | Cold boot entri console; desktop tidak dimulai, `journalctl -b` dapat dibaca dari TTY |
| Plymouth | Logo/progres terlihat, Escape membuka log, boot tetap maju; kegagalan grafis tidak memutus jalur teks |
| Installer live | **Install ConstOS** membuka **Welcome** Calamares dalam sesi Cage dengan disk uji yang memenuhi syarat. Tanpa disk, tampil pesan **No eligible empty disk found**. Uji bahasa Inggris awal, Tab, Enter, Esc, dan pemilihan ulang setelah batal atau gagal |
| SDDM | Buka **Sign-in options** untuk memilih pengguna, sesi, dan tata letak keyboard. Uji fokus Tab, Enter, dan menu daya. Dengan beberapa akun tanpa riwayat, pilih akun secara eksplisit. Uji juga jalur tanpa sesi terdaftar |
| Login target | Pada boot pertama dengan satu akun baru, pastikan nama akun tampil dan fokus berada di kata sandi. Enter mengirim login ke SDDM, kata sandi salah menampilkan error dan fokus kembali ke kolom, kata sandi benar membuka sesi ConstOS. Login ulang memakai akun terakhir yang masih tersedia |
| Recovery greeter | Pilih tema stock lewat konfigurasi di TTY sesuai panduan build, restart SDDM, dan pastikan login masih tersedia |

Simpan screenshot setiap tahap yang benar-benar terlihat. Live autologin dapat melewati greeter saat boot; itu bukan bukti tampilan greeter sudah diperiksa. Jangan menguji password atau sesi pribadi pada screenshot yang akan dibagikan.

Biarkan timeout GRUB memilih **Install ConstOS**. Batalkan wizard dari **Disk** dan **Summary** pada percobaan terpisah, lalu pastikan layar tindakan menawarkan **Open installer**, **Restart**, dan **Shut down**. Jalankan **Open installer** untuk memulai ulang. Pada cold boot lain, pilih **ConstOS Diagnostics** dan periksa TTY. Lanjutkan jalur utama sampai reboot tanpa ISO dan login di target.

## Welcome dan Recommended Apps

| Skenario | Hasil yang harus diamati |
| --- | --- |
| Login pertama | Setelah login ke disk terpasang, **Welcome** terbuka satu kali. Cek fokus dan Tab, cocokkan tiga pintasan dengan aksi, lalu tekan **Done** atau **Skip**. |
| Login berikutnya | Keluar dan masuk kembali. Welcome tidak muncul otomatis. Cari **Welcome** dan **Recommended Apps** di Wofi. Uji kedua entri ketika salah satunya sudah terbuka, lalu uji akun kedua yang belum pernah melihat Welcome. |
| Pemasangan | Buka katalog, klik **Install** pada satu aplikasi, amati status selama transaksi, lalu cocokkan **Installed** dengan `flatpak info --user ID_APLIKASI`. Buka aplikasi dari Wofi dan verifikasi aplikasi tetap tersedia setelah login ulang. |
| Kegagalan | Uji tanpa jaringan dan dengan remote bernama sama yang salah pada akun uji terpisah. Pastikan tidak ada status sukses, remote lama tetap utuh, dan percobaan ulang setelah kondisi dipulihkan berhasil. |

## Desktop terpasang

Uji skenario berikut setelah reboot dari disk. Gunakan fixture lokal nonpribadi untuk teks, gambar, PDF, dan arsip.

| Bagian | Skenario dan bukti |
| --- | --- |
| Launcher dan file | Buka Firefox, editor, viewer gambar/PDF, dan arsip dari launcher. Buka file serta URL dari Thunar; aplikasi default, nama, dan ikon harus sesuai |
| Clipboard teks | Copy/paste teks Indonesia, beraksen, dan non-Latin antar aplikasi; label/font tetap terbaca |
| Screenshot area | Tekan Print, pilih area berisi fixture, lalu paste gambar di aplikasi penerima. Isi dan dimensi harus sesuai pilihan |
| Screenshot cancel | Isi clipboard dengan teks yang diketahui, mulai seleksi lalu Escape. Paste kembali; clipboard lama tidak boleh berubah |
| Screenshot layar/error | Jalankan aksi layar dari panel dan periksa hasil. Uji tool/backend gagal hanya pada VM disposable; error harus terlihat tanpa notifikasi sukses palsu |
| Audio | Putar audio fixture, ubah volume/mute serta output melalui pavucontrol; dengarkan hasil. Jika perangkat input tersedia, periksa sumber dan level mikrofon secara terpisah |
| Portal | Buka file chooser dari aplikasi portal dan screen sharing browser. Pilih sumber fixture, periksa isi yang benar, lalu Stop/cancel/denied. Introspeksi interface saja bukan bukti screen sharing |
| Jaringan | Periksa DHCP dan akses halaman melalui jaringan VM. Wi-Fi fisik diuji pada perangkat tersendiri, bukan disimpulkan dari NAT VM |
| Bluetooth | Buka UI pairing. Jika adapter tidak diteruskan, catat unavailable; pairing hanya lulus bila diuji dengan perangkat nyata |
| Lock/logout | Lock dari keyboard/menu, autentikasi, logout lalu login ulang dua kali. Tidak boleh ada panel, tray, atau daemon notifikasi duplikat |
| Otorisasi | Dialog polkit tampil dalam sesi ketika aksi membutuhkannya; cancel tidak menjalankan aksi |
| Penyimpanan dan font | Uji trash, arsip, mount/eject media virtual tambahan, font fallback, dan layout keyboard yang dipilih |
| Ukuran dan keyboard | Periksa 100%/200%, layar kecil, fokus terlihat, Tab/Shift+Tab/Enter/Escape. Multi-monitor dan fractional scaling dicatat per skenario, bukan dianggap lulus dari satu output |

Diagnosis awal dari terminal guest:

```bash
systemctl --failed
systemctl --user --failed
hyprctl configerrors
nmcli general status
wpctl status
zramctl
xdg-mime query default text/plain
xdg-mime query default application/pdf
xdg-settings get default-web-browser
busctl --user introspect org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop
```

Output bersih atau interface tersedia tidak menggantikan aksi pengguna pada tabel. Jangan membagikan seluruh output `wpctl`, daftar koneksi, atau journal tanpa memeriksa informasi pribadi.

## Installer dan reboot tanpa ISO

Gunakan **ConstOS Diagnostics** untuk memeriksa binary dan modul Disk sesuai [panduan build](build-guide.md#siapkan-host-build). Log runtime ditulis ke `/run/constos-installer/calamares.log` dan `/run/constos-installer/pacman.log`.

1. Boot **Install ConstOS** dari GRUB. Periksa **Welcome → Location → Keyboard → Disk → Users → Summary**. Pertahankan bahasa bawaan untuk uji Inggris. Pada percobaan terpisah, pilih bahasa lain di **Welcome** dan periksa bahwa Calamares menerapkan pilihan itu pada halaman bawaannya.
2. Pilih disk kosong yang identitasnya sudah dicocokkan. Periksa path, kapasitas, dan detail identitas yang tersedia. Ketik path salah dan uji bahwa **Next** tetap nonaktif. Ketik path yang benar, lalu kembali dan ganti pilihan pada VM dengan dua disk uji untuk memastikan konfirmasi dikosongkan. Disk berpartisi, bermount, atau memiliki signature harus ditolak. Setelah Cancel, periksa bahwa disk uji belum berubah dan pilih **Open installer**.
3. Buat akun baru, periksa disk pada **Summary**, lalu pilih **Install**. Periksa bahwa password tidak muncul pada Summary atau log. Halaman selesai hanya boleh muncul setelah seluruh backend berhasil.
4. Pada VM terpisah, uji jaringan/mirror gagal sebelum preflight, lalu uji putus jaringan setelah preflight selesai. Pemasangan sesudah partisi harus memakai arsip transaksi terverifikasi tanpa sinkronisasi atau unduhan repo baru.
5. Setelah selesai, matikan guest, lalu jalankan **`vm -boot order=c`** dari shell host yang sama. Tidak ada drive ISO pada perintah ini. Jangan sekadar reboot dengan ISO masih terpasang.
6. Login melalui SDDM dengan akun baru. Periksa `/etc/os-release`, kernel, jaringan, desktop, filesystem, ZRAM, dan ulangi skenario desktop di atas.

Pemeriksaan target dilakukan di guest yang baru terpasang:

```bash
findmnt /
findmnt /home
findmnt /.snapshots
findmnt /boot/efi
cat /etc/fstab
cat /proc/cmdline
getent passwd liveuser
systemctl is-enabled NetworkManager sddm
pacman -Q constos-core constos-desktop linux-cachyos-bore
snapper -c root list
```

`getent passwd liveuser` diharapkan tidak menemukan akun (exit 2), bukan lulus karena command exit 0. Periksa pula bahwa tidak ada sudo tanpa password khusus ISO, autologin live, service pacman-init khusus ISO, hook `archiso`, atau repo paket sementara pada target. Jangan memasang Calamares atau alat build ISO ke target sebagai pengganti pemisahan yang benar.

Setelah integrasi kompatibilitas tersedia, lanjutkan dengan [skenario penerimaan aplikasi Windows dan Android](app-compatibility.md#skenario-penerimaan) pada target yang sama. Putuskan jaringan sesudah instalasi ConstOS untuk membuktikan penggunaan pertama runtime yang sudah disediakan.

## ConstOS Doctor

Di sistem terpasang, jalankan `const doctor` sebagai pengguna biasa dari terminal desktop dan TTY. Bandingkan hasil dengan `uname -r`, `/proc/swaps`, `systemctl --failed`, keberadaan `/etc/snapper/configs/root`, `df -h /`, dan `findmnt --mountpoint /.snapshots`. `WARN` mencatat kondisi seperti penanda BORE yang tidak ditemukan. `FAIL` melaporkan temuan seperti unit gagal, ruang tersedia di `/` habis, atau `/.snapshots` tidak ter-mount. `UNKNOWN` berarti pemeriksaan tidak selesai. Doctor mengembalikan exit status `1` jika ada `FAIL` atau `UNKNOWN` dan `0` jika keduanya absen.

Untuk menguji kegagalan pada VM disposable, jalankan `sudo systemd-run --unit=constos-doctor-qa --wait /usr/bin/false`, lalu jalankan kembali `const doctor` tanpa `sudo`. Pastikan laporan menyebut `constos-doctor-qa.service` dan exit status `1`. Bersihkan unit uji dengan `sudo systemctl reset-failed constos-doctor-qa.service`. Penerimaan restore file dan rollback tetap mengikuti skenario recovery di bawah.

## Update dan recovery

Di ConstOS terpasang, jalankan `const update` dari terminal sebagai pengguna dengan hak administrasi. Masukkan password jika diminta `sudo`. Tinjau daftar paket dari pacman dan konfirmasi sesuai prompt. OS dan aplikasi yang tersedia dari repo pacman yang dikonfigurasi ikut dalam transaksi penuh. Paket ConstOS dapat ikut diperbarui setelah repo rilisnya tersedia. Aplikasi dari pengelola paket lain mengikuti mekanisme masing-masing.

- Di VM uji, catat daftar paket terpasang sebelum transaksi. Batalkan pada prompt akhir dan cocokkan kembali daftar tersebut. Sinkronisasi database repo dapat terjadi sebelum pembatalan.
- Jalankan `const update` kembali dan setujui transaksi. Periksa versi paket dan hasil akhir pacman. Jika kernel berubah, reboot dari disk tanpa ISO, periksa kernel/initramfs, jaringan, preferensi pengguna, dan jalankan `const doctor`.
- Uji terminal noninteraktif, sesi live, koneksi putus, dan paket ditolak. Kegagalan sebelum atau selama transaksi harus menghasilkan status keluar sesuai hasil yang dilaporkan. Untuk daftar yang sudah mutakhir, pastikan pacman melaporkan bahwa tidak ada paket yang perlu dipasang.
- Buat snapshot sebelum perubahan fixture sistem yang dapat dipulihkan. Buktikan restore satu file dari snapshot, lalu latihan recovery sistem melalui jalur rescue yang didokumentasikan. Snapshot terdaftar saja belum membuktikan rollback bisa boot.
- Jika greeter/compositor gagal, boot Diagnostics/rescue dari ISO dan ambil diagnosis dari TTY. Gunakan hanya disk virtual dengan identitas yang sama saat melakukan mount/chroot.
- ESP dan `/boot` yang terpisah tidak otomatis tercakup snapshot root. Jangan mengklaim pemulihan kernel, bootloader, atau data home dari snapshot root tanpa mengujinya.

LUKS, dual boot, offline install, Secure Boot, dan GPU khusus berada di luar jalur uji awal ini. Tema adaptif Settings, recorder, dan Harness juga tidak ikut dinyatakan selesai oleh pengujian boot/installer.

## Catatan hasil

Untuk setiap skenario tulis **lulus**, **gagal**, **belum diuji**, atau **tidak tersedia**, beserta lingkungan live/installed/hardware, build/checksum, versi, langkah, hasil aktual, dan lokasi bukti. Simpan log instalasi untuk kegagalan, tetapi redaksi password, username pribadi, serial perangkat, SSID, dan path sensitif. Jangan commit ISO, disk VM, NVRAM, atau rekaman mentah.
