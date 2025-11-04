#include <Servo.h>

Servo myServo;
int angle = 90;

void setup() {
  myServo.attach(2);        // Sesuaikan pin servo
  myServo.write(angle);     // Posisi awal
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {

    angle = Serial.read();              // Baca data dari Python
    angle = constrain(angle, 0, 180);   // Batasi agar aman

    // Membalik arah pergerakan servo
    int reversedAngle = 180 - angle;

    // Gerakkan servo
    myServo.write(reversedAngle);
  }
}
