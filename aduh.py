import struct
import os
import math


# ==========================================
# 0. KONVERSI FORMAT KE BMP (SATU-SATUNYA BAGIAN PAKAI LIBRARY)
# ==========================================
def konversi_ke_bmp(filepath_input, filepath_output=None):
    """Konversi gambar (PNG/JPEG/GIF) ke BMP. Satu-satunya fungsi pakai library."""
    from PIL import Image
    if filepath_output is None:
        nama_tanpa_ext = os.path.splitext(filepath_input)[0]
        filepath_output = nama_tanpa_ext + ".bmp"
    img = Image.open(filepath_input)
    img.save(filepath_output)
    print(f"[INFO] '{filepath_input}' dikonversi ke '{filepath_output}'")
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
# 2. BACA PIKSEL BMP KE MATRIKS (MANUAL, TANPA LIBRARY)
# ==========================================
def baca_bmp_ke_matriks(filepath):
    """Membaca file BMP dan mengekstrak piksel ke matriks grayscale 2D.
    Sepenuhnya manual: baca byte per byte, hitung grayscale sendiri."""
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

        # Hitung padding per baris (setiap baris BMP harus kelipatan 4 byte)
        if bit_count == 24:
            bytes_per_row = width * 3
        elif bit_count == 32:
            bytes_per_row = width * 4
        else:  # 8-bit
            bytes_per_row = width

        padding = (4 - (bytes_per_row % 4)) % 4
        row_size = bytes_per_row + padding

        # Baca semua baris piksel
        matriks = [[0 for _ in range(width)] for _ in range(height)]

        for row_idx in range(height):
            row_data = f.read(row_size)

            # BMP default = bottom-up (baris pertama di file = baris paling bawah)
            if top_down:
                y = row_idx
            else:
                y = (height - 1) - row_idx

            for x in range(width):
                if bit_count == 24:
                    # BMP menyimpan urutan BGR (bukan RGB!)
                    b = row_data[x * 3]
                    g = row_data[x * 3 + 1]
                    r = row_data[x * 3 + 2]
                    # Konversi RGB ke grayscale (rumus luminance standar)
                    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                    matriks[y][x] = gray
                elif bit_count == 32:
                    b = row_data[x * 4]
                    g = row_data[x * 4 + 1]
                    r = row_data[x * 4 + 2]
                    # byte ke-4 = alpha, diabaikan
                    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                    matriks[y][x] = gray
                elif bit_count == 8:
                    matriks[y][x] = row_data[x]

    return matriks, info


# ==========================================
# 3. SIMPAN MATRIKS KE FILE BMP (MANUAL, TANPA LIBRARY)
# ==========================================
def simpan_matriks_ke_bmp(matriks, nama_file_output):
    """Menyimpan matriks grayscale 2D ke file BMP 8-bit.
    Menulis header + palette + piksel byte per byte, tanpa library."""
    tinggi = len(matriks)
    lebar = len(matriks[0])

    # BMP 8-bit butuh color table (palette): 256 warna x 4 byte = 1024 byte
    palette_size = 256 * 4

    # Hitung padding per baris
    bytes_per_row = lebar
    padding = (4 - (bytes_per_row % 4)) % 4
    row_size = bytes_per_row + padding

    pixel_data_size = row_size * tinggi
    pixel_offset = 14 + 40 + palette_size  # file header + DIB header + palette
    file_size = pixel_offset + pixel_data_size

    with open(nama_file_output, 'wb') as f:
        # === FILE HEADER (14 byte) ===
        f.write(b'BM')                              # Signature
        f.write(struct.pack('<I', file_size))        # Ukuran file
        f.write(struct.pack('<HH', 0, 0))            # Reserved
        f.write(struct.pack('<I', pixel_offset))     # Offset ke data piksel

        # === DIB HEADER - BITMAPINFOHEADER (40 byte) ===
        f.write(struct.pack('<I', 40))               # Ukuran DIB header
        f.write(struct.pack('<i', lebar))             # Lebar
        f.write(struct.pack('<i', tinggi))            # Tinggi (positif = bottom-up)
        f.write(struct.pack('<H', 1))                # Planes
        f.write(struct.pack('<H', 8))                # Bit per piksel (8 = grayscale)
        f.write(struct.pack('<I', 0))                # Kompresi (0 = tidak ada)
        f.write(struct.pack('<I', pixel_data_size))  # Ukuran data piksel
        f.write(struct.pack('<i', 2835))             # X piksel per meter (~72 DPI)
        f.write(struct.pack('<i', 2835))             # Y piksel per meter
        f.write(struct.pack('<I', 256))              # Jumlah warna
        f.write(struct.pack('<I', 0))                # Warna penting

        # === COLOR TABLE (PALETTE GRAYSCALE) ===
        # 256 entry: (B=i, G=i, R=i, 0x00) untuk setiap level abu-abu
        for i in range(256):
            f.write(struct.pack('BBBB', i, i, i, 0))

        # === DATA PIKSEL (bottom-up) ===
        padding_bytes = b'\x00' * padding
        for y in range(tinggi - 1, -1, -1):  # tulis dari baris bawah ke atas
            for x in range(lebar):
                val = matriks[y][x]
                if val < 0: val = 0
                if val > 255: val = 255
                f.write(struct.pack('B', int(val)))
            f.write(padding_bytes)

    print(f"[SUKSES] File disimpan sebagai: {nama_file_output}")


# ==========================================
# 4. 6 FUNGSI MANIPULASI PENGOLAHAN CITRA (TANPA LIBRARY)
# ==========================================
def batasi_nilai(nilai):
    if nilai < 0: return 0
    if nilai > 255: return 255
    return int(nilai)

def ubah_brightness(matriks, nilai_tambah):
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[0 for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[y][x] = batasi_nilai(matriks[y][x] + nilai_tambah)
    return hasil

def ubah_contrast(matriks, faktor):
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[0 for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[y][x] = batasi_nilai(faktor * (matriks[y][x] - 128) + 128)
    return hasil

def pencerminan_horizontal(matriks):
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[0 for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[y][(lebar - 1) - x] = matriks[y][x]
    return hasil

def rotasi_90_derajat(matriks):
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[0 for _ in range(tinggi)] for _ in range(lebar)]
    for y in range(tinggi):
        for x in range(lebar):
            hasil[x][(tinggi - 1) - y] = matriks[y][x]
    return hasil

def noise_reduction_mean(matriks):
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [row[:] for row in matriks]  # salin asli untuk piksel pinggir
    for y in range(1, tinggi - 1):
        for x in range(1, lebar - 1):
            total = (
                matriks[y-1][x-1] + matriks[y-1][x] + matriks[y-1][x+1] +
                matriks[y][x-1]   + matriks[y][x]   + matriks[y][x+1] +
                matriks[y+1][x-1] + matriks[y+1][x] + matriks[y+1][x+1]
            )
            hasil[y][x] = batasi_nilai(total / 9)
    return hasil

def deteksi_tepi(matriks):
    tinggi, lebar = len(matriks), len(matriks[0])
    hasil = [[0 for _ in range(lebar)] for _ in range(tinggi)]
    for y in range(1, tinggi - 1):
        for x in range(1, lebar - 1):
            atas   = matriks[y-1][x]
            bawah  = matriks[y+1][x]
            kiri   = matriks[y][x-1]
            kanan  = matriks[y][x+1]
            tengah = matriks[y][x]

            # Rumus Laplacian 4-tetangga
            nilai_tepi = (tengah * 4) - (atas + bawah + kiri + kanan)
            hasil[y][x] = batasi_nilai(nilai_tepi)
    return hasil


def tampilkan_informasi_gambar(matriks, info):
    tinggi = len(matriks)
    lebar = len(matriks[0])
    
    total_piksel = lebar * tinggi
    
    nilai_max = 0
    nilai_min = 255
    total_intensitas = 0
    
    for y in range(tinggi):
        for x in range(lebar):
            val = matriks[y][x]
            if val > nilai_max: 
                nilai_max = val
            if val < nilai_min: 
                nilai_min = val
            total_intensitas += val
            
    rata_rata = total_intensitas / total_piksel
    
    bit_depth_aktual = max(1, math.ceil(math.log2(nilai_max + 1)))
    
    print("\n==========================================")
    print("      INFORMASI DETAIL CITRA (GAMBAR)       ")
    print("==========================================")
    print("[1] Properti File:")
    print(f"    - Format File : {info.get('format', 'BMP')}")
    print(f"    - Ukuran File : {info.get('file_size', 0)} byte")
    print(f"    - Offset Data : {info.get('pixel_offset', 0)} byte")
    
    print("\n[2] Resolusi:")
    print(f"    - Dimensi     : {lebar} x {tinggi} piksel")
    print(f"    - Total Piksel: {total_piksel} piksel")
    
    print("\n[3] Kedalaman Warna (Color Depth):")
    print(f"    - Bit Depth Header : {info.get('bit_depth', 8)} bit")
    print(f"    - Aktual Terpakai  : {bit_depth_aktual} bit (karena max intensitas {nilai_max})")
    
    print("\n[4] Intensitas Warna:")
    print(f"    - Intensitas Minimum : {nilai_min}")
    print(f"    - Intensitas Maksimum: {nilai_max}")
    print(f"    - Rata-rata (Mean)   : {rata_rata:.2f}")
    print("==========================================\n")


def cek_titik_koordinat(matriks):
    tinggi = len(matriks)
    lebar = len(matriks[0])
    
    print("\n--- CEK INTENSITAS PIKSEL ---")
    print(f"Batas X: 0 s.d {lebar - 1}")
    print(f"Batas Y: 0 s.d {tinggi - 1}")
    
    while True:
        try:
            x_input = input("\nMasukkan koordinat X (ketik 'q' untuk kembali ke menu): ").strip()
            if x_input.lower() == 'q':
                break
            x = int(x_input)
            
            y_input = input("Masukkan koordinat Y (ketik 'q' untuk kembali ke menu): ").strip()
            if y_input.lower() == 'q':
                break
            y = int(y_input)
            
            if 0 <= x < lebar and 0 <= y < tinggi:
                intensitas = matriks[y][x]
                print(f"[HASIL] Intensitas warna di koordinat (X={x}, Y={y}) adalah: {intensitas}")
            else:
                print(f"[WARNING] Koordinat melebihi batas! Maksimal X={lebar-1}, Y={tinggi-1}")
                
        except ValueError:
            print("[ERROR] Masukkan angka bilangan bulat atau huruf 'q' untuk keluar.")


# ==========================================
# 5. MENU UTAMA (CLI)
# ==========================================
def main():
    print("==========================================")
    print(" PROGRAM PENGOLAHAN CITRA DIGITAL (CLI)   ")
    print("==========================================")

    filepath = input("Masukkan nama/path file gambar: ").strip()

    # Cek apakah file ada
    if not os.path.exists(filepath):
        print(f"[ERROR] File '{filepath}' tidak ditemukan!")
        return

    # Jika bukan BMP, konversi dulu (satu-satunya langkah pakai library)
    if not filepath.lower().endswith('.bmp'):
        print(f"[INFO] File bukan BMP, mengkonversi otomatis...")
        filepath = konversi_ke_bmp(filepath)

    # Baca piksel secara manual (tanpa library)
    matriks_asli, info = baca_bmp_ke_matriks(filepath)
    if matriks_asli is None:
        print(f"[ERROR] Gagal membaca file: {info.get('error', 'Unknown')}")
        return

    print(f"\n[INFO] Berhasil memuat gambar!")
    print(f"Format : {info['format']} | Resolusi: {info['width']}x{info['height']} | Bit Depth: {info['bit_depth']}")

    while True:
        print("\n--- PILIH SKENARIO PENGOLAHAN ---")
        print("1. Ubah Brightness (Kecerahan)")
        print("2. Ubah Contrast (Kontras)")
        print("3. Pencerminan Horizontal (Mirror)")
        print("4. Rotasi 90 Derajat")
        print("5. Noise Reduction (Smoothing)")
        print("6. Deteksi Tepi (Edge Detection)")
        print("7. Informasi Detail Gambar")
        print("8. Cek Intensitas Piksel (Koordinat)")
        print("0. Keluar Program")

        pilihan = input("\nMasukkan nomor pilihan (0-8): ").strip()

        if pilihan == '0':
            print("Keluar dari program. Terima kasih!")
            break

        if pilihan == '7':
            tampilkan_informasi_gambar(matriks_asli, info)
            continue
            
        if pilihan == '8':
            cek_titik_koordinat(matriks_asli)
            continue

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
        else:
            print("[WARNING] Pilihan tidak valid.")
            continue

        if hasil_matriks:
            simpan_matriks_ke_bmp(hasil_matriks, output_nama)


if __name__ == "__main__":
    main()
