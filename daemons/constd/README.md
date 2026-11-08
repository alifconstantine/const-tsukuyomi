# constd — ConstOS System Monitor & OS-MCP Bridge Daemon

`constd` adalah daemon sistem ringan yang dirancang khusus untuk **ConstOS**. Daemon ini menjembatani antarmuka agen **Const Harness** dengan subsistem kernel Linux melalui pembacaan virtual filesystem `/proc` dan `/sys`.

## Fitur Utama:
1. **CPU Scheduling Inspection:** Membaca load average, thread count, dan status scheduler BORE tanpa beban komputasi tinggi.
2. **Paging & ZRAM Compression Watcher:** Membaca utilisasi memori real-time dan rasio kompresi ZRAM (`orig_size` vs `compr_size`).
3. **Process State Monitoring:** Menghitung jumlah proses berdasarkan state kernel (`R`: Running, `S`: Sleeping, `Z`: Zombie) dan mendeteksi proses berisiko OOM.
4. **Zero-Overhead Endpoint:** Menyediakan endpoint REST / JSON-RPC di `http://127.0.0.1:9099/metrics` untuk di-query oleh agen workbench atau widget status bar Waybar.
