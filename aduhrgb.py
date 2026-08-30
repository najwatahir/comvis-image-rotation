import struct
import os


# ==========================================
# 0. KONVERSI FORMAT KE BMP (SATU-SATUNYA BAGIAN PAKAI LIBRARY)
# ==========================================
def konversi_ke_bmp(filepath_input, filepath_output=None):
    """Konversi gambar (PNG/JPEG/GIF) ke BMP 24-bit RGB. Satu-satunya fungsi pakai library."""
    from PIL import Image
    if filepath_output is None:
        nama_tanpa_ext = os.path.splitext(filepath_input)[0]
        filepath_output = nama_tanpa_ext + ".bmp"
    # Konversi ke RGB agar dipastikan 24-bit (bukan palette/grayscale)
    img = Image.open(filepath_input).convert('RGB')
    img.save(filepath_output)
    print(f"[INFO] '{filepath_input}' dikonversi ke '{filepath_output}' (24-bit RGB)")
    return filepath_output


# ==========================================
# 1. BACA INFO HEADER BMP (MANUAL, TANPA LIBRARY)
# ==========================================
def baca_info_bmp(filepath):
    """Membaca header BMP secara manual menggunakan struct."""
    if not os.path.exists(filepath):
        return {"error": "File tidak ditemukan"}

    try:
        with open(filepath, 'rb') as f:
            # --- File Header (14 byte) ---
            signature = f.read(2)
            if signature != b'BM':
                return {"error": "Bukan file BMP valid (signature bukan 'BM')"}

            file_size, = struct.unpack('<I', f.read(4))
            f.read(4)  # reserved
            pixel_offset, = struct.unpack('<I', f.read(4))

            # --- DIB Header ---
            dib_size, = struct.unpack('<I', f.read(4))

            if dib_size == 12:  # BITMAPCOREHEADER (jarang)
                width, height = struct.unpack('<HH', f.read(4))
                f.read(2)  # planes
                bit_count, = struct.unpack('<H', f.read(2))
                compression = 0
            else:  # BITMAPINFOHEADER (40 byte) atau lebih besar
                width, height = struct.unpack('<ii', f.read(8))
                f.read(2)  # planes
                bit_count, = struct.unpack('<H', f.read(2))
                compression, = struct.unpack('<I', f.read(4))

            return {
                'format': 'BMP',
                'width': abs(width),
                'height': abs(height),
                'bit_depth': bit_count,
                'compression': compression,
                'pixel_offset': pixel_offset,
                'top_down': height < 0,
                'file_size': file_size
            }
    except Exception as e:
        return {"error": f"Terjadi kesalahan: {str(e)}"}


# ==========================================
# 2. BACA PIKSEL BMP KE MATRIKS RGB (MANUAL, TANPA LIBRARY)
# ==========================================
def baca_bmp_ke_matriks_rgb(filepath):
    """Membaca file BMP 24-bit dan mengekstrak piksel ke matriks RGB 2D.
    Setiap elemen matriks adalah tuple (R, G, B), nilai masing-masing 0-255.
    Sepenuhnya manual: baca byte per byte menggunakan struct."""
    info = baca_info_bmp(filepath)
    if "error" in info:
        return None, info

    width = info['width']
    height = info['height']
    bit_count = info['bit_depth']
    pixel_offset = info['pixel_offset']
    top_down = info['top_down']

    if bit_count != 24:
        return None, {"error": f"File ini {bit_count}-bit. aduhrgb.py hanya mendukung BMP 24-bit RGB."}

    with open(filepath, 'rb') as f:
        f.seek(pixel_offset)

        # BMP 24-bit: setiap piksel = 3 byte (B, G, R)
        bytes_per_row = width * 3
        # Setiap baris BMP harus kelipatan 4 byte — tambahkan padding jika perlu
        padding = (4 - (bytes_per_row % 4)) % 4
        row_size = bytes_per_row + padding

        # Inisialisasi matriks 2D berisi tuple (R, G, B)
        matriks = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

        for row_idx in range(height):
            row_data = f.read(row_size)

            # BMP default = bottom-up: baris ke-0 di file = baris paling bawah gambar
            if top_down:
                y = row_idx
            else:
                y = (height - 1) - row_idx

            for x in range(width):
                # BMP menyimpan urutan BGR, bukan RGB!
                b = row_data[x * 3]
                g = row_data[x * 3 + 1]
                r = row_data[x * 3 + 2]
                matriks[y][x] = (r, g, b)

    return matriks, info


# ==========================================
# 3. SIMPAN MATRIKS RGB KE FILE BMP 24-BIT (MANUAL, TANPA LIBRARY)
# ==========================================
def simpan_matriks_rgb_ke_bmp(matriks, nama_file_output):
    """Menyimpan matriks RGB 2D ke file BMP 24-bit.
    Menulis header + piksel byte per byte, tanpa library."""
    tinggi = len(matriks)
    lebar = len(matriks[0])

    # Hitung padding per baris
    bytes_per_row = lebar * 3
    padding = (4 - (bytes_per_row % 4)) % 4
    row_size = bytes_per_row + padding

    pixel_data_size = row_size * tinggi
    pixel_offset = 14 + 40  # file header + DIB header (tanpa palette untuk 24-bit)
    file_size = pixel_offset + pixel_data_size

    with open(nama_file_output, 'wb') as f:
        # === FILE HEADER (14 byte) ===
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<HH', 0, 0))           # Reserved
        f.write(struct.pack('<I', pixel_offset))

        # === DIB HEADER - BITMAPINFOHEADER (40 byte) ===
        f.write(struct.pack('<I', 40))              # Ukuran DIB header
        f.write(struct.pack('<i', lebar))            # Lebar
        f.write(struct.pack('<i', tinggi))           # Tinggi (positif = bottom-up)
        f.write(struct.pack('<H', 1))               # Planes
        f.write(struct.pack('<H', 24))              # Bit per piksel (24 = RGB)
        f.write(struct.pack('<I', 0))               # Kompresi (0 = tidak ada)
        f.write(struct.pack('<I', pixel_data_size)) # Ukuran data piksel
        f.write(struct.pack('<i', 2835))            # X piksel per meter (~72 DPI)
        f.write(struct.pack('<i', 2835))            # Y piksel per meter
        f.write(struct.pack('<I', 0))               # Jumlah warna (0 = semua)
        f.write(struct.pack('<I', 0))               # Warna penting

        # === DATA PIKSEL (bottom-up, urutan BGR) ===
        padding_bytes = b'\x00' * padding
        for y in range(tinggi - 1, -1, -1):  # tulis dari baris bawah ke atas
            for x in range(lebar):
                r, g, b = matriks[y][x]
                # Pastikan nilai valid 0-255
                r = max(0, min(255, int(r)))
                g = max(0, min(255, int(g)))
                b = max(0, min(255, int(b)))
                f.write(struct.pack('BBB', b, g, r))  # tulis BGR!
            f.write(padding_bytes)

    print(f"[SUKSES] File disimpan sebagai: {nama_file_output}")


# ==========================================
# 4. FUNGSI PEMBANTU
# ==========================================
def batasi_nilai(nilai):
    """Pastikan nilai piksel per channel tetap di range 0–255."""
    if nilai < 0: return 0
    if nilai > 255: return 255
    return int(nilai)

def proses_rgb(matriks, fungsi_per_piksel):
    """Helper: terapkan fungsi ke setiap piksel (R,G,B) dan kembalikan matriks baru."""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[y][x] = fungsi_per_piksel(matriks[y][x], y, x)
    return hasil


# ==========================================
# 5. 6 FUNGSI MANIPULASI PENGOLAHAN CITRA RGB
# ==========================================

def ubah_brightness(matriks, nilai_tambah):
    """Tambahkan nilai_tambah ke setiap channel R, G, B secara independen."""
    def proses(piksel, y, x):
        r, g, b = piksel
        return (
            batasi_nilai(r + nilai_tambah),
            batasi_nilai(g + nilai_tambah),
            batasi_nilai(b + nilai_tambah)
        )
    return proses_rgb(matriks, proses)


def ubah_contrast(matriks, faktor):
    """Terapkan faktor kontras ke setiap channel R, G, B secara independen.
    Rumus: channel_baru = faktor × (channel_lama - 128) + 128"""
    def proses(piksel, y, x):
        r, g, b = piksel
        return (
            batasi_nilai(faktor * (r - 128) + 128),
            batasi_nilai(faktor * (g - 128) + 128),
            batasi_nilai(faktor * (b - 128) + 128)
        )
    return proses_rgb(matriks, proses)


def pencerminan_horizontal(matriks):
    """Balik gambar secara horizontal (flip kiri-kanan).
    Piksel di kolom x → pindah ke kolom (lebar-1-x)."""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[y][(lebar - 1) - x] = matriks[y][x]
    return hasil


def rotasi_90_derajat(matriks):
    """Rotasi gambar 90 derajat searah jarum jam.
    Piksel (y, x) → pindah ke (x, tinggi-1-y). Dimensi lebar & tinggi bertukar."""
    tinggi, lebar = len(matriks), len(matriks[0])
    # Hasil: lebar_baru = tinggi_lama, tinggi_baru = lebar_lama
    hasil = [[(0, 0, 0) for _ in range(tinggi)] for _ in range(lebar)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[x][(tinggi - 1) - y] = matriks[y][x]
    return hasil


def noise_reduction_mean(matriks):
    """Mean filter 3×3: setiap piksel diganti rata-rata 9 tetangganya.
    Diterapkan per channel (R, G, B) secara terpisah."""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [row[:] for row in matriks]  # salin asli untuk piksel pinggir
    for y in range(1, tinggi - 1):
        for x in range(1, lebar - 1):
            # Kumpulkan 9 tetangga dan rata-rata per channel
            total_r = total_g = total_b = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    r, g, b = matriks[y + dy][x + dx]
                    total_r += r
                    total_g += g
                    total_b += b
            hasil[y][x] = (
                batasi_nilai(total_r / 9),
                batasi_nilai(total_g / 9),
                batasi_nilai(total_b / 9)
            )
    return hasil


def deteksi_tepi(matriks):
    """Deteksi tepi menggunakan filter Laplacian 4-tetangga per channel.
    Rumus: channel_tepi = (tengah × 4) - (atas + bawah + kiri + kanan)"""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(1, tinggi - 1):
        for x in range(1, lebar - 1):
            for ch in range(3):  # ch=0 → R, ch=1 → G, ch=2 → B
                tengah = matriks[y][x][ch]
                atas   = matriks[y - 1][x][ch]
                bawah  = matriks[y + 1][x][ch]
                kiri   = matriks[y][x - 1][ch]
                kanan  = matriks[y][x + 1][ch]
                nilai_tepi = (tengah * 4) - (atas + bawah + kiri + kanan)
                # Simpan channel ke tuple hasil
                r, g, b = hasil[y][x]
                if ch == 0:
                    hasil[y][x] = (batasi_nilai(nilai_tepi), g, b)
                elif ch == 1:
                    hasil[y][x] = (r, batasi_nilai(nilai_tepi), b)
                else:
                    hasil[y][x] = (r, g, batasi_nilai(nilai_tepi))
    return hasil


def swap_channel(matriks, channel_a, channel_b):
    """Tukar dua channel warna. Contoh: swap R dan B → efek "negative color shift".
    channel: 0=R, 1=G, 2=B"""
    def proses(piksel, y, x):
        p = list(piksel)
        p[channel_a], p[channel_b] = p[channel_b], p[channel_a]
        return tuple(p)
    return proses_rgb(matriks, proses)


# ==========================================
# 6. MENU UTAMA (CLI)
# ==========================================
def main():
    print("==========================================")
    print("  PROGRAM PENGOLAHAN CITRA RGB (CLI)      ")
    print("==========================================")

    filepath = input("Masukkan nama/path file gambar: ").strip()

    if not os.path.exists(filepath):
        print(f"[ERROR] File '{filepath}' tidak ditemukan!")
        return

    # Jika bukan BMP, konversi dulu (satu-satunya langkah pakai library)
    if not filepath.lower().endswith('.bmp'):
        print(f"[INFO] File bukan BMP, mengkonversi otomatis...")
        filepath = konversi_ke_bmp(filepath)

    # Baca piksel RGB secara manual (tanpa library)
    matriks_asli, info = baca_bmp_ke_matriks_rgb(filepath)
    if matriks_asli is None:
        print(f"[ERROR] Gagal membaca file: {info.get('error', 'Unknown')}")
        return

    print(f"\n[INFO] Berhasil memuat gambar!")
    print(f"Format : {info['format']} | Resolusi: {info['width']}x{info['height']} | Bit Depth: {info['bit_depth']}")

    # Tampilkan contoh nilai piksel pertama
    r, g, b = matriks_asli[0][0]
    print(f"Contoh piksel (0,0): R={r}, G={g}, B={b}")

    while True:
        print("\n--- PILIH SKENARIO PENGOLAHAN ---")
        print("1. Ubah Brightness (Kecerahan)")
        print("2. Ubah Contrast (Kontras)")
        print("3. Pencerminan Horizontal (Mirror)")
        print("4. Rotasi 90 Derajat")
        print("5. Noise Reduction (Smoothing)")
        print("6. Deteksi Tepi (Edge Detection)")
        print("7. Swap Channel Warna (R↔B, R↔G, atau G↔B)")
        print("0. Keluar Program")

        pilihan = input("\nMasukkan nomor pilihan (0-7): ").strip()

        if pilihan == '0':
            print("Keluar dari program. Terima kasih!")
            break

        output_nama = input("Masukkan nama file hasil (contoh: hasil.bmp): ").strip()
        if not output_nama.lower().endswith('.bmp'):
            output_nama += '.bmp'

        hasil_matriks = None

        if pilihan == '1':
            val = int(input("Masukkan nilai brightness (-255 s.d 255): "))
            hasil_matriks = ubah_brightness(matriks_asli, val)

        elif pilihan == '2':
            val = float(input("Masukkan faktor kontras (misal 1.5 naik, 0.5 turun): "))
            hasil_matriks = ubah_contrast(matriks_asli, val)

        elif pilihan == '3':
            hasil_matriks = pencerminan_horizontal(matriks_asli)

        elif pilihan == '4':
            hasil_matriks = rotasi_90_derajat(matriks_asli)

        elif pilihan == '5':
            hasil_matriks = noise_reduction_mean(matriks_asli)

        elif pilihan == '6':
            hasil_matriks = deteksi_tepi(matriks_asli)

        elif pilihan == '7':
            print("Pilih channel yang akan ditukar:")
            print("  a. R ↔ B  (merah jadi biru, biru jadi merah)")
            print("  b. R ↔ G  (merah jadi hijau, hijau jadi merah)")
            print("  c. G ↔ B  (hijau jadi biru, biru jadi hijau)")
            sub = input("Pilihan (a/b/c): ").strip().lower()
            if sub == 'a':
                hasil_matriks = swap_channel(matriks_asli, 0, 2)
            elif sub == 'b':
                hasil_matriks = swap_channel(matriks_asli, 0, 1)
            elif sub == 'c':
                hasil_matriks = swap_channel(matriks_asli, 1, 2)
            else:
                print("[WARNING] Pilihan tidak valid.")
                continue

        else:
            print("[WARNING] Pilihan tidak valid.")
            continue

        if hasil_matriks:
            simpan_matriks_rgb_ke_bmp(hasil_matriks, output_nama)


if __name__ == "__main__":
    main()
