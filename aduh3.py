"""
=======================================================================
PROGRAM PENGOLAHAN CITRA & VISI KOMPUTER: DETEKSI GEOMETRI (OPENCV)
File: aduh3.py
Fitur Utama:
1. Deteksi Garis (Line Detection) - HoughLines & HoughLinesP
2. Deteksi Lingkaran / Bulat (Circle Detection) - HoughCircles & Contour Circularity
3. Deteksi Oval / Elips (Oval/Ellipse Detection) - Contour Ellipse Fitting (cv2.fitEllipse)
=======================================================================
Menggunakan OpenCV (cv2) dan NumPy.
Antarmuka berbasis Menu Interaktif CLI (selaras dengan aduh.py & aduh2.py).
"""

import os
import sys
import math
import numpy as np
import cv2


# =======================================================================
# 1. UTILITAS I/O DAN TAMPILAN
# =======================================================================
def muat_gambar(filepath, mode_warna=cv2.IMREAD_COLOR):
    """
    Membaca citra dari path file dengan penanganan path Windows/spasi.
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File '{filepath}' tidak ditemukan!")
        return None

    # Menggunakan cv2.imdecode untuk mendukung path dengan karakter non-ASCII / spasi di Windows
    try:
        with open(filepath, "rb") as f:
            bytes_data = bytearray(f.read())
            array_np = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(array_np, mode_warna)
            if img is None:
                print(f"[ERROR] Format citra '{filepath}' tidak valid atau rusak!")
                return None
            h, w = img.shape[:2]
            print(f"[INFO] Berhasil memuat: '{filepath}' ({w}x{h} piksel)")
            return img
    except Exception as e:
        print(f"[ERROR] Gagal membaca gambar: {e}")
        return None


def simpan_gambar(img, filepath_output):
    """
    Menyimpan citra ke file output dengan dukungan karakter Windows/spasi.
    """
    try:
        folder = os.path.dirname(filepath_output)
        if folder:
            os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(filepath_output)[1]
        if not ext:
            ext = ".png"
            filepath_output += ext

        sukses, buffer = cv2.imencode(ext, img)
        if sukses:
            with open(filepath_output, "wb") as f:
                f.write(buffer)
            print(f"[SUKSES] Citra berhasil disimpan ke: '{filepath_output}'")
            return True
        else:
            print(f"[ERROR] Gagal melakukan encode citra ke format {ext}")
            return False
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan gambar: {e}")
        return False


def buat_komparasi(img_asli, img_hasil, judul_kiri="Citra Asli", judul_kanan="Hasil Deteksi"):
    """
    Menggabungkan citra asli dan citra hasil deteksi secara berdampingan (Side-by-Side).
    """
    h_a, w_a = img_asli.shape[:2]
    h_b, w_b = img_hasil.shape[:2]

    # Samakan tinggi jika berbeda
    h_max = max(h_a, h_b)
    scale_a = h_max / h_a
    scale_b = h_max / h_b

    resized_a = cv2.resize(img_asli, (int(w_a * scale_a), h_max))
    resized_b = cv2.resize(img_hasil, (int(w_b * scale_b), h_max))

    # Pastikan format 3 channel BGR
    if len(resized_a.shape) == 2:
        resized_a = cv2.cvtColor(resized_a, cv2.COLOR_GRAY2BGR)
    if len(resized_b.shape) == 2:
        resized_b = cv2.cvtColor(resized_b, cv2.COLOR_GRAY2BGR)

    # Tambahkan header label
    header_h = 45
    w_gabung = resized_a.shape[1] + resized_b.shape[1]
    kanvas = np.zeros((h_max + header_h, w_gabung, 3), dtype=np.uint8)
    kanvas[:header_h, :] = (35, 35, 35)

    cv2.putText(kanvas, judul_kiri, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(kanvas, judul_kanan, (resized_a.shape[1] + 20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)

    kanvas[header_h:, :resized_a.shape[1]] = resized_a
    kanvas[header_h:, resized_a.shape[1]:] = resized_b

    # Garis pemisah tengah
    cv2.line(kanvas, (resized_a.shape[1], 0), (resized_a.shape[1], h_max + header_h), (80, 80, 80), 2)
    return kanvas


def tampilkan_window(nama_window, img, tunggu=True):
    """
    Menampilkan gambar dalam window OpenCV jika lingkungan mendukung GUI.
    """
    try:
        cv2.namedWindow(nama_window, cv2.WINDOW_NORMAL)
        # Batasi ukuran display agar tidak keluar layar monitor
        h, w = img.shape[:2]
        max_dim = 900
        if max(h, w) > max_dim:
            skala = max_dim / max(h, w)
            cv2.resizeWindow(nama_window, int(w * skala), int(h * skala))
        cv2.imshow(nama_window, img)
        if tunggu:
            print(f"[INFO] Menampilkan jendela '{nama_window}'. Tekan sembarang tombol di jendela untuk melanjutkan...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    except Exception as e:
        print(f"[WARNING] Tidak dapat membuka jendela GUI OpenCV: {e}")


# =======================================================================
# 2. FITUR 1: DETEKSI GARIS (LINE DETECTION)
# =======================================================================
def deteksi_garis(img_bgr, min_line_length=50, max_line_gap=10, canny_thresh1=50, canny_thresh2=150, hough_thresh=80, metode="probabilistik"):
    """
    Mendeteksi garis lurus menggunakan Transformasi Hough.
    Metode:
    - 'probabilistik' (HoughLinesP): Mengembalikan segmen garis nyata [x1, y1, x2, y2].
    - 'standar' (HoughLines): Mengembalikan garis matematis tak terhingga (rho, theta).
    """
    img_hasil = img_bgr.copy()
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Reduksi derau dengan Gaussian Blur
    blur = cv2.GaussianBlur(gray, (5, 5), 1.5)

    # 2. Deteksi tepi dengan Canny
    edges = cv2.Canny(blur, canny_thresh1, canny_thresh2)

    data_garis = []

    if metode == "probabilistik":
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=hough_thresh,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap
        )

        if lines is not None:
            lines = lines.reshape(-1, 4)
            for idx, line in enumerate(lines):
                x1, y1, x2, y2 = map(int, line)
                panjang = math.hypot(x2 - x1, y2 - y1)
                sudut = math.degrees(math.atan2(y2 - y1, x2 - x1))
                data_garis.append({"id": idx + 1, "p1": (x1, y1), "p2": (x2, y2), "panjang": round(panjang, 1), "sudut": round(sudut, 1)})

                # Gambar garis pada citra hasil
                cv2.line(img_hasil, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA)
                # Gambar titik ujung
                cv2.circle(img_hasil, (x1, y1), 3, (0, 255, 0), -1)
                cv2.circle(img_hasil, (x2, y2), 3, (255, 0, 0), -1)
    else:
        # Metode Standar (HoughLines)
        lines = cv2.HoughLines(edges, rho=1, theta=np.pi / 180, threshold=hough_thresh)
        if lines is not None:
            lines = lines.reshape(-1, 2)
            h, w = img_bgr.shape[:2]
            diag = int(math.hypot(h, w))
            for idx, line in enumerate(lines):
                rho, theta = float(line[0]), float(line[1])
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + diag * (-b))
                y1 = int(y0 + diag * (a))
                x2 = int(x0 - diag * (-b))
                y2 = int(y0 - diag * (a))

                sudut = math.degrees(theta)
                data_garis.append({"id": idx + 1, "rho": round(rho, 1), "theta_deg": round(sudut, 1)})
                cv2.line(img_hasil, (x1, y1), (x2, y2), (0, 165, 255), 2, cv2.LINE_AA)

    # Tambahkan overlay statistik teks di pojok kiri atas
    jml = len(data_garis)
    info_text = f"Deteksi Garis ({metode.capitalize()}): {jml} ditemukan"
    cv2.putText(img_hasil, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img_hasil, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

    return img_hasil, edges, data_garis


# =======================================================================
# 3. FITUR 2: DETEKSI LINGKARAN / BULAT (CIRCLE DETECTION)
# =======================================================================
def deteksi_lingkaran(img_bgr, min_dist=40, param1=100, param2=30, min_radius=10, max_radius=0, metode="hough"):
    """
    Mendeteksi lingkaran menggunakan:
    - 'hough': cv2.HoughCircles (HOUGH_GRADIENT)
    - 'kontur': Deteksi kontur berbasis circularity (4 * pi * Area / Perimeter^2 >= 0.82)
    """
    img_hasil = img_bgr.copy()
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    data_lingkaran = []

    if metode == "hough":
        # MedianBlur sangat efektif meredam salt & pepper noise pada deteksi lingkaran
        gray_blur = cv2.medianBlur(gray, 5)

        circles = cv2.HoughCircles(
            gray_blur,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_dist,
            param1=param1,  # Ambang atas Canny
            param2=param2,  # Ambang akumulator pusat lingkaran
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is not None:
            circles = circles.reshape(-1, 3)
            circles = np.uint16(np.around(circles))
            for idx, c in enumerate(circles):
                cx, cy, r = int(c[0]), int(c[1]), int(c[2])
                data_lingkaran.append({"id": idx + 1, "pusat": (cx, cy), "radius": r})

                # Gambar keliling lingkaran (Hijau)
                cv2.circle(img_hasil, (cx, cy), r, (0, 255, 0), 2, cv2.LINE_AA)
                # Gambar titik pusat (Merah)
                cv2.circle(img_hasil, (cx, cy), 3, (0, 0, 255), -1)
                # Label ID dan Radius
                label = f"#{idx+1} r={r}"
                cv2.putText(img_hasil, label, (cx - 20, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(img_hasil, label, (cx - 20, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
    else:
        # Metode Kontur dengan Metrik Kebulatan (Circularity)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kontur_list, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        idx = 1
        for cnt in kontur_list:
            area = cv2.contourArea(cnt)
            if area < (math.pi * (min_radius ** 2)):
                continue

            keliling = cv2.arcLength(cnt, True)
            if keliling == 0:
                continue

            # Rumus sirkularitas: 4 * pi * Area / Perimeter^2
            # Lingkaran sempurna mendekati nilai 1.0
            circularity = 4 * math.pi * (area / (keliling * keliling))

            if circularity >= 0.80:
                (cx, cy), r = cv2.minEnclosingCircle(cnt)
                cx, cy, r = int(cx), int(cy), int(r)
                if max_radius > 0 and r > max_radius:
                    continue

                data_lingkaran.append({"id": idx, "pusat": (cx, cy), "radius": r, "circularity": round(circularity, 3)})
                cv2.circle(img_hasil, (cx, cy), r, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.circle(img_hasil, (cx, cy), 3, (0, 0, 255), -1)
                cv2.putText(img_hasil, f"C#{idx} ({circularity:.2f})", (cx - 30, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
                idx += 1

    jml = len(data_lingkaran)
    info_text = f"Deteksi Lingkaran: {jml} ditemukan"
    cv2.putText(img_hasil, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img_hasil, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

    return img_hasil, data_lingkaran


# =======================================================================
# 4. FITUR 3: DETEKSI OVAL / ELIPS (OVAL & ELLIPSE DETECTION)
# =======================================================================
def deteksi_oval(img_bgr, min_area=300, min_aspect_ratio=0.15, max_aspect_ratio=0.88, canny1=50, canny2=150):
    """
    Mendeteksi bentuk oval/elips menggunakan contour extraction dan fitting elips (cv2.fitEllipse).
    Perbedaan Oval vs Lingkaran:
    - Lingkaran memiliki Aspect Ratio (sumbu_minor / sumbu_mayor) mendekati 1.0 (biasanya > 0.88 - 0.90).
    - Oval/Elips memiliki Aspect Ratio antara min_aspect_ratio (misal 0.15) hingga max_aspect_ratio (misal 0.88).
    """
    img_hasil = img_bgr.copy()
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1.2)

    # Gabungkan Canny Edge + Thresholding adaptif untuk menangkap kontur oval dengan baik
    edges = cv2.Canny(blur, canny1, canny2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    kontur_list, _ = cv2.findContours(edges_closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    data_oval = []
    idx = 1

    for cnt in kontur_list:
        # cv2.fitEllipse membutuhkan minimal 5 titik pada kontur
        if len(cnt) < 5:
            continue

        area_kontur = cv2.contourArea(cnt)
        if area_kontur < min_area:
            continue

        try:
            elips = cv2.fitEllipse(cnt)
            (cx, cy), (sumbu_a, sumbu_b), sudut_rotasi = elips

            mayor = max(sumbu_a, sumbu_b)
            minor = min(sumbu_a, sumbu_b)

            if mayor <= 0:
                continue

            aspect_ratio = minor / mayor
            luas_elips = (math.pi * mayor * minor) / 4.0

            # Verifikasi kesesuaian kontur dengan bentuk elips (Solidity / Fit Ratio)
            if luas_elips > 0:
                fit_ratio = area_kontur / luas_elips
            else:
                fit_ratio = 0

            # Kriteria Oval:
            # 1. Aspek rasio berada di rentang oval (tidak memanjang seperti jarum dan tidak bulat sempurna)
            # 2. Area kontur konsisten dengan area elips teoritis (fit_ratio ~ 0.7 s.d 1.3)
            if (min_aspect_ratio <= aspect_ratio <= max_aspect_ratio) and (0.65 <= fit_ratio <= 1.35):
                # Hindari duplikat oval yang hampir sama posisinya
                duplikat = False
                for d in data_oval:
                    dx = d["pusat"][0] - cx
                    dy = d["pusat"][1] - cy
                    if math.hypot(dx, dy) < 15 and abs(d["mayor"] - mayor) < 15:
                        duplikat = True
                        break

                if not duplikat:
                    data_oval.append({
                        "id": idx,
                        "pusat": (int(cx), int(cy)),
                        "mayor": round(mayor, 1),
                        "minor": round(minor, 1),
                        "aspect_ratio": round(aspect_ratio, 3),
                        "sudut": round(sudut_rotasi, 1)
                    })

                    # Gambar garis elips berwarna Cyan
                    cv2.ellipse(img_hasil, elips, (255, 255, 0), 2, cv2.LINE_AA)
                    # Gambar titik pusat elips
                    cv2.circle(img_hasil, (int(cx), int(cy)), 3, (0, 0, 255), -1)

                    # Gambar sumbu mayor dan sumbu minor
                    rad = math.radians(sudut_rotasi)
                    cos_a, sin_a = math.cos(rad), math.sin(rad)
                    p1_mayor = (int(cx + (mayor / 2) * (-sin_a)), int(cy + (mayor / 2) * (cos_a)))
                    p2_mayor = (int(cx - (mayor / 2) * (-sin_a)), int(cy - (mayor / 2) * (cos_a)))
                    cv2.line(img_hasil, p1_mayor, p2_mayor, (200, 200, 0), 1, cv2.LINE_AA)

                    label = f"Oval #{idx} (AR:{aspect_ratio:.2f})"
                    cv2.putText(img_hasil, label, (int(cx) - 35, int(cy) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA)
                    idx += 1
        except Exception:
            continue

    jml = len(data_oval)
    info_text = f"Deteksi Oval / Elips: {jml} ditemukan"
    cv2.putText(img_hasil, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img_hasil, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

    return img_hasil, edges_closed, data_oval


# =======================================================================
# 5. FITUR 4: DETEKSI SEMUA BENTUK (ALL-IN-ONE DETECTOR)
# =======================================================================
def deteksi_semua_bentuk(img_bgr):
    """
    Mendeteksi Garis, Lingkaran (Bulat), dan Oval secara terpadu pada satu citra,
    dengan pembedaan warna visual yang kontras.
    - Garis: Merah (Red)
    - Lingkaran (Bulat): Hijau (Green)
    - Oval (Elips): Cyan (Biru Muda)
    """
    hasil = img_bgr.copy()

    # 1. Deteksi Garis
    _, _, lines = deteksi_garis(img_bgr, min_line_length=60, max_line_gap=10, hough_thresh=80)
    for l in lines:
        x1, y1 = l["p1"]
        x2, y2 = l["p2"]
        cv2.line(hasil, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA)

    # 2. Deteksi Lingkaran (Bulat)
    _, circles = deteksi_lingkaran(img_bgr, min_dist=40, param1=100, param2=32, min_radius=15)
    for c in circles:
        cx, cy = c["pusat"]
        r = c["radius"]
        cv2.circle(hasil, (cx, cy), r, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(hasil, (cx, cy), 3, (0, 0, 255), -1)

    # 3. Deteksi Oval
    _, _, ovals = deteksi_oval(img_bgr, min_area=400, min_aspect_ratio=0.25, max_aspect_ratio=0.85)
    for o in ovals:
        cx, cy = o["pusat"]
        mayor = o["mayor"]
        minor = o["minor"]
        sudut = o["sudut"]
        elips_param = ((float(cx), float(cy)), (float(minor), float(mayor)), float(sudut))
        cv2.ellipse(hasil, elips_param, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(hasil, (cx, cy), 3, (0, 0, 255), -1)

    # Legend / Legenda Keterangan di Atas Citra
    overlay = hasil.copy()
    cv2.rectangle(overlay, (10, 10), (320, 125), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.75, hasil, 0.25, 0, hasil)

    cv2.putText(hasil, "HASIL DETEKSI MULTI-BENTUK:", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(hasil, f"- Garis (Merah): {len(lines)}", (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.putText(hasil, f"- Lingkaran Bulat (Hijau): {len(circles)}", (20, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(hasil, f"- Oval / Elips (Cyan): {len(ovals)}", (20, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2, cv2.LINE_AA)

    return hasil, lines, circles, ovals


# =======================================================================
# 6. GENERATOR CITRA UJI SINTETIS (UNTUK DEMO LANGSUNG)
# =======================================================================
def buat_citra_sampel_uji(filepath_output="img/sampel_geometri.png"):
    """
    Membuat citra sintetis yang memuat garis, lingkaran bulat, dan oval
    secara otomatis agar pengguna dapat langsung menguji program tanpa unduhan eksternal.
    """
    folder = os.path.dirname(filepath_output)
    if folder:
        os.makedirs(folder, exist_ok=True)

    w, h = 800, 600
    kanvas = np.ones((h, w, 3), dtype=np.uint8) * 245

    # 1. Menggambar Garis
    cv2.line(kanvas, (60, 80), (380, 80), (20, 20, 20), 3)       # Horizontal
    cv2.line(kanvas, (100, 120), (100, 480), (40, 40, 40), 3)    # Vertikal
    cv2.line(kanvas, (140, 150), (360, 360), (30, 30, 30), 4)    # Diagonal
    cv2.line(kanvas, (60, 450), (360, 380), (25, 25, 25), 3)

    # 2. Menggambar Lingkaran Bulat
    cv2.circle(kanvas, (550, 140), 65, (30, 30, 30), 3)          # Bulat Besar
    cv2.circle(kanvas, (680, 230), 38, (45, 45, 45), 3)          # Bulat Sedang
    cv2.circle(kanvas, (450, 250), 25, (20, 20, 20), -1)         # Bulat Solid

    # 3. Menggambar Oval / Elips
    cv2.ellipse(kanvas, ((580, 420), (160, 80), 30), (30, 30, 30), 3)    # Oval Miring 30 derajad
    cv2.ellipse(kanvas, ((300, 480), (140, 60), 0), (25, 25, 25), 3)     # Oval Horizontal
    cv2.ellipse(kanvas, ((680, 460), (70, 130), 0), (35, 35, 35), -1)    # Oval Vertikal Solid

    # Tambahkan sedikit noise realistis
    noise = np.random.normal(0, 5, kanvas.shape).astype(np.int16)
    kanvas_noisy = np.clip(kanvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    simpan_gambar(kanvas_noisy, filepath_output)
    print(f"[INFO] Citra uji sintetis berhasil dibuat di: '{filepath_output}'")
    return filepath_output


# =======================================================================
# 7. MENU INTERAKTIF CLI
# =======================================================================
def cetak_header():
    print("=" * 72)
    print("      PROGRAM DETEKSI GARIS, LINGKARAN & OVAL (OPENCV)")
    print("                   Mata Kuliah: Visi Komputer")
    print("=" * 72)


def main():
    cetak_header()

    citra_aktif_path = None
    citra_aktif = None

    # Opsi gambar default awal jika tersedia
    kandidat_default = ["img/sampel_geometri.png", "poto.png", "poto.bmp", "noise-2.png"]
    for k in kandidat_default:
        if os.path.exists(k):
            citra_aktif_path = k
            citra_aktif = muat_gambar(k)
            break

    while True:
        print("\n" + "-" * 72)
        status_img = f"'{citra_aktif_path}'" if citra_aktif_path else "[Belum ada gambar yang dimuat]"
        print(f"Citra Aktif Saat Ini : {status_img}")
        print("-" * 72)
        print(" [1] Muat / Ganti Citra Input (File Gambar)")
        print(" [2] Deteksi GARIS (Line Detection - HoughLinesP / HoughLines)")
        print(" [3] Deteksi LINGKARAN BULAT (Circle Detection - HoughCircles)")
        print(" [4] Deteksi OVAL / ELIPS (Ellipse Detection - Contour Fit)")
        print(" [0] Keluar")
        print("-" * 72)

        pilihan = input("Pilih menu (0-4): ").strip()

        if pilihan == "0":
            print("\n[INFO] Terima kasih! Program selesai.")
            break

        elif pilihan == "1":
            path_input = input("Masukkan path file gambar (contoh: img/test.jpg atau drag-and-drop): ").strip().strip('"').strip("'")
            if not path_input:
                continue
            img = muat_gambar(path_input)
            if img is not None:
                citra_aktif_path = path_input
                citra_aktif = img

        elif pilihan in ("2", "3", "4"):
            if citra_aktif is None:
                print("[PERINGATAN] Silakan muat gambar terlebih dahulu melalui Menu [1]!")
                continue

            nama_basis = os.path.splitext(os.path.basename(citra_aktif_path))[0]

            if pilihan == "2":
                # DETEKSI GARIS
                print("\n--- PENGATURAN DETEKSI GARIS ---")
                metode = input("Metode Hough: (1) Probabilistik [Rekomendasi], (2) Standar [default 1]: ").strip()
                metode_str = "standar" if metode == "2" else "probabilistik"

                def_min_len = "50"
                def_max_gap = "10"
                def_thresh = "80"

                try:
                    min_len = int(input(f"Min Line Length (default {def_min_len}): ") or def_min_len)
                    max_gap = int(input(f"Max Line Gap (default {def_max_gap}): ") or def_max_gap)
                    hough_th = int(input(f"Hough Threshold (default {def_thresh}): ") or def_thresh)
                except ValueError:
                    min_len, max_gap, hough_th = 50, 10, 80

                print("[PROSES] Mendeteksi garis lurus dengan Hough Transform...")
                hasil_img, edge_img, data = deteksi_garis(
                    citra_aktif,
                    min_line_length=min_len,
                    max_line_gap=max_gap,
                    hough_thresh=hough_th,
                    metode=metode_str
                )

                print(f"[HASIL] Terdeteksi {len(data)} garis.")
                for d in data[:10]:
                    print(f"  -> Garis #{d['id']}: P1={d.get('p1')} P2={d.get('p2')} Panjang={d.get('panjang')} Sudut={d.get('sudut')} deg")
                if len(data) > 10:
                    print(f"  ... dan {len(data)-10} garis lainnya.")

                out_hasil = f"hasil_deteksi_garis_{nama_basis}.png"
                out_komp = f"komparasi_garis_{nama_basis}.png"
                komparasi = buat_komparasi(citra_aktif, hasil_img, "Citra Asli", f"Deteksi Garis ({len(data)} segmen)")
                simpan_gambar(hasil_img, out_hasil)
                simpan_gambar(komparasi, out_komp)
                tampilkan_window("Deteksi Garis", komparasi)

            elif pilihan == "3":
                # DETEKSI LINGKARAN BULAT
                print("\n--- PENGATURAN DETEKSI LINGKARAN BULAT ---")
                def_min_dist = "40"
                def_min_r = "10"
                def_max_r = "0"
                def_param2 = "30"

                try:
                    min_dist = int(input(f"Jarak minimum antar pusat lingkaran (default {def_min_dist}): ") or def_min_dist)
                    min_r = int(input(f"Radius minimum (default {def_min_r}): ") or def_min_r)
                    max_r = int(input(f"Radius maksimum (0 = otomatis, default {def_max_r}): ") or def_max_r)
                    param2 = int(input(f"Sensitivitas akumulator Hough (default {def_param2}, semakin kecil makin sensitif): ") or def_param2)
                except ValueError:
                    min_dist, min_r, max_r, param2 = 40, 10, 0, 30

                print("[PROSES] Mendeteksi lingkaran bulat dengan Hough Circles...")
                hasil_img, data = deteksi_lingkaran(
                    citra_aktif,
                    min_dist=min_dist,
                    param1=100,
                    param2=param2,
                    min_radius=min_r,
                    max_radius=max_r
                )

                print(f"[HASIL] Terdeteksi {len(data)} lingkaran bulat.")
                for d in data[:10]:
                    print(f"  -> Lingkaran #{d['id']}: Pusat={d['pusat']}, Radius={d['radius']} px")
                if len(data) > 10:
                    print(f"  ... dan {len(data)-10} lingkaran lainnya.")

                out_hasil = f"hasil_deteksi_lingkaran_{nama_basis}.png"
                out_komp = f"komparasi_lingkaran_{nama_basis}.png"
                komparasi = buat_komparasi(citra_aktif, hasil_img, "Citra Asli", f"Deteksi Lingkaran ({len(data)} objek)")
                simpan_gambar(hasil_img, out_hasil)
                simpan_gambar(komparasi, out_komp)
                tampilkan_window("Deteksi Lingkaran", komparasi)

            elif pilihan == "4":
                # DETEKSI OVAL / ELIPS
                print("\n--- PENGATURAN DETEKSI OVAL / ELIPS ---")
                def_min_area = "300"
                def_min_ar = "0.20"
                def_max_ar = "0.88"

                try:
                    min_area = int(input(f"Luas area kontur minimum (default {def_min_area}): ") or def_min_area)
                    min_ar = float(input(f"Batas bawah Aspect Ratio (default {def_min_ar}): ") or def_min_ar)
                    max_ar = float(input(f"Batas atas Aspect Ratio (default {def_max_ar}): ") or def_max_ar)
                except ValueError:
                    min_area, min_ar, max_ar = 300, 0.20, 0.88

                print("[PROSES] Mendeteksi bentuk oval dan fitting elips kontur...")
                hasil_img, edge_img, data = deteksi_oval(
                    citra_aktif,
                    min_area=min_area,
                    min_aspect_ratio=min_ar,
                    max_aspect_ratio=max_ar
                )

                print(f"[HASIL] Terdeteksi {len(data)} oval/elips.")
                for d in data[:10]:
                    print(f"  -> Oval #{d['id']}: Pusat={d['pusat']}, Mayor={d['mayor']}px, Minor={d['minor']}px, Rasio Sumbu={d['aspect_ratio']}, Rotasi={d['sudut']} deg")
                if len(data) > 10:
                    print(f"  ... dan {len(data)-10} oval lainnya.")

                out_hasil = f"hasil_deteksi_oval_{nama_basis}.png"
                out_komp = f"komparasi_oval_{nama_basis}.png"
                komparasi = buat_komparasi(citra_aktif, hasil_img, "Citra Asli", f"Deteksi Oval ({len(data)} objek)")
                simpan_gambar(hasil_img, out_hasil)
                simpan_gambar(komparasi, out_komp)
                tampilkan_window("Deteksi Oval", komparasi)

        else:
            print("[PERINGATAN] Pilihan tidak valid. Silakan pilih 0-4.")


if __name__ == "__main__":
    main()
