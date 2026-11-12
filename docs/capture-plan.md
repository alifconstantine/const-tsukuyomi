# Rencana screenshot dan perekaman ConstOS

## Pemakaian di desktop

- **Super+Shift+S** atau **Screenshot** di launcher membuka toolbar. **Area** dan **Screen** membuka pratinjau, dengan **Copy**, **Save PNG**, dan **Annotate**. Di Satty, Enter mengembalikan gambar yang sudah diekspor dan Escape membatalkan edit. Gunakan persegi panjang solid untuk redaksi. Screenshot tersimpan di subfolder `Screenshots` pada XDG Pictures.
- **Record audio** menampilkan sumber PipeWire. Pilih mikrofon atau output audio sistem, lalu tekan **Start**. Indikator dan durasi muncul setelah sampel diterima. **Stop** memfinalisasi WAV 48 kHz stereo ke subfolder `Recordings` pada XDG Music. **Play** membuka hasil di aplikasi audio.
- **Print** dan **Alt+Print** langsung menyalin area dan layar. Escape saat memilih area menjaga pratinjau serta clipboard sebelumnya. Akun lama dapat membuka toolbar dari launcher sambil menggabungkan [binding baru](desktop-shortcuts.md). Login ulang setelah upgrade agar sesi memuat unit capture.

## Urutan integrasi

Target pertama adalah alur pilih → pratinjau → salin atau simpan dan alur pilih sumber audio → mulai → Stop → buka hasil. Ryoku memakai Super+Shift+S untuk membuka Ryoshot, yang menampilkan toolbar pemilihan, anotasi, dan aksi rekam region. Rekaman video didelegasikan ke GPU Screen Recorder melalui satu pemilik sesi dengan status dan kontrol Stop. Opsi mikrofon dan desktop audio yang terlihat di Ryoshot adalah opsi audio untuk video. ConstOS merencanakan mode audio-only dengan kontrol yang serupa. [Ryoshot](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/shell/quickshell/ryoshot/shell.qml) · [Backend rekam Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/shell/scripts/ryoku-cmd-record) · [Status perekaman Ryoku](https://github.com/Ryoku-dev/ryoku/blob/f7197d72de8a21e44b0bea922bdd915f28f6b327/ryoku/shell/quickshell/shell/services/Recorder.qml)

| Urutan | Implementasi | Gerbang |
| --- | --- | --- |
| 1. Screenshot | Toolbar Quickshell memakai `grim` dan `slurp` melalui `constos-capture`. Print dan Alt+Print memakai [jalur cepat](../desktop/scripts/constos-screenshot). | Tambah countdown, opsi cursor, dan mode jendela setelah backend mendukungnya. Uji error tulis, dua output, skala campuran, dan koordinat negatif. |
| 2. Anotasi | **Annotate** membuka Satty dari pratinjau. Ekspor PNG kembali ke toolbar untuk disalin atau disimpan. | Uji crop, teks, dan redaksi solid dengan fixture terpisah. Redaksi harus menutup piksel asli di hasil saat dibuka di editor lain. [Satty](https://github.com/Satty-org/Satty/tree/v0.22.0) |
| 3. Rekam audio saja | Rust membaca node dari `pw-dump` dan menulis PCM `pw-record` sebagai WAV. Pilihan sumber, indikator, durasi, Stop, dan Play memakai status dari backend. | Uji sumber fisik, cabut perangkat, disk penuh, level input, dan format tambahan. [PipeWire pw-record](https://docs.pipewire.org/page_man_pw-cat_1.html) |
| 4. Rekam layar | Evaluasi GPU Screen Recorder sebagaimana Ryoku, termasuk kemampuan nyata pada GPU, VM, dan backend portal target. Tawarkan layar atau area sesuai hasil probe. Tambah pilihan audio dan Pause jika backend membuktikan keduanya. | Putar video, periksa framing dan sinkronisasi A/V, serta uji picker ditolak, Stop, dan kehilangan sumber. Gunakan kontrol status yang sama dengan mode audio. |

Shot dan Record masuk melalui aksi pengguna dari shortcut, launcher, atau panel. Gunakan satu pemilik status dan Stop, dengan dukungan direktori sementara privat dan pesan berdasarkan hasil backend. Detail izin, lifecycle, dan penerimaan ada di [fase 07A](../implementation_plan.md#fase-07a--screenshot-rekaman-video-dan-rekaman-audio).

Backend berkoordinasi dengan Dux melalui IPC `screenshot begin` dan `screenshot end`. Uji pemulihan popout setelah Copy, Escape, dan error pada setiap konfigurasi panel yang didukung. [IPC screenshot Dux](https://github.com/duxlabs-dev/dux-shell/blob/43255a46ea01e9d0de1fe8ce9897c0d71566b2a8/quickshell/DMSShellIPC.qml#L312)
