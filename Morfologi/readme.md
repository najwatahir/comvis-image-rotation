# Digital Image Processing - Morphological Operation Library

Repository ini berisi implementasi **operasi morfologi citra digital** menggunakan library computer vision.

Operasi morfologi merupakan teknik pengolahan citra yang digunakan untuk menganalisis dan memodifikasi bentuk objek berdasarkan hubungan spasial antar piksel menggunakan **Structuring Element (SE)**.


## Technology Stack

Implementasi menggunakan:

- OpenCV
- OpenCV-Contrib
- NumPy
- Matplotlib


---

# 1. Overview


Morfologi citra bekerja berdasarkan bentuk dan struktur objek pada citra.

Berbeda dengan operasi konvolusi yang memproses nilai intensitas piksel, operasi morfologi menggunakan:

- Foreground
- Background
- Structuring Element (SE)


Konsep dasar:


```
Input Image

      |
      v

Structuring Element

      |
      v

Morphological Operation

      |
      v

Output Image
```


Project ini mendukung:

- Citra grayscale
- Citra binary
- Hasil segmentasi citra


---

# 2. Features


## 2.1 Dilation


Dilation adalah operasi untuk memperbesar area foreground.


Library:

```python
cv2.dilate()
```


Tujuan:

- Memperbesar objek
- Menghubungkan objek terputus
- Menutup celah kecil


Pipeline:


```
Input Image

      |
      v

Structuring Element

      |
      v

Maximum Operation

      |
      v

Dilated Image
```


Aplikasi:

- Object expansion
- Image segmentation
- Object connection


---

# 2.2 Erosion


Erosion merupakan operasi untuk mengurangi ukuran objek.


Library:

```python
cv2.erode()
```


Tujuan:

- Menghilangkan noise kecil
- Mengecilkan objek
- Memisahkan objek berdekatan


Pipeline:


```
Input Image

      |
      v

Structuring Element

      |
      v

Minimum Operation

      |
      v

Eroded Image
```


Aplikasi:

- Noise removal
- Object separation


---

# 2.3 Opening


Opening merupakan kombinasi:


```
Opening = Erosion + Dilation
```


Library:


```python
cv2.MORPH_OPEN
```


Tujuan:

- Menghilangkan noise kecil
- Membersihkan hasil threshold


Pipeline:


```
Binary Image

      |
      v

Erosion

      |
      v

Dilation

      |
      v

Clean Object
```


Aplikasi:

- Cleaning segmentation mask
- Noise filtering


---

# 2.4 Closing


Closing merupakan kombinasi:


```
Closing = Dilation + Erosion
```


Library:


```python
cv2.MORPH_CLOSE
```


Tujuan:

- Mengisi lubang kecil
- Menyambungkan objek yang terputus


Pipeline:


```
Binary Image

      |
      v

Dilation

      |
      v

Erosion

      |
      v

Filled Object
```


Aplikasi:

- Crack connection
- Object filling


---

# 2.5 Top-Hat Transform


Top-Hat digunakan untuk mengambil fitur terang kecil dari background.


Formula:


```
Top-Hat = Original Image - Opening
```


Library:


```python
cv2.MORPH_TOPHAT
```


Pipeline:


```
Input Grayscale

      |
      v

Opening

      |
      v

Original - Opening

      |
      v

Bright Feature
```


Aplikasi:

- Detail enhancement
- Uneven illumination correction
- Small object detection


---

# 2.6 Hit-or-Miss Transform


Hit-or-Miss digunakan untuk mencari pola tertentu pada citra binary.


Library:


```python
cv2.MORPH_HITMISS
```


Konsep:


```
1  = foreground harus ada

0  = background harus ada

-1 = tidak diperhatikan
```


Pipeline:


```
Binary Image

      |
      v

Pattern Matching

      |
      v

Detected Pattern
```


Aplikasi:

- Shape detection
- Pattern matching
- Character analysis


---

# 2.7 Skeletonization Zhang-Suen


Skeletonization mengubah objek menjadi representasi garis tengah dengan ketebalan satu piksel.


Algoritma:

```
Zhang-Suen Thinning Algorithm
```


Implementasi:

```python
cv2.ximgproc.thinning()
```


Referensi:

Zhang, T. Y., & Suen, C. Y. (1984).  
*A Fast Parallel Algorithm for Thinning Digital Patterns.*  
Communications of the ACM, 27(3), 236–239.


Pipeline:


```
Binary Object

      |
      v

Boundary Pixel Removal

      |
      v

Connectivity Checking

      |
      v

One Pixel Skeleton
```


Contoh:


Sebelum:

```
████████
████████
████████
```


Sesudah:

```
   |
---+---
   |
```


Aplikasi:

- Crack analysis
- Blood vessel analysis
- Shape analysis


---

# 2.8 Thinning Zhang-Suen


Thinning merupakan proses mengurangi ketebalan objek hingga satu piksel dengan mempertahankan struktur objek.


Algoritma:

```
Zhang-Suen Algorithm
```


Library:


```python
cv2.ximgproc.thinning()
```


Pipeline:


```
Binary Image

      |
      v

Remove Boundary Pixel

      |
      v

Topology Check

      |
      v

Thin Image
```


Aplikasi:

- OCR
- Character recognition
- Pattern analysis


---

# 3. Structuring Element (SE)


Structuring Element menentukan pola piksel yang digunakan dalam operasi morfologi.


## Cross SE


```
0 1 0
1 1 1
0 1 0
```


Digunakan untuk:

- Skeletonization
- Thinning
- Menjaga konektivitas


---

## Rectangle SE


```
1 1 1
1 1 1
1 1 1
```


Digunakan untuk:

- Dilation
- Erosion
- Opening
- Closing


Pengaruh ukuran:


| Ukuran SE | Pengaruh |
|---|---|
| Kecil | Detail lebih terjaga |
| Besar | Perubahan struktur lebih kuat |


---

# 4. Dependency


## Python Version


```
Python >= 3.9
```


## Install Library


```bash
pip install opencv-contrib-python
pip install numpy
pip install matplotlib
```


atau:


```bash
pip install -r requirements.txt
```


requirements.txt:


```
opencv-contrib-python
numpy
matplotlib
```


---

# 5. Project Structure


```
Morphology-Image-Processing/

│
├── main.py
│
├── input/
│   └── image.png
│
├── output_DILASI/
│   └── hasil_DILASI.png
│
├── output_SKELETONIZATION_ZHANG_SUEN/
│   └── hasil_SKELETONIZATION_ZHANG_SUEN.png
│
├── requirements.txt
│
└── README.md

```


---

# 6. How To Run


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
Start Program

      |
      v

Select Morphological Operation

      |
      v

Input Image Path

      |
      v

Binary Check

      |
      v

Morphological Processing

      |
      v

Display Before-After

      |
      v

Save Result

```


---

# 7. Menu


Program menyediakan:


```
========================================

1. DILATION
2. EROSION
3. OPENING
4. CLOSING
5. TOP-HAT TRANSFORM
6. HIT-OR-MISS
7. SKELETONIZATION (ZHANG-SUEN)
8. THINNING (ZHANG-SUEN)

0. EXIT

========================================
```


---

# 8. Output


Setiap operasi menghasilkan satu file:


Format:


```
output_NAMAOPERASI/

└── hasil_NAMAOPERASI.png
```


Contoh:


Dilation:


```
output_DILASI/

└── hasil_DILASI.png
```


Opening:


```
output_OPENING/

└── hasil_OPENING.png
```


Skeleton:


```
output_SKELETONIZATION_ZHANG_SUEN/

└── hasil_SKELETONIZATION_ZHANG_SUEN.png
```


---

# 9. Computer Vision Pipeline Example


Contoh penggunaan untuk deteksi retakan:


```
Input Image

      |
      v

Segmentation

      |
      v

Binary Crack Mask

      |
      v

Opening

(Remove Noise)

      |
      v

Closing

(Connect Crack)

      |
      v

Skeletonization

(Zhang-Suen)

      |
      v

Feature Extraction

- Crack Length
- Crack Direction
- Branch Point

```


---

# 10. Notes


- Skeletonization dan thinning membutuhkan citra binary.
- Thresholding diperlukan apabila input masih berupa grayscale.
- Structuring Element mempengaruhi hasil operasi.
- OpenCV-Contrib diperlukan untuk Zhang-Suen thinning.
- Hasil sangat bergantung pada kualitas segmentasi awal.


---