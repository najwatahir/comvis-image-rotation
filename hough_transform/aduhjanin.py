import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
import os


# =====================================================
# 1. LOAD IMAGE
# =====================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "img", "janin", "images.jpg"))

img = cv2.imread(IMAGE_PATH)

if img is None:
    raise Exception(f"Gambar tidak ditemukan di path: {IMAGE_PATH}")


result = img.copy()


gray = cv2.cvtColor(
    img,
    cv2.COLOR_BGR2GRAY
)



# =====================================================
# 2. PREPROCESSING
# =====================================================

# mengurangi noise USG

blur = cv2.medianBlur(
    gray,
    7
)


# meningkatkan kontras

clahe = cv2.createCLAHE(
    clipLimit=3,
    tileGridSize=(8,8)
)


enhanced = clahe.apply(
    blur
)



# =====================================================
# 3. DETEKSI PUSAT KEPALA (HOUGH CIRCLE)
# =====================================================

h, w = gray.shape

circles = cv2.HoughCircles(
    enhanced,
    cv2.HOUGH_GRADIENT,
    dp=1.2,
    minDist=100,
    param1=100,
    param2=45,
    minRadius=50,
    maxRadius=115
)

if circles is None:
    # Fallback ke pusat gambar jika Hough Circle gagal
    cx, cy, r = w // 2, h // 2, min(w, h) // 3
else:
    circles = np.uint16(np.around(circles))
    # Pilih lingkaran yang paling mendekati pusat gambar
    # Cast ke int agar tidak overflow saat pengurangan (uint16 tidak bisa negatif)
    circle = min(circles[0], key=lambda c: (int(c[0]) - w // 2) ** 2 + (int(c[1]) - h // 2) ** 2)
    cx, cy, r = int(circle[0]), int(circle[1]), int(circle[2])

print("Center kepala:", cx, cy)
print("Radius perkiraan:", r)

# Gambar hasil Hough Circle (Biru)
cv2.circle(
    result,
    (cx, cy),
    r,
    (255, 0, 0),
    2
)


# =====================================================
# 4. EDGE DETECTION PADA SELURUH GAMBAR
# =====================================================

edges = cv2.Canny(enhanced, 30, 100)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)


# =====================================================
# 5. CARI & FIT ELIPS KEPALA (GREEN ELLIPSE)
# =====================================================

contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

best_ellipse = None
max_score = 0

for cnt in contours:
    if len(cnt) < 30:
        continue
    
    try:
        ellipse = cv2.fitEllipse(cnt)
    except:
        continue

    (e_cx, e_cy), (d1, d2), angle = ellipse
    major = max(d1, d2)
    minor = min(d1, d2)

    if minor == 0:
        continue

    aspect_ratio = major / minor
    dist_to_center = math.hypot(e_cx - cx, e_cy - cy)

    # Filter kontur yang benar-benar membatasi tengkorak kepala:
    # 1. Aspek rasio elips 1.0 - 1.5
    # 2. Ukuran major axis wajar terhadap perkiraan radius
    # 3. Pusat elips dekat dengan pusat kepala
    if 1.0 <= aspect_ratio <= 1.5 and 0.7 * (2 * r) <= major <= 2.2 * (2 * r) and dist_to_center < r * 0.6:
        score = cv2.arcLength(cnt, False)
        if score > max_score:
            max_score = score
            best_ellipse = ellipse

# Jika kontur terpisah-pisah, kumpulkan titik edge di sekitar batas ring tengkorak
# 0.7*r - 1.05*r = target tengah-tengah garis putih tengkorak (bukan tepi terluar)
if best_ellipse is None:
    y_indices, x_indices = np.where(edges > 0)
    skull_pts = []
    for x, y in zip(x_indices, y_indices):
        dist = math.hypot(x - cx, y - cy)
        if 0.7 * r <= dist <= 1.05 * r:
            skull_pts.append([[x, y]])

    if len(skull_pts) >= 5:
        skull_pts = np.array(skull_pts, dtype=np.int32)
        best_ellipse = cv2.fitEllipse(skull_pts)

if best_ellipse is None:
    raise Exception("Ellipse tidak ditemukan")

center, axes, angle = best_ellipse
major = max(axes)
minor = min(axes)

print("Major axis (px):", round(major, 2))
print("Minor axis (px):", round(minor, 2))

# Gambar hasil Ellipse Fitting (Hijau)
cv2.ellipse(
    result,
    best_ellipse,
    (0, 255, 0),
    3
)



# =====================================================
# 8. HITUNG HEAD CIRCUMFERENCE
# =====================================================


a=major/2
b=minor/2



HC_pixel = math.pi*(

    3*(a+b)
    -
    math.sqrt(
        (3*a+b)*(a+3*b)
    )

)



print(
    "HC pixel:",
    HC_pixel
)



# =====================================================
# 9. KONVERSI PIXEL -> MM
# =====================================================

# sementara
# nanti diganti pixel spacing DICOM

pixel_mm=0.45


HC_mm=HC_pixel*pixel_mm



print(
    "HC mm:",
    HC_mm
)



# =====================================================
# 10. ESTIMASI UMUR
# =====================================================

# contoh saja
# gunakan Hadlock untuk penelitian

GA=(0.15*HC_mm)-8.5



print(
    "Umur janin:",
    round(GA,2),
    "minggu"
)



# =====================================================
# 11. VISUALISASI
# =====================================================


plt.figure(
    figsize=(10,7)
)


plt.imshow(
    cv2.cvtColor(
        result,
        cv2.COLOR_BGR2RGB
    )
)


plt.title(
    "Fetal Head Detection"
)


plt.axis("off")


plt.show()