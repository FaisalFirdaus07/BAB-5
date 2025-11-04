import cv2
import numpy as np
import serial
import serial.tools.list_ports
import time

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
    
    # Coba deteksi Arduino otomatis
    arduino_keywords = ['Arduino', 'CH340', 'USB-SERIAL', 'USB Serial']
    for port in ports:
        for keyword in arduino_keywords:
            if keyword.lower() in port.description.lower():
                print(f"Arduino terdeteksi di: {port.device}")
                return port.device
    
    # Jika tidak terdeteksi otomatis, minta user pilih
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

def test_arduino_connection(port, baudrates=[9600, 115200, 57600]):
    """Test koneksi Arduino dengan berbagai baudrate"""
    print(f"Testing koneksi ke {port}...")
    
    for baudrate in baudrates:
        try:
            print(f"Mencoba baudrate {baudrate}...")
            arduino = serial.Serial(port, baudrate, timeout=2)
            time.sleep(2)  # Wait for Arduino to reset
            
            # Test komunikasi
            arduino.write(b'90')  # Send test data
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

def get_shape(contour):
    approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
    num_vertices = len(approx)

    if num_vertices == 3:
        return "Segitiga"
    elif num_vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h

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

    elif num_vertices == 5:
        return "Pentagon"
    elif num_vertices == 6:
        return "Heksagon"
    elif num_vertices == 8:
        return "Oktagon"
    else:
        area = cv2.contourArea(contour)
        (x, y), radius = cv2.minEnclosingCircle(contour)
        if radius > 0:
            circle_area = np.pi * (radius ** 2)
            if area / circle_area > 0.8:
                return "Lingkaran"
        return "Bentuk Tidak Dikenal"

def get_color_name(hsv_pixel, color_ranges):
    h, s, v = hsv_pixel

    if v < 50:
        return "Hitam"

    for color_name, (lower, upper) in color_ranges.items():
        if color_name == "Merah":
            lower_red1, upper_red1 = lower
            lower_red2, upper_red2 = upper
            if ((lower_red1[0] <= h <= upper_red1[0] or lower_red2[0] <= h <= upper_red2[0]) and
                lower_red1[1] <= s <= upper_red1[1] and
                lower_red1[2] <= v <= upper_red1[2]):
                return "Merah"
        else:
            if (lower[0] <= h <= upper[0] and
                lower[1] <= s <= upper[1] and
                lower[2] <= v <= upper[2]):
                return color_name
    return "Warna Lain"

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
            else:
                print("Pilihan tidak valid. Ulangi.")
        except ValueError:
            print("Masukkan angka yang valid.")

def main():
    print("=== SHAPE TRACKER WITH ARDUINO ===")
    
    # Pilih bentuk target
    bentuk_target = pilih_bentuk()
    print(f"Tracking akan dilakukan pada bentuk: {bentuk_target}")
    
    # Setup Arduino connection
    arduino = None
    use_arduino = input("Gunakan Arduino? (y/n): ").lower() == 'y'
    
    if use_arduino:
        # Cari port Arduino
        arduino_port = find_arduino_port()
        
        if arduino_port:
            # Test koneksi
            arduino = test_arduino_connection(arduino_port)
            
            if arduino:
                print("✓ Arduino siap digunakan!")
            else:
                print("✗ Tidak dapat terhubung ke Arduino.")
                use_manual = input("Lanjutkan tanpa Arduino? (y/n): ").lower() == 'y'
                if not use_manual:
                    return
        else:
            print("Port Arduino tidak ditemukan.")
            use_manual = input("Lanjutkan tanpa Arduino? (y/n): ").lower() == 'y'
            if not use_manual:
                return
    
    # Setup camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Tidak dapat membuka kamera.")
        return

    # Color ranges
    color_ranges = {
        "Biru": (np.array([90, 50, 50]), np.array([130, 255, 255])),
        "Hijau": (np.array([40, 50, 50]), np.array([80, 255, 255])),
        "Kuning": (np.array([20, 100, 100]), np.array([30, 255, 255])),
        "Ungu": (np.array([130, 50, 50]), np.array([160, 255, 255])),
        "Merah": ((np.array([0, 50, 50]), np.array([10, 255, 255])),
                  (np.array([170, 50, 50]), np.array([180, 255, 255])))
    }

    current_angle = 90
    smoothing_factor = 0.1
    frame_count = 0
    
    print("\nTracking dimulai! Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Tidak dapat membaca frame dari kamera.")
            break

        frame_count += 1
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 50, 100)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_contour = None
        max_area = 1000

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                shape = get_shape(contour)
                if shape == bentuk_target:
                    max_area = area
                    largest_contour = contour

        # Status display
        status_text = f"Target: {bentuk_target}"
        cv2.putText(frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        arduino_status = "Arduino: Connected" if arduino and arduino.is_open else "Arduino: Disconnected"
        cv2.putText(frame, arduino_status, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                   (0, 255, 0) if arduino and arduino.is_open else (0, 0, 255), 2)

        if largest_contour is not None:
            shape = get_shape(largest_contour)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cX = int(x + w / 2)
            cY = int(y + h / 2)

            # Get color
            color_name = "Warna Tidak Dikenal"
            if 0 <= cY < hsv_frame.shape[0] and 0 <= cX < hsv_frame.shape[1]:
                hsv_pixel = hsv_frame[cY, cX]
                color_name = get_color_name(hsv_pixel, color_ranges)

            # Draw detection
            label = f"{color_name} {shape}"
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Arduino control
            if arduino and arduino.is_open:
                try:
                    frame_center = frame.shape[1] // 2
                    deviation = cX - frame_center
                    target_angle = int(90 + (deviation / frame_center) * 90)
                    target_angle = max(0, min(180, target_angle))
                    current_angle = int(current_angle + smoothing_factor * (target_angle - current_angle))

                    # Send to Arduino (limit frequency)
                    if frame_count % 3 == 0 and abs(current_angle - target_angle) > 1:
                        arduino.write(bytes([current_angle]))
                        
                    # Display angle
                    angle_text = f"Angle: {current_angle}"
                    cv2.putText(frame, angle_text, (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                    
                except Exception as e:
                    print(f"Arduino communication error: {e}")
                    arduino = None

        # Draw center line
        frame_center = frame.shape[1] // 2
        cv2.line(frame, (frame_center, 0), (frame_center, frame.shape[0]), (255, 255, 255), 1)

        cv2.imshow("Shape Tracker", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r') and not arduino:
            # Reconnect Arduino
            print("Mencoba reconnect ke Arduino...")
            arduino_port = find_arduino_port()
            if arduino_port:
                arduino = test_arduino_connection(arduino_port)

        time.sleep(0.02)

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    if arduino and arduino.is_open:
        arduino.close()
        print("Arduino connection closed.")

if __name__ == "__main__":
    main()
