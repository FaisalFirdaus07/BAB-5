import cv2
import numpy as np
from collections import defaultdict

class ShapeColorDetector:
    def __init__(self):
        # Definisi range warna dalam HSV
        self.color_ranges = {
            'merah': [(0, 50, 50), (10, 255, 255), (170, 50, 50), (180, 255, 255)],
            'biru': [(100, 50, 50), (130, 255, 255)],
            'hijau': [(40, 50, 50), (80, 255, 255)],
            'kuning': [(20, 50, 50), (40, 255, 255)],
            'orange': [(10, 50, 50), (20, 255, 255)],
            'ungu': [(130, 50, 50), (170, 255, 255)],
            'pink': [(150, 50, 50), (170, 255, 255)]
        }
    
    def detect_color(self, hsv_roi):
        """Mendeteksi warna dominan dari region of interest"""
        for color_name, ranges in self.color_ranges.items():
            if color_name == 'merah':
                # Merah memiliki dua range karena wraparound di HSV
                mask1 = cv2.inRange(hsv_roi, np.array(ranges[0]), np.array(ranges[1]))
                mask2 = cv2.inRange(hsv_roi, np.array(ranges[2]), np.array(ranges[3]))
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                mask = cv2.inRange(hsv_roi, np.array(ranges[0]), np.array(ranges[1]))
            
            # Hitung persentase pixel yang cocok
            percentage = (cv2.countNonZero(mask) / mask.size) * 100
            if percentage > 15:  # Threshold 15%
                return color_name, percentage
        
        return 'tidak diketahui', 0
    
    def detect_shape(self, contour):
        """Mendeteksi bentuk berdasarkan contour"""
        # Approximate contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)
        
        # Hitung area dan perimeter
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if area < 500:  # Filter objek yang terlalu kecil
            return None
        
        # Deteksi berdasarkan jumlah vertices
        if vertices == 3:
            return "segitiga"
        elif vertices == 4:
            # Cek apakah persegi atau persegi panjang
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            if 0.8 <= aspect_ratio <= 1.2:
                return "persegi"
            else:
                return "persegi_panjang"
        elif vertices == 5:
            return "pentagon"
        elif vertices == 6:
            return "hexagon"
        else:
            # Cek apakah lingkaran berdasarkan circularity
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity > 0.7:
                    return "lingkaran"
            return "poligon"
    
    def process_frame(self, frame):
        """Memproses frame untuk deteksi shape dan color"""
        # Convert ke HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Convert ke grayscale untuk edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection menggunakan Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Morfologi untuk membersihkan noise
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        results = []
        output_frame = frame.copy()
        
        for contour in contours:
            # Deteksi shape
            shape = self.detect_shape(contour)
            if shape is None:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Extract ROI untuk deteksi warna
            roi = frame[y:y+h, x:x+w]
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Deteksi warna
            color, confidence = self.detect_color(hsv_roi)
            
            # Draw contour dan label
            cv2.drawContours(output_frame, [contour], -1, (0, 255, 0), 2)
            
            # Label dengan shape dan color
            label = f"{color.title()} {shape.replace('_', ' ').title()}"
            label_pos = (x, y - 10)
            
            # Background untuk text
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(output_frame, (x, y - label_h - 15), (x + label_w, y), (255, 255, 255), -1)
            
            # Text
            cv2.putText(output_frame, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Simpan hasil
            results.append({
                'shape': shape,
                'color': color,
                'confidence': confidence,
                'area': cv2.contourArea(contour),
                'position': (x + w//2, y + h//2)
            })
        
        return output_frame, results

def main():
    # Inisialisasi detector
    detector = ShapeColorDetector()
    
    print("Shape and Color Detection")
    print("========================")
    print("Pilih mode:")
    print("1. Webcam (tekan 'q' untuk keluar)")
    print("2. Image file")
    print("3. Video file")
    
    choice = input("Masukkan pilihan (1/2/3): ")
    
    if choice == "1":
        # Mode webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Tidak dapat mengakses webcam")
            return
        
        print("Webcam aktif. Tekan 'q' untuk keluar, 's' untuk screenshot")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            output_frame, results = detector.process_frame(frame)
            
            # Tampilkan statistik
            if results:
                stats = defaultdict(int)
                for result in results:
                    key = f"{result['color']} {result['shape']}"
                    stats[key] += 1
                
                y_pos = 30
                for item, count in stats.items():
                    text = f"{item.title()}: {count}"
                    cv2.putText(output_frame, text, (10, y_pos), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    y_pos += 25
            
            cv2.imshow('Shape and Color Detection', output_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite('screenshot.jpg', output_frame)
                print("Screenshot disimpan sebagai screenshot.jpg")
        
        cap.release()
    
    elif choice == "2":
        # Mode image
        image_path = input("Masukkan path image: ")
        
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                print("Error: Tidak dapat membaca image")
                return
            
            # Process image
            output_frame, results = detector.process_frame(frame)
            
            # Tampilkan hasil
            print(f"\nDeteksi pada {image_path}:")
            print("-" * 40)
            
            if results:
                stats = defaultdict(int)
                for result in results:
                    key = f"{result['color']} {result['shape']}"
                    stats[key] += 1
                    print(f"- {result['color'].title()} {result['shape'].replace('_', ' ').title()}")
                    print(f"  Area: {result['area']:.0f}, Confidence: {result['confidence']:.1f}%")
                
                print(f"\nRingkasan:")
                for item, count in stats.items():
                    print(f"- {item.title()}: {count} objek")
            else:
                print("Tidak ada objek terdeteksi")
            
            # Tampilkan image
            cv2.imshow('Result', output_frame)
            cv2.waitKey(0)
            
            # Simpan hasil
            output_path = image_path.replace('.', '_detected.')
            cv2.imwrite(output_path, output_frame)
            print(f"\nHasil disimpan sebagai: {output_path}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == "3":
        # Mode video
        video_path = input("Masukkan path video: ")
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print("Error: Tidak dapat membaca video")
                return
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Setup video writer
            output_path = video_path.replace('.', '_detected.')
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            print("Memproses video... Tekan 'q' untuk berhenti")
            
            frame_count = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                output_frame, results = detector.process_frame(frame)
                
                # Write frame
                out.write(output_frame)
                
                # Show progress
                frame_count += 1
                progress = (frame_count / total_frames) * 100
                print(f"\rProgress: {progress:.1f}% ({frame_count}/{total_frames})", end="")
                
                # Display frame (optional, bisa dicomment jika slow)
                cv2.imshow('Processing', output_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            out.release()
            print(f"\n\nVideo hasil disimpan sebagai: {output_path}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        print("Pilihan tidak valid")
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()