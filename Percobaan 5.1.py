import cv2
import numpy as np

# Load gambar
img = cv2.imread('foto1.jpg')  # Ganti dengan lokasi gambar Anda
if img is None:
    raise FileNotFoundError("Gambar tidak ditemukan.")

# 1. RGB Extraction
b, g, r = cv2.split(img)
rgb_image = cv2.merge([r, g, b])
print("RGB Extraction selesai.")
# 2. Grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print("Grayscale selesai.")
# 3. Threshold & Binarization
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
print("Threshold & Binarization selesai.")
# 4. Convolution (misalnya edge detection sederhana)
kernel = np.array([[-1, -1, -1],
                   [-1,  8, -1],
                   [-1, -1, -1]])
convolved = cv2.filter2D(gray, -1, kernel)
print("Convolution selesai.")

# Menyimpan hasil Preprocessing
cv2.imwrite('hasil_rgb.jpg', rgb_image)
cv2.imwrite('hasil_gray.jpg', gray)
cv2.imwrite('hasil_binary.jpg', binary)
cv2.imwrite('hasil_convolution.jpg', convolved)
