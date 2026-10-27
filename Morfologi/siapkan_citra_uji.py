import os
import cv2
import numpy as np
from skimage import data


def buat_folder_input():
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_uji")
    os.makedirs(folder, exist_ok=True)
    return folder


def simpan(folder, nama_file, img):
    path = os.path.join(folder, nama_file)
    cv2.imwrite(path, img)
    print(f"[OK] Tersimpan: {path}")


def generate_semua_citra():
    folder = buat_folder_input()
    print("=" * 60)
    print(" MENYIAPKAN CITRA UJI DUNIA NYATA UNTUK OPERASI MORFOLOGI")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. DILATION: Restorasi Teks Dokumen / Struk Thermal yang Putus (OCR)
    # Sumber: skimage.data.page() (dokumen hasil scan nyata dengan bayangan)
    # ------------------------------------------------------------------
    page = data.page()
    # Invert & ratakan bayangan pojok kiri bawah dengan Top-Hat agar latar belakang hitam bersih
    page_inv = 255 - page
    se_page = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    page_flat = cv2.morphologyEx(page_inv, cv2.MORPH_TOPHAT, se_page)
    _, dilasi_img = cv2.threshold(page_flat, 55, 255, cv2.THRESH_BINARY)
    simpan(folder, "1_dilasi_restorasi_teks_ocr.png", dilasi_img)

    # ------------------------------------------------------------------
    # Persiapan objek dasar 24 koin yang bulat utuh (solid) dari skimage.data.coins()
    # ------------------------------------------------------------------
    coins = data.coins()
    # Hilangkan pencahayaan tidak merata di pojok kiri atas menggunakan Top-Hat
    se_bg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (65, 65))
    coins_flat = cv2.morphologyEx(coins, cv2.MORPH_TOPHAT, se_bg)
    _, coins_mask = cv2.threshold(coins_flat, 42, 255, cv2.THRESH_BINARY)
    # Pisahkan sedikit lalu gunakan Convex Hull per koin agar tiap koin bulat solid
    # dan TIDAK menyatu satu sama lain
    coins_sep = cv2.erode(coins_mask, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(coins_sep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    coins_clean = np.zeros_like(coins_mask)
    centers = []
    for cnt in contours:
        if cv2.contourArea(cnt) > 120:
            hull = cv2.convexHull(cnt)
            cv2.drawContours(coins_clean, [hull], -1, 255, -1)
            M = cv2.moments(hull)
            if M["m00"] > 0:
                centers.append((int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])))

    # ------------------------------------------------------------------
    # 2. EROSION: Pemisahan Objek/Sel yang Menempel Tipis + Hapus Bintik Noise
    # ------------------------------------------------------------------
    erosi_img = coins_clean.copy()
    # Hubungkan beberapa koin yang bersebelahan dengan jembatan tipis (ketebalan 2 piksel)
    # agar saat di-Erosi (iterasi 2x), jembatan ini putus dan objek kembali terpisah!
    centers_sorted = sorted(centers, key=lambda c: (c[1] // 60, c[0]))
    for i in range(len(centers_sorted) - 1):
        c1, c2 = centers_sorted[i], centers_sorted[i + 1]
        if abs(c1[1] - c2[1]) < 35 and abs(c1[0] - c2[0]) < 85:
            cv2.line(erosi_img, c1, c2, 255, 2)
    rng = np.random.default_rng(42)
    small_specks = (rng.random(erosi_img.shape) > 0.985).astype(np.uint8) * 255
    small_specks = cv2.dilate(small_specks, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=1)
    erosi_img = cv2.bitwise_or(erosi_img, small_specks)
    simpan(folder, "2_erosi_pemisahan_sel_mikroskop.png", erosi_img)

    # ------------------------------------------------------------------
    # 3. OPENING: Pembersihan Noise Bintik ("Salt Noise") pada Citra Koin/Medis
    # ------------------------------------------------------------------
    noise = (rng.random(coins_clean.shape) > 0.975).astype(np.uint8) * 255
    noise = cv2.dilate(noise, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
    opening_img = cv2.bitwise_or(coins_clean, noise)
    simpan(folder, "3_opening_hapus_noise_bintik.png", opening_img)

    # ------------------------------------------------------------------
    # 4. CLOSING: Menutup Lubang Kecil (Pori/Retakan) pada Segmen Objek / X-Ray
    # ------------------------------------------------------------------
    closing_base = coins_clean.copy()
    # Buat lubang-lubang hitam kecil (1 piksel) di dalam koin putih agar tertutup rapat saat Closing
    holes = (rng.random(closing_base.shape) > 0.92).astype(np.uint8) * 255
    closing_img = cv2.bitwise_and(closing_base, cv2.bitwise_not(holes))
    simpan(folder, "4_closing_tutup_lubang_objek.png", closing_img)

    # ------------------------------------------------------------------
    # 5. TOP-HAT: Deteksi Bintang Redup (Astronomi) / Mikrokalsifikasi Medis
    # Sumber: skimage.data.hubble_deep_field() (Citra Teleskop Hubble NASA)
    # ------------------------------------------------------------------
    try:
        hubble = data.hubble_deep_field()
        hubble_gray = cv2.cvtColor(hubble, cv2.COLOR_RGB2GRAY)
        hubble_gray = cv2.resize(hubble_gray, (500, 500), interpolation=cv2.INTER_AREA)
    except Exception:
        hubble_gray = np.zeros((500, 500), dtype=np.uint8)
        for _ in range(180):
            y_s, x_s = rng.integers(5, 495), rng.integers(5, 495)
            cv2.circle(hubble_gray, (int(x_s), int(y_s)), int(rng.integers(2, 6)), int(rng.integers(180, 255)), -1)
    # Tambahkan iluminasi latar belakang tidak merata (vignetting/nebula) tanpa membuat bintang saturasi
    h, w = hubble_gray.shape[:2]
    Y, X = np.ogrid[:h, :w]
    nebula_glow = np.exp(-((X - w * 0.5) ** 2 + (Y - h * 0.5) ** 2) / (2.0 * (min(h, w) * 0.32) ** 2))
    nebula_glow = (nebula_glow * 130).astype(np.uint8)
    tophat_img = cv2.add((hubble_gray * 0.75).astype(np.uint8), nebula_glow)
    simpan(folder, "5_tophat_astronomi_bintang_hubble.png", tophat_img)

    # ------------------------------------------------------------------
    # 6. HIT-OR-MISS: Inspeksi Wafer/PCB (Dead Pixel, Sudut IC, & Ujung Jalur)
    # Dirancang agar cocok dengan KETIGA pola di aduh2.py (Pola 1, 2, dan 3)
    # ------------------------------------------------------------------
    pcb = np.zeros((300, 400), dtype=np.uint8)
    # Pola 1: Titik terisolasi 1 piksel (Hot pixel / debu mikro pada sensor/wafer)
    titik_koordinat = [(40, 50), (80, 120), (60, 250), (140, 330), (220, 80), (250, 290)]
    for y, x in titik_koordinat:
        pcb[y, x] = 255

    # Pola 2: Komponen IC persegi (memiliki sudut kiri-atas untuk deteksi posisi chip)
    cv2.rectangle(pcb, (60, 90), (130, 150), 255, -1)
    cv2.rectangle(pcb, (180, 70), (250, 130), 255, -1)
    cv2.rectangle(pcb, (290, 160), (360, 230), 255, -1)

    # Pola 3: Jalur sirkuit PCB vertikal (memiliki ujung garis vertikal di bagian atas)
    for x_line, y_start, y_end in [(95, 180, 270), (150, 160, 270), (215, 155, 270), (265, 100, 240)]:
        pcb[y_start:y_end, x_line] = 255

    simpan(folder, "6_hit_or_miss_inspeksi_pcb.png", pcb)

    # ------------------------------------------------------------------
    # 7. SKELETONIZATION: Pembuluh Darah Retina Mata & Siluet Morfologi
    # Sumber A: skimage.data.retina() (Foto Fundus Retina Mata Manusia Asli)
    # Sumber B: skimage.data.horse() (Siluet Kuda Klasik untuk Medial Axis)
    # ------------------------------------------------------------------
    try:
        retina_rgb = data.retina()
        # Channel hijau memiliki kontras pembuluh darah paling tinggi pada fundus fotografi
        green_ch = retina_rgb[:, :, 1]
        # Buat mask area bola mata supaya pinggiran luar tidak ikut
        _, fov_mask = cv2.threshold(green_ch, 15, 255, cv2.THRESH_BINARY)
        fov_mask = cv2.erode(fov_mask, np.ones((15, 15), np.uint8), iterations=2)
        # Ekstrak pembuluh darah (gelap di atas terang) menggunakan Black-Hat lalu threshold
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        green_eq = clahe.apply(green_ch)
        se_vessel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        vessels = cv2.morphologyEx(green_eq, cv2.MORPH_BLACKHAT, se_vessel)
        vessels = cv2.bitwise_and(vessels, fov_mask)
        _, vessels_bin = cv2.threshold(vessels, 18, 255, cv2.THRESH_BINARY)
        vessels_bin = cv2.morphologyEx(vessels_bin, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    except Exception:
        # Fallback jaringan pembuluh darah bercabang jika dataset retina belum terunduh
        vessels_bin = np.zeros((400, 400), dtype=np.uint8)
        cv2.line(vessels_bin, (30, 200), (160, 200), 255, 14)
        cv2.line(vessels_bin, (160, 200), (280, 110), 255, 10)
        cv2.line(vessels_bin, (160, 200), (290, 290), 255, 10)
        cv2.line(vessels_bin, (280, 110), (370, 60), 255, 7)
        cv2.line(vessels_bin, (280, 110), (370, 150), 255, 7)
        cv2.line(vessels_bin, (290, 290), (370, 240), 255, 7)
        cv2.line(vessels_bin, (290, 290), (370, 340), 255, 7)
    simpan(folder, "7a_skeleton_pembuluh_darah_retina.png", vessels_bin)

    # Siluet Kuda (invert agar objek kuda berwarna putih 255 di latar hitam 0)
    horse = data.horse()
    horse_uint8 = ((horse == 0) * 255).astype(np.uint8)
    simpan(folder, "7b_skeleton_siluet_kuda.png", horse_uint8)

    # ------------------------------------------------------------------
    # 8. THINNING (Zhang-Suen): Biometrik Sidik Jari & Karakter Tulisan (OCR)
    # ------------------------------------------------------------------
    # Buat pola alur sidik jari (fingerprint ridges) tebal dengan cabang (bifurcation) & ridge ending
    fp = np.zeros((400, 400), dtype=np.uint8)
    center = (200, 220)
    for r in range(25, 175, 18):
        cv2.ellipse(fp, center, (int(r * 0.8), int(r * 1.1)), 0, 195, 345, 255, 7)
        cv2.ellipse(fp, center, (int(r * 0.8), int(r * 1.1)), 0, 10, 165, 255, 7)
    simpan(folder, "8a_thinning_alur_sidik_jari.png", fp)

    # Contoh kedua untuk Thinning: Karakter Huruf/Angka Tebal untuk OCR
    ocr_canvas = np.zeros((250, 500), dtype=np.uint8)
    cv2.putText(ocr_canvas, "VISKOM 26", (25, 160), cv2.FONT_HERSHEY_SIMPLEX, 2.5, 255, 14, cv2.LINE_AA)
    _, ocr_canvas = cv2.threshold(ocr_canvas, 127, 255, cv2.THRESH_BINARY)
    simpan(folder, "8b_thinning_karakter_ocr.png", ocr_canvas)

    print("\n" + "=" * 60)
    print(" SELESAI! Semua citra siap dipakai di aduh2.py")
    print(f" Lokasi folder: {folder}")
    print("=" * 60)


if __name__ == "__main__":
    generate_semua_citra()
