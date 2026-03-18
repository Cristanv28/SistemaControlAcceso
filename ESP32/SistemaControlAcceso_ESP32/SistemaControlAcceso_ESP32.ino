#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configuración WiFi
#define WIFI_SSID     "Totalplay-7"
#define WIFI_PASSWORD ""

// URL del servidor 
#define SERVER_URL "https://acceso-universitario-api-production.up.railway.app"
#define ID_NODO 1

// Pines RC522
#define SS_PIN_1  5   // ENTRADA
#define RST_PIN_1 22

#define SS_PIN_2  21  // SALIDA
#define RST_PIN_2 4

// Pines LEDs y Buzzer
#define LED_VERDE 15
#define LED_ROJO  2
#define BUZZER    14

MFRC522 rfid1(SS_PIN_1, RST_PIN_1);
MFRC522 rfid2(SS_PIN_2, RST_PIN_2);

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid1.PCD_Init();
  rfid2.PCD_Init();

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO,  OUTPUT);
  pinMode(BUZZER,    OUTPUT);

  // Indicador de arranque
  digitalWrite(LED_ROJO, HIGH);
  delay(300);
  digitalWrite(LED_ROJO, LOW);

  // Conectar WiFi
  Serial.println("Conectando a WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
  Serial.println("IP: " + WiFi.localIP().toString());

  // Parpadeo verde = listo
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_VERDE, HIGH);
    delay(200);
    digitalWrite(LED_VERDE, LOW);
    delay(200);
  }
}

//Leer UID 
String leerUID(MFRC522 &rfid) {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

//Verificar acceso con el servidor
void verificarAcceso(String uid, String tipoEvento) {
  Serial.println("─────────────────────────");
  Serial.println("UID: " + uid);
  Serial.println("Evento: " + tipoEvento);

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Sin WiFi");
    errorSinWifi();
    return;
  }

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/acceso/verificar");
  http.addHeader("Content-Type", "application/json");


  StaticJsonDocument<200> doc;
  doc["uid_rfid"]    = uid;
  doc["tipo_evento"] = tipoEvento;
  doc["id_nodo"]     = ID_NODO;
  String body;
  serializeJson(doc, body);

  int httpCode = http.POST(body);
  Serial.println("HTTP Codigo: " + String(httpCode));

  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("Respuesta: " + response);

    StaticJsonDocument<200> res;
    deserializeJson(res, response);

    bool permitido = res["permitido"];

    if (permitido) {
      String nombre = res["nombre"].as<String>();
      String control = res["numero_control"].as<String>();
      Serial.println(" oermitido: " + nombre + " (" + control + ")");
      accesoPermitido();
    } else {
      String motivo = res["motivo"].as<String>();
      Serial.println(" denegado: " + motivo);
      accesoDenegado();
    }
  } else {
    Serial.println(" Error servidor: " + String(httpCode));
    errorServidor();
  }

  http.end();
}

//Indicadores 
void accesoPermitido() {
  digitalWrite(LED_VERDE, HIGH);
  tone(BUZZER, 1000, 200);
  delay(1500);
  digitalWrite(LED_VERDE, LOW);
}

void accesoDenegado() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_ROJO, HIGH);
    tone(BUZZER, 300, 150);
    delay(300);
    digitalWrite(LED_ROJO, LOW);
    delay(150);
  }
}

void errorServidor() {
  digitalWrite(LED_ROJO, HIGH);
  tone(BUZZER, 200, 1000);
  delay(1000);
  digitalWrite(LED_ROJO, LOW);
}

void errorSinWifi() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_ROJO, HIGH);
    delay(100);
    digitalWrite(LED_ROJO, LOW);
    delay(100);
  }
}

// Loop principal 
void loop() {
  // Lector 1 - ENTRADA
  if (rfid1.PICC_IsNewCardPresent() && rfid1.PICC_ReadCardSerial()) {
    String uid = leerUID(rfid1);
    verificarAcceso(uid, "entrada");
    rfid1.PICC_HaltA();
    rfid1.PCD_StopCrypto1();
    delay(2000);
  }

  // Lector 2 - SALIDA
  if (rfid2.PICC_IsNewCardPresent() && rfid2.PICC_ReadCardSerial()) {
    String uid = leerUID(rfid2);
    verificarAcceso(uid, "salida");
    rfid2.PICC_HaltA();
    rfid2.PCD_StopCrypto1();
    delay(2000);
  }
}
