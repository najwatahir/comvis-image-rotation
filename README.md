# 📷 Program Pengolahan Citra Digital (aduh.py)

Program ini melakukan **pengolahan citra (image processing)** secara manual menggunakan Python — tanpa bergantung pada library pemrosesan gambar. Semua operasi baca/tulis piksel dihitung sendiri dari nol.

> **Cocok untuk:** Junior programmer yang belajar Python dan ingin memahami bagaimana gambar digital bekerja di level paling dasar (byte per byte).

---

## 🔧 Dependencies (Ketergantungan Library)

| Library | Bawaan Python? | Dipakai untuk apa |
|---|---|---|
| `struct` | ✅ Ya | Membaca & menulis data biner (bytes) menjadi angka |
| `os` | ✅ Ya | Mengecek apakah file ada di disk |
| `Pillow (PIL)` | ❌ Harus install | **Hanya** untuk konversi format PNG/JPEG → BMP |

### Cara Install Pillow

```bash
pip install Pillow
```

> **Catatan penting:** Pillow **hanya** dipakai sekali, yaitu saat mengkonversi gambar non-BMP menjadi BMP. Setelah itu, semua operasi dilakukan manual tanpa library apapun.

---

## 🤔 Kenapa Harus Format BMP?

Format **BMP (Bitmap)** dipilih karena paling sederhana:

- **Tidak ada kompresi** → data piksel disimpan apa adanya di file
- **Mudah dibaca manual** → tinggal cari offset, lalu baca byte satu per satu
- Cocok untuk belajar karena tidak ada langkah "decode" yang rumit

Bandingkan dengan PNG (pakai kompresi zlib) atau JPEG (pakai kompresi DCT) yang jauh lebih kompleks untuk dibaca secara manual.

---

## 📁 Struktur File BMP (Konsep Dasar)

Sebelum memahami kode, pahami dulu bagaimana file BMP disusun:

```
[ File Header - 14 byte ]
    - Signature "BM"     (2 byte)
    - Ukuran file total  (4 byte)
    - Reserved           (4 byte)
    - Offset data piksel (4 byte)  ← "mulai baca piksel dari sini"

[ DIB Header - 40 byte ]
    - Lebar gambar       (4 byte)
    - Tinggi gambar      (4 byte)
    - Bit per piksel     (2 byte)  ← 24 berarti RGB, 8 berarti grayscale
    - ... (field lainnya)

[ Data Piksel ]
    - Urutan warna: BIRU, HIJAU, MERAH (bukan RGB tapi BGR!)
    - Disimpan dari BARIS PALING BAWAH ke atas (bottom-up)
    - Setiap baris harus kelipatan 4 byte (padding jika perlu)
```

---

## 🗂️ Struktur Kode (5 Bagian)

### Bagian 0 — `konversi_ke_bmp()` *(Satu-satunya pakai library)*

```python
def konversi_ke_bmp(filepath_input, filepath_output=None):
```

Fungsi ini menggunakan **Pillow** untuk mengkonversi file PNG/JPEG/GIF ke format BMP.
Dipanggil otomatis di `main()` jika file input bukan `.bmp`.

---

### Bagian 1 — `baca_info_bmp()` *(Baca Header)*

```python
def baca_info_bmp(filepath):
```

Membaca **metadata gambar** (lebar, tinggi, bit depth) langsung dari byte-byte file BMP.

**Alur Perhitungan:**
```
Buka file → baca 2 byte signature → harus "BM"
         → baca 4 byte ukuran file
         → baca 4 byte offset piksel  ← disimpan untuk nanti
         → baca 4 byte ukuran DIB header
         → baca 4+4 byte = lebar & tinggi gambar
         → baca 2 byte bit depth (24 = berwarna, 8 = grayscale)
```

Fungsi `struct.unpack()` dipakai untuk mengubah bytes menjadi angka:
```python
# '<I' artinya: baca 4 byte, format Little-Endian, hasilnya unsigned int
width, height = struct.unpack('<ii', f.read(8))
```
- `<` = Little-Endian (byte terkecil duluan, format yang dipakai BMP & Windows)
- `i` = signed integer 4 byte
- `H` = unsigned short 2 byte

---

### Bagian 2 — `baca_bmp_ke_matriks()` *(Baca Piksel)*

```python
def baca_bmp_ke_matriks(filepath):
```

Membaca **semua piksel** dari file BMP dan menyimpannya dalam matriks 2D Python.

**Alur Perhitungan:**

#### 1. Hitung ukuran baris + padding
```
BMP 24-bit: setiap piksel = 3 byte (B, G, R)
bytes_per_row = lebar × 3

Padding = sisa agar baris jadi kelipatan 4 byte
padding = (4 - (bytes_per_row % 4)) % 4

Contoh: lebar=300
  bytes_per_row = 300 × 3 = 900
  padding = (4 - (900 % 4)) % 4 = (4 - 0) % 4 = 0
  → tidak ada padding karena 900 sudah kelipatan 4
```

#### 2. Baca baris dari bawah ke atas
```
BMP menyimpan baris pertama = bagian bawah gambar (bottom-up)
Jadi baris ke-0 di file = baris ke-(tinggi-1) di gambar

y = (tinggi - 1) - row_idx
```

#### 3. Konversi BGR ke Grayscale
```
BMP 24-bit menyimpan 3 byte per piksel dalam urutan: B, G, R

gray = 0.299×R + 0.587×G + 0.114×B

Ini adalah rumus luminance standar ITU-R BT.601.
Mata manusia lebih sensitif terhadap hijau (G), sehingga bobotnya paling besar.
```

**Ilustrasi matriks hasil:**
```
matriks[0][0]   = nilai piksel di sudut kiri atas
matriks[0][299] = nilai piksel di sudut kanan atas
matriks[299][0] = nilai piksel di sudut kiri bawah

Setiap nilai = 0 (hitam) sampai 255 (putih)
```

---

### Bagian 3 — `simpan_matriks_ke_bmp()` *(Tulis Piksel)*

```python
def simpan_matriks_ke_bmp(matriks, nama_file_output):
```

Kebalikan dari fungsi baca: mengubah matriks 2D kembali menjadi file BMP 8-bit grayscale.

**Alur Penulisan:**
```
1. Tulis File Header (14 byte) → signature "BM", ukuran file, offset
2. Tulis DIB Header  (40 byte) → lebar, tinggi, bit_depth=8
3. Tulis Color Table (1024 byte) → 256 warna grayscale × 4 byte
   Contoh entry ke-i: (i, i, i, 0) = abu-abu level i
4. Tulis Data Piksel → dari baris bawah ke atas, tambah padding
```

> BMP 8-bit membutuhkan **color table (palette)**: tabel 256 warna yang mendefinisikan arti setiap nilai 0–255. Untuk grayscale, entry ke-i = warna abu-abu level i.

---

### Bagian 4 — 6 Fungsi Manipulasi Citra

Semua fungsi ini bekerja dengan pola yang sama:
1. Buat matriks hasil kosong
2. Loop setiap piksel `(y, x)`
3. Hitung nilai piksel baru berdasarkan rumus
4. Simpan ke matriks hasil

#### `batasi_nilai(nilai)` — Fungsi Pembantu
```
Memastikan nilai piksel tetap di range 0–255.
Nilai < 0  → 0   (hitam penuh)
Nilai > 255 → 255 (putih penuh)
```

#### 1. `ubah_brightness(matriks, nilai_tambah)`
```
Rumus: piksel_baru = piksel_lama + nilai_tambah

Contoh: nilai_tambah = +50
  piksel lama = 100 → piksel baru = 150 (lebih terang)
  piksel lama = 220 → piksel baru = 270 → dibatasi = 255

nilai_tambah positif → gambar lebih terang
nilai_tambah negatif → gambar lebih gelap
```

#### 2. `ubah_contrast(matriks, faktor)`
```
Rumus: piksel_baru = faktor × (piksel_lama - 128) + 128

Cara kerja:
  - Geser nilai ke titik tengah (dikurang 128)
  - Kali dengan faktor (regangkan atau sempitkan rentang)
  - Geser kembali (tambah 128)

Contoh: faktor = 2.0
  piksel lama = 200 → (200-128) × 2 + 128 = 272 → 255
  piksel lama =  50 → (50-128)  × 2 + 128 = -28 → 0

faktor > 1 → kontras naik (lebih hitam-putih)
faktor < 1 → kontras turun (lebih abu-abu)
```

#### 3. `pencerminan_horizontal(matriks)`
```
Rumus: posisi_x_baru = (lebar - 1) - x

Contoh: lebar = 300
  piksel di x=0   → pindah ke x=299
  piksel di x=1   → pindah ke x=298
  piksel di x=149 → pindah ke x=150

Efek: gambar seperti dicerminkan (flip horizontal)
```

#### 4. `rotasi_90_derajat(matriks)`
```
Ukuran gambar berubah! Tinggi dan lebar bertukar.
Gambar 300×300 tetap 300×300, tapi gambar 200×400 → jadi 400×200

Rumus pemetaan koordinat:
  (y, x) di gambar asli → (x, tinggi-1-y) di gambar hasil

Contoh: tinggi=300
  piksel di (y=0, x=0)   → pindah ke (x=0,   y=299)
  piksel di (y=0, x=299) → pindah ke (x=299, y=299)
```

#### 5. `noise_reduction_mean(matriks)` — Mean Filter 3×3
```
Rumus: piksel_baru = rata-rata 9 piksel di sekitarnya

[ y-1,x-1 | y-1,x | y-1,x+1 ]
[ y,  x-1 | y,  x | y,  x+1 ]  ← 9 piksel ini dirata-rata
[ y+1,x-1 | y+1,x | y+1,x+1 ]

Efek: mengurangi noise (bintik-bintik), gambar jadi lebih halus/blur
Catatan: piksel di tepi gambar tidak diproses karena tidak punya 9 tetangga lengkap
```

#### 6. `deteksi_tepi(matriks)` — Filter Laplacian
```
Rumus (Laplacian 4-tetangga):
  nilai_tepi = (tengah × 4) - (atas + bawah + kiri + kanan)

Cara kerja:
  - Jika area rata (semua piksel sama) → hasilnya = 0 (hitam)
  - Jika ada perbedaan nilai         → hasilnya besar (putih = tepi terdeteksi)

Contoh 1 — tidak ada tepi:
  Tengah=200, Atas=200, Bawah=200, Kiri=200, Kanan=200
  → (200×4) - (200+200+200+200) = 800 - 800 = 0

Contoh 2 — ada tepi:
  Tengah=200, Atas=50, Bawah=200, Kiri=200, Kanan=200
  → (200×4) - (50+200+200+200) = 800 - 650 = 150
```

---

## 🔄 Alur Program Keseluruhan

```
[Mulai]
    │
    ▼
Input nama file gambar (misal: foto.png)
    │
    ▼
Apakah file .bmp?
  Tidak → konversi_ke_bmp() pakai Pillow → hasilkan foto.bmp
  Ya    → langsung lanjut
    │
    ▼
baca_info_bmp() → baca header → dapat: lebar, tinggi, bit_depth
    │
    ▼
baca_bmp_ke_matriks() → baca piksel satu per satu
  → konversi BGR ke grayscale (0.299R + 0.587G + 0.114B)
  → simpan ke matriks[y][x]
    │
    ▼
Tampilkan menu pilihan operasi (loop)
    │
    ├─ 1 → ubah_brightness()
    ├─ 2 → ubah_contrast()
    ├─ 3 → pencerminan_horizontal()
    ├─ 4 → rotasi_90_derajat()
    ├─ 5 → noise_reduction_mean()
    ├─ 6 → deteksi_tepi()
    └─ 0 → Keluar
    │
    ▼ (setelah pilih operasi)
simpan_matriks_ke_bmp()
  → tulis header BMP
  → tulis palette grayscale
  → tulis piksel dari bawah ke atas
  → hasilkan file .bmp baru
    │
    ▼
[Kembali ke menu / Selesai]
```

---

## 🚀 Cara Menjalankan

```bash
# 1. Install Pillow (hanya perlu sekali)
pip install Pillow

# 2. Jalankan program
python aduh.py
```

**Contoh sesi penggunaan:**
```
==========================================
 PROGRAM PENGOLAHAN CITRA DIGITAL (CLI)
==========================================
Masukkan nama/path file gambar: poto.png
[INFO] File bukan BMP, mengkonversi otomatis...
[INFO] 'poto.png' dikonversi ke 'poto.bmp'

[INFO] Berhasil memuat gambar!
Format : BMP | Resolusi: 300x300 | Bit Depth: 24

--- PILIH SKENARIO PENGOLAHAN ---
1. Ubah Brightness (Kecerahan)
...

Masukkan nomor pilihan (0-6): 1
Masukkan nama file hasil: hasil_terang.bmp
Masukkan nilai brightness (-255 s.d 255): 80
[SUKSES] File disimpan sebagai: hasil_terang.bmp
```

---

## 💡 Tips untuk Junior Programmer

1. **Mulai dari sini:** Baca fungsi `baca_info_bmp()` dulu. Coba buka file BMP dengan hex editor (HxD di Windows) dan cocokkan byte-bytenya dengan kode.

2. **Pahami `struct.unpack`:** Format `'<I'` berarti:
   - `<` = Little-Endian (byte terkecil duluan)
   - `I` = unsigned int (4 byte, nilai 0 s.d. ~4 miliar)
   - `i` = signed int (4 byte, bisa negatif)
   - `H` = unsigned short (2 byte, nilai 0–65535)

3. **Debug dengan print:** Tambahkan `print()` di dalam loop piksel untuk melihat nilai yang sedang diproses.

4. **Eksperimen:** Coba brightness +200, -200, contrast 3.0, 0.1 — lihat hasilnya berbeda.

5. **Grayscale itu 1 angka:** Setiap piksel grayscale hanyalah angka 0–255. Gambar 300×300 = 90.000 angka.

---

## ❓ Kenapa Gambar Dikonversi ke Grayscale?

Ini adalah pertanyaan bagus, terutama karena file input bisa jadi gambar berwarna (24-bit RGB).

### Alasan 1 — Kesederhanaan Data

Gambar **berwarna (RGB)** = setiap piksel punya **3 angka** (R, G, B):
```
matriks_merah[y][x] = 200
matriks_hijau[y][x] = 150
matriks_biru[y][x]  = 80
```

Gambar **grayscale** = setiap piksel hanya **1 angka**:
```
matriks[y][x] = 172   ← satu nilai mewakili seberapa "terang" piksel itu
```

Dengan grayscale, kode jauh lebih sederhana karena kita hanya perlu mengelola **satu matriks**, bukan tiga.

### Alasan 2 — Rumus Manipulasi Lebih Mudah Dipahami

Semua 6 fungsi manipulasi (brightness, contrast, deteksi tepi, dll.) bekerja pada **satu nilai angka per piksel**. Jika gambar berwarna, setiap rumus harus diulang 3 kali (untuk R, G, B masing-masing), yang membuat kode lebih panjang dan membingungkan untuk pemula.

Contoh perbandingan untuk brightness:

```python
# Grayscale → sederhana
hasil[y][x] = batasi_nilai(matriks[y][x] + 50)

# RGB → harus proses 3 channel
hasil_r[y][x] = batasi_nilai(r[y][x] + 50)
hasil_g[y][x] = batasi_nilai(g[y][x] + 50)
hasil_b[y][x] = batasi_nilai(b[y][x] + 50)
```

### Alasan 3 — Operasi Seperti Deteksi Tepi Lebih Natural di Grayscale

Filter seperti **Laplacian** (deteksi tepi) dan **mean filter** (noise reduction) pada dasarnya bekerja pada **intensitas cahaya**, bukan warna. Gambar grayscale langsung mewakili intensitas, sehingga hasilnya lebih intuitif.

### Rumus Konversi yang Dipakai

```python
gray = 0.299 × R + 0.587 × G + 0.114 × B
```

Bobot ini **bukan asal-asalan** — ini adalah standar internasional **ITU-R BT.601** yang didasarkan pada penelitian tentang sensitivitas mata manusia:

| Warna | Bobot | Alasan |
|---|---|---|
| Merah (R) | 0.299 | Mata cukup sensitif terhadap merah |
| Hijau (G) | **0.587** | Mata paling sensitif terhadap hijau (paling besar) |
| Biru (B) | 0.114 | Mata paling tidak sensitif terhadap biru |

Jika kita pakai bobot rata-rata biasa `(R+G+B)/3`, hasilnya kurang akurat secara persepsi visual — gambar bisa terlihat terlalu terang atau terlalu gelap di area tertentu.

### Contoh Nyata

```
Piksel merah murni: R=255, G=0, B=0
  gray = 0.299×255 + 0.587×0 + 0.114×0 = 76

Piksel hijau murni: R=0, G=255, B=0
  gray = 0.299×0 + 0.587×255 + 0.114×0 = 150   ← lebih terang!

Piksel biru murni: R=0, G=0, B=255
  gray = 0.299×0 + 0.587×0 + 0.114×255 = 29    ← lebih gelap!
```

Ini masuk akal: secara visual, hijau memang terasa lebih terang daripada merah, dan biru terasa paling gelap — meskipun ketiga warna tersebut sama-sama "penuh" (nilai 255).

### Kesimpulan

| Pertimbangan | Gambar Berwarna (RGB) | Gambar Grayscale |
|---|---|---|
| Jumlah nilai per piksel | 3 (R, G, B) | 1 |
| Kompleksitas kode | Tinggi | Rendah ✅ |
| Mudah untuk belajar | ❌ | ✅ |
| Cocok untuk deteksi tepi | Perlu digabung dulu | Langsung ✅ |

> Untuk tujuan belajar **konsep pengolahan citra** seperti yang dilakukan program ini, grayscale adalah pilihan yang tepat. Setelah paham dasarnya, baru bisa dikembangkan ke pemrosesan gambar berwarna (RGB/HSV) yang lebih kompleks.

---

---

# 🌈 aduhrgb.py — Versi RGB (Berwarna)

File `aduhrgb.py` adalah versi lanjutan dari `aduh.py` yang memproses gambar **berwarna penuh (RGB)** alih-alih grayscale. Konsep dasarnya sama, namun setiap piksel kini menyimpan **3 nilai** (R, G, B) bukan satu angka tunggal.

---

## Perbedaan Utama: aduh.py vs aduhrgb.py

| Aspek | aduh.py (Grayscale) | aduhrgb.py (RGB) |
|---|---|---|
| Nilai per piksel | `matriks[y][x] = 172` | `matriks[y][x] = (255, 128, 60)` |
| Tipe data piksel | `int` | `tuple` (R, G, B) |
| Output BMP | 8-bit + palette grayscale | 24-bit tanpa palette |
| Ukuran file output | Lebih kecil | 3× lebih besar |
| Kompleksitas kode | Lebih sederhana | Lebih kompleks |
| Operasi tambahan | — | ✅ Swap Channel Warna |
| Cocok untuk belajar | ⭐⭐⭐ Pemula | ⭐⭐ Menengah |

---

## Struktur Matriks RGB

```python
# aduh.py → 1 angka per piksel (grayscale)
matriks[0][0] = 172

# aduhrgb.py → tuple 3 angka per piksel (R, G, B)
matriks[0][0] = (255, 128, 60)
#                 R     G    B
```

Karena setiap piksel adalah `tuple`, cara mengaksesnya:
```python
r, g, b = matriks[y][x]  # "unpack" tuple
# atau:
r = matriks[y][x][0]     # index 0 = R
g = matriks[y][x][1]     # index 1 = G
b = matriks[y][x][2]     # index 2 = B
```

---

## Struktur File BMP 24-bit (Output aduhrgb.py)

BMP 24-bit **tidak butuh color table (palette)** karena setiap piksel sudah menyimpan warna penuhnya:

```
[ File Header - 14 byte ]
[ DIB Header  - 40 byte ]   ← bit_depth = 24 (tidak ada palette!)
[ Data Piksel            ]   ← B G R B G R B G R ... (3 byte per piksel)
```

Ukuran file: `14 + 40 + (lebar × tinggi × 3) + padding`

---

## Penjelasan 7 Fungsi Manipulasi

Semua fungsi manipulasi di `aduhrgb.py` bekerja **per channel secara independen** — artinya rumus yang sama diterapkan ke R, G, dan B masing-masing.

#### 1. `ubah_brightness(matriks, nilai_tambah)`
```
Rumus: R_baru = batasi(R + nilai_tambah)
       G_baru = batasi(G + nilai_tambah)
       B_baru = batasi(B + nilai_tambah)

Hasilnya: seluruh gambar jadi lebih terang/gelap tanpa mengubah warna
```

#### 2. `ubah_contrast(matriks, faktor)`
```
Rumus: R_baru = batasi(faktor × (R - 128) + 128)
       G_baru = batasi(faktor × (G - 128) + 128)
       B_baru = batasi(faktor × (B - 128) + 128)

Hasilnya: warna-warna ekstrem makin mencolok, tengah makin pudar
```

#### 3. `pencerminan_horizontal(matriks)`
```
Sama persis dengan versi grayscale, tapi menyalin tuple (R,G,B) utuh:
hasil[y][(lebar-1)-x] = matriks[y][x]   ← salin tuple langsung
```

#### 4. `rotasi_90_derajat(matriks)`
```
Sama persis dengan versi grayscale:
hasil[x][(tinggi-1)-y] = matriks[y][x]  ← salin tuple langsung
```

#### 5. `noise_reduction_mean(matriks)` — Mean Filter 3×3 per Channel
```
Rata-rata 9 tetangga dihitung TERPISAH untuk R, G, dan B:

R_baru = (R[-1,-1] + R[-1,0] + R[-1,1] + ... + R[1,1]) / 9
G_baru = (G[-1,-1] + G[-1,0] + G[-1,1] + ... + G[1,1]) / 9
B_baru = (B[-1,-1] + B[-1,0] + B[-1,1] + ... + B[1,1]) / 9
```

#### 6. `deteksi_tepi(matriks)` — Laplacian per Channel
```
Laplacian dihitung TERPISAH untuk setiap channel (ch = R, G, atau B):

nilai_tepi_ch = (tengah_ch × 4) - (atas_ch + bawah_ch + kiri_ch + kanan_ch)

Hasilnya: tepi berwarna (tepi merah, tepi hijau, tepi biru terdeteksi sendiri-sendiri)
```

#### 7. `swap_channel(matriks, channel_a, channel_b)` *(Fitur Baru RGB!)*
```
Tukar dua channel warna di setiap piksel:

Pilihan:
  R ↔ B → warna merah jadi biru, biru jadi merah (efek "cold shift")
  R ↔ G → warna merah jadi hijau, hijau jadi merah
  G ↔ B → warna hijau jadi biru, biru jadi hijau

Contoh: piksel (200, 100, 50) swap R↔B → (50, 100, 200)
```

---

## Alur Program aduhrgb.py

```
[Mulai]
    │
    ▼
Input nama file gambar
    │
    ▼
Bukan .bmp? → konversi_ke_bmp() dengan convert('RGB') ← satu-satunya pakai PIL
    │
    ▼
baca_bmp_ke_matriks_rgb() → baca piksel satu per satu
  → setiap piksel → tuple (R, G, B)   ← TIDAK dikonversi ke grayscale!
  → simpan ke matriks[y][x] = (r, g, b)
    │
    ▼
Tampilkan menu pilihan 1–7
    │
    ├─ 1 → ubah_brightness()      → proses R, G, B masing-masing
    ├─ 2 → ubah_contrast()        → proses R, G, B masing-masing
    ├─ 3 → pencerminan_horizontal() → salin tuple
    ├─ 4 → rotasi_90_derajat()    → salin tuple, tukar dimensi
    ├─ 5 → noise_reduction_mean() → rata-rata per channel
    ├─ 6 → deteksi_tepi()         → Laplacian per channel
    ├─ 7 → swap_channel()         → tukar 2 channel
    └─ 0 → Keluar
    │
    ▼
simpan_matriks_rgb_ke_bmp()
  → tulis header 24-bit (tanpa palette)
  → tulis piksel dalam urutan BGR (bottom-up)
  → hasilkan file .bmp berwarna
```

---

## Cara Menjalankan aduhrgb.py

```bash
# Pastikan Pillow sudah terinstall
pip install Pillow

# Jalankan program
python aduhrgb.py
```

**Contoh sesi:**
```
==========================================
  PROGRAM PENGOLAHAN CITRA RGB (CLI)
==========================================
Masukkan nama/path file gambar: poto.png
[INFO] File bukan BMP, mengkonversi otomatis...
[INFO] 'poto.png' dikonversi ke 'poto.bmp' (24-bit RGB)

[INFO] Berhasil memuat gambar!
Format : BMP | Resolusi: 300x300 | Bit Depth: 24
Contoh piksel (0,0): R=162, G=169, B=185

--- PILIH SKENARIO PENGOLAHAN ---
1. Ubah Brightness (Kecerahan)
...
7. Swap Channel Warna (R↔B, R↔G, atau G↔B)
0. Keluar Program

Masukkan nomor pilihan (0-7): 7
Masukkan nama file hasil: swap_rb.bmp
Pilih channel yang akan ditukar:
  a. R ↔ B
  b. R ↔ G
  c. G ↔ B
Pilihan (a/b/c): a
[SUKSES] File disimpan sebagai: swap_rb.bmp
```

