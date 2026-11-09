# Aturan kerja ConstOS

ConstOS dikembangkan sebagai distro Linux untuk pengembangan perangkat lunak dan penggunaan desktop sehari-hari. Gunakan bahasa Indonesia untuk dokumentasi repositori; pertahankan nama API, paket, dan simbol kode sesuai sumbernya. Pisahkan fitur tersedia, konfigurasi yang belum diuji, keputusan desain, dan rencana.

## Mulai dari sumber yang tepat

1. Baca [README.md](README.md) untuk status pengguna dan [implementation_plan.md](implementation_plan.md) untuk prioritas, dependensi, dan gerbang penerimaan.
2. Baca [docs/architecture.md](docs/architecture.md) sebelum mengubah batas komponen, IPC, izin, lifecycle, atau kepemilikan paket/config.
3. Gunakan [SKILLS.md](SKILLS.md) untuk menemukan prosedur yang cocok. Baca skill terkait sebelum mengubah atau memverifikasi subsistemnya.
4. Periksa kode/config yang benar-benar dimuat. Status di dokumen bukan pengganti pemeriksaan implementasi; bukti VM bukan bukti perangkat fisik.
5. Untuk installer, pemilihan paket, login, dan desktop pertama, baca [spesifikasi installer](docs/installer-plan.md). Ikuti gerbang di [panduan penerimaan](docs/acceptance-guide.md#installer-dan-reboot-tanpa-iso) sebelum beralih ke perluasan shell.

## Batas desain

- Jalur awal resmi: CachyOS x86_64 UEFI + Hyprland. Jangan menambah dukungan BIOS/Secure Boot/GPU atau skenario instalasi tanpa uji tersendiri.
- Desktop dasar harus bekerja tanpa Harness, akun AI, Ollama, atau koneksi ke penyedia model.
- Bedakan profil live dengan target terpasang. Jangan membawa liveuser, autologin, sudo khusus ISO, atau repo sementara ke target.
- `iso/buildiso.sh` menentukan file desktop yang di-stage. Jangan mengedit konfigurasi Hyprland lama lalu mengklaim sesi live berubah tanpa memeriksa jalur pemuatannya.
- Gunakan satu sumber collector, state, dan konfigurasi vendor; preferensi pengguna terpisah. Cutover harus memigrasikan konsumen sebelum menghapus jalur lama.
- Capture pengguna berbeda dari computer use. Jangan memberikan grant agen melalui shortcut screenshot atau sesi recorder. Tidak ada akses root/input global atau bypass consent untuk membuat fitur tampak berjalan.
- Jangan menambah data contoh, fallback palsu, status sukses sebelum backend selesai, atau lisensi aset yang diasumsikan.
- Perubahan disk/partisi hanya pada disk uji yang identitasnya sudah dikonfirmasi. Jangan menghapus perubahan pengguna atau artefak yang tidak dibuat oleh pekerjaan ini.

## Dokumen yang harus ikut berubah

Perbarui dokumen yang terdampak dalam perubahan/PR yang sama. Tidak perlu menyentuh semua file untuk setiap perubahan. Tautkan detail ke satu sumber; jangan menyalin roadmap ke README, arsitektur, dan skill sekaligus.

| Perubahan | Dokumen yang wajib diperiksa dan diperbarui bila terdampak |
| --- | --- |
| Fitur, batas dukungan, shortcut publik, cara pakai, atau hasil verifikasi baru | `README.md`; `implementation_plan.md` untuk status, bukti, backlog, dan gerbang yang berubah; panduan pengguna terkait bila ada. |
| Scope, urutan, dependensi, kriteria penerimaan, atau blocker | `implementation_plan.md`. Centang hanya skenario yang benar-benar lulus; catat lingkungan dan bukti. |
| Batas proses, IPC/schema, izin, data/config, paket pemilik, atau lifecycle | `docs/architecture.md`; roadmap bila langkah/dependensi berubah; README bila dampaknya terlihat pengguna. |
| Prasyarat, command, path staging/build, tool, atau prosedur verifikasi | `docs/build-guide.md` atau panduan prosedur terkait; `.agents/skills/constos-development/SKILL.md` bila alur kerjanya berubah. |
| Aturan kontribusi, keamanan kerja, atau kebijakan sinkronisasi dokumen | `AGENTS.md`; periksa skill agar tidak memberi instruksi yang bertentangan. |
| Skill baru, rename, trigger, atau lokasi skill | `SKILLS.md` dan file `SKILL.md` terkait; perbarui pemanggil bila ada. |
| Aset/token/widget/capture baru | Roadmap untuk status/bukti; arsitektur bila kontraknya berubah; manifest aset dan panduan terkait ketika implementasinya dibuat. |
| Refactor internal tanpa perubahan kontrak/perilaku/cara kerja | Jangan mengubah dokumen yang masih akurat hanya untuk menghasilkan diff. Sebutkan alasan dokumen tidak berubah dalam laporan akhir. |

Aturan ini adalah kewajiban workflow bagi kontributor/agen yang membacanya, bukan watcher yang otomatis memperbarui file atau jaminan semua klien memuatnya. Periksa dampak dokumentasi sebelum menyelesaikan setiap pekerjaan. Jika perubahan diblokir, tulis blocker dan batas bukti; jangan menandai pekerjaan selesai.

## Verifikasi dan bukti

- Jalankan skenario pada surface yang diubah. Build/config saja tidak membuktikan boot, UI, capture, instalasi, atau recovery. Jangan mengulang pemeriksaan hanya untuk mengonfirmasi kegagalan yang sudah dilaporkan pengguna.
- Build penuh di Linux x86_64 sesuai [panduan build](docs/build-guide.md). Staging di host lain tidak membuktikan symlink, paket, atau boot Linux benar.
- Untuk UI, periksa tampilan dan interaksi pada sesi Wayland nyata/VM target, termasuk cancel/error serta keyboard. Untuk media, buka hasil dan putar rekaman; berkas ada atau ukuran nonzero bukan bukti capture benar.
- Regresi permanen harus menguji perilaku yang bisa rusak bagi pengguna, bukan mencocokkan teks sumber, wiring, atau menyalin implementasi ke test.
- Perubahan khusus dokumen: periksa tautan lokal/anchor, blok Markdown, istilah/status yang kontradiktif, dan referensi file lama. Tidak perlu build ISO jika perilaku build tidak berubah.
- Catat SHA/build, versi, VM/perangkat, skenario, hasil, dan lokasi bukti yang relevan. Redaksi nama pengguna, SSID, token, isi clipboard, serta media pribadi sebelum dibagikan. Jangan commit ISO, rekaman mentah, model, atau kredensial.

## Sebelum menyelesaikan pekerjaan

1. Semua pemanggil serta konfigurasi yang terdampak sudah dimigrasikan; tidak ada alias atau dokumentasi lama yang bertentangan.
2. Bukti penerimaan sesuai perubahan tersedia, atau batas verifikasi disebutkan secara eksplisit.
3. Matriks dokumentasi di atas sudah diperiksa; update yang relevan ikut disertakan, dan dokumen yang sengaja tidak berubah tetap akurat.
4. Laporkan apa yang berubah, apa yang benar-benar diperiksa, dan blocker yang masih ada. Jangan menyebut rencana atau konfigurasi yang belum diuji sebagai fitur siap pakai.
