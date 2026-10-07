# Digital Image Processing - Shape Detection Library

Repository ini berisi implementasi **deteksi bentuk geometris pada citra digital** menggunakan teknik Computer Vision berbasis OpenCV.

Project ini melakukan ekstraksi bentuk objek berdasarkan karakteristik geometris seperti:

- Garis (Line)
- Lingkaran (Circle)
- Elips/Oval (Ellipse)


## Technology Stack

Implementasi menggunakan:

- OpenCV
- NumPy
- Matplotlib


---

# 1. Overview


Shape Detection merupakan proses untuk menemukan dan mengenali bentuk geometris tertentu pada citra.

Metode ini banyak digunakan dalam bidang:

- Computer Vision
- Object Detection
- Industrial Inspection
- Autonomous System
- Medical Image Analysis


Pipeline umum:


```
Input Image

      |
      v

Preprocessing

(Grayscale,
Gaussian Blur,
Edge Detection)

      |
      v

Feature Extraction

      |
      |
      +----------------+
      |                |
      v                v

Hough Transform   Contour Analysis

      |                |
      v                v

Line/Circle       Ellipse

      |
      v

Visualization
```


---

# 2. Features


Project ini memiliki tiga fitur utama:


| No | Feature | Method |
|-|-|-|
| 1 | Line Detection | Hough Line Transform |
| 2 | Circle Detection | Hough Circle Transform |
| 3 | Ellipse Detection | Contour + Ellipse Fitting |


---

# 3. Line Detection


## Method

Line Detection menggunakan:

```python
cv2.HoughLinesP()
```


Metode ini merupakan implementasi **Probabilistic Hough Line Transform**.


---

## Konsep


Garis pada citra:

\[
\rho=xcos(\theta)+ysin(\theta)
\]


Setiap titik edge akan dipetakan ke ruang parameter.

Jika banyak titik memiliki parameter yang sama, maka dianggap sebagai sebuah garis.


Pipeline:


```
Input Image

      |
      v

Grayscale

      |
      v

Gaussian Blur

      |
      v

Canny Edge Detection

      |
      v

Hough Line Transform

      |
      v

Detected Line
```


---

## Parameter utama


```python
cv2.HoughLinesP()
```


| Parameter | Fungsi |
|-|-|
| rho | Resolusi jarak |
| theta | Resolusi sudut |
| threshold | Minimal voting |
| minLineLength | Panjang minimum garis |
| maxLineGap | Jarak maksimum antar segmen |


---

## Application


Contoh penggunaan:

- Deteksi marka jalan
- Deteksi batas objek
- Analisis struktur bangunan


---

# 4. Circle Detection


## Method


Circle detection menggunakan:


```python
cv2.HoughCircles()
```


Metode:

```
Hough Circle Transform
```


---

## Konsep


Lingkaran memiliki persamaan:


\[
(x-a)^2+(y-b)^2=r^2
\]


Dengan:

| Parameter | Keterangan |
|-|-|
| a | Koordinat pusat x |
| b | Koordinat pusat y |
| r | Radius |


Pipeline:


```
Input Image

      |
      v

Grayscale

      |
      v

Median Blur

      |
      v

Hough Circle Transform

      |
      v

Detected Circle
```


---

## Parameter penting


```python
cv2.HoughCircles()
```


| Parameter | Fungsi |
|-|-|
| dp | Resolusi accumulator |
| minDist | Jarak antar lingkaran |
| param1 | Threshold edge |
| param2 | Threshold deteksi |
| minRadius | Radius minimum |
| maxRadius | Radius maksimum |


---

## Application


Contoh:

- Deteksi koin
- Deteksi roda
- Deteksi lubang
- Inspeksi produk


---

# 5. Ellipse Detection


## Method


OpenCV tidak menyediakan:

```python
cv2.HoughEllipse()
```


Sehingga digunakan pendekatan:


```
Contour Detection

        |

        v

Ellipse Fitting

        |

        v

cv2.fitEllipse()
```


---

## Pipeline


```
Input Image

      |
      v

Grayscale

      |
      v

Threshold

      |
      v

Contour Detection

      |
      v

Fit Ellipse

      |
      v

Detected Ellipse
```


---

## Konsep


Persamaan ellipse:


\[
\frac{(x-h)^2}{a^2}
+
\frac{(y-k)^2}{b^2}
=1
\]


Parameter:

| Parameter | Keterangan |
|-|-|
| h,k | Titik pusat |
| a | Sumbu mayor |
| b | Sumbu minor |


---

## Application


Contoh:

- Deteksi objek oval
- Analisis bentuk biologis
- Pemeriksaan produk industri


---

# 6. Preprocessing


Sebelum melakukan deteksi bentuk, citra dilakukan preprocessing.


Tahapan:


## Grayscale


Mengubah citra RGB menjadi intensitas:


```
RGB Image

      |

      v

Grayscale Image
```


---

## Gaussian Blur


Tujuan:

- Mengurangi noise
- Menghaluskan citra


Implementasi:


```python
cv2.GaussianBlur()
```


---

## Canny Edge Detection


Tujuan:

Mendeteksi perubahan intensitas.


Implementasi:


```python
cv2.Canny()
```


Pipeline:


```
Image

 |
 v

Blur

 |
 v

Canny

 |
 v

Edge Map
```


---

# 7. Dependency


## Python Version


```
Python >= 3.9
```


## Install Library


```bash
pip install opencv-python
pip install numpy
pip install matplotlib
```


atau:


```bash
pip install -r requirements.txt
```


requirements.txt:


```
opencv-python
numpy
matplotlib
```


---

# 8. Project Structure


```
Shape-Detection/

│
├── main.py
│
├── input/
│   └── image.png
│
├── output_LINE/
│   └── hasil_line.png
│
├── output_CIRCLE/
│   └── hasil_circle.png
│
├── output_ELLIPSE/
│   └── hasil_ellipse.png
│
├── requirements.txt
│
└── README.md

```


---

# 9. How To Run


## Install Dependency


```bash
pip install -r requirements.txt
```


---

## Run Program


```bash
python main.py
```


---

## Program Workflow


```
Start

 |

v

Select Detection Method

 |

v

Input Image Path

 |

v

Preprocessing

 |

v

Detection Process

 |

v

Visualization

 |

v

Save Result

```


---

# 10. Menu


Program menyediakan:


```
================================

SHAPE DETECTION

1. Line Detection
2. Circle Detection
3. Ellipse Detection

0. Exit

================================
```


---

# 11. Output


Setiap metode menghasilkan file:


## Line Detection


```
output_LINE/

└── hasil_line.png
```


---

## Circle Detection


```
output_CIRCLE/

└── hasil_circle.png
```


---

## Ellipse Detection


```
output_ELLIPSE/

└── hasil_ellipse.png
```


---

# 12. Computer Vision Pipeline Example


Contoh pipeline inspeksi objek:


```
Input Image

      |
      v

Preprocessing

      |
      v

Edge Detection

      |
      v

Shape Detection

      |
      +------------+
      |            |
      v            v

Line          Circle/Ellipse

      |
      v

Object Analysis
```


---

# 13. Notes


- Hough Transform membutuhkan edge yang baik agar hasil optimal.
- Parameter threshold sangat mempengaruhi jumlah deteksi.
- Noise tinggi dapat menyebabkan false detection.
- Ellipse detection bergantung pada kualitas contour.
- Tidak semua objek memiliki bentuk geometris sempurna.
