# Digital Image Processing - Manual Image Processing Library

Repository ini berisi implementasi dasar **Digital Image Processing (DIP)** menggunakan pendekatan manual tanpa library pengolahan citra seperti OpenCV atau Scikit-image.

Program dibuat menggunakan:

- Python Standard Library
- Struct
- Math
- Pillow (hanya untuk konversi format gambar)

Sebagian besar algoritma pengolahan citra diimplementasikan secara manual mulai dari:

- Membaca struktur file BMP
- Mengambil data piksel
- Konversi grayscale
- Manipulasi intensitas piksel
- Transformasi geometris
- Reduksi noise
- Image smoothing
- Edge detection


---

# 1. Overview


Digital Image Processing adalah proses manipulasi citra digital untuk meningkatkan kualitas gambar atau memperoleh informasi tertentu dari citra.

Program ini bekerja dengan konsep dasar:

```
Input Image

      |
      v

BMP File Structure

      |
      v

Pixel Matrix

      |
      v

Image Processing Operation

      |
      v

Output BMP Image
```


Berbeda dengan pendekatan menggunakan OpenCV yang menyediakan fungsi siap pakai, project ini membangun proses pengolahan citra dari level dasar:

- membaca byte file,
- memahami struktur BMP,
- mengakses nilai intensitas piksel,
- melakukan operasi matematika pada matriks citra.


---

# 2. Features


# 2.1 BMP File Processing


Program mampu membaca dan menulis file BMP secara manual.


Fitur:

- Membaca BMP Header
- Membaca DIB Header
- Membaca informasi ukuran gambar
- Membaca bit depth
- Membaca offset pixel
- Membaca data piksel


Struktur BMP:

```
BMP File

|
|
+-- Bitmap File Header
|
+-- DIB Header
|
+-- Color Palette
|
+-- Pixel Data

```


Informasi yang dapat diperoleh:

- Format file
- Ukuran file
- Resolusi gambar
- Bit depth
- Offset data piksel


---

# 2.2 Manual Pixel Extraction


Program membaca nilai piksel secara langsung dari byte BMP.


Support:

- 8-bit grayscale BMP
- 24-bit BMP
- 32-bit BMP


Untuk citra RGB:

BMP menggunakan format:

```
B G R
```


Kemudian dikonversi menjadi grayscale:


Formula:


```
Gray =
0.299R +
0.587G +
0.114B
```


Pipeline:


```
BMP File

      |
      v

Read Pixel Byte

      |
      v

RGB Extraction

      |
      v

Grayscale Conversion

      |
      v

Pixel Matrix
```


---

# 3. Image Processing Features


# 3.1 Brightness Adjustment


Brightness digunakan untuk mengubah tingkat kecerahan citra.


Formula:


```
Output = Input + Brightness Value
```


Parameter:

- Nilai positif → gambar lebih terang
- Nilai negatif → gambar lebih gelap


Pipeline:


```
Input Image

      |
      v

Read Pixel Intensity

      |
      v

Add Brightness Value

      |
      v

Clipping 0-255

      |
      v

Output Image
```


Contoh:

```
Input pixel = 120

Brightness +50


Output:

170

```


---

# 3.2 Contrast Enhancement


Contrast digunakan untuk memperbesar atau memperkecil perbedaan intensitas.


Formula:


```
Ko = G(Ki - P) + P
```


Keterangan:

| Parameter | Arti |
|-|-|
| Ki | Intensitas input |
| Ko | Intensitas output |
| G | Faktor penguatan kontras |
| P | Titik pusat kontras |


Pengaruh:

```
G > 1

Contrast meningkat


0 < G < 1

Contrast menurun
```


Pipeline:


```
Input Image

      |
      v

Calculate Contrast Formula

      |
      v

Intensity Transformation

      |
      v

Output Image
```


---

# 3.3 Horizontal Mirroring


Operasi pencerminan horizontal membalik posisi piksel terhadap sumbu vertikal.


Contoh:


Sebelum:

```
ABC

```


Sesudah:

```
CBA

```


Pipeline:


```
Input Matrix

      |
      v

Reverse X Coordinate

      |
      v

Mirrored Image

```


---

# 3.4 Rotation 90 Degree


Melakukan rotasi citra sebesar 90 derajat.


Konsep:


```
(x,y)

menjadi

(y,new_x)

```


Pipeline:


```
Input Matrix

      |
      v

Create New Matrix

      |
      v

Mapping Coordinate

      |
      v

Rotated Image
```


---

# 3.5 Noise Reduction


Program menyediakan metode pengurangan noise.


Metode:

1. Median Filtering
2. Mean Filtering 9 titik
3. Mean Filtering 5 titik


---

## Median Filter


Median filter bekerja dengan mengambil nilai tengah dari piksel tetangga.


Contoh:


Window:

```
10 20 30

20 90 40

30 40 50

```


Urutkan:

```
10 20 20 30 30 40 40 50 90

```


Median:

```
30
```


Pipeline:


```
Input Image

      |
      v

Take Neighbor Window

      |
      v

Sort Pixel Value

      |
      v

Take Median

      |
      v

Output Image
```


Kegunaan:

- Menghilangkan salt and pepper noise
- Mempertahankan edge


---

## Mean Filter


Mean filtering melakukan perataan berdasarkan nilai rata-rata tetangga.


Mask 3x3:


```
1/9 1/9 1/9

1/9 1/9 1/9

1/9 1/9 1/9

```


Pipeline:


```
Input Image

      |
      v

Take Neighbor Pixels

      |
      v

Calculate Average

      |
      v

Replace Pixel

```


Kegunaan:

- Image smoothing
- Mengurangi variasi intensitas


---

# 3.6 Edge Detection


Program menggunakan operator Laplacian 9 titik.


Formula:


```
Edge =
|8(center) - jumlah(tetangga)|
```


Neighborhood:


```
P1 P2 P3

P4 P5 P6

P7 P8 P9

```


Pipeline:


```
Input Image

      |
      v

Take 8 Neighbor Pixels

      |
      v

Apply Laplacian Operator

      |
      v

Calculate Gradient Difference

      |
      v

Edge Image
```


Kegunaan:

- Deteksi perubahan intensitas
- Ekstraksi batas objek


---

# 4. Dependency


## Python Version


Recommended:


```
Python >= 3.9
```


## Required Package


Install:


```bash
pip install pillow
```


Library lainnya menggunakan Python standard library.


Dependency:


```
Pillow
```


---

# 5. Project Structure


```
Manual-Digital-Image-Processing/

│
├── main.py
│
├── input/
│
├── output/
│
├── requirements.txt
│
└── README.md

```


---

# 6. How To Run


## Step 1

Install dependency:


```bash
pip install pillow
```


---

## Step 2

Jalankan program:


```bash
python main.py
```


---

## Step 3

Masukkan file gambar:


Contoh:


```
image.png

atau

image.bmp

```


Jika input bukan BMP:

Program otomatis melakukan konversi:


```
PNG/JPEG

      |

      v

BMP

```


---

# 7. Program Menu


Menu utama:


```
1. Brightness Adjustment

2. Contrast Enhancement

3. Horizontal Mirror

4. Rotation 90 Degree

5. Noise Reduction / Smoothing

6. Edge Detection

7. Image Information

8. Pixel Coordinate Check

0. Exit

```


---

# 8. Image Processing Pipeline


## General Pipeline


```
Input Image

      |
      v

Format Conversion

      |
      v

BMP Reader

      |
      v

Pixel Matrix

      |
      v

Image Processing

      |
      v

Save BMP

```


---

# 9. Educational Purpose


Project ini dibuat untuk memahami fundamental pengolahan citra digital:

- Struktur file gambar
- Representasi piksel
- Transformasi intensitas
- Filtering
- Transformasi geometris
- Deteksi tepi


Dengan implementasi manual, pengguna dapat memahami proses internal sebelum menggunakan library seperti:

- OpenCV
- MATLAB Image Processing Toolbox
- Scikit-image


---

# 10. Limitations


- Hanya mendukung BMP secara penuh.
- Format lain harus dikonversi terlebih dahulu.
- Belum mendukung citra warna penuh sebagai output.
- Pemrosesan menggunakan nested loop sehingga lebih lambat dibanding library optimized.


---