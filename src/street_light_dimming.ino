/*
 * Real-Time Automatic Street Light Dimming System
 * 
 * Features:
 * - Automatic brightness control based on ambient light
 * - Motion detection for increased brightness when pedestrians/vehicles detected
 * - Real-time monitoring and data logging
 * - Energy-efficient PWM dimming
 * 
 * Hardware Required:
 * - ESP32/Arduino Uno
 * - LDR (Light Dependent Resistor)
 * - PIR Motion Sensor (HC-SR501)
 * - LED/Street Light (12V LED strip recommended)
 * - MOSFET (IRF540N) for LED control
 * - 10K Ohm resistor for LDR
 */

// Pin Definitions
#define LDR_PIN 34          // Analog pin for LDR (ESP32: 34, Arduino: A0)
#define PIR_PIN 27          // Digital pin for PIR sensor
#define LED_PIN 25          // PWM pin for LED control
#define LED_CHANNEL 0       // PWM channel (ESP32 only)

// Configuration Constants
#define PWM_FREQ 5000       // PWM frequency in Hz
#define PWM_RESOLUTION 8    // 8-bit resolution (0-255)
#define MIN_BRIGHTNESS 20   // Minimum brightness (0-255)
#define MAX_BRIGHTNESS 255  // Maximum brightness (0-255)
#define MOTION_BRIGHTNESS 255 // Brightness when motion detected
#define MOTION_TIMEOUT 30000  // Time to keep high brightness after motion (ms)

// Thresholds
#define DARK_THRESHOLD 1000   // LDR value for darkness (adjust based on your LDR)
#define TWILIGHT_THRESHOLD 2000 // LDR value for twilight

// Global Variables
int currentBrightness = 0;
unsigned long lastMotionTime = 0;
bool motionDetected = false;
int ambientLight = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(LDR_PIN, INPUT);
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Setup PWM for LED control (ESP32)
  #ifdef ESP32
    ledcSetup(LED_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(LED_PIN, LED_CHANNEL);
  #endif
  
  Serial.println("=== Automatic Street Light Dimming System ===");
  Serial.println("System initialized...");
  delay(2000); // Allow PIR sensor to stabilize
}

void loop() {
  // Read sensors
  ambientLight = analogRead(LDR_PIN);
  motionDetected = digitalRead(PIR_PIN);
  
  // Update motion timer
  if (motionDetected) {
    lastMotionTime = millis();
  }
  
  // Calculate target brightness based on conditions
  int targetBrightness = calculateBrightness();
  
  // Smooth brightness transition
  if (currentBrightness < targetBrightness) {
    currentBrightness += 5;
    if (currentBrightness > targetBrightness) {
      currentBrightness = targetBrightness;
    }
  } else if (currentBrightness > targetBrightness) {
    currentBrightness -= 5;
    if (currentBrightness < targetBrightness) {
      currentBrightness = targetBrightness;
    }
  }
  
  // Apply brightness to LED
  setLEDBrightness(currentBrightness);
  
  // Send real-time data to serial (for monitoring)
  sendDataToSerial();
  
  delay(100); // Update every 100ms
}

int calculateBrightness() {
  // Check if motion was detected recently
  bool recentMotion = (millis() - lastMotionTime) < MOTION_TIMEOUT;
  
  // Daytime - lights off
  if (ambientLight > TWILIGHT_THRESHOLD) {
    return 0;
  }
  
  // Twilight - dim lights
  if (ambientLight > DARK_THRESHOLD) {
    if (recentMotion) {
      return MOTION_BRIGHTNESS;
    }
    return MIN_BRIGHTNESS + (MAX_BRIGHTNESS - MIN_BRIGHTNESS) / 3;
  }
  
  // Night time
  if (recentMotion) {
    return MOTION_BRIGHTNESS;
  }
  
  // Night time without motion - medium brightness
  return MIN_BRIGHTNESS + (MAX_BRIGHTNESS - MIN_BRIGHTNESS) / 2;
}

void setLEDBrightness(int brightness) {
  brightness = constrain(brightness, 0, 255);
  
  #ifdef ESP32
    ledcWrite(LED_CHANNEL, brightness);
  #else
    analogWrite(LED_PIN, brightness);
  #endif
}

void sendDataToSerial() {
  // Send data in CSV format for easy parsing
  Serial.print(millis());
  Serial.print(",");
  Serial.print(ambientLight);
  Serial.print(",");
  Serial.print(currentBrightness);
  Serial.print(",");
  Serial.print(motionDetected ? 1 : 0);
  Serial.print(",");
  Serial.println((millis() - lastMotionTime) < MOTION_TIMEOUT ? 1 : 0);
}

// Function to print formatted data (for debugging)
void printStatus() {
  Serial.println("\n--- Street Light Status ---");
  Serial.print("Ambient Light: ");
  Serial.println(ambientLight);
  Serial.print("Current Brightness: ");
  Serial.print(currentBrightness);
  Serial.println("/255");
  Serial.print("Motion Detected: ");
  Serial.println(motionDetected ? "YES" : "NO");
  Serial.print("Power Consumption: ");
  Serial.print((currentBrightness * 100.0) / 255.0);
  Serial.println("%");
  Serial.println("---------------------------\n");
}
