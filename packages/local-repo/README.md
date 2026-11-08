# ConstOS Local Pacman Repository

Direktori ini berfungsi sebagai repositori pacman lokal untuk menampung paket biner `.pkg.tar.zst` yang dibuat khusus untuk ConstOS sebelum dibakar ke dalam file ISO.

## Cara Menggunakan:

1. Letakkan paket biner pacman hasil build di folder ini, misalnya:
   * `const-harness-desktop-0.0.2-1-x86_64.pkg.tar.zst`
2. Jalankan perintah pembuatan database repositori:
   ```bash
   repo-add constos-local.db.tar.zst *.pkg.tar.zst
   ```
3. File database `constos-local.db.tar.zst` dan symlink `constos-local.db` akan terbuat secara otomatis.

Build saat ini memakai `packages/build-local.sh DIR` untuk membuat paket `constos-core` dan `constos-desktop` beserta checksum di direktori output baru. Berikan direktori itu melalui `iso/buildiso.sh --packages-dir DIR`; installer mengonsumsi artefak lokal terverifikasi dari ISO, tanpa menambahkan repo sementara ke konfigurasi target. Prosedur repo-add di atas hanya untuk eksperimen repo terpisah, bukan prasyarat build live atau jalur update resmi. Resep Harness belum memuat runtime lengkap.
