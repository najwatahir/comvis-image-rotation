import cv2
import numpy as np
import matplotlib.pyplot as plt
import os



# ==========================================================
# LOAD IMAGE
# ==========================================================

def load_image(path):

    img = cv2.imread(
        path
    )

    if img is None:
        raise FileNotFoundError(
            "Gambar tidak ditemukan"
        )

    return img



# ==========================================================
# PREPROCESSING
# ==========================================================

def preprocessing(img):

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )


    blur = cv2.GaussianBlur(
        gray,
        (5,5),
        0
    )


    edges = cv2.Canny(
        blur,
        50,
        150
    )


    return edges



# ==========================================================
# 1. LINE DETECTION
# Hough Line Transform
# ==========================================================

def detect_line(img):


    edges = preprocessing(
        img
    )


    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=80,
        minLineLength=50,
        maxLineGap=10
    )


    result = img.copy()


    if lines is not None:

        for line in lines:

            x1,y1,x2,y2 = line[0]


            cv2.line(
                result,
                (x1,y1),
                (x2,y2),
                (0,0,255),
                3
            )


    return result



# ==========================================================
# 2. CIRCLE DETECTION
# Hough Circle Transform
# ==========================================================

def detect_circle(img):


    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )


    gray = cv2.medianBlur(
        gray,
        5
    )


    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,
        param1=100,
        param2=30,
        minRadius=10,
        maxRadius=200
    )


    result = img.copy()


    if circles is not None:


        circles = np.uint16(
            np.around(circles)
        )


        for c in circles[0]:

            x,y,r = c


            cv2.circle(
                result,
                (x,y),
                r,
                (0,255,0),
                3
            )


            cv2.circle(
                result,
                (x,y),
                2,
                (255,0,0),
                3
            )


    return result



# ==========================================================
# 3. ELLIPSE DETECTION
# Contour + Ellipse Fitting
# ==========================================================

def detect_ellipse(img):


    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )


    blur = cv2.GaussianBlur(
        gray,
        (5,5),
        0
    )


    _, binary = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )


    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    result = img.copy()


    for cnt in contours:


        if len(cnt) >= 5:


            ellipse = cv2.fitEllipse(
                cnt
            )


            cv2.ellipse(
                result,
                ellipse,
                (255,0,255),
                3
            )


    return result



# ==========================================================
# SAVE OUTPUT
# ==========================================================

def save_image(
        img,
        folder,
        filename
):

    os.makedirs(
        folder,
        exist_ok=True
    )


    path = os.path.join(
        folder,
        filename
    )


    cv2.imwrite(
        path,
        img
    )


    print(
        "Saved:",
        path
    )



# ==========================================================
# SHOW RESULT
# ==========================================================

def show(
        img,
        title
):

    img_rgb = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )


    plt.figure(
        figsize=(8,6)
    )


    plt.imshow(
        img_rgb
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
================================

SHAPE DETECTION

1. Line Detection
2. Circle Detection
3. Ellipse Detection

0. Exit

================================
""")



# ==========================================================
# MAIN
# ==========================================================

def main():


    while True:


        menu()


        choice=input(
            "Pilih metode : "
        )


        if choice=="0":

            break



        path=input(
            "Masukkan path gambar : "
        )


        img=load_image(
            path
        )



        if choice=="1":


            result = detect_line(
                img
            )


            save_image(
                result,
                "output_LINE",
                "hasil_line.png"
            )


            show(
                result,
                "Line Detection"
            )



        elif choice=="2":


            result = detect_circle(
                img
            )


            save_image(
                result,
                "output_CIRCLE",
                "hasil_circle.png"
            )


            show(
                result,
                "Circle Detection"
            )



        elif choice=="3":


            result = detect_ellipse(
                img
            )


            save_image(
                result,
                "output_ELLIPSE",
                "hasil_ellipse.png"
            )


            show(
                result,
                "Ellipse Detection"
            )


        else:

            print(
                "Pilihan tidak tersedia"
            )



if __name__=="__main__":

    main()