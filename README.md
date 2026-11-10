# SIPRES — Smart School (Vercel)

Versi web dari notebook `Untitled6.ipynb`. Aplikasi menggunakan frontend HTML/CSS/JavaScript, API Python FastAPI, Pandas, OpenPyXL, dan Plotly.js.

## Fitur yang dipertahankan
- Dashboard KPI: total siswa, total alpa, total menit terlambat, total sanksi.
- Upload dan validasi Excel `.xlsx`.
- Evaluasi otomatis status Aman / Perlu SP 1 / Perlu SP 2 dengan ambang batas sesuai notebook.
- Ringkasan evaluasi BK.
- Pusat Peringatan Dini.
- Tabel seluruh siswa dan detail saat baris diklik.
- Grafik interaktif distribusi status dan jenis pelanggaran.
- Panduan aturan SP.
- Unggah logo sekolah dari perangkat pengguna.

## Struktur
```text
SIPRES_Vercel/
├── index.py
├── public/
│   └── index.html
├── requirements.txt
├── vercel.json
├── .gitignore
└── README.md
```

## Format Excel wajib
Nama kolom harus tepat seperti berikut:
`NIS`, `Nama`, `Kelas`, `Alpa`, `Menit_Terlambat`, `Jumlah_Sanksi`

Kolom angka tidak boleh kosong, harus angka, dan tidak boleh negatif. File maksimal 4 MB untuk konfigurasi ini.

## Deploy ke Vercel (cara paling mudah: GitHub)
1. Ekstrak ZIP ini di komputer.
2. Buat akun / masuk ke GitHub.
3. Buat repository baru, misalnya `sipres-smart-school`.
4. Upload seluruh isi folder `SIPRES_Vercel` ke repository (bukan file ZIP-nya).
5. Masuk ke https://vercel.com dan login menggunakan GitHub.
6. Pilih **Add New → Project**.
7. Import repository `sipres-smart-school`.
8. Biarkan Framework Preset terdeteksi otomatis sebagai **FastAPI**. Jika tidak terdeteksi, pilih **Other**. Root Directory: `./`.
9. Klik **Deploy**. Tunggu proses build selesai.
10. Buka domain `.vercel.app` yang diberikan Vercel.

## Pengamanan data siswa (sangat disarankan)
Data siswa bersifat pribadi. Sebelum membagikan URL aplikasi:
1. Buka Project di Vercel → **Settings → Environment Variables**.
2. Tambahkan:
   - Name: `SIPRES_ACCESS_CODE`
   - Value: buat kode akses rahasia yang kuat dan unik.
   - Environment: Production (tambahkan Preview jika diperlukan).
3. Simpan, lalu lakukan **Redeploy** dari tab Deployments.
4. Saat membuka aplikasi, pengguna diminta memasukkan kode akses tersebut.

Catatan: kode akses ini adalah gerbang sederhana bersama, bukan akun individual dan bukan pengganti sistem login sekolah. Jangan unggah data siswa sungguhan ke deployment publik tanpa persetujuan dan tata kelola sekolah.

## Catatan teknis penting
- Tidak menggunakan Google Colab atau Ngrok lagi.
- Aplikasi berjalan sebagai fungsi serverless. Data hasil unggahan hanya berada di respons/browser sesi saat itu; tidak disimpan permanen di database.
- Jika halaman dimuat ulang, unggah ulang Excel untuk membangun dashboard kembali.
- Batas upload 4 MB diterapkan agar sesuai batas request umum Vercel Functions. Untuk file lebih besar atau penyimpanan permanen, perlu rancangan penyimpanan cloud/database terpisah.
- Logo yang diunggah dari browser hanya ditampilkan di perangkat tersebut, tidak disimpan di server.
- Aturan SP sama dengan notebook asal: SP 2 diperiksa lebih dahulu, kemudian SP 1.
