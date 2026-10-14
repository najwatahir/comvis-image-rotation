import struct
import os
import math


# ==========================================
# 0. KONVERSI FORMAT KE BMP (SATU-SATUNYA BAGIAN PAKAI LIBRARY)
# ==========================================
def konversi_ke_bmp(filepath_input, filepath_output=None):
    """Konversi gambar (PNG/JPEG/GIF) ke BMP 24-bit RGB.
    Satu-satunya fungsi yang pakai library (Pillow)."""
    from PIL import Image
    if filepath_output is None:
        nama_tanpa_ext = os.path.splitext(filepath_input)[0]
        filepath_output = nama_tanpa_ext + ".bmp"
    img = Image.open(filepath_input)
    img = img.convert("RGB")  # Pastikan 24-bit RGB
    img.save(filepath_output)
    print(f"[INFO] '{filepath_input}' dikonversi ke '{filepath_output}' (24-bit RGB)")
    return filepath_output


# ==========================================
# 1. BACA INFO HEADER BMP (MANUAL, TANPA LIBRARY)
# ==========================================
def baca_info_bmp(filepath):
    """
    Membaca header BMP secara manual menggunakan module struct.
    """
    if not os.path.exists(filepath):
        return {"error": f"File '{filepath}' tidak ditemukan"}

    try:
        with open(filepath, 'rb') as f:
            # === BITMAP FILE HEADER (14 byte) ===
            signature = f.read(2)
            if signature != b'BM':
                return {"error": "Bukan file BMP valid (signature bukan 'BM')"}

            file_size, = struct.unpack('<I', f.read(4))
            reserved = f.read(4)
            pixel_offset, = struct.unpack('<I', f.read(4))

            # === DIB HEADER (BITMAPINFOHEADER) ===
            dib_size, = struct.unpack('<I', f.read(4))

            if dib_size == 12:
                # BITMAPCOREHEADER
                width, height = struct.unpack('<HH', f.read(4))
                planes, = struct.unpack('<H', f.read(2))
                bit_count, = struct.unpack('<H', f.read(2))
                compression = 0
            else:
                # BITMAPINFOHEADER
                width, height = struct.unpack('<ii', f.read(8))
                planes, = struct.unpack('<H', f.read(2))
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
                'file_size': file_size,
                'planes': planes,
                'header_size': 14 + dib_size
            }
    except Exception as e:
        return {"error": f"Terjadi kesalahan saat membaca header BMP: {str(e)}"}


# ==========================================
# 2. BACA PIKSEL BMP KE MATRIKS RGB (MANUAL, TANPA LIBRARY)
# ==========================================
def baca_bmp_ke_matriks_rgb(filepath):
    """Membaca file BMP dan menyimpan piksel sebagai matriks tuple (R, G, B).
    Sepenuhnya manual: baca byte per byte, TIDAK dikonversi ke grayscale."""
    info = baca_info_bmp(filepath)
    if "error" in info:
        return None, info

    width = info['width']
    height = info['height']
    bit_count = info['bit_depth']
    pixel_offset = info['pixel_offset']
    top_down = info['top_down']

    if bit_count not in (8, 24, 32):
        return None, {"error": f"Bit depth {bit_count} belum didukung (hanya 8, 24, 32)"}

    with open(filepath, 'rb') as f:
        f.seek(pixel_offset)

        if bit_count == 24:
            bytes_per_row = width * 3
        elif bit_count == 32:
            bytes_per_row = width * 4
        else:  # 8-bit
            bytes_per_row = width

        padding = (4 - (bytes_per_row % 4)) % 4
        row_size = bytes_per_row + padding

        # Matriks RGB (tuple per piksel)
        matriks = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

        for row_idx in range(height):
            row_data = f.read(row_size)

            # BMP default = bottom-up
            if top_down:
                y = row_idx
            else:
                y = (height - 1) - row_idx

            for x in range(width):
                if bit_count == 24:
                    # BMP menyimpan BGR (bukan RGB!)
                    b = row_data[x * 3]
                    g = row_data[x * 3 + 1]
                    r = row_data[x * 3 + 2]
                    matriks[y][x] = (r, g, b)
                elif bit_count == 32:
                    b = row_data[x * 4]
                    g = row_data[x * 4 + 1]
                    r = row_data[x * 4 + 2]
                    matriks[y][x] = (r, g, b)
                elif bit_count == 8:
                    val = row_data[x]
                    matriks[y][x] = (val, val, val)

    return matriks, info


# ==========================================
# 3a. SIMPAN MATRIKS RGB KE FILE BMP 24-BIT (MANUAL)
# ==========================================
def simpan_matriks_rgb_ke_bmp(matriks, nama_file_output):
    """Menyimpan matriks RGB (tuple R,G,B) ke file BMP 24-bit.
    Menulis header + piksel byte per byte, tanpa library, tanpa palette."""
    tinggi = len(matriks)
    lebar = len(matriks[0])

    bytes_per_row = lebar * 3
    padding = (4 - (bytes_per_row % 4)) % 4
    row_size = bytes_per_row + padding

    pixel_data_size = row_size * tinggi
    pixel_offset = 14 + 40  # file header + DIB header (tanpa palette)
    file_size = pixel_offset + pixel_data_size

    with open(nama_file_output, 'wb') as f:
        # === FILE HEADER (14 byte) ===
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<HH', 0, 0))
        f.write(struct.pack('<I', pixel_offset))

        # === DIB HEADER - BITMAPINFOHEADER (40 byte) ===
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<i', lebar))
        f.write(struct.pack('<i', tinggi))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 24))          # 24 bit per piksel (RGB)
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', pixel_data_size))
        f.write(struct.pack('<i', 2835))
        f.write(struct.pack('<i', 2835))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', 0))

        # === DATA PIKSEL (bottom-up, format BGR) ===
        padding_bytes = b'\x00' * padding
        for y in range(tinggi - 1, -1, -1):
            for x in range(lebar):
                r, g, b = matriks[y][x]
                r = max(0, min(255, int(r)))
                g = max(0, min(255, int(g)))
                b = max(0, min(255, int(b)))
                f.write(struct.pack('BBB', b, g, r))  # BMP = BGR
            f.write(padding_bytes)

    print(f"[SUKSES] File RGB 24-bit disimpan sebagai: {nama_file_output}")


# ==========================================
# 3b. SIMPAN MATRIKS GRAYSCALE KE FILE BMP 8-BIT (MANUAL)
# ==========================================
def simpan_matriks_gray_ke_bmp(matriks, nama_file_output):
    """Menyimpan matriks grayscale 2D (int 0-255) ke file BMP 8-bit + palette."""
    tinggi = len(matriks)
    lebar = len(matriks[0])

    palette_size = 256 * 4
    bytes_per_row = lebar
    padding = (4 - (bytes_per_row % 4)) % 4
    row_size = bytes_per_row + padding

    pixel_data_size = row_size * tinggi
    pixel_offset = 14 + 40 + palette_size
    file_size = pixel_offset + pixel_data_size

    with open(nama_file_output, 'wb') as f:
        # === FILE HEADER (14 byte) ===
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<HH', 0, 0))
        f.write(struct.pack('<I', pixel_offset))

        # === DIB HEADER (40 byte) ===
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<i', lebar))
        f.write(struct.pack('<i', tinggi))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 8))            # 8 bit per piksel (grayscale)
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', pixel_data_size))
        f.write(struct.pack('<i', 2835))
        f.write(struct.pack('<i', 2835))
        f.write(struct.pack('<I', 256))
        f.write(struct.pack('<I', 0))

        # === COLOR TABLE (PALETTE GRAYSCALE) ===
        for i in range(256):
            f.write(struct.pack('BBBB', i, i, i, 0))

        # === DATA PIKSEL (bottom-up) ===
        padding_bytes = b'\x00' * padding
        for y in range(tinggi - 1, -1, -1):
            for x in range(lebar):
                val = max(0, min(255, int(matriks[y][x])))
                f.write(struct.pack('B', val))
            f.write(padding_bytes)

    print(f"[SUKSES] File grayscale 8-bit disimpan sebagai: {nama_file_output}")


# ==========================================
# 4. FUNGSI MANIPULASI CITRA RGB (TANPA LIBRARY, MANUAL)
# ==========================================
def batasi_nilai(nilai):
    if nilai < 0: return 0
    if nilai > 255: return 255
    return int(nilai)


def ubah_brightness(matriks, nilai_tambah):
    """Brightness per channel: C' = clamp(C + nilai_tambah)"""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            r, g, b = matriks[y][x]
            hasil[y][x] = (
                batasi_nilai(r + nilai_tambah),
                batasi_nilai(g + nilai_tambah),
                batasi_nilai(b + nilai_tambah)
            )
    return hasil


def ubah_contrast(matriks, g_faktor, p=128):
    """
    Peningkatan Kontras per channel (Modul Hal. 15):
        Ko = G * (Ki - P) + P
    G = koefisien penguatan, P = pusat pengontrasan (default 128)
    """
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            r, g, b = matriks[y][x]
            hasil[y][x] = (
                batasi_nilai(round(g_faktor * (r - p) + p)),
                batasi_nilai(round(g_faktor * (g - p) + p)),
                batasi_nilai(round(g_faktor * (b - p) + p))
            )
    return hasil


def pencerminan_horizontal(matriks):
    """Flip horizontal: posisi_x_baru = (lebar - 1) - x"""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[y][(lebar - 1) - x] = matriks[y][x]
    return hasil


def rotasi_90_derajat(matriks):
    """Rotasi 90 derajat clockwise. Dimensi bertukar."""
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(tinggi)] for _ in range(lebar)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[x][(tinggi - 1) - y] = matriks[y][x]
    return hasil


def reduksi_noise_median(matriks, ukuran=3):
    """
    Reduksi Noise Median per channel (Modul Hal. 31):
    Ambil jendela tetangga, urutkan, ambil nilai tengah.
    """
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [row[:] for row in matriks]
    radius = ukuran // 2

    for y in range(radius, tinggi - radius):
        for x in range(radius, lebar - radius):
            jendela_r, jendela_g, jendela_b = [], [], []
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    pr, pg, pb = matriks[y + dy][x + dx]
                    jendela_r.append(pr)
                    jendela_g.append(pg)
                    jendela_b.append(pb)
            jendela_r.sort(); jendela_g.sort(); jendela_b.sort()
            tengah = len(jendela_r) // 2
            hasil[y][x] = (
                batasi_nilai(jendela_r[tengah]),
                batasi_nilai(jendela_g[tengah]),
                batasi_nilai(jendela_b[tengah])
            )
    return hasil


def penghalusan_citra_mean(matriks, mode='9_titik'):
    """
    Penghalusan Citra per channel (Modul Hal. 29):
    - '9_titik' 3x3 bobot 1/9
    - '5_titik' salib bobot 1/5
    """
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [row[:] for row in matriks]

    for y in range(1, tinggi - 1):
        for x in range(1, lebar - 1):
            if mode == '5_titik':
                koordinat = [(y-1, x), (y+1, x), (y, x-1), (y, x+1), (y, x)]
                pembagi = 5.0
            else:
                koordinat = [
                    (y-1, x-1), (y-1, x), (y-1, x+1),
                    (y,   x-1), (y,   x), (y,   x+1),
                    (y+1, x-1), (y+1, x), (y+1, x+1)
                ]
                pembagi = 9.0

            total_r = total_g = total_b = 0
            for (yy, xx) in koordinat:
                pr, pg, pb = matriks[yy][xx]
                total_r += pr
                total_g += pg
                total_b += pb

            hasil[y][x] = (
                batasi_nilai(round(total_r / pembagi)),
                batasi_nilai(round(total_g / pembagi)),
                batasi_nilai(round(total_b / pembagi))
            )
    return hasil


def deteksi_tepi(matriks):
    """
    Deteksi Tepi Laplacian 9 titik per channel:
        nilai_tepi = |8*tengah - (jumlah 8 tetangga)|
    """
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[(0, 0, 0) for _ in range(lebar)] for _ in range(tinggi)]

    for y in range(1, tinggi - 1):
        for x in range(1, lebar - 1):
            tetangga = [
                matriks[y-1][x-1], matriks[y-1][x], matriks[y-1][x+1],
                matriks[y][x-1],   matriks[y][x+1],
                matriks[y+1][x-1], matriks[y+1][x], matriks[y+1][x+1]
            ]
            tr, tg, tb = matriks[y][x]

            sr = sum(p[0] for p in tetangga)
            sg = sum(p[1] for p in tetangga)
            sb = sum(p[2] for p in tetangga)

            hasil[y][x] = (
                batasi_nilai(abs(8 * tr - sr)),
                batasi_nilai(abs(8 * tg - sg)),
                batasi_nilai(abs(8 * tb - sb))
            )
    return hasil


def konversi_grayscale(matriks):
    """
    Konversi RGB ke grayscale (ITU-R BT.601), manual:
        gray = 0.299*R + 0.587*G + 0.114*B
    Output: matriks 2D (int) siap disimpan sebagai BMP 8-bit.
    """
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[0 for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            r, g, b = matriks[y][x]
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            hasil[y][x] = batasi_nilai(gray)
    return hasil


# ==========================================
# 5. VISUALISASI (matplotlib - HANYA untuk tampilan)
# ==========================================
def tampilkan_sebelum_sesudah(matriks_sebelum, matriks_sesudah, judul):
    """
    Tampilkan citra sebelum & sesudah operasi side-by-side.
    Matriks RGB (tuple) ATAU grayscale (int) ditangani otomatis.
    matplotlib HANYA dipakai untuk visualisasi.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    def ke_array(m):
        # Konversi matriks manual ke numpy array hanya untuk ditampilkan
        return np.array(m, dtype=np.uint8)

    arr_before = ke_array(matriks_sebelum)
    arr_after = ke_array(matriks_sesudah)

    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    if arr_before.ndim == 3:
        plt.imshow(arr_before)
    else:
        plt.imshow(arr_before, cmap="gray")
    plt.title("SEBELUM")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    if arr_after.ndim == 3:
        plt.imshow(arr_after)
    else:
        plt.imshow(arr_after, cmap="gray")
    plt.title(f"SESUDAH - {judul}")
    plt.axis("off")

    plt.tight_layout()
    plt.show()


# ==========================================
# 6. INFORMASI & UTILITAS CLI
# ==========================================
def tampilkan_informasi_gambar(matriks, info):
    tinggi = len(matriks)
    lebar = len(matriks[0])

    total_piksel = lebar * tinggi

    min_r = min_g = min_b = 255
    max_r = max_g = max_b = 0
    total_r = total_g = total_b = 0

    for y in range(tinggi):
        for x in range(lebar):
            r, g, b = matriks[y][x]
            if r > max_r: max_r = r
            if r < min_r: min_r = r
            if g > max_g: max_g = g
            if g < min_g: min_g = g
            if b > max_b: max_b = b
            if b < min_b: min_b = b
            total_r += r
            total_g += g
            total_b += b

    rata_r = total_r / total_piksel
    rata_g = total_g / total_piksel
    rata_b = total_b / total_piksel

    print("\n==========================================")
    print("      INFORMASI DETAIL CITRA (RGB)          ")
    print("==========================================")
    print("[1] Properti File:")
    print(f"    - Format File : {info.get('format', 'BMP')}")
    print(f"    - Ukuran File : {info.get('file_size', 0)} byte")
    print(f"    - Offset Data : {info.get('pixel_offset', 0)} byte")

    print("\n[2] Resolusi:")
    print(f"    - Dimensi     : {lebar} x {tinggi} piksel")
    print(f"    - Total Piksel: {total_piksel} piksel")

    print("\n[3] Kedalaman Warna (Color Depth):")
    print(f"    - Bit Depth Header : {info.get('bit_depth', 24)} bit")

    print("\n[4] Intensitas Warna (per channel):")
    print(f"    - Merah (R) : min={min_r}, max={max_r}, rata={rata_r:.2f}")
    print(f"    - Hijau (G) : min={min_g}, max={max_g}, rata={rata_g:.2f}")
    print(f"    - Biru  (B) : min={min_b}, max={max_b}, rata={rata_b:.2f}")
    print("==========================================\n")


def tampilkan_semua_intensitas(matriks):
    """Loop SEMUA piksel dan tampilkan ke CLI dengan format f(x,y) = r,g,b"""
    tinggi = len(matriks)
    lebar = len(matriks[0])

    print(f"\nMenampilkan {lebar * tinggi} piksel...\n")
    for y in range(tinggi):
        for x in range(lebar):
            r, g, b = matriks[y][x]
            print(f"f({x},{y}) = {r},{g},{b}")
    print()


# ==========================================
# 7. MENU UTAMA (CLI)
# ==========================================
def main():
    print("==========================================")
    print(" PROGRAM PENGOLAHAN CITRA RGB (CLI)        ")
    print("==========================================")

    filepath = input("Masukkan nama/path file gambar: ").strip().strip('"')

    if not os.path.exists(filepath):
        print(f"[ERROR] File '{filepath}' tidak ditemukan!")
        return

    # Konversi ke BMP bila bukan BMP (satu-satunya langkah pakai library)
    if not filepath.lower().endswith('.bmp'):
        print("[INFO] File bukan BMP, mengkonversi otomatis...")
        filepath = konversi_ke_bmp(filepath)

    # Baca piksel manual (tanpa library) -> matriks RGB
    matriks_asli, info = baca_bmp_ke_matriks_rgb(filepath)
    if matriks_asli is None:
        print(f"[ERROR] Gagal membaca file: {info.get('error', 'Unknown')}")
        return

    print(f"\n[INFO] Berhasil memuat gambar!")
    print(f"Format : {info['format']} | Resolusi: {info['width']}x{info['height']} | Bit Depth: {info['bit_depth']}")
    print(f"Contoh piksel (0,0): R={matriks_asli[0][0][0]}, G={matriks_asli[0][0][1]}, B={matriks_asli[0][0][2]}")

    while True:
        print("\n--- PILIH SKENARIO PENGOLAHAN ---")
        print("1. Ubah Brightness (Kecerahan)")
        print("2. Ubah Contrast (Kontras)")
        print("3. Pencerminan Horizontal (Mirror)")
        print("4. Rotasi 90 Derajat")
        print("5. Noise Reduction (Smoothing)")
        print("6. Deteksi Tepi (Edge Detection)")
        print("7. Informasi Detail Gambar")
        print("8. Tampilkan Semua Intensitas Piksel (f(x,y)=r,g,b)")
        print("9. Konversi ke GRAYSCALE")
        print("0. Keluar Program")

        pilihan = input("\nMasukkan nomor pilihan (0-9): ").strip()

        if pilihan == '0':
            print("Keluar dari program. Terima kasih!")
            break

        if pilihan == '7':
            tampilkan_informasi_gambar(matriks_asli, info)
            continue

        if pilihan == '8':
            tampilkan_semua_intensitas(matriks_asli)
            continue

        # Operasi 9 = grayscale (output 8-bit)
        if pilihan == '9':
            output_nama = input("Masukkan nama file hasil (contoh: abu.bmp): ").strip()
            if not output_nama.lower().endswith('.bmp'):
                output_nama += '.bmp'
            hasil_gray = konversi_grayscale(matriks_asli)
            simpan_matriks_gray_ke_bmp(hasil_gray, output_nama)
            tampilkan_sebelum_sesudah(matriks_asli, hasil_gray, "GRAYSCALE")
            continue

        # Operasi 1-6 (output 24-bit RGB)
        if pilihan not in ('1', '2', '3', '4', '5', '6'):
            print("[WARNING] Pilihan tidak valid.")
            continue

        output_nama = input("Masukkan nama file hasil (contoh: hasil.bmp): ").strip()
        if not output_nama.lower().endswith('.bmp'):
            output_nama += '.bmp'

        hasil_matriks = None
        judul = ""

        if pilihan == '1':
            val = int(input("Masukkan nilai brightness (-255 s.d 255): "))
            hasil_matriks = ubah_brightness(matriks_asli, val)
            judul = "Brightness"

        elif pilihan == '2':
            val_g = float(input("Masukkan koefisien penguatan kontras G (misal 1.5 naik, 0.5 turun): "))
            p_input = input("Masukkan nilai pusat pengontrasan P (tekan Enter untuk default 128): ").strip()
            val_p = int(p_input) if p_input else 128
            hasil_matriks = ubah_contrast(matriks_asli, val_g, val_p)
            judul = "Contrast"

        elif pilihan == '3':
            hasil_matriks = pencerminan_horizontal(matriks_asli)
            judul = "Mirror"

        elif pilihan == '4':
            hasil_matriks = rotasi_90_derajat(matriks_asli)
            judul = "Rotasi 90"

        elif pilihan == '5':
            print("\nPilih Metode Reduksi Noise / Penghalusan:")
            print("1. Operasi Median (Reduksi Noise - Modul Hal. 31) [Rekomendasi]")
            print("2. Mask 9 Titik Bertetangga / 3x3 Bobot 1/9 (Penghalusan - Modul Hal. 29)")
            print("3. Mask 5 Titik Bertetangga Bobot 1/5 (Penghalusan - Modul Hal. 29)")
            metode_noise = input("Pilihan (1/2/3, default 1): ").strip()
            if metode_noise == '2':
                hasil_matriks = penghalusan_citra_mean(matriks_asli, mode='9_titik')
                judul = "Mean 9-titik"
            elif metode_noise == '3':
                hasil_matriks = penghalusan_citra_mean(matriks_asli, mode='5_titik')
                judul = "Mean 5-titik"
            else:
                hasil_matriks = reduksi_noise_median(matriks_asli, ukuran=3)
                judul = "Median"

        elif pilihan == '6':
            hasil_matriks = deteksi_tepi(matriks_asli)
            judul = "Edge Detection"

        if hasil_matriks:
            simpan_matriks_rgb_ke_bmp(hasil_matriks, output_nama)
            tampilkan_sebelum_sesudah(matriks_asli, hasil_matriks, judul)


if __name__ == "__main__":
    main()
