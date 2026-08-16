"""
=======================================================================
PROGRAM VISI KOMPUTER (VERSI SEDERHANA)
- Resolusi Citra
- Color Depth
- Rotasi Piksel (rumus matematika manual, tanpa fungsi library)
=======================================================================
Catatan:
- PIL/Pillow HANYA dipakai untuk baca & simpan file gambar (I/O).
- Semua perhitungan (resolusi, color depth, rotasi) dihitung manual.
"""

from PIL import Image

PI = 3.14159265358979323846


# =======================================================================
# 1. RESOLUSI CITRA
# =======================================================================
def hitung_resolusi(lebar, tinggi):
    # Resolusi = lebar x tinggi (jumlah total piksel)
    total_piksel = lebar * tinggi
    return total_piksel


# =======================================================================
# 2. COLOR DEPTH (tanpa math.log2 -> dihitung manual)
# =======================================================================
def log2_manual(n):
    """
    Mencari bit minimum agar 2^bit >= n, TANPA memakai math.log2().
    Contoh: n = 256 -> 2^8 = 256 -> bit = 8
    """
    if n <= 1:
        return 1
    bit = 0
    pangkat_dua = 1          # 2^0
    while pangkat_dua < n:
        pangkat_dua *= 2      # coba naikkan pangkat 2 sedikit demi sedikit
        bit += 1
    return bit


def hitung_color_depth(pixel_data, lebar, tinggi, jumlah_channel):
    """
    Color depth dihitung dari nilai maksimum piksel per channel.
    bit_per_channel = log2_manual(nilai_max + 1)
    total_depth      = bit_per_channel x jumlah_channel
    """
    # Cari nilai maksimum tiap channel secara manual
    nilai_max = [0] * jumlah_channel

    for y in range(tinggi):
        for x in range(lebar):
            piksel = pixel_data[y][x]
            if jumlah_channel == 1:
                nilai = [piksel]
            else:
                nilai = piksel

            for c in range(jumlah_channel):
                if nilai[c] > nilai_max[c]:
                    nilai_max[c] = nilai[c]

    bit_per_channel = [log2_manual(v + 1) for v in nilai_max]
    total_depth = sum(bit_per_channel)

    return bit_per_channel, total_depth


# =======================================================================
# 3. ROTASI PIKSEL (rumus rotasi + sin/cos manual via Deret Taylor)
# =======================================================================
def sin_manual(x):
    # sin(x) = x - x^3/3! + x^5/5! - ...
    hasil = 0.0
    suku = x
    for n in range(1, 15):
        hasil += suku
        suku = suku * (-1.0) * x * x / ((2 * n) * (2 * n + 1))
    return hasil


def cos_manual(x):
    # cos(x) = 1 - x^2/2! + x^4/4! - ...
    hasil = 0.0
    suku = 1.0
    for n in range(1, 15):
        hasil += suku
        suku = suku * (-1.0) * x * x / ((2 * n - 1) * (2 * n))
    return hasil


def rotasi_piksel(pixel_data, lebar, tinggi, sudut_derajat, piksel_kosong):
    """
    Rotasi memakai pendekatan PEMETAAN KE DEPAN (Forward Mapping).
    Akan menghasilkan efek titik-titik hitam (berlubang).
    Sesuai dengan referensi MATLAB:
        x2 = round(x * cosa - y * sina)
        y2 = round(y * cosa + x * sina)
    """
    rad = sudut_derajat * PI / 180.0
    cosa = cos_manual(rad)
    sina = sin_manual(rad)

    hasil = [[piksel_kosong for _ in range(lebar)] for _ in range(tinggi)]

    for y in range(tinggi):
        for x in range(lebar):
            # Rumus pemetaan ke depan persis seperti di gambar
            x2 = round(x * cosa - y * sina)
            y2 = round(y * cosa + x * sina)

            # Filter batas matriks (0-indexed untuk Python)
            if 0 <= x2 < lebar and 0 <= y2 < tinggi:
                hasil[y2][x2] = pixel_data[y][x]

    return hasil


# =======================================================================
# UTILITAS I/O (PIL hanya untuk baca/simpan file)
# =======================================================================
def baca_gambar(path):
    img = Image.open(path)
    if img.mode == "P":
        img = img.convert("RGB")
    elif img.mode == "1":
        img = img.convert("L")

    lebar, tinggi = img.size
    mode = img.mode
    jumlah_channel = 1 if mode == "L" else len(mode)

    pixel_data = [[img.getpixel((x, y)) for x in range(lebar)] for y in range(tinggi)]
    return pixel_data, lebar, tinggi, mode, jumlah_channel


def simpan_gambar(pixel_data, lebar, tinggi, mode, path_output):
    img_out = Image.new(mode, (lebar, tinggi))
    for y in range(tinggi):
        for x in range(lebar):
            img_out.putpixel((x, y), pixel_data[y][x])
    img_out.save(path_output)


# =======================================================================
# PROGRAM UTAMA
# =======================================================================
def main():
    path = input("Masukkan path file gambar: ").strip().strip('"')
    pixel_data, lebar, tinggi, mode, jumlah_channel = baca_gambar(path)

    # 1. Resolusi
    total_piksel = hitung_resolusi(lebar, tinggi)
    print(f"\nResolusi     : {lebar} x {tinggi}")
    print(f"Total Piksel : {total_piksel}")

    # 2. Color Depth
    bit_per_channel, total_depth = hitung_color_depth(pixel_data, lebar, tinggi, jumlah_channel)
    print(f"\nMode Citra   : {mode}")
    print(f"Bit/Channel  : {bit_per_channel}")
    print(f"Color Depth  : {total_depth} bit")

    # 3. Cek Titik Koordinat
    print("\n--- Cek Titik Koordinat ---")
    lanjut_cek = input("Ingin mengecek nilai piksel di titik koordinat tertentu? (y/n): ").strip().lower()
    while lanjut_cek == 'y':
        try:
            a = int(input(f"Masukkan koordinat A (X) [0 - {lebar-1}]: "))
            b = int(input(f"Masukkan koordinat B (Y) [0 - {tinggi-1}]: "))
            if 0 <= a < lebar and 0 <= b < tinggi:
                nilai = pixel_data[b][a]
                if isinstance(nilai, int):
                    array_rgba = [nilai]
                else:
                    array_rgba = list(nilai)
                print(f"{a}, {b} = {array_rgba}")
            else:
                print("Koordinat di luar batas gambar.")
        except ValueError:
            print("Input koordinat tidak valid.")
        
        lanjut_cek = input("Cek titik koordinat lain? (y/n): ").strip().lower()

    # 4. Rotasi
    sudut = float(input("\nMasukkan sudut rotasi (derajat): ").strip())
    piksel_kosong = 0 if mode == "L" else (0,) * jumlah_channel
    hasil_rotasi = rotasi_piksel(pixel_data, lebar, tinggi, sudut, piksel_kosong)

    path_output = "hasil_rotasi.png"
    simpan_gambar(hasil_rotasi, lebar, tinggi, mode, path_output)
    print(f"\nHasil rotasi disimpan di: {path_output}")


if __name__ == "__main__":
    main()