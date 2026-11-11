# Audit jendela dalam satu workspace

Laporan pengguna menyebut hanya jendela terakhir yang terlihat setelah beberapa jendela dibuka di workspace yang sama. Referensi Ryoku memperlihatkan banyak jendela terminal terpisah dalam susunan tile Dwindle. Audit memakai ConstOS `c5bd13a` dengan perubahan desktop dan Dux Shell `v2.1.2`, versi yang dicatat dalam [bukti Tsukuyomi](../../implementation_plan.md#koreksi-tsukuyomi--11-november-2026).

## Temuan sumber

- [Konfigurasi Hyprland efektif](../../desktop/hypr/hyprland.lua) memilih `dwindle` dan menyediakan fokus arah lewat Super+panah. `desktop/install.sh` memasangnya di `/etc/skel`. Akun yang sudah dibuat memakai konfigurasi di home, sehingga audit regresi harus membaca konfigurasi efektif akun tersebut. [Dokumentasi Dwindle](https://wiki.hypr.land/configuring/layouts/dwindle-layout/)
- Payload Ryoku `f7197d72d` juga memilih `dwindle`. Ryoku menyediakan Super+F untuk toggle fullscreen dan mengaktifkan `movefocus_cycles_fullscreen` dengan penanganan fokus lintas output. Aturan floating di Ryoku juga membatasi ukuran beberapa aplikasi terhadap monitor. Pertimbangkan perilaku tersebut jika bukti menunjukkan fullscreen atau jendela floating yang menutupi tile. [Bind Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/hyprland/modules/binds.lua#L20) · [Aturan jendela Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/hyprland/modules/window_rules.lua#L1)
- Ryoku mengabaikan permintaan maximize dari aplikasi. ConstOS menerapkan aturan serupa khusus pada kelas `kitty`. Kitty dapat mengingat state maximize dari instans sebelumnya. Super+F dapat mengembalikan jendela aktif dari fullscreen atau maximized ke ukuran tile. [Aturan maximize Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/hyprland/modules/window_rules.lua#L65) · [Konfigurasi Kitty](https://sw.kovidgoyal.net/kitty/conf/#opt-kitty.remember_window_size)
- [Preset Dux ConstOS](../../desktop/dms/settings.json) memasang `workspaceSwitcher` di panel. Pada Dux `v2.1.2`, ikon aplikasi workspace adalah opsi tersendiri. Jika diaktifkan, Dux bisa mengelompokkan beberapa jendela satu aplikasi dan membatasi jumlah ikon. Satu ikon dapat mewakili beberapa jendela yang masih ada di Hyprland. [Logika ikon Dux](https://github.com/duxlabs-dev/dux-shell/blob/43255a46ea01e9d0de1fe8ce9897c0d71566b2a8/quickshell/Modules/DBar/Widgets/WorkspaceSwitcher.qml#L114) · [Opsi Dux](https://github.com/duxlabs-dev/dux-shell/blob/43255a46ea01e9d0de1fe8ce9897c0d71566b2a8/quickshell/Common/settings/BarWidgetDefaults.js#L93)

## Bukti VM

Salinan disk QA Tsukuyomi `edd97e6` boot dengan QEMU/KVM 11.1.3, OVMF, satu output 1280 × 800, Hyprland `0.57.2-1`, dan Dux `2.1.2-1` aktif. SHA-256 konfigurasi Hyprland pada akun uji sama dengan sumber ConstOS saat audit. Dua Kitty dan satu Mousepad muncul sebagai tiga tile berbeda di workspace 1. Ketiganya mapped dan tidak overlap. Laporan pengguna belum terulang pada alur ini.

Saat Mousepad dibuat fullscreen secara sengaja, hanya Mousepad yang terlihat. Dua Kitty masih tercatat di IPC dan muncul kembali setelah keluar dari fullscreen. Pada konfigurasi awal, Super+Kiri saat fullscreen tetap berfokus pada Mousepad. Dalam uji sementara di VM, bind Super+F dari Ryoku mengaktifkan fullscreen dan `movefocus_cycles_fullscreen` membuat Super+Kiri berpindah ke Kitty. Ini kandidat perbaikan akses fokus jika sesi yang terdampak terbukti mengalami fullscreen.

Bukti uji awal berada di `iso/out/constos-workspace-vm-20261111.MI2Mjw/`.

### Uji delapan terminal lewat shortcut

Pada VM target yang sama, delapan kali Super+Enter dengan konfigurasi sebelum aturan Kitty memetakan delapan jendela. Jendela terakhir memiliki `fullscreen=1` (maximized) dan menutup area kerja. Bukti geometri awal ada di `iso/out/constos-desktop-keys-20261111.0k7KHk/guest-tiles.log`.

Setelah memasang paket final `constos-desktop-0.1.0-8-any` dan menerapkan default pada akun QA, delapan jendela berada di workspace 1, tanpa overlap, floating, group, atau fullscreen. Percobaan `kitty --start-as=maximized` juga menghasilkan tile. Super+F mengembalikan jendela fullscreen dan maximized ke tiling. Super+panah berpindah fokus dari fullscreen, Super+Shift+panah memindahkan tile, Alt+Tab kembali ke fokus sebelumnya, dan Super+Tab membuka overview Dux. Bukti lokal ada di `iso/out/constos-kitty-tiling-20261111.bxCfi0/`, termasuk `guest-tiles.log`, `shortcut-checks.log`, dan `eight-terminal-tiles-redacted.png`.

## Penerapan dan pemeriksaan lanjutan

1. Terapkan [default dan shortcut](../desktop-shortcuts.md) pada akun yang terdampak dengan mempertahankan pengaturan lokal. Ulangi delapan kali Super+Enter dan uji kembali dari fullscreen.
2. Jika gejala tersisa, baca `hyprctl configerrors`, `hyprctl getoption general:layout`, `hyprctl -j activeworkspace`, dan `hyprctl -j clients`. Catat workspace, mapped/hidden, fullscreen/floating/group, dan geometri dengan redaksi data pribadi. Periksa perubahan state saat fokus atau output berubah.
3. Jika tile tetap terlihat tetapi bar atau overview kehilangan entri, reproduksi opsi grouping dan batas ikon Dux, lalu telusuri ID jendela sebelum mengubah preset atau mengajukan perbaikan upstream. Perangkat fisik dan output kedua memerlukan pengujian tersendiri.

Status pelaksanaan mengikuti [roadmap desktop](../../implementation_plan.md#fase-07--fungsi-di-balik-menu-dan-shell).
