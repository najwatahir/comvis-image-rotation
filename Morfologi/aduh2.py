import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

from skimage.morphology import medial_axis



# ==========================================================
# LOAD IMAGE
# ==========================================================

def load_image(path):

    img = cv2.imread(
        path,
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        raise FileNotFoundError(
            "Gambar tidak ditemukan"
        )

    return img



# ==========================================================
# THRESHOLD
# ==========================================================

def threshold_image(img):

    _, binary = cv2.threshold(
        img,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )

    return binary



# ==========================================================
# STRUCTURING ELEMENT
# ==========================================================

def create_SE(
        size=3,
        shape="cross"
):

    if shape == "cross":

        SE = cv2.getStructuringElement(
            cv2.MORPH_CROSS,
            (size, size)
        )

    else:

        SE = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (size, size)
        )

    return SE



# ==========================================================
# 1. DILATION
# ==========================================================

def dilation(img, SE):

    return cv2.dilate(
        img,
        SE,
        iterations=1
    )



# ==========================================================
# 2. EROSION
# ==========================================================

def erosion(img, SE):

    return cv2.erode(
        img,
        SE,
        iterations=2
    )



# ==========================================================
# 3. OPENING
# ==========================================================

def opening(img, SE):

    return cv2.morphologyEx(
        img,
        cv2.MORPH_OPEN,
        SE,
        iterations=5
    )



# ==========================================================
# 4. CLOSING
# ==========================================================

def closing(img, SE):

    return cv2.morphologyEx(
        img,
        cv2.MORPH_CLOSE,
        SE
    )



# ==========================================================
# 5. TOP-HAT
# ==========================================================

def top_hat(img, SE):

    # Khusus Top-Hat, ukuran SE harus lebih besar dari ukuran bintang/fitur terang
    # (namun lebih kecil dari kabut background) agar bintang tidak ikut terhapus.
    if SE is None or SE.shape[0] <= 3:
        ksize = max(31, (min(img.shape[:2]) // 12) | 1)
        SE = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (ksize, ksize)
        )

    res = cv2.morphologyEx(
        img,
        cv2.MORPH_TOPHAT,
        SE
    )

    # Normalisasi rentang intensitas ke 0-255 agar objek terang tampak jelas
    return cv2.normalize(
        res,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )



# ==========================================================
# 6. HIT OR MISS
# ==========================================================

def hit_or_miss(img):

    """
    Hit-or-Miss: mendeteksi pola tertentu pada citra binary.
    1 = harus putih, -1 = harus hitam, 0 = tidak peduli
    """

    patterns = {

        # titik terisolasi (noise / bintik kecil)
        "1": np.array([
            [-1, -1, -1],
            [-1,  1, -1],
            [-1, -1, -1]
        ], dtype=np.int32),

        # sudut kiri-atas objek putih
        "2": np.array([
            [-1, -1, -1],
            [-1,  1,  1],
            [-1,  1,  0]
        ], dtype=np.int32),

        # ujung garis (garis vertikal berakhir di atas)
        "3": np.array([
            [-1, -1, -1],
            [-1,  1, -1],
            [ 0,  1,  0]
        ], dtype=np.int32)
    }

    print("""
Pilih pola Hit-or-Miss:
1. Titik terisolasi
2. Sudut kiri-atas
3. Ujung garis
""")

    p = input("Pola : ")

    if p not in patterns:
        p = "1"

    # pastikan binary 0 / 255
    binary = (img > 0).astype(np.uint8) * 255

    result = cv2.morphologyEx(
        binary,
        cv2.MORPH_HITMISS,
        patterns[p]
    )

    # hasilnya cuma titik 1 piksel, dibesarkan supaya terlihat
    result = cv2.dilate(
        result,
        np.ones((5, 5), np.uint8)
    )

    return result



# ==========================================================
# 7. SKELETONIZATION
# ==========================================================

def skeletonization(img):

    """
    Skeletonization menggunakan
    Medial Axis Transform.

    Input:
    Binary image

    Output:
    Centerline skeleton
    """

    binary = img > 0

    skeleton = medial_axis(
        binary
    )

    return (
        skeleton.astype(np.uint8)
        *
        255
    )



# ==========================================================
# 8. THINNING
# ==========================================================

def thinning(img):

    """
    Thinning menggunakan
    OpenCV thinning algorithm.
    (butuh opencv-contrib-python)
    """

    result = cv2.ximgproc.thinning(
        img
    )

    return result



# ==========================================================
# SAVE RESULT
# ==========================================================

def save_result(
        result,
        operation
):

    folder = (
        "output_" +
        operation
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    filename = (
        "hasil_" +
        operation +
        ".png"
    )

    path = os.path.join(
        folder,
        filename
    )

    cv2.imwrite(
        path,
        result
    )

    print("\n==============================")
    print("HASIL DISIMPAN")
    print("==============================")
    print(path)
    print("==============================\n")



# ==========================================================
# DISPLAY (CITRA AWAL vs CITRA AKHIR)
# ==========================================================

def show_result(
        original,
        processed_input,
        result,
        title,
        use_threshold=False
):

    # Kumpulkan gambar yang akan ditampilkan
    images = [
        (original, "CITRA AWAL")
    ]

    # Kalau pakai threshold otomatis, tampilkan juga tahap tengahnya
    if use_threshold:
        images.append(
            (processed_input, "HASIL THRESHOLD")
        )

    images.append(
        (result, "CITRA AKHIR\n" + title)
    )

    total = len(images)

    fig = plt.figure(
        figsize=(4 * total, 4)
    )

    for i, (image, label) in enumerate(images):

        plt.subplot(
            1,
            total,
            i + 1
        )

        plt.imshow(
            image,
            cmap="gray"
        )

        plt.title(
            label
        )

        plt.axis(
            "off"
        )

    plt.tight_layout()

    # Simpan gambar perbandingan
    folder = "output_" + title

    os.makedirs(
        folder,
        exist_ok=True
    )

    compare_path = os.path.join(
        folder,
        "perbandingan_" + title + ".png"
    )

    fig.savefig(
        compare_path,
        dpi=150,
        bbox_inches="tight"
    )

    print("Perbandingan disimpan di :", compare_path)

    plt.show()



# ==========================================================
# MENU
# ==========================================================

def menu():

    print("""
========================================
 DIGITAL IMAGE MORPHOLOGY PROCESSING
========================================

1. DILATION
2. EROSION
3. OPENING
4. CLOSING
5. TOP-HAT TRANSFORM
6. HIT-OR-MISS
7. SKELETONIZATION
8. THINNING

0. EXIT

========================================
""")



# ==========================================================
# MAIN
# ==========================================================

def main():

    operations = {

        "1":
        (
            "DILASI",
            dilation,
            True
        ),

        "2":
        (
            "EROSI",
            erosion,
            True
        ),

        "3":
        (
            "OPENING",
            opening,
            True
        ),

        "4":
        (
            "CLOSING",
            closing,
            True
        ),

        "5":
        (
            "TOPHAT",
            top_hat,
            True
        ),

        "6":
        (
            "HIT_OR_MISS",
            hit_or_miss,
            False
        ),

        "7":
        (
            "SKELETONIZATION",
            skeletonization,
            False
        ),

        "8":
        (
            "THINNING",
            thinning,
            False
        )

    }


    while True:

        menu()

        choice = input(
            "Pilih operasi : "
        )

        if choice == "0":

            print(
                "Program selesai"
            )

            break

        if choice not in operations:

            print(
                "Pilihan tidak tersedia"
            )

            continue

        name, function, use_SE = operations[choice]

        path = input(
            "\nMasukkan path gambar : "
        )

        try:

            img = load_image(
                path
            )

        except Exception as e:

            print(e)

            continue

        print("""
========================================

Apakah gambar sudah binary?

1. Ya
2. Threshold otomatis

========================================
""")

        binary_choice = input(
            "Pilihan : "
        )

        if binary_choice == "2":

            img_process = threshold_image(
                img
            )

        else:

            img_process = img

        if use_SE:

            SE = create_SE(
                size=3,
                shape="cross"
            )

            result = function(
                img_process,
                SE
            )

        else:

            result = function(
                img_process
            )

        save_result(
            result,
            name
        )

        show_result(
            img,                                # citra awal (asli)
            img_process,                        # citra setelah threshold (jika ada)
            result,                             # citra akhir
            name,
            use_threshold=(binary_choice == "2")
        )



# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()
