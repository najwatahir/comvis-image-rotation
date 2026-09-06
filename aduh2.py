"""
=======================================================================
PROGRAM PENGOLAHAN CITRA DIGITAL: OPERASI MORFOLOGI LENGKAP (CLI)
- Dilasi (Dilation) & Erosi (Erosion)
- Opening & Closing
- Top-Hat & Black-Hat Transform
- Hit-or-Miss Transform (HMT)
- Skeletonization (Kerangka Morfologi)
- Thinning (Penipisan Kontur 1-Piksel)
- Morfologi Gradient (Deteksi Tepi)
- Studi Kasus Nyata & Citra Input di folder img/
=======================================================================
Menggunakan Library NumPy dan Pillow (PIL).
Konsep antarmuka berbasis menu interaktif CLI (mirip aduh.py).
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# =======================================================================
# 1. I/O CITRA & UTILITAS
# =======================================================================
def muat_gambar(filepath, mode="L"):
    """
    Membaca file gambar dan mengonversinya ke numpy array 2D.
    Mode 'L' untuk Grayscale (default).
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File '{filepath}' tidak ditemukan!")
        return None
    try:
        img = Image.open(filepath).convert(mode)
        matriks = np.array(img, dtype=np.uint8)
        return matriks
    except Exception as e:
        print(f"[ERROR] Gagal membaca gambar: {e}")
        return None


def simpan_gambar(matriks, filepath_output):
    """Menyimpan matriks numpy 2D ke format file gambar (PNG/BMP/JPG)."""
    try:
        folder = os.path.dirname(filepath_output)
        if folder:
            os.makedirs(folder, exist_ok=True)
        matriks_clipped = np.clip(matriks, 0, 255).astype(np.uint8)
        img = Image.fromarray(matriks_clipped)
        img.save(filepath_output)
        print(f"[SUKSES] Gambar berhasil disimpan ke: '{filepath_output}'")
        return True
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan gambar: {e}")
        return False


def buat_gambar_komparasi(path_input, path_output, path_hasil, label_judul):
    """Membuat citra perbandingan berdampingan (Side-by-Side) Sebelum vs Sesudah."""
    try:
        im1 = Image.open(path_input).convert("RGB")
        im2 = Image.open(path_output).convert("RGB")
        w, h = im1.size
        total_w = w * 2 + 30
        total_h = h + 55
        gabungan = Image.new("RGB", (total_w, total_h), color=(30, 30, 30))
        gabungan.paste(im1, (10, 40))
        gabungan.paste(im2, (w + 20, 40))

        draw = ImageDraw.Draw(gabungan)
        draw.text((15, 12), f"{label_judul} - SEBELUM (INPUT)", fill=(255, 200, 50))
        draw.text((w + 25, 12), f"{label_judul} - SESUDAH (OUTPUT)", fill=(100, 255, 120))
        folder = os.path.dirname(path_hasil)
        if folder:
            os.makedirs(folder, exist_ok=True)
        gabungan.save(path_hasil)
        print(f"[INFO] Citra perbandingan disimpan ke: '{path_hasil}'")
    except Exception as e:
        print(f"[WARNING] Gagal membuat gambar komparasi: {e}")


def tampilkan_info_gambar(matriks, nama_file=""):
    """Menampilkan metadata dan statistik sederhana dari citra."""
    if matriks is None:
        return
    tinggi, lebar = matriks.shape
    min_val = int(np.min(matriks))
    max_val = int(np.max(matriks))
    rata_rata = float(np.mean(matriks))
    total_piksel = tinggi * lebar

    print("\n==========================================")
    print(f" INFORMASI CITRA: {os.path.basename(nama_file) if nama_file else 'Memori'}")
    print("==========================================")
    print(f" Dimensi (Resolusi)  : {lebar} x {tinggi} piksel")
    print(f" Total Piksel        : {total_piksel:,} piksel")
    print(f" Nilai Min Intensitas: {min_val}")
    print(f" Nilai Max Intensitas: {max_val}")
    print(f" Nilai Rata-rata      : {rata_rata:.2f}")
    is_biner = set(np.unique(matriks)).issubset({0, 255})
    print(f" Tipe Citra           : {'Biner (0 & 255)' if is_biner else 'Grayscale (0-255)'}")
    print("==========================================")


# =======================================================================
# 2. BINARISASI (OTSU & MANUAL)
# =======================================================================
def hitung_otsu_threshold(matriks_gray):
    """Menghitung threshold optimal secara otomatis menggunakan metode Otsu."""
    hist, _ = np.histogram(matriks_gray, bins=256, range=(0, 256))
    total = matriks_gray.size

    current_max = 0.0
    threshold_optimal = 128
    sum_total = np.dot(np.arange(256), hist)

    sum_b = 0.0
    weight_b = 0

    for t in range(256):
        weight_b += hist[t]
        if weight_b == 0:
            continue
        weight_f = total - weight_b
        if weight_f == 0:
            break

        sum_b += t * hist[t]
        mean_b = sum_b / weight_b
        mean_f = (sum_total - sum_b) / weight_f

        var_between = weight_b * weight_f * ((mean_b - mean_f) ** 2)

        if var_between > current_max:
            current_max = var_between
            threshold_optimal = t

    return threshold_optimal


def binarisasi_citra(matriks_gray, threshold=None):
    """Mengubah citra grayscale menjadi citra biner (0 atau 255)."""
    if threshold is None:
        threshold = hitung_otsu_threshold(matriks_gray)
        print(f"[INFO] Threshold otomatis (Metode Otsu): {threshold}")
    else:
        print(f"[INFO] Threshold manual: {threshold}")

    matriks_biner = np.where(matriks_gray >= threshold, 255, 0).astype(np.uint8)
    return matriks_biner


# =======================================================================
# 3. KERNEL (STRUCTURING ELEMENT)
# =======================================================================
def buat_kernel(ukuran=3, bentuk="square"):
    """
    Membuat Structuring Element (Kernel) untuk operasi morfologi.
    Ukuran harus bilangan ganjil (3, 5, 7, ...).
    Bentuk: 'square' (persegi penuh) atau 'cross' (tanda tambah/salib).
    """
    if ukuran % 2 == 0:
        ukuran += 1

    if bentuk.lower() == "cross":
        kernel = np.zeros((ukuran, ukuran), dtype=np.uint8)
        tengah = ukuran // 2
        kernel[tengah, :] = 1
        kernel[:, tengah] = 1
    else:  # square
        kernel = np.ones((ukuran, ukuran), dtype=np.uint8)

    return kernel


# =======================================================================
# 4. OPERASI MORFOLOGI DASAR: DILASI & EROSI
# =======================================================================
def dilasi(matriks, kernel=None, iterasi=1):
    """
    Operasi Dilasi (Dilation):
    Memperluas/menebalkan area piksel foreground (warna putih).
    Menggunakan ImageFilter C-SIMD untuk kernel persegi dan numpy reduce untuk cross.
    """
    if kernel is None:
        kernel = buat_kernel(3, "square")

    k_tinggi, k_lebar = kernel.shape
    hasil = matriks.copy()

    # Fast path untuk kernel persegi (all ones) via PIL ImageFilter
    if k_tinggi == k_lebar and np.all(kernel == 1):
        pil_img = Image.fromarray(hasil)
        for _ in range(iterasi):
            pil_img = pil_img.filter(ImageFilter.MaxFilter(size=k_tinggi))
        return np.array(pil_img, dtype=np.uint8)

    # Fast path untuk kernel cross 3x3
    if k_tinggi == 3 and k_lebar == 3 and kernel[0, 1] == 1 and kernel[0, 0] == 0:
        for _ in range(iterasi):
            p = np.pad(hasil, 1, mode="constant", constant_values=0)
            c = p[1:-1, 1:-1]
            u = p[0:-2, 1:-1]
            d = p[2:, 1:-1]
            l = p[1:-1, 0:-2]
            r = p[1:-1, 2:]
            hasil = np.maximum.reduce([c, u, d, l, r])
        return hasil

    # Fallback sliding window umum
    pad_y = k_tinggi // 2
    pad_x = k_lebar // 2
    mask_kernel = kernel == 1

    for _ in range(iterasi):
        tinggi, lebar = hasil.shape
        padded = np.pad(hasil, ((pad_y, pad_y), (pad_x, pad_x)), mode="constant", constant_values=0)
        temp = np.zeros_like(hasil)
        for y in range(tinggi):
            for x in range(lebar):
                window = padded[y : y + k_tinggi, x : x + k_lebar]
                temp[y, x] = np.max(window[mask_kernel])
        hasil = temp

    return hasil


def erosi(matriks, kernel=None, iterasi=1):
    """
    Operasi Erosi (Erosion):
    Mengikis batas luar piksel foreground (warna putih).
    Menggunakan ImageFilter C-SIMD untuk kernel persegi dan numpy reduce untuk cross.
    """
    if kernel is None:
        kernel = buat_kernel(3, "square")

    k_tinggi, k_lebar = kernel.shape
    hasil = matriks.copy()

    # Fast path untuk kernel persegi (all ones) via PIL ImageFilter
    if k_tinggi == k_lebar and np.all(kernel == 1):
        pil_img = Image.fromarray(hasil)
        for _ in range(iterasi):
            pil_img = pil_img.filter(ImageFilter.MinFilter(size=k_tinggi))
        return np.array(pil_img, dtype=np.uint8)

    # Fast path untuk kernel cross 3x3
    if k_tinggi == 3 and k_lebar == 3 and kernel[0, 1] == 1 and kernel[0, 0] == 0:
        for _ in range(iterasi):
            p = np.pad(hasil, 1, mode="constant", constant_values=255)
            c = p[1:-1, 1:-1]
            u = p[0:-2, 1:-1]
            d = p[2:, 1:-1]
            l = p[1:-1, 0:-2]
            r = p[1:-1, 2:]
            hasil = np.minimum.reduce([c, u, d, l, r])
        return hasil

    # Fallback sliding window umum
    pad_y = k_tinggi // 2
    pad_x = k_lebar // 2
    mask_kernel = kernel == 1

    for _ in range(iterasi):
        tinggi, lebar = hasil.shape
        padded = np.pad(hasil, ((pad_y, pad_y), (pad_x, pad_x)), mode="constant", constant_values=255)
        temp = np.zeros_like(hasil)
        for y in range(tinggi):
            for x in range(lebar):
                window = padded[y : y + k_tinggi, x : x + k_lebar]
                temp[y, x] = np.min(window[mask_kernel])
        hasil = temp

    return hasil


# =======================================================================
# 5. OPERASI MORFOLOGI LANJUTAN: OPENING, CLOSING, GRADIENT, TOP-HAT
# =======================================================================
def opening(matriks, kernel=None, iterasi=1):
    """
    Opening = Erosi kemudian Dilasi.
    Menghilangkan noise bintik putih kecil (salt noise) tanpa mengubah ukuran objek.
    """
    step1 = erosi(matriks, kernel, iterasi)
    step2 = dilasi(step1, kernel, iterasi)
    return step2


def closing(matriks, kernel=None, iterasi=1):
    """
    Closing = Dilasi kemudian Erosi.
    Menutup lubang hitam kecil (pepper noise) dan celah sempit di dalam objek.
    """
    step1 = dilasi(matriks, kernel, iterasi)
    step2 = erosi(step1, kernel, iterasi)
    return step2


def morfologi_gradient(matriks, kernel=None):
    """Morfologi Gradient = Dilasi - Erosi (Mengekstrak garis tepi/kontur)."""
    dil = dilasi(matriks, kernel, iterasi=1)
    ero = erosi(matriks, kernel, iterasi=1)
    return np.clip(dil.astype(np.int16) - ero.astype(np.int16), 0, 255).astype(np.uint8)


def top_hat(matriks, kernel=None):
    """
    White Top-Hat Transform = Citra Asli - Opening.
    Mengekstrak elemen/detail terang yang lebih kecil dari ukuran kernel
    pada latar belakang dengan pencahayaan tidak merata (uneven illumination).
    """
    if kernel is None:
        kernel = buat_kernel(15, "square")
    opened = opening(matriks, kernel)
    hasil = np.clip(matriks.astype(np.int16) - opened.astype(np.int16), 0, 255).astype(np.uint8)
    return hasil


def black_hat(matriks, kernel=None):
    """
    Black Top-Hat (Bottom-Hat) Transform = Closing - Citra Asli.
    Mengekstrak elemen/detail gelap kecil pada latar belakang terang.
    """
    if kernel is None:
        kernel = buat_kernel(15, "square")
    closed = closing(matriks, kernel)
    hasil = np.clip(closed.astype(np.int16) - matriks.astype(np.int16), 0, 255).astype(np.uint8)
    return hasil


# =======================================================================
# 6. HIT-OR-MISS TRANSFORM (HMT)
# =======================================================================
def hit_or_miss(matriks_biner, pattern):
    """
    Hit-or-Miss Transform (HMT):
    A (*) B = (A (erosi) B1) INTERSECT (A_komplemen (erosi) B2)
    Pattern matrix:
       1 : Foreground harus ada (Hit)
      -1 : Background harus ada (Miss)
       0 : Don't care
    """
    b1 = (pattern == 1).astype(np.uint8)
    b2 = (pattern == -1).astype(np.uint8)

    if np.any(b1):
        res_fg = erosi(matriks_biner, b1)
    else:
        res_fg = np.full_like(matriks_biner, 255)

    comp = np.where(matriks_biner > 0, 0, 255).astype(np.uint8)
    if np.any(b2):
        res_bg = erosi(comp, b2)
    else:
        res_bg = np.full_like(matriks_biner, 255)

    return np.where((res_fg == 255) & (res_bg == 255), 255, 0).astype(np.uint8)


# =======================================================================
# 7. SKELETONIZATION & THINNING
# =======================================================================
def skeletonization(matriks_biner, kernel=None, max_iter=100):
    """
    Morfologi Kerangka (Skeletonization) via formula morfologi Lantuéjoul:
    S(A) = UNION over k: [ (A erosi kB) - ((A erosi kB) opening B) ]
    """
    if kernel is None:
        kernel = buat_kernel(3, "cross")

    skeleton = np.zeros_like(matriks_biner, dtype=np.uint8)
    temp = matriks_biner.copy()

    for _ in range(max_iter):
        if not np.any(temp > 0):
            break
        opened = opening(temp, kernel)
        subset = np.clip(temp.astype(np.int16) - opened.astype(np.int16), 0, 255).astype(np.uint8)
        skeleton = np.bitwise_or(skeleton, subset)
        eroded = erosi(temp, kernel)
        if np.array_equal(temp, eroded):
            skeleton = np.bitwise_or(skeleton, eroded)
            break
        temp = eroded

    return skeleton


def thinning(matriks_biner):
    """
    Penipisan Morfologi (Thinning) menggunakan algoritma Zhang-Suen:
    Menghasilkan garis kontur setebal 1 piksel tanpa memutus topologi & konektivitas.
    """
    im = (matriks_biner > 128).astype(np.uint8)
    prev = np.zeros_like(im)

    while True:
        # --- Sub-iterasi 1 ---
        p = np.pad(im, 1, mode="constant")
        p2 = p[0:-2, 1:-1]
        p3 = p[0:-2, 2:]
        p4 = p[1:-1, 2:]
        p5 = p[2:, 2:]
        p6 = p[2:, 1:-1]
        p7 = p[2:, 0:-2]
        p8 = p[1:-1, 0:-2]
        p9 = p[0:-2, 0:-2]

        b = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
        a = (
            ((p2 == 0) & (p3 == 1)).astype(np.uint8)
            + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
            + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
            + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
            + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
            + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
            + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
            + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
        )

        m1 = (im == 1) & (b >= 2) & (b <= 6) & (a == 1) & ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)
        im[m1] = 0

        # --- Sub-iterasi 2 ---
        p = np.pad(im, 1, mode="constant")
        p2 = p[0:-2, 1:-1]
        p3 = p[0:-2, 2:]
        p4 = p[1:-1, 2:]
        p5 = p[2:, 2:]
        p6 = p[2:, 1:-1]
        p7 = p[2:, 0:-2]
        p8 = p[1:-1, 0:-2]
        p9 = p[0:-2, 0:-2]

        b = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
        a = (
            ((p2 == 0) & (p3 == 1)).astype(np.uint8)
            + ((p3 == 0) & (p4 == 1)).astype(np.uint8)
            + ((p4 == 0) & (p5 == 1)).astype(np.uint8)
            + ((p5 == 0) & (p6 == 1)).astype(np.uint8)
            + ((p6 == 0) & (p7 == 1)).astype(np.uint8)
            + ((p7 == 0) & (p8 == 1)).astype(np.uint8)
            + ((p8 == 0) & (p9 == 1)).astype(np.uint8)
            + ((p9 == 0) & (p2 == 1)).astype(np.uint8)
        )

        m2 = (im == 1) & (b >= 2) & (b <= 6) & (a == 1) & ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0)
        im[m2] = 0

        if np.array_equal(im, prev):
            break
        prev = im.copy()

    return (im * 255).astype(np.uint8)


# =======================================================================
# 8. GENERATOR CITRA INPUT STUDI KASUS (DI KELOMPOKKAN KE img/<operasi>/)
# =======================================================================
def generate_semua_citra_input():
    """Membuat dan menyimpan seluruh citra input studi kasus ke subfolder img/<operasi>/."""
    # 1. DILASI INPUT
    folder_dil = os.path.join("img", "dilasi")
    os.makedirs(folder_dil, exist_ok=True)
    img1 = Image.new("L", (500, 160), color=0)
    draw1 = ImageDraw.Draw(img1)
    try:
        font = ImageFont.truetype("arial.ttf", 44)
    except Exception:
        font = ImageFont.load_default()
    draw1.text((30, 40), "OCR 2026 TEST", fill=255, font=font)
    draw1.line([(30, 110), (470, 110)], fill=255, width=2)
    mat1 = np.array(img1, dtype=np.uint8)
    np.random.seed(42)
    for x in range(35, 465, 8):
        mat1[:, x : x + 2] = 0
    noise_mask = np.random.rand(160, 500) < 0.12
    mat1[noise_mask & (mat1 == 255)] = 0
    Image.fromarray(mat1).save(os.path.join(folder_dil, "input.png"))

    # 2. EROSI INPUT
    folder_ero = os.path.join("img", "erosi")
    os.makedirs(folder_ero, exist_ok=True)
    img2 = Image.new("L", (500, 250), color=0)
    draw2 = ImageDraw.Draw(img2)
    draw2.ellipse([80, 65, 200, 185], fill=255)
    draw2.ellipse([220, 65, 340, 185], fill=255)
    draw2.rectangle([180, 122, 240, 128], fill=255)
    draw2.ellipse([370, 80, 460, 170], fill=255)
    mat2 = np.array(img2, dtype=np.uint8)
    np.random.seed(99)
    mat2[np.random.rand(250, 500) < 0.015] = 255
    Image.fromarray(mat2).save(os.path.join(folder_ero, "input.png"))

    # 3. OPENING INPUT
    folder_op = os.path.join("img", "opening")
    os.makedirs(folder_op, exist_ok=True)
    img3 = Image.new("L", (500, 180), color=0)
    draw3 = ImageDraw.Draw(img3)
    try:
        font3 = ImageFont.truetype("arial.ttf", 42)
    except Exception:
        font3 = ImageFont.load_default()
    draw3.text((40, 35), "OPENING TEST", fill=255, font=font3)
    draw3.polygon([(380, 40), (420, 115), (340, 115)], fill=255)
    draw3.ellipse([400, 75, 470, 145], fill=255)
    mat3 = np.array(img3, dtype=np.uint8)
    np.random.seed(123)
    mat3[np.random.rand(180, 500) < 0.02] = 255
    for _ in range(50):
        ry = np.random.randint(0, 178)
        rx = np.random.randint(0, 498)
        mat3[ry : ry + 2, rx : rx + 2] = 255
    Image.fromarray(mat3).save(os.path.join(folder_op, "input.png"))

    # 4. CLOSING INPUT
    folder_cl = os.path.join("img", "closing")
    os.makedirs(folder_cl, exist_ok=True)
    img4 = Image.new("L", (500, 200), color=0)
    draw4 = ImageDraw.Draw(img4)
    draw4.rounded_rectangle([40, 35, 230, 165], radius=15, fill=255)
    draw4.ellipse([270, 35, 450, 165], fill=255)
    mat4 = np.array(img4, dtype=np.uint8)
    np.random.seed(456)
    for _ in range(60):
        ry = np.random.randint(45, 155)
        rx = np.random.randint(50, 220)
        if mat4[ry, rx] == 255:
            mat4[ry : ry + 3, rx : rx + 3] = 0
    for _ in range(60):
        ry = np.random.randint(45, 155)
        rx = np.random.randint(280, 440)
        if mat4[ry, rx] == 255:
            mat4[ry : ry + 3, rx : rx + 3] = 0
    mat4[98:102, 330:390] = 0
    Image.fromarray(mat4).save(os.path.join(folder_cl, "input.png"))

    # 5. TOP-HAT INPUT
    folder_th = os.path.join("img", "tophat")
    os.makedirs(folder_th, exist_ok=True)
    w, h = 500, 250
    x_grad = np.linspace(25, 190, w, dtype=np.float32)
    bg = np.tile(x_grad, (h, 1))
    fg = Image.new("L", (w, h), color=0)
    draw_fg = ImageDraw.Draw(fg)
    draw_fg.line([(50, 60), (120, 80), (150, 130)], fill=90, width=2)
    draw_fg.line([(220, 170), (280, 130), (330, 160)], fill=90, width=2)
    draw_fg.line([(380, 70), (450, 90), (470, 150)], fill=90, width=2)
    for cx, cy in [(80, 180), (190, 60), (300, 75), (420, 200), (250, 100), (360, 120)]:
        draw_fg.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=100)
    fg_arr = np.array(fg, dtype=np.float32)
    final_tophat = np.clip(bg + fg_arr, 0, 255).astype(np.uint8)
    Image.fromarray(final_tophat).save(os.path.join(folder_th, "input.png"))

    # 6. HIT-OR-MISS INPUT
    folder_hmt = os.path.join("img", "hit_or_miss")
    os.makedirs(folder_hmt, exist_ok=True)
    img6 = Image.new("L", (500, 250), color=0)
    draw6 = ImageDraw.Draw(img6)
    draw6.line([(60, 60), (200, 60)], fill=255, width=8)
    draw6.line([(200, 60), (200, 160)], fill=255, width=8)
    draw6.line([(100, 160), (320, 160)], fill=255, width=8)
    draw6.line([(210, 160), (210, 230)], fill=255, width=8)
    draw6.line([(300, 60), (440, 60)], fill=255, width=8)
    draw6.line([(350, 100), (350, 140)], fill=255, width=8)
    draw6.rectangle([410, 130, 430, 150], fill=255)
    img6.save(os.path.join(folder_hmt, "input.png"))

    # 7. SKELETONIZATION INPUT
    folder_sk = os.path.join("img", "skeletonization")
    os.makedirs(folder_sk, exist_ok=True)
    img7 = Image.new("L", (500, 280), color=0)
    draw7 = ImageDraw.Draw(img7)
    draw7.line([(70, 140), (220, 140)], fill=255, width=32)
    draw7.line([(220, 140), (350, 70)], fill=255, width=26)
    draw7.line([(220, 140), (350, 210)], fill=255, width=26)
    draw7.line([(350, 70), (450, 40)], fill=255, width=18)
    draw7.line([(350, 70), (450, 100)], fill=255, width=18)
    draw7.line([(350, 210), (450, 180)], fill=255, width=18)
    draw7.line([(350, 210), (450, 245)], fill=255, width=18)
    img7.save(os.path.join(folder_sk, "input.png"))

    # 8. THINNING INPUT
    folder_thn = os.path.join("img", "thinning")
    os.makedirs(folder_thn, exist_ok=True)
    img8 = Image.new("L", (500, 280), color=0)
    draw8 = ImageDraw.Draw(img8)
    draw8.ellipse([80, 40, 200, 150], outline=255, width=20)
    draw8.ellipse([70, 130, 210, 250], outline=255, width=22)
    draw8.line([(300, 40), (300, 240)], fill=255, width=20)
    draw8.arc([280, 40, 410, 145], start=270, end=90, fill=255, width=20)
    draw8.arc([280, 135, 420, 240], start=270, end=90, fill=255, width=20)
    img8.save(os.path.join(folder_thn, "input.png"))

    print("[INFO] Seluruh citra input studi kasus tersimpan rapi di subfolder 'img/<operasi>/'.")


# =======================================================================
# 9. EKSEKUTOR STUDI KASUS INTERAKTIF
# =======================================================================
def get_path_studi_kasus(op):
    """Mendapatkan path file input, output, dan perbandingan dalam folder img/<op>/."""
    folder = os.path.join("img", op)
    os.makedirs(folder, exist_ok=True)
    path_in = os.path.join(folder, "input.png")
    path_out = os.path.join(folder, "output.png")
    path_cmp = os.path.join(folder, "perbandingan.png")
    return path_in, path_out, path_cmp


def jalankan_studi_kasus_dilasi():
    print("\n=======================================================")
    print(" STUDI KASUS: DILASI (DILATION)")
    print(" 'Restorasi Teks Terputus & Garis Patah pada Dokumen OCR'")
    print("=======================================================")
    print("Masalah: Dokumen scan dengan binarisasi jelek menghasilkan huruf patah/retak.")
    print("Solusi : Dilasi memperlebar piksel karakter sehingga celah mikro tertutup.\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("dilasi")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = dilasi(img, buat_kernel(3, "square"), iterasi=1)
    simpan_gambar(hasil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "DILASI")


def jalankan_studi_kasus_erosi():
    print("\n=======================================================")
    print(" STUDI KASUS: EROSI (EROSION)")
    print(" 'Pemisahan Sel Berhimpit (Clumping) & Eliminasi Salt Noise'")
    print("=======================================================")
    print("Masalah: Dua sel mikroskopis saling menempel & terdapat bintik noise putih.")
    print("Solusi : Erosi mengikis lapisan luar, memutus jembatan kontak sempit & hapus noise.\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("erosi")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = erosi(img, buat_kernel(9, "square"), iterasi=1)
    simpan_gambar(hasil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "EROSI")


def jalankan_studi_kasus_opening():
    print("\n=======================================================")
    print(" STUDI KASUS: OPENING (EROSI -> DILASI)")
    print(" 'Penghapusan Bintik Pengotor (Salt Noise) Tanpa Mengubah Ukuran Objek'")
    print("=======================================================")
    print("Masalah: Citra teks/bentuk terpolusi bintik putih halus di latar & tepi.")
    print("Solusi : Opening mengikis habis bintik kecil (erosi), lalu mengembalikan")
    print("         ketebalan objek utama ke ukuran semula (dilasi).\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("opening")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = opening(img, buat_kernel(3, "square"), iterasi=1)
    simpan_gambar(hasil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "OPENING")


def jalankan_studi_kasus_closing():
    print("\n=======================================================")
    print(" STUDI KASUS: CLOSING (DILASI -> EROSI)")
    print(" 'Penutupan Celah Retak & Lubang Hitam (Pepper Noise) pada Objek Solid'")
    print("=======================================================")
    print("Masalah: Cacat porositas / lubang hitam kecil di dalam objek plat/koin.")
    print("Solusi : Closing menutup lubang hitam di dalam objek (dilasi), lalu mengikis")
    print("         kembali batas luar ke ukuran semula (erosi).\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("closing")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = closing(img, buat_kernel(7, "square"), iterasi=1)
    simpan_gambar(hasil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "CLOSING")


def jalankan_studi_kasus_tophat():
    print("\n=======================================================")
    print(" STUDI KASUS: TOP-HAT TRANSFORM (WHITE TOP-HAT)")
    print(" 'Koreksi Pencahayaan Tidak Merata & Ekstraksi Detail Terang Halus'")
    print("=======================================================")
    print("Masalah: Latar belakang memiliki gradien intensitas cahaya (uneven lighting),")
    print("         membuat thresholding biasa gagal total.")
    print("Solusi : Top-Hat mengestimasi latar belakang via opening kernel besar, lalu")
    print("         mengurangkannya dari citra asli sehingga objek terang terisolasi sempurna.\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("tophat")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = top_hat(img, buat_kernel(21, "square"))
    hasil_kontras = np.clip(hasil * 3, 0, 255).astype(np.uint8)
    simpan_gambar(hasil_kontras, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "TOP-HAT")


def jalankan_studi_kasus_hit_or_miss():
    print("\n=======================================================")
    print(" STUDI KASUS: HIT-OR-MISS TRANSFORM (HMT)")
    print(" 'Deteksi Pola Spesifik: Sudut Siku 90 Derajat pada Jalur Sirkuit PCB'")
    print("=======================================================")
    print("Masalah: Inspeksi otomatis PCB memerlukan lokasi pasti belokan sudut/ujung jalur.")
    print("Solusi : HMT mencocokkan pola piksel foreground (hit) dan background (miss)")
    print("         secara presisi hanya di lokasi yang memenuhi konfigurasi sudut siku.\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("hit_or_miss")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    pola_sudut = np.array([
        [-1, -1, -1],
        [ 0,  1, -1],
        [ 1,  1, -1]
    ], dtype=np.int8)

    hasil = hit_or_miss(img, pola_sudut)
    hasil_tampil = dilasi(hasil, buat_kernel(7, "square"), iterasi=1)
    simpan_gambar(hasil_tampil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "HIT-OR-MISS")


def jalankan_studi_kasus_skeletonization():
    print("\n=======================================================")
    print(" STUDI KASUS: SKELETONIZATION (KERANGKA MEDIAL AXIS)")
    print(" 'Ekstraksi Kerangka Percabangan Pembuluh Darah / Jalur Jaringan'")
    print("=======================================================")
    print("Masalah: Analisis morfometri (panjang dan sudut percabangan) terhalang oleh")
    print("         ketebalan pembuluh darah yang tidak seragam.")
    print("Solusi : Skeletonization mengikis objek sampai menjadi kerangka median tipis")
    print("         yang merepresentasikan sumbu simetri bentuk geometris objek.\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("skeletonization")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = skeletonization(img, buat_kernel(3, "cross"))
    simpan_gambar(hasil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "SKELETONIZATION")


def jalankan_studi_kasus_thinning():
    print("\n=======================================================")
    print(" STUDI KASUS: THINNING (PENIPISAN KONTUR)")
    print(" 'Penipisan Karakter Tulisan Tangan Tebal untuk OCR & Pengenalan Bentuk'")
    print("=======================================================")
    print("Masalah: Goresan pena pada tulisan tangan memiliki ketebalan bervariasi.")
    print("Solusi : Thinning mengikis piksel lapis demi lapis hingga terbentuk garis")
    print("         1-piksel sempurna dengan menjaga loop/lingkaran dan topologi asli.\n")
    path_in, path_out, path_cmp = get_path_studi_kasus("thinning")
    if not os.path.exists(path_in):
        generate_semua_citra_input()
    img = muat_gambar(path_in)
    hasil = thinning(img)
    simpan_gambar(hasil, path_out)
    buat_gambar_komparasi(path_in, path_out, path_cmp, "THINNING")


# =======================================================================
# 10. MENU UTAMA (CLI)
# =======================================================================

def main():
    print("=======================================================")
    print("    PROGRAM PENGOLAHAN CITRA DIGITAL: MORFOLOGI (CLI)  ")
    print("             DILASI, EROSI, OPENING, CLOSING,          ")
    print("         TOP-HAT, HIT-OR-MISS, SKELETON, THINNING      ")
    print("=======================================================")

    matriks_aktif = None
    nama_file_aktif = ""

    while True:
        print("\n--- MENU OPERASI MORFOLOGI CITRA ---")
        print("1. Muat Citra dari File (PNG / JPG / BMP)")
        print("2. Dilasi Citra (Dilation)")
        print("3. Erosi Citra (Erosion)")
        print("4. Opening (Erosi -> Dilasi: Bersihkan Noise)")
        print("5. Closing (Dilasi -> Erosi: Tutup Celah/Lubang)")
        print("6. Top-Hat Transform (Ekstraksi Objek Terang di Latar Gradien)")
        print("7. Hit-or-Miss Transform (Pencocokan Pola Khusus)")
        print("8. Skeletonization (Morfologi Kerangka Medial Axis)")
        print("9. Thinning (Penipisan Kontur Garis 1-Piksel)")
        print("10. Morfologi Gradient (Deteksi Garis Batas / Tepi)")
        print("11. Binarisasi Citra (Otsu / Threshold Manual)")
        print("0. Keluar Program")

        pilihan = input("\nMasukkan nomor pilihan (0-11): ").strip()

        if pilihan == "0":
            print("Keluar dari program. Terima kasih dan semoga sukses!")
            break

        if pilihan == "1":
            filepath = input("Masukkan path/nama file gambar: ").strip()
            matriks_aktif = muat_gambar(filepath)
            if matriks_aktif is not None:
                nama_file_aktif = filepath
                tampilkan_info_gambar(matriks_aktif, nama_file_aktif)
            continue

        if matriks_aktif is None:
            print("[PERINGATAN] Silakan muat gambar terlebih dahulu (Pilihan 1).")
            continue

        if pilihan == "11":
            mode_t = input("Pilih metode thresholding: (1) Otomatis Otsu, (2) Manual: ").strip()
            if mode_t == "2":
                try:
                    val_t = int(input("Masukkan nilai threshold (0-255): "))
                except ValueError:
                    val_t = 128
            else:
                val_t = None

            hasil_matriks = binarisasi_citra(matriks_aktif, val_t)
            output_nama = input("Masukkan nama file hasil (contoh: biner.png): ").strip()
            if output_nama:
                simpan_gambar(hasil_matriks, output_nama)
                tanya = input("Gunakan hasil ini sebagai citra aktif saat ini? (y/n): ").strip().lower()
                if tanya == "y":
                    matriks_aktif = hasil_matriks
                    nama_file_aktif = output_nama
            continue

        # Operasi Khusus: Hit-or-Miss, Skeletonization, Thinning
        if pilihan == "7":
            print("Pilih Pola Hit-or-Miss:")
            print("1. Deteksi Sudut Siku Kanan-Bawah (Corner)")
            print("2. Deteksi Titik Terisolasi (Isolated Point)")
            p_opt = input("Pilih (default 1): ").strip()
            if p_opt == "2":
                pola = np.array([
                    [-1, -1, -1],
                    [-1,  1, -1],
                    [-1, -1, -1]
                ], dtype=np.int8)
            else:
                pola = np.array([
                    [-1, -1, -1],
                    [ 0,  1, -1],
                    [ 1,  1, -1]
                ], dtype=np.int8)
            print("[PROSES] Menjalankan Hit-or-Miss Transform...")
            hasil_matriks = hit_or_miss(matriks_aktif, pola)
        elif pilihan == "8":
            print("[PROSES] Menghitung Skeletonization (Kerangka Morfologi)...")
            hasil_matriks = skeletonization(matriks_aktif)
        elif pilihan == "9":
            print("[PROSES] Menghitung Thinning (Penipisan Kontur 1-Piksel)...")
            hasil_matriks = thinning(matriks_aktif)
        else:
            # Operasi Berbasis Kernel (2, 3, 4, 5, 6, 10)
            default_k = "21" if pilihan == "6" else "3"
            try:
                k_size = int(input(f"Masukkan ukuran kernel ganjil (default {default_k}): ") or default_k)
                if k_size % 2 == 0:
                    k_size += 1
            except ValueError:
                k_size = int(default_k)

            bentuk = input("Pilih bentuk kernel: (1) Persegi/Square, (2) Salib/Cross [default 1]: ").strip()
            bentuk_str = "cross" if bentuk == "2" else "square"
            kernel = buat_kernel(k_size, bentuk_str)

            iterasi = 1
            if pilihan in ("2", "3", "4", "5"):
                try:
                    iterasi = int(input("Masukkan jumlah iterasi pengulangan (default 1): ") or "1")
                except ValueError:
                    iterasi = 1

            print(f"[PROSES] Menerapkan operasi dengan kernel {k_size}x{k_size} ({bentuk_str})...")

            if pilihan == "2":
                hasil_matriks = dilasi(matriks_aktif, kernel, iterasi)
            elif pilihan == "3":
                hasil_matriks = erosi(matriks_aktif, kernel, iterasi)
            elif pilihan == "4":
                hasil_matriks = opening(matriks_aktif, kernel, iterasi)
            elif pilihan == "5":
                hasil_matriks = closing(matriks_aktif, kernel, iterasi)
            elif pilihan == "6":
                hasil_matriks = top_hat(matriks_aktif, kernel)
            elif pilihan == "10":
                hasil_matriks = morfologi_gradient(matriks_aktif, kernel)
            else:
                print("[PERINGATAN] Pilihan tidak valid.")
                continue

        if hasil_matriks is not None:
            output_nama = input("Masukkan nama file hasil (contoh: hasil.png): ").strip()
            if not output_nama:
                output_nama = "hasil_operasi.png"
            simpan_gambar(hasil_matriks, output_nama)

            tanya = input("Apakah ingin menggunakan hasil ini untuk operasi berikutnya? (y/n): ").strip().lower()
            if tanya == "y":
                matriks_aktif = hasil_matriks
                nama_file_aktif = output_nama


if __name__ == "__main__":
    main()
