# Skills ConstOS

Indeks prosedur kerja yang dapat dipakai ulang oleh agen atau kontributor. Aturan lintas pekerjaan ada di [AGENTS.md](AGENTS.md), bukan disalin ke setiap skill.

| Skill | Gunakan ketika | Sumber |
| --- | --- | --- |
| `constos-development` | Mengubah atau meninjau profil ISO, staging desktop, installer, capture, daemon, packaging, atau dokumentasi ConstOS; memilih verifikasi dan dokumen yang terdampak. | [SKILL.md](.agents/skills/constos-development/SKILL.md) |

`SKILLS.md` adalah katalog biasa, bukan format pemuat skill. Prosedur sebenarnya berada di `.agents/skills/<nama>/SKILL.md` dengan frontmatter `name` dan `description`. Klien yang mendukung discovery lokasi tersebut dapat memuatnya; pada klien lain, baca file skill melalui tautan di atas. Jangan mengasumsikan semua tool/agen otomatis menemukannya.

Tambahkan skill terpisah hanya jika ada prosedur khusus yang sudah bisa dijalankan dan cukup berbeda untuk dipakai ulang. Jangan membuat skill kosong untuk setiap fase roadmap atau menaruh status fitur di skill. Ketika command/path/prasyarat berubah, perbarui prosedurnya; ketika skill ditambah, dipindah, atau diubah trigger-nya, perbarui indeks ini.
