#include <WiFiS3.h>
#include <ArduinoJson.h>

// --- WiFi Configuration ---
char ssid[] = "emin";        // Your network SSID (name)
char pass[] = "88888888";    // Your network password
int status = WL_IDLE_STATUS; // The WiFi radio's status

// --- Flask Server Configuration ---
const char* serverHost = "192.168.165.62"; // <<<< IMPORTANT: REPLACE WITH YOUR FLASK SERVER'S IP ADDRESS
const int serverPort = 5000;                     // Port your Flask server is running on

// --- Data Fetching Interval ---
const unsigned long fetchInterval = 10000; // Fetch data every 10 seconds (10000 ms)
unsigned long lastFetchTime = 0;

// --- Relay Pin Definitions ---
const int happyPin = 2;
const int sadPin = 3;
const int neutralPin = 4;
const int angryPin = 5;

// --- Global Variables for API Data ---
unsigned long sprayPeriodMinutes = 0;
unsigned long sprayDurationSeconds = 0;
bool deviceOn = false;
String currentEmotion = "";

// --- Timing Variables for Relays ---
unsigned long sprayPeriodMillis = 0;
unsigned long sprayDurationMillis = 0;
unsigned long lastSprayTimeHappy = 0;
unsigned long lastSprayTimeSad = 0;
unsigned long lastSprayTimeNeutral = 0;
unsigned long lastSprayTimeAngry = 0;

bool isSprayingHappy = false;
bool isSprayingSad = false;
bool isSprayingNeutral = false;
bool isSprayingAngry = false;

unsigned long sprayStartTimeHappy = 0;
unsigned long sprayStartTimeSad = 0;
unsigned long sprayStartTimeNeutral = 0;
unsigned long sprayStartTimeAngry = 0;

WiFiClient client; // WiFiClient moved to global scope for simplicity in this structure

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 5000); // Wait for serial port to connect, with a timeout

  pinMode(happyPin, OUTPUT);
  pinMode(sadPin, OUTPUT);
  pinMode(neutralPin, OUTPUT);
  pinMode(angryPin, OUTPUT);
  deactivateAllRelays(); // Relays are active-LOW

  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }

  connectToWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Attempting to reconnect...");
    connectToWiFi();
    lastFetchTime = millis(); // Reset fetch timer to avoid immediate fetch after reconnect
    return; // Skip the rest of the loop until reconnected
  }

  unsigned long currentTime = millis();
  if (currentTime - lastFetchTime >= fetchInterval) {
    lastFetchTime = currentTime;
    fetchDataFromServer();
  }

  // Relay control logic (runs every loop)
  if (!deviceOn) {
    deactivateAllRelays();
    isSprayingHappy = false;
    isSprayingSad = false;
    isSprayingNeutral = false;
    isSprayingAngry = false;
  } else {
    sprayPeriodMillis = sprayPeriodMinutes * 60000UL;
    sprayDurationMillis = sprayDurationSeconds * 1000UL;

    handleEmotionRelay(happyPin, currentEmotion, "Happy", lastSprayTimeHappy, isSprayingHappy, sprayStartTimeHappy);
    handleEmotionRelay(sadPin, currentEmotion, "Sad", lastSprayTimeSad, isSprayingSad, sprayStartTimeSad);
    handleEmotionRelay(neutralPin, currentEmotion, "Neutral", lastSprayTimeNeutral, isSprayingNeutral, sprayStartTimeNeutral);
    handleEmotionRelay(angryPin, currentEmotion, "Angry", lastSprayTimeAngry, isSprayingAngry, sprayStartTimeAngry);
  }
}

void connectToWiFi() {
  Serial.print("Attempting to connect to SSID: ");
  Serial.println(ssid);
  status = WiFi.begin(ssid, pass);
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 30000) { // 30-second timeout
    Serial.print(".");
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi");
    printWifiStatus();
  } else {
    Serial.println("\nFailed to connect to WiFi.");
  }
}

void fetchDataFromServer() {
  Serial.print("\nConnecting to server: ");
  Serial.println(serverHost);

  if (client.connect(serverHost, serverPort)) {
    Serial.println("Connected to server. Sending GET request...");
    // Make an HTTP GET request:
    client.println("GET /device HTTP/1.1");
    client.print("Host: ");
    client.println(serverHost);
    client.println("Connection: close"); // Request server to close connection after response
    client.println(); // End of HTTP request headers

    // Wait for response with a timeout
    unsigned long timeout = millis();
    while (!client.available() && millis() - timeout < 5000) { // 5 second timeout
      delay(10);
    }

    if (!client.available() && client.connected()) {
        Serial.println("No response from server after 5s (still connected)");
        client.stop();
        return;
    }
    if (!client.connected() && !client.available()){
        Serial.println("Client disconnected before response or no data.");
        return;
    }


    // Read the HTTP response
    String responseLine;
    bool jsonStarted = false;
    String jsonPayload = "";

    while (client.connected() || client.available()) {
      if (client.available()) {
        responseLine = client.readStringUntil('\n');
        responseLine.trim(); // Remove \r
        // Serial.println(responseLine); // For debugging headers

        if (responseLine.length() == 0) { // Blank line indicates end of headers
          jsonStarted = true;
          continue;
        }

        if (jsonStarted) {
          jsonPayload += responseLine; // Append lines after headers (this assumes JSON is compact on one line or multiple lines)
                                       // A more robust parser would look for Content-Length
        }
      } else if(!client.connected() && jsonPayload.length() > 0) {
          break; // Connection closed, but we might have read something
      } else if (!client.connected()){
          Serial.println("Client disconnected prematurely.");
          break;
      }
    }
    client.stop(); // Ensure client is stopped

    Serial.print("JSON Payload received: ");
    Serial.println(jsonPayload);

    if (jsonPayload.length() > 0) {
      parseJsonData(jsonPayload);
    } else {
      Serial.println("No JSON payload received or empty response.");
    }

  } else {
    Serial.println("Connection to Flask server failed.");
  }
}

void parseJsonData(String jsonData) {
  DynamicJsonDocument doc(256); // Adjust size as needed
  DeserializationError error = deserializeJson(doc, jsonData);

  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }

  // Your Flask app sends values as strings from the file. Convert them.
  if (doc.containsKey("sprayPeriod")) {
    sprayPeriodMinutes = doc["sprayPeriod"].as<String>().toInt(); // Convert string to int
    Serial.print("sprayPeriod (min): ");
    Serial.println(sprayPeriodMinutes);
  }
  if (doc.containsKey("sprayDuration")) {
    sprayDurationSeconds = doc["sprayDuration"].as<String>().toInt(); // Convert string to int
    Serial.print("sprayDuration (sec): ");
    Serial.println(sprayDurationSeconds);
  }
  if (doc.containsKey("deviceOn")) {
    String deviceOnStr = doc["deviceOn"].as<String>();
    deviceOnStr.toLowerCase(); // Convert to lowercase for consistent check
    deviceOn = (deviceOnStr == "true"); // Check if the string is "true"
    Serial.print("deviceOn: ");
    Serial.println(deviceOn ? "True" : "False");
  }
  if (doc.containsKey("currentEmotion")) {
    currentEmotion = doc["currentEmotion"].as<String>();
    Serial.print("currentEmotion: ");
    Serial.println(currentEmotion);
  }
}

void deactivateAllRelays() {
  digitalWrite(happyPin, HIGH);    // HIGH deactivates an active-LOW relay
  digitalWrite(sadPin, HIGH);
  digitalWrite(neutralPin, HIGH);
  digitalWrite(angryPin, HIGH);
  // Serial.println("All relays DEACTIVATED (set to HIGH)"); // Less verbose during normal operation
}

void printWifiStatus() {
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  long rssi = WiFi.RSSI();
  Serial.print("Signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}

void handleEmotionRelay(int pin, const String& targetEmotion, const char* emotionName, unsigned long& lastSprayTime, bool& isSpraying, unsigned long& sprayStartTime) {
  bool emotionMatches = (currentEmotion == emotionName);

  if (emotionMatches) {
    if (!isSpraying && (millis() - lastSprayTime >= sprayPeriodMillis || lastSprayTime == 0) && sprayPeriodMillis > 0 && sprayDurationMillis > 0) {
      Serial.print("ACTIVATING spray for ");
      Serial.println(emotionName);
      digitalWrite(pin, LOW); // LOW activates an active-LOW relay
      isSpraying = true;
      sprayStartTime = millis();
      lastSprayTime = millis();
    }
  } else {
    if (digitalRead(pin) == LOW || isSpraying) { // If currently active (LOW) or was spraying
      digitalWrite(pin, HIGH); // HIGH deactivates an active-LOW relay
      isSpraying = false;
      // Serial.print(emotionName); // Less verbose
      // Serial.println(" relay DEACTIVATED (emotion changed or not active).");
    }
  }

  if (isSpraying && emotionMatches) {
    if (millis() - sprayStartTime >= sprayDurationMillis) {
      Serial.print("DEACTIVATING spray for ");
      Serial.println(emotionName);
      digitalWrite(pin, HIGH); // HIGH deactivates an active-LOW relay
      isSpraying = false;
    }
  } else if (isSpraying && !emotionMatches) { // If it was spraying but emotion changed
    if (digitalRead(pin) == LOW) { // Check actual pin state
        digitalWrite(pin, HIGH);
        isSpraying = false; // Correct the flag
        // Serial.print("Force DEACTIVATING stray spray for "); // Less verbose
        // Serial.println(emotionName);
    }
  }
}