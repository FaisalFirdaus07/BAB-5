import cv2
import numpy as np
import serial
import serial.tools.list_ports
import time


# ============================================================
#  AUTO DETECT ARDUINO
# ============================================================
def find_arduino_port():
    """Mencari port Arduino secara otomatis"""
    print("Mencari port Arduino...")
    ports = serial.tools.list_ports.comports()

    if not ports:
        print("Tidak ada port serial yang ditemukan.")
        return None

    print("Port serial yang tersedia:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")

    # Deteksi otomatis berdasarkan kata kunci
    arduino_keywords = ['Arduino', 'CH340', 'USB-SERIAL', 'USB Serial']
    for port in ports:
        for keyword in arduino_keywords:
            if keyword.lower() in port.description.lower():
                print(f"Arduino terdeteksi di: {port.device}")
                return port.device

    # Manual pilih jika tidak terdeteksi
    while True:
        try:
            choice = int(input(f"Pilih port (1-{len(ports)}) atau 0 untuk skip: "))
            if choice == 0:
                return None
            if 1 <= choice <= len(ports):
                return ports[choice-1].device
            else:
                print("Pilihan tidak valid!")
        except ValueError:
            print("Masukkan angka yang valid!")


# ============================================================
#  TEST KONEKSI ARDUINO
# ============================================================
def test_arduino_connection(port, baudrates=[9600, 115200, 57600]):
    """Test koneksi Arduino dengan berbagai baudrate"""
    print(f"Testing koneksi ke {port}...")

    for baudrate in baudrates:
        try:
            print(f"Mencoba baudrate {baudrate}...")
            arduino = serial.Serial(port, baudrate, timeout=2)
            time.sleep(2)

            arduino.write(b'90')
            time.sleep(0.1)

            if arduino.is_open:
                print(f"✓ Berhasil terhubung ke {port} dengan baudrate {baudrate}")
                return arduino

        except serial.SerialException as e:
            print(f"✗ Gagal dengan baudrate {baudrate}: {e}")
            continue
        except Exception as e:
            print(f"✗ Error lain: {e}")
            continue

    print("✗ Tidak dapat terhubung ke Arduino")
    return None


# ============================================================
#  DETEKSI BENTUK
# ============================================================
def get_shape(contour):
    approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
    num_vertices = len(approx)

    # Segitiga
    if num_vertices == 3:
        return "Segitiga"

    # Segiempat / Persegi / Persegi Panjang
    elif num_vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h

        # cek sudut-sudut
        max_cos = 0
        for i in range(2, num_vertices + 1):
            pt1 = approx[i % num_vertices][0]
            pt2 = approx[i - 2][0]
            pt3 = approx[i - 1][0]

            v1_x = pt1[0] - pt2[0]
            v1_y = pt1[1] - pt2[1]
            v2_x = pt3[0] - pt2[0]
            v2_y = pt3[1] - pt2[1]

            dot_product = v1_x * v2_x + v1_y * v2_y
            magnitude_v1 = np.sqrt(v1_x**2 + v1_y**2)
            magnitude_v2 = np.sqrt(v2_x**2 + v2_y**2)

            if magnitude_v1 == 0 or magnitude_v2 == 0:
                max_cos = 1
            else:
                cosine_angle = dot_product / (magnitude_v1 * magnitude_v2)
                max_cos = max(max_cos, abs(cosine_angle))

        if 0.95 <= aspect_ratio <= 1.05 and max_cos < 0.1:
            return "Persegi"
        elif max_cos < 0.1:
            return "Persegi Panjang"
        elif max_cos > 0.2:
            return "Jajar Genjang"
        else:
            return "Segiempat Tidak Dikenal"

    # Pentagon
    elif num_vertices == 5:
        return "Pentagon"

    # Hexagon
    elif num_vertices == 6:
        return "Heksagon"

    # Octagon
    elif num_vertices == 8:
        return "Oktagon"

    # Circle
    else:
        area = cv2.contourArea(contour)
        (x, y), radius = cv2.minEnclosingCircle(contour)
        if radius > 0:
            circle_area = np.pi * (radius ** 2)
            if area / circle_area > 0.8:
                return "Lingkaran"
        return "Bentuk Tidak Dikenal"


# ============================================================
#  DETEKSI WARNA
# ============================================================
def get_color_name(hsv_pixel, color_ranges):
    h, s, v = hsv_pixel

    if v < 50:
        return "Hitam"

    for color_name, (lower, upper) in color_ranges.items():
        if color_name == "Merah":
            lower1, upper1 = lower
            lower2, upper2 = upper
            if ((lower1[0] <= h <= upper1[0] or lower2[0] <= h <= upper2[0]) and
                lower1[1] <= s <= upper1[1] and
                lower1[2] <= v <= upper1[2]):
                return "Merah"
        else:
            if lower[0] <= h <= upper[0] and lower[1] <= s <= upper[1] and lower[2] <= v <= upper[2]:
                return color_name

    return "Warna Lain"


# ============================================================
#  SELECT TARGET SHAPE
# ============================================================
def pilih_bentuk():
    daftar_bentuk = [
        "Segitiga", "Persegi", "Persegi Panjang", "Jajar Genjang",
        "Pentagon", "Heksagon", "Oktagon", "Lingkaran"
    ]

    print("Pilih bentuk yang ingin di-tracking:")
    for i, bentuk in enumerate(daftar_bentuk, 1):
        print(f"{i}. {bentuk}")

    while True:
        try:
            pilihan = int(input("Masukkan nomor bentuk (1-8): "))
            if 1 <= pilihan <= len(daftar_bentuk):
                return daftar_bentuk[pilihan - 1]
            print("Pilihan tidak valid.")
        except ValueError:
            print("Masukkan angka yang valid.")


# ============================================================
#  MAIN PROGRAM
# ============================================================
def main():
    print("=== SHAPE TRACKER WITH ARDUINO ===")

    # Bentuk target
    bentuk_target = pilih_bentuk()
    print(f"Tracking akan dilakukan pada bentuk: {bentuk_target}")

    # Arduino
    arduino = None
    use_arduino = input("Gunakan Arduino? (y/n): ").lower() == 'y'

    if use_arduino:
        arduino_port = find_arduino_port()
        if arduino_port:
            arduino = test_arduino_connection(arduino_port)
            if arduino:
                print("✓ Arduino siap digunakan!")
        if not arduino:
            if input("Lanjut tanpa Arduino? (y/n): ").lower() != 'y':
                return

    # Kamera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Tidak dapat membuka kamera.")
        return

    # Warna HSV range
    color_ranges = {
        "Biru": (np.array([90, 50, 50]), np.array([130, 255, 255])),
        "Hijau": (np.array([40, 50, 50]), np.array([80, 255, 255])),
        "Kuning": (np.array([20, 100, 100]), np.array([30, 255, 255])),
        "Ungu": (np.array([130, 50, 50]), np.array([160, 255, 255])),
        "Merah": (
            (np.array([0, 50, 50]), np.array([10, 255, 255])),
            (np.array([170, 50, 50]), np.array([180, 255, 255]))
        )
    }

    current_angle = 90
    smoothing_factor = 0.1
    frame_count = 0

    print("\nTracking dimulai! Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 50, 100)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_contour = None
        max_area = 1000

        # cari contour terbesar sesuai bentuk target
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                shape = get_shape(contour)
                if shape == bentuk_target:
                    max_area = area
                    largest_contour = contour

        # info status
        cv2.putText(frame, f"Target: {bentuk_target}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if arduino and arduino.is_open:
            cv2.putText(frame, "Arduino: Connected", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Arduino: Disconnected", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if largest_contour is not None:
            shape = get_shape(largest_contour)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cX = x + w // 2
            cY = y + h // 2

            # ambil warna
            hsv_pixel = hsv_frame[cY, cX]
            color_name = get_color_name(hsv_pixel, color_ranges)

            # gambar bounding box
            label = f"{color_name} {shape}"
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # ====================================================
            # SERVO CONTROL
            # ====================================================
            if arduino and arduino.is_open:
                try:
                    frame_center = frame.shape[1] // 2
                    deviation = cX - frame_center

                    target_angle = int(90 + (deviation / frame_center) * 90)
                    target_angle = max(0, min(180, target_angle))

                    current_angle = int(current_angle + smoothing_factor * (target_angle - current_angle))

                    if frame_count % 3 == 0:
                        arduino.write(bytes([current_angle]))

                    cv2.putText(frame, f"Angle: {current_angle}", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                except Exception as e:
                    print("Arduino communication error:", e)
                    arduino = None

        # garis tengah layar
        frame_center = frame.shape[1] // 2
        cv2.line(frame, (frame_center, 0), (frame_center, frame.shape[0]),
                 (255, 255, 255), 1)

        cv2.imshow("Shape Tracker", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r') and not arduino:
            arduino_port = find_arduino_port()
            if arduino_port:
                arduino = test_arduino_connection(arduino_port)

    cap.release()
    cv2.destroyAllWindows()

    if arduino and arduino.is_open:
        arduino.close()
        print("Arduino connection closed.")


# ============================================================
#  RUN
# ============================================================
if __name__ == "__main__":
    main()
