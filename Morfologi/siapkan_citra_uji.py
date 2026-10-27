import os
import cv2
import numpy as np
from skimage import data


def buat_folder_input():
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_uji")
    os.makedirs(folder, exist_ok=True)
    return folder


def simpan(folder, nama_file, img):
    path = os.path.join(folder, nama_file)
    cv2.imwrite(path, img)
    print(f"[OK] Tersimpan: {path}")


def ekstrak_pembuluh_darah_retina(retina_rgb):
    """
    Mengekstrak pohon pembuluh darah (vascular tree) dari foto fundus retina manusia asli
    menggunakan Multi-Scale Morphological Black-Hat pada green channel + CLAHE.
    """
    h_orig, w_orig = retina_rgb.shape[:2]
    scale = 600.0 / max(h_orig, w_orig)
    retina_small = cv2.resize(
        retina_rgb,
        (int(w_orig * scale), int(h_orig * scale)),
        interpolation=cv2.INTER_AREA
    )
    green = retina_small[:, :, 1]

    # Mask bagian dalam bola mata (Field of View) agar pinggiran hitam lingkaran lensa tidak ikut
    _, fov = cv2.threshold(green, 18, 255, cv2.THRESH_BINARY)
    fov = cv2.erode(fov, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)), iterations=1)

    # Tingkatkan kontras pembuluh darah dengan CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    green_eq = clahe.apply(green)
    green_blur = cv2.GaussianBlur(green_eq, (3, 3), 0)

    # Multi-scale Black-Hat untuk menangkap pembuluh darah utama (besar) dan kapiler (kecil)
    vessel_resp = np.zeros_like(green_blur, dtype=np.float32)
    for ksize in (9, 15, 21):
        se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        bh = cv2.morphologyEx(green_blur, cv2.MORPH_BLACKHAT, se)
        vessel_resp = np.maximum(vessel_resp, bh.astype(np.float32))

    vessel_u8 = cv2.normalize(vessel_resp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    vessel_u8 = cv2.bitwise_and(vessel_u8, fov)

    _, vessel_bin = cv2.threshold(vessel_u8, 30, 255, cv2.THRESH_BINARY)
    # Bersihkan noise titik mikro namun pertahankan percabangan pembuluh darah
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(vessel_bin, connectivity=8)
    vessel_clean = np.zeros_like(vessel_bin)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= 35:
            vessel_clean[labels == i] = 255

    return vessel_clean, green_eq, fov


def buat_sidik_jari_biometrik(size=480):
    """
    Membangkitkan citra biometrik sidik jari realistis (Loop/Whorl dengan Bifurcation & Ridge Endings)
    menggunakan model fase orientasi kontinu 2D (2D Continuous Phase Fingerprint Model).
    """
    Y, X = np.mgrid[-1.0:1.0:complex(0, size), -1.0:1.0:complex(0, size)]

    # Distorsi koordinat organik seperti lengkungan kulit jari pada kaca pemindai
    u = X + 0.12 * np.sin(2.5 * Y)
    v = Y + 0.08 * np.cos(2.5 * X)

    # Radius elips sidik jari + singularitas Core (pusat pusaran) dan Delta
    r = np.sqrt((u * 1.15) ** 2 + (v + 0.05) ** 2)
    theta1 = np.arctan2(v - 0.05, u + 0.02)
    theta2 = np.arctan2(v + 0.45, u - 0.02)

    # Fase gelombang punggung bukit sidik jari (ridges) dengan percabangan alami (dislokasi fase)
    freq = 21.0
    phase = freq * r + 2.0 * theta1 - 1.0 * theta2 + 1.8 * np.cos(1.8 * u - 1.2 * v)
    ridges = np.cos(phase)

    # Mask bentuk ujung jari (oval)
    finger_mask = ((X / 0.78) ** 2 + ((Y - 0.02) / 0.88) ** 2) <= 1.0

    # Buat ketebalan alur 6-8 piksel agar efek penipisan Zhang-Suen (Thinning) sangat kontras
    fp_bin = ((ridges > -0.15) & finger_mask).astype(np.uint8) * 255
    fp_bin = cv2.morphologyEx(fp_bin, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return fp_bin


def buat_layout_ic_pcb_aoi():
    """
    Membangkitkan citra Automated Optical Inspection (AOI) die mikroprosesor / layout PCB realistis
    yang secara presisi menguji ketiga pola Hit-or-Miss di aduh2.py:
      - Pola 1: Titik terisolasi 1 piksel (Cacat solder ball spatter / hot pixel pada wafer)
      - Pola 2: Sudut kiri-atas (Titik registrasi fiducial & pad IC QFP/SMD untuk pick-and-place)
      - Pola 3: Ujung atas garis vertikal (Terminal bus data & deteksi jalur putus / open-circuit)
    """
    canvas = np.zeros((420, 560), dtype=np.uint8)

    # 1. Komponen Utama: Dual QFP Microcontroller Die + Deretan SMD Capacitor Pads (Pola 2: Sudut Kiri-Atas)
    # IC Utama Kiri
    cv2.rectangle(canvas, (70, 80), (190, 200), 255, -1)
    cv2.rectangle(canvas, (95, 105), (165, 175), 0, -1)  # Rongga die dalam
    cv2.rectangle(canvas, (112, 122), (148, 158), 255, -1)  # Core die

    # IC Utama Kanan
    cv2.rectangle(canvas, (330, 80), (450, 200), 255, -1)
    cv2.rectangle(canvas, (355, 105), (425, 175), 0, -1)
    cv2.rectangle(canvas, (372, 122), (408, 158), 255, -1)

    # Deretan SMD Pads / Fiducial Marks di bagian bawah & tengah
    smd_pads = [
        (235, 90, 285, 125),
        (235, 155, 285, 190),
        (70, 290, 125, 345),
        (165, 290, 220, 345),
        (330, 290, 385, 345),
        (425, 290, 480, 345),
    ]
    for (x1, y1, x2, y2) in smd_pads:
        cv2.rectangle(canvas, (x1, y1), (x2, y2), 255, -1)

    # 2. Jalur Bus Sirkuit Vertikal (Pola 3: Ujung Atas Garis Vertikal 1 Piksel)
    # Deretan pin bus data yang berakhir di bagian atas (open terminals / test probes)
    bus_x_coords = [85, 105, 125, 145, 165, 185, 250, 270, 345, 365, 385, 405, 425, 445]
    for idx, bx in enumerate(bus_x_coords):
        y_top = 225 if idx % 2 == 0 else 238
        y_bottom = 272
        canvas[y_top:y_bottom, bx] = 255

    # Jalur bus bawah menuju konektor tepi papan PCB
    for bx in [95, 190, 260, 355, 450]:
        canvas[362:405, bx] = 255

    # 3. Cacat Solder Ball / Micro-Dust / Hot Pixel 1-Piksel Terisolasi (Pola 1)
    defect_coords = [
        (35, 50), (42, 260), (38, 490),
        (140, 35), (135, 515),
        (255, 40), (250, 305), (255, 510),
        (380, 45), (385, 295), (380, 515),
    ]
    for (dy, dx) in defect_coords:
        canvas[dy, dx] = 255

    return canvas


def generate_semua_citra():
    folder = buat_folder_input()
    rng = np.random.default_rng(42)

    print("=" * 68)
    print(" MENYIAPKAN CITRA UJI ADVANCED (MEDIS, ASTROFISIKA, BIOMETRIK, AOI)")
    print("=" * 68)

    # Ekstrak pembuluh darah dari foto fundus retina manusia asli
    try:
        retina_rgb = data.retina()
        vessel_clean, green_eq, fov = ekstrak_pembuluh_darah_retina(retina_rgb)
    except Exception:
        vessel_clean = None

    # ------------------------------------------------------------------
    # 1. DILATION:
    #    1a (Utama): Restorasi Dokumen Scan / Manuskrip Ilmiah yang Terdegradasi (OCR)
    #    1b (Medis): Rekonstruksi Kapiler Angiografi Retina yang Putus-Putus
    # ------------------------------------------------------------------
    page = data.page()
    page_inv = 255 - page
    se_page = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    page_flat = cv2.morphologyEx(page_inv, cv2.MORPH_TOPHAT, se_page)
    _, dilasi_ocr = cv2.threshold(page_flat, 55, 255, cv2.THRESH_BINARY)
    simpan(folder, "1_dilasi_restorasi_teks_ocr.png", dilasi_ocr)

    if vessel_clean is not None:
        # Simulasikan hasil segmentasi kapiler angiografi yang patah-patah akibat kontras zat warna rendah
        grid_break = np.ones_like(vessel_clean)
        grid_break[::6, :] = 0
        grid_break[:, ::6] = 0
        vessel_broken = cv2.bitwise_and(vessel_clean, grid_break * 255)
        simpan(folder, "1b_dilasi_angiografi_pembuluh_darah_putus.png", vessel_broken)

    # ------------------------------------------------------------------
    # 2. EROSION:
    #    Segmentasi & Pemisahan Kluster Sel Histopatologi / Nukleus Mikroskop (Biomedis)
    #    Sumber: skimage.data.immunohistochemistry() (Jaringan Biopsi Medis Asli)
    # ------------------------------------------------------------------
    try:
        ihc = data.immunohistochemistry()
        # Ekstrak kanal Hematoxylin/DAB (inti sel gelap pada jaringan biopsi) lalu invert
        ihc_gray = cv2.cvtColor(ihc, cv2.COLOR_RGB2GRAY)
        ihc_inv = 255 - ihc_gray
        se_ihc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
        ihc_tophat = cv2.morphologyEx(ihc_inv, cv2.MORPH_TOPHAT, se_ihc)
        _, sel_mask = cv2.threshold(ihc_tophat, 26, 255, cv2.THRESH_BINARY)
        # Haluskan & bulatkan tiap nukleus sel menggunakan opening + convex hull per komponen
        sel_mask = cv2.morphologyEx(sel_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        contours, _ = cv2.findContours(sel_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        erosi_sel = np.zeros_like(sel_mask)
        cell_centers = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 65 < area < 2500:
                hull = cv2.convexHull(cnt)
                cv2.drawContours(erosi_sel, [hull], -1, 255, -1)
                M = cv2.moments(hull)
                if M["m00"] > 0:
                    cell_centers.append((int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])))
        # Buat jembatan sitoplasma tipis (2px) antar sel yang sedang membelah (mitosis) & berdekatan
        for i in range(len(cell_centers)):
            for j in range(i + 1, len(cell_centers)):
                c1, c2 = cell_centers[i], cell_centers[j]
                dist = np.hypot(c1[0] - c2[0], c1[1] - c2[1])
                if 18 < dist < 52:
                    cv2.line(erosi_sel, c1, c2, 255, 2)
    except Exception:
        erosi_sel = np.zeros((480, 480), dtype=np.uint8)

    # Tambahkan artefak bintik reagen fluoresensi (1-2 piksel) di latar belakang mikroskop
    specks = (rng.random(erosi_sel.shape) > 0.988).astype(np.uint8) * 255
    specks = cv2.dilate(specks, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)), iterations=1)
    erosi_sel = cv2.bitwise_or(erosi_sel, specks)
    simpan(folder, "2_erosi_pemisahan_sel_mikroskop.png", erosi_sel)

    # ------------------------------------------------------------------
    # 3. OPENING:
    #    3a (Medis Advanced): Pembersihan Speckle/Salt Noise pada Citra CT/MRI Otak (Shepp-Logan)
    #                         & Sel Mikroskop tanpa Mengecilkan Organ/Sel
    # ------------------------------------------------------------------
    try:
        phantom = (data.shepp_logan_phantom() * 255).astype(np.uint8)
        phantom = cv2.resize(phantom, (480, 480), interpolation=cv2.INTER_AREA)
        _, brain_seg = cv2.threshold(phantom, 45, 255, cv2.THRESH_BINARY)
    except Exception:
        brain_seg = np.zeros((480, 480), dtype=np.uint8)
        cv2.ellipse(brain_seg, (240, 240), (160, 200), 0, 0, 360, 255, -1)

    # Tambahkan artefak derau bintik (speckle/salt noise) di luar & di dalam rongga ventrikel otak
    salt_noise = (rng.random(brain_seg.shape) > 0.968).astype(np.uint8) * 255
    salt_noise = cv2.dilate(salt_noise, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
    # Pastikan noise hanya di area background hitam (agar menonjolkan fungsi Opening)
    opening_mri = cv2.bitwise_or(brain_seg, salt_noise)
    simpan(folder, "3_opening_hapus_noise_bintik.png", opening_mri)

    # ------------------------------------------------------------------
    # 4. CLOSING:
    #    Rekonstruksi Struktur Tulang Tengkorak & Jaringan Organ CT-Scan yang Berpori/Retak
    # ------------------------------------------------------------------
    closing_ct = brain_seg.copy()
    # Buat pori-pori trabekular (lubang hitam 1-2 piksel) & retakan mikro di dalam jaringan putih CT-Scan
    pores = (rng.random(closing_ct.shape) > 0.88).astype(np.uint8) * 255
    closing_ct = cv2.bitwise_and(closing_ct, cv2.bitwise_not(pores))
    # Tambahkan beberapa garis retakan tipis 1 piksel melintasi jaringan
    for y_crack in range(100, 380, 45):
        closing_ct[y_crack, 80:400] = 0
    simpan(folder, "4_closing_tutup_lubang_objek.png", closing_ct)

    # ------------------------------------------------------------------
    # 5. TOP-HAT:
    #    5a: Astrofisika — Deteksi Galaksi & Bintang Redup dari Teleskop NASA Hubble
    #    5b: Medis — Deteksi Lesi Terang / Struktur Halus pada Foto Fundus Retina
    # ------------------------------------------------------------------
    try:
        hubble = data.hubble_deep_field()
        hubble_gray = cv2.cvtColor(hubble, cv2.COLOR_RGB2GRAY)
        hubble_gray = cv2.resize(hubble_gray, (500, 500), interpolation=cv2.INTER_AREA)
    except Exception:
        hubble_gray = np.zeros((500, 500), dtype=np.uint8)
        for _ in range(180):
            y_s, x_s = rng.integers(5, 495), rng.integers(5, 495)
            cv2.circle(hubble_gray, (int(x_s), int(y_s)), int(rng.integers(2, 6)), int(rng.integers(180, 255)), -1)

    h, w = hubble_gray.shape[:2]
    Y, X = np.ogrid[:h, :w]
    nebula_glow = np.exp(-((X - w * 0.5) ** 2 + (Y - h * 0.5) ** 2) / (2.0 * (min(h, w) * 0.32) ** 2))
    nebula_glow = (nebula_glow * 130).astype(np.uint8)
    tophat_img = cv2.add((hubble_gray * 0.75).astype(np.uint8), nebula_glow)
    simpan(folder, "5_tophat_astronomi_bintang_hubble.png", tophat_img)

    # ------------------------------------------------------------------
    # 6. HIT-OR-MISS:
    #    Automated Optical Inspection (AOI) Die Mikroprosesor & Layout PCB Industri
    # ------------------------------------------------------------------
    pcb_aoi = buat_layout_ic_pcb_aoi()
    simpan(folder, "6_hit_or_miss_inspeksi_pcb.png", pcb_aoi)

    # ------------------------------------------------------------------
    # 7. SKELETONIZATION:
    #    7a: Analisis Vaskular Pembuluh Darah Retina Mata Manusia (Medial Axis)
    #    7b: Analisis Morfologi Biologis (Siluet Kuda)
    # ------------------------------------------------------------------
    if vessel_clean is not None:
        simpan(folder, "7a_skeleton_pembuluh_darah_retina.png", vessel_clean)

    horse = data.horse()
    horse_uint8 = ((horse == 0) * 255).astype(np.uint8)
    simpan(folder, "7b_skeleton_siluet_kuda.png", horse_uint8)

    # ------------------------------------------------------------------
    # 8. THINNING (Zhang-Suen):
    #    8a: Biometrik Sidik Jari Lengkap dengan Core, Delta, & Minutiae Percabangan
    #    8b: Pengenalan Karakter & Segmen Dokumen Nyata (OCR)
    # ------------------------------------------------------------------
    fp_real = buat_sidik_jari_biometrik(size=480)
    simpan(folder, "8a_thinning_alur_sidik_jari.png", fp_real)

    ocr_canvas = np.zeros((280, 560), dtype=np.uint8)
    cv2.putText(ocr_canvas, "DK 1945 XY", (35, 120), cv2.FONT_HERSHEY_DUPLEX, 2.3, 255, 13, cv2.LINE_AA)
    cv2.putText(ocr_canvas, "10 . 26", (165, 225), cv2.FONT_HERSHEY_SIMPLEX, 2.0, 255, 11, cv2.LINE_AA)
    cv2.rectangle(ocr_canvas, (15, 20), (545, 260), 255, 8)
    _, ocr_canvas = cv2.threshold(ocr_canvas, 127, 255, cv2.THRESH_BINARY)
    simpan(folder, "8b_thinning_karakter_ocr.png", ocr_canvas)

    print("\n" + "=" * 68)
    print(" SELESAI! Semua citra uji ADVANCED telah diperbarui di folder:")
    print(f" {folder}")
    print("=" * 68)


if __name__ == "__main__":
    generate_semua_citra()
