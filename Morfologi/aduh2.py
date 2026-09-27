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
            (size,size)
        )

    else:

        SE = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (size,size)
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
        iterations=1
    )



# ==========================================================
# 3. OPENING
# ==========================================================

def opening(img, SE):

    return cv2.morphologyEx(
        img,
        cv2.MORPH_OPEN,
        SE
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

    return cv2.morphologyEx(
        img,
        cv2.MORPH_TOPHAT,
        SE
    )



# ==========================================================
# 6. HIT OR MISS
# ==========================================================

def hit_or_miss(img, SE):

    return cv2.morphologyEx(
        img,
        cv2.MORPH_HITMISS,
        SE
    )



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
# DISPLAY
# ==========================================================

def show_result(
        before,
        after,
        title
):

    plt.figure(
        figsize=(10,4)
    )


    plt.subplot(
        1,
        2,
        1
    )

    plt.imshow(
        before,
        cmap="gray"
    )

    plt.title(
        "BEFORE"
    )

    plt.axis(
        "off"
    )



    plt.subplot(
        1,
        2,
        2
    )

    plt.imshow(
        after,
        cmap="gray"
    )

    plt.title(
        title
    )

    plt.axis(
        "off"
    )


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
            True
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
            img_process,
            result,
            name
        )



# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()