# Shortcut desktop ConstOS

Konfigurasi ini mengikuti pintasan Ryoku yang punya padanan pada desktop ConstOS. Super adalah tombol Windows pada kebanyakan keyboard. Welcome menampilkan pintasan utama dan dapat dibuka lagi dari launcher. [Binding Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/hyprland/modules/binds.lua)

| Tombol | Aksi |
| --- | --- |
| Super+Enter | Buka jendela Kitty. Ulangi pada workspace yang sama untuk membuat tile tambahan. |
| Super+B | Buka browser default sesi. Jika belum ada, tampilkan pemberitahuan. Pilihan mengikuti default akun, termasuk Firefox, Chromium, atau Zen dari installer. |
| Super+E / Super+N | Buka Nautilus / Mousepad. |
| Super+Space / Super+koma | Buka launcher / Settings. |
| Super+Esc atau Super+A | Buka Quick Settings Dux. |
| Super+Tab | Buka atau tutup overview workspace Dux dan pilih jendela. |
| Super+panah / Super+Shift+panah | Pindah fokus / pindahkan jendela ke arah panah. |
| Alt+Tab | Kembali ke jendela yang terakhir difokuskan. |
| Super+F / Super+V | Toggle fullscreen / floating untuk jendela aktif. Keluar dari fullscreen untuk melihat tile lain. |
| Super+1…0 / Super+Shift+1…0 | Pindah workspace / pindahkan jendela ke workspace lain. |
| Super+Q / Super+L | Tutup jendela aktif / kunci sesi. |
| Super+Shift+S atau Print / Alt+Print | Pilih area untuk disalin / salin tangkapan layar penuh. [Rencana capture](capture-plan.md) |

Paket `constos-desktop` memasang default di `/etc/skel/.config/hypr/hyprland.lua`. Akun baru mengambilnya saat dibuat. Pada akun lama, bandingkan default tersebut dengan `~/.config/hypr/hyprland.lua`, simpan salinan konfigurasi akun, lalu gabungkan aturan `kitty-suppress-maximize`, pengaturan `binds.movefocus_cycles_fullscreen`, dan binding yang diinginkan. Muat ulang dengan `hyprctl reload` di sesi ConstOS.

Wallpaper picker, riwayat clipboard, dan Kit Ryoku punya dependensi UI sendiri. Evaluasi padanan dan bentrok shortcut saat fitur tersebut dikerjakan. Super+V sudah digunakan untuk floating di ConstOS.
