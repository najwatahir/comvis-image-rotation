"""
PROGRAM DETEKSI GEOMETRI CITRA

Fitur:
1. Deteksi garis dengan HoughLinesP
   + filter
   + merge garis duplikat
2. Deteksi satu lingkaran dengan HoughCircles
3. Deteksi oval/elips dengan fitEllipse
"""

import os
import math
import cv2
import numpy as np


# =====================================================
# LOAD IMAGE
# =====================================================
def load_image(path):
    if not os.path.exists(path):
        print("File tidak ditemukan")
        return None

    image = cv2.imread(path)
    if image is None:
        print("Gambar gagal dibaca")
        return None

    return image


# =====================================================
# SAVE IMAGE
# =====================================================
def save_image(image, filename):
    cv2.imwrite(filename, image)
    print("Berhasil disimpan:", filename)


# =====================================================
# PREPROCESSING
# =====================================================
def preprocessing(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    edge = cv2.Canny(blur, 100, 200)
    return gray, edge


# =====================================================
# MERGE GARIS DUPLIKAT
# =====================================================
def gabungkan_garis(lines, jarak_maks=30, sudut_maks=5):
    """
    Menggabungkan garis yang:
    - sudut hampir sama
    - posisi berdekatan
    """
    if lines is None:
        return []

    garis_unik = []

    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        panjang = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # Buang garis pendek
        if panjang < 100:
            continue

        sudut = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
        sudah_gabung = False

        for garis in garis_unik:
            gx1, gy1, gx2, gy2, gsudut = garis
            beda_sudut = abs(sudut - gsudut)
            jarak = min(
                abs(x1 - gx1),
                abs(x1 - gx2),
                abs(x2 - gx1),
                abs(x2 - gx2)
            )

            if beda_sudut < sudut_maks and jarak < jarak_maks:
                panjang_lama = np.sqrt((gx2 - gx1) ** 2 + (gy2 - gy1) ** 2)
                if panjang > panjang_lama:
                    garis[0] = x1
                    garis[1] = y1
                    garis[2] = x2
                    garis[3] = y2
                    garis[4] = sudut
                sudah_gabung = True
                break

        if not sudah_gabung:
            garis_unik.append([x1, y1, x2, y2, sudut])

    return garis_unik


# =====================================================
# 1. DETEKSI GARIS
# =====================================================
def detect_line(image):
    result = image.copy()
    gray, edge = preprocessing(image)

    lines = cv2.HoughLinesP(
        edge,
        rho=1,
        theta=np.pi / 180,
        threshold=120,
        minLineLength=100,
        maxLineGap=30
    )

    # Gabungkan garis mirip
    garis_unik = gabungkan_garis(lines, jarak_maks=30, sudut_maks=5)
    jumlah = 0

    for line in garis_unik:
        x1, y1, x2, y2, sudut = line

        # Hanya garis horizontal dan vertikal
        if sudut < 5 or abs(sudut - 90) < 5:
            cv2.line(result, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
            jumlah += 1

    cv2.putText(
        result,
        f"Garis: {jumlah}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    return result


# =====================================================
# 2. DETEKSI SATU LINGKARAN
# =====================================================
def detect_circle(image):
    result = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=100,
        param2=40,
        minRadius=20,
        maxRadius=300
    )

    jumlah = 0
    if circles is not None:
        circles = np.uint16(np.around(circles))
        x, y, r = circles[0][0]

        # Gambar keliling lingkaran (hijau) dan titik pusat (merah)
        cv2.circle(result, (x, y), r, (0, 255, 0), 3)
        cv2.circle(result, (x, y), 5, (0, 0, 255), -1)
        jumlah = 1

    cv2.putText(
        result,
        f"Lingkaran: {jumlah}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    return result


# =====================================================
# 3. DETEKSI OVAL
# =====================================================
def detect_ellipse(image):
    result = image.copy()
    gray, edge = preprocessing(image)

    contours, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    jumlah = 0

    for cnt in contours:
        if len(cnt) < 5:
            continue

        area = cv2.contourArea(cnt)
        if area < 300:
            continue

        ellipse = cv2.fitEllipse(cnt)
        cv2.ellipse(result, ellipse, (255, 0, 255), 3)
        jumlah += 1

    cv2.putText(
        result,
        f"Oval: {jumlah}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 255),
        2
    )

    return result


# =====================================================
# MAIN
# =====================================================
def main():
    print("============================")
    print(" DETEKSI GEOMETRI CITRA")
    print("============================")

    path = input("Masukkan gambar: ").strip()
    image = load_image(path)

    if image is None:
        return

    print("""
Pilih operasi:

1. Garis
2. Lingkaran
3. Oval
""")

    pilihan = input("Pilihan: ").strip()

    if pilihan == "1":
        hasil = detect_line(image)
        output = "hasil_garis.png"
    elif pilihan == "2":
        hasil = detect_circle(image)
        output = "hasil_lingkaran.png"
    elif pilihan == "3":
        hasil = detect_ellipse(image)
        output = "hasil_oval.png"
    else:
        print("Pilihan salah")
        return

    cv2.imshow("Hasil Deteksi", hasil)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    save_image(hasil, output)


if __name__ == "__main__":
    main()