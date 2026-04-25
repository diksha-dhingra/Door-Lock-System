//  SMART LOCK  —  Face → RFID → PIN
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>
#include <Keypad.h>

#define SDA_PIN 10
#define RST_PIN 9
#define BUZZER  A1

MFRC522 mfrc522(SDA_PIN, RST_PIN);

Servo myServo;
const int servoPin = A0;

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

const byte ROWS = 4, COLS = 3;
char keys[ROWS][COLS] = {
  {'1','2','3'},
  {'4','5','6'},
  {'7','8','9'},
  {'*','0','#'}
};
byte rowPins[ROWS] = {8, 7, 6, 5};
byte colPins[COLS]  = {2, 3, 4};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

byte authorizedUID[] = {0x0D, 0x22, 0xD2, 0x06};

// Store password in flash — saves RAM
const char masterPassword[] PROGMEM = "1234";

// ===========================================
void setup() {
  pinMode(BUZZER, OUTPUT);
  Serial.begin(9600);
  Wire.begin();

  // OLED first — always
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("OLED FAIL"));
    tone(BUZZER, 500, 2000);
    while (1);
  }

  Serial.println(F("OLED OK"));

  display.setTextColor(WHITE);
  display.cp437(true);         

  // SPI after OLED
  SPI.begin();
  mfrc522.PCD_Init();

  myServo.attach(servoPin);
  myServo.write(0);

  welcomeBeep();
  resetSystem();
}

// ======================================
void loop() {
  if (Serial.available()) {
    char signal = Serial.read();
    while (Serial.available()) Serial.read();

    if (signal == 'F') {
      rfidAndPinFlow();
    } else if (signal == 'D') {
      showTwoLine(F("ACCESS"), F("DENIED :("));
      beepError();
      delay(2000);
      resetSystem();
    }
  }
}

// =======================================
void rfidAndPinFlow() {
  showTwoLine(F("Scan"), F("Your Card"));

  unsigned long start = millis();

  while (millis() - start < 15000) {
    if (!mfrc522.PICC_IsNewCardPresent()) continue;
    if (!mfrc522.PICC_ReadCardSerial())   continue;

    beepCard();

    if (checkUID(mfrc522.uid.uidByte, mfrc522.uid.size)) {
      showTwoLine(F("Card OK!"), F("Enter PIN"));

      if (askPassword()) {
        beepSuccess();
        accessGranted();
      } else {
        showTwoLine(F("WRONG"), F("PIN :("));
        beepError();
        delay(2000);
      }
    } else {
      showTwoLine(F("WRONG"), F("CARD :("));
      beepError();
      delay(2000);
    }

    mfrc522.PICC_HaltA();
    resetSystem();
    return;
  }

  showTwoLine(F("TIMEOUT"), F("Try again"));
  beepError();
  delay(2000);
  resetSystem();
}

// ========================================
bool askPassword() {
  String input = "";
  unsigned long startTime = millis();

  while (millis() - startTime < 10000) {
    char key = keypad.getKey();
    if (!key) continue;

    beepKey();

    if (key == '#') {
      // Compare against PROGMEM password
      char pwd[10];
      strcpy_P(pwd, masterPassword);
      return (input == String(pwd));
    } else if (key == '*') {
      input = "";
    } else {
      input += key;
    }

    display.clearDisplay();
    display.setTextColor(WHITE);
    display.setTextSize(2);
    display.setCursor(0, 5);
    display.print(F("PIN:"));

    display.setCursor(0, 35);
    for (unsigned int i = 0; i < input.length(); i++) {
      display.print(F("*"));   // ✅ no String object created
    }
    display.display();
  }

  return false;
}

// =======================================
void accessGranted() {
  showTwoLine(F("ACCESS"), F("GRANTED :)"));
  myServo.write(90);
  delay(4000);
  myServo.write(0);
}

bool checkUID(byte *scan, byte size) {
  if (size != 4) return false;
  for (byte i = 0; i < size; i++) {
    if (scan[i] != authorizedUID[i]) return false;
  }
  return true;
}

// ============================================================
// showTwoLine now takes F() strings directly
// ============================================================
void showTwoLine(const __FlashStringHelper* line1,
                 const __FlashStringHelper* line2) {
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(2);
  display.setCursor(0, 8);
  display.println(line1);
  display.setCursor(0, 36);
  display.println(line2);
  display.display();
}

void resetSystem() {
  myServo.write(0);
  showTwoLine(F("LOOK AT"), F("CAMERA"));
  mfrc522.PICC_HaltA();
}

// ===========================================
void beepKey()   { tone(BUZZER, 2000, 80); }
void beepCard()  { tone(BUZZER, 1000, 150); }

void welcomeBeep() {
  tone(BUZZER, 2000, 100); delay(150);
  tone(BUZZER, 1500, 100); delay(150);
  tone(BUZZER, 2000, 100); delay(200);
}

void beepSuccess() {
  tone(BUZZER, 1500, 100); delay(150);
  tone(BUZZER, 2000, 150); delay(150);
  tone(BUZZER, 1500, 100); delay(150);
  tone(BUZZER, 2000, 150);
}

void beepError() {
  tone(BUZZER, 400, 300); delay(350);
  tone(BUZZER, 300, 300);
}