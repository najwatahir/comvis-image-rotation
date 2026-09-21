import cv2
import numpy as np
import matplotlib.pyplot as plt
import math


# =====================================================
# 1. LOAD IMAGE
# =====================================================

img = cv2.imread("img/janin/images.jpg")

if img is None:
    raise Exception("Gambar tidak ditemukan")


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
# 3. DETEKSI PUSAT KEPALA
#    HOUGH CIRCLE
# =====================================================


circles = cv2.HoughCircles(
    enhanced,
    cv2.HOUGH_GRADIENT,
    dp=1,
    minDist=100,
    param1=80,
    param2=35,
    minRadius=60,
    maxRadius=180
)



if circles is None:
    raise Exception(
        "Kepala tidak ditemukan"
    )


circles=np.uint16(
    np.around(circles)
)


# ambil lingkaran terbesar

circle=max(
    circles[0],
    key=lambda x:x[2]
)



# convert dari uint16 ke int
# supaya tidak overflow

cx=int(circle[0])
cy=int(circle[1])
r=int(circle[2])



print(
    "Center kepala:",
    cx,
    cy
)

print(
    "Radius:",
    r
)



# gambar hasil circle

cv2.circle(
    result,
    (cx,cy),
    r,
    (255,0,0),
    3
)



# =====================================================
# 4. BUAT ROI KEPALA
# =====================================================


margin=30


x1=max(
    cx-r-margin,
    0
)

y1=max(
    cy-r-margin,
    0
)


x2=min(
    cx+r+margin,
    gray.shape[1]
)

y2=min(
    cy+r+margin,
    gray.shape[0]
)



print(
    "ROI:",
    x1,y1,x2,y2
)



roi=enhanced[
    y1:y2,
    x1:x2
]



if roi.size==0:
    raise Exception(
        "ROI kosong"
    )



# =====================================================
# 5. EDGE DETECTION
# =====================================================


edges=cv2.Canny(
    roi,
    40,
    120
)



# rapikan edge

kernel=np.ones(
    (3,3),
    np.uint8
)


edges=cv2.morphologyEx(
    edges,
    cv2.MORPH_CLOSE,
    kernel
)



# =====================================================
# 6. CARI KONTOUR KEPALA
# =====================================================


contours,_=cv2.findContours(
    edges,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_NONE
)



best=None
max_area=0



for cnt in contours:


    area=cv2.contourArea(cnt)


    if area < 300:
        continue


    if len(cnt)>=5:


        ellipse=cv2.fitEllipse(cnt)


        if area>max_area:

            max_area=area
            best=ellipse



# =====================================================
# 7. ELLIPSE FITTING
# =====================================================


if best is None:

    raise Exception(
        "Ellipse tidak ditemukan"
    )


center,axes,angle=best


major=max(axes)
minor=min(axes)



print(
    "Major axis:",
    major
)

print(
    "Minor axis:",
    minor
)



# pindahkan koordinat ROI ke gambar utama

global_center=(

    int(center[0]+x1),
    int(center[1]+y1)

)


ellipse_global=(

    global_center,
    axes,
    angle

)



cv2.ellipse(
    result,
    ellipse_global,
    (0,255,0),
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