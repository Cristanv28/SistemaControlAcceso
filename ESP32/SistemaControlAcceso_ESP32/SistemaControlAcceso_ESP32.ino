#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

#define WIFI_SSID     "ZTE Axon 70"
#define WIFI_PASSWORD "Nolas1128."

#define SERVER_URL "https://acceso-universitario-api-production.up.railway.app"
#define ID_NODO 1

#define SS_PIN_1  5
#define RST_PIN_1 22
#define SS_PIN_2  21
#define RST_PIN_2 4

#define LED_VERDE   33
#define LED_ROJO    32
#define BUZZER      13

#define SERVO_ENTRADA_PIN 26
#define SERVO_SALIDA_PIN  27

#define SERVO_CERRADO 0
#define SERVO_ABIERTO 90

MFRC522 rfid1(SS_PIN_1, RST_PIN_1);
MFRC522 rfid2(SS_PIN_2, RST_PIN_2);

Servo servoEntrada;
Servo servoSalida;

String ultimoUID = "";
unsigned long ultimoTiempoUID = 0;
#define BLOQUEO_UID 3000

bool modoRegistro = false;
unsigned long ultimoCheck = 0;
#define INTERVALO_CHECK 4000

unsigned long ultimoHeartbeat = 0;
#define INTERVALO_HEARTBEAT 30000

void setup() {
  Serial.begin(115200);
  SPI.begin();

  rfid1.PCD_Init();
  rfid2.PCD_Init();

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);

  servoEntrada.attach(SERVO_ENTRADA_PIN);
  servoSalida.attach(SERVO_SALIDA_PIN);

  servoEntrada.write(SERVO_CERRADO);
  servoSalida.write(SERVO_CERRADO);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }

  Serial.println("\nWiFi OK");
}

// ─────────────────────────────

String leerUID(MFRC522 &rfid) {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

bool esDuplicado(String uid) {
  if (uid == ultimoUID && (millis() - ultimoTiempoUID < BLOQUEO_UID)) {
    return true;
  }

  ultimoUID = uid;
  ultimoTiempoUID = millis();
  return false;
}


bool obtenerModoRegistro() {
  if (millis() - ultimoCheck < INTERVALO_CHECK) {
    return modoRegistro;
  }

  ultimoCheck = millis();

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/tarjetas/modo-registro");

  int code = http.GET();

  if (code == 200) {
    StaticJsonDocument<200> doc;
    deserializeJson(doc, http.getString());
    modoRegistro = doc["activo"];
  }

  http.end();
  return modoRegistro;
}


void registrarUID(String uid) {

  tone(BUZZER, 1200, 50); // feedback inmediato

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/tarjetas/registrar-uid");
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<100> doc;
  doc["uid_rfid"] = uid;

  String body;
  serializeJson(doc, body);

  int code = http.POST(body);

  if (code == 200) {
    digitalWrite(LED_VERDE, HIGH);
    delay(300);
    digitalWrite(LED_VERDE, LOW);
  } else {
    errorServidor();
  }

  http.end();
}

void verificarAcceso(String uid, String tipo) {

  tone(BUZZER, 1000, 50); // respuesta inmediata

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/acceso/verificar");
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<150> doc;
  doc["uid_rfid"] = uid;
  doc["tipo_evento"] = tipo;
  doc["id_nodo"] = ID_NODO;

  String body;
  serializeJson(doc, body);

  int code = http.POST(body);

  if (code == 200) {
    StaticJsonDocument<200> res;
    deserializeJson(res, http.getString());

    if (res["permitido"]) {
      accesoPermitido(tipo);
    } else {
      accesoDenegado();
    }
  } else {
    errorServidor();
  }

  http.end();
}

// ─────────────────────────────

void accesoPermitido(String tipo) {

  digitalWrite(LED_VERDE, HIGH);

  if (tipo == "entrada") {
    servoEntrada.write(SERVO_ABIERTO);
  } else {
    servoSalida.write(SERVO_ABIERTO);
  }

  delay(800);

  servoEntrada.write(SERVO_CERRADO);
  servoSalida.write(SERVO_CERRADO);

  digitalWrite(LED_VERDE, LOW);
}

// ─────────────────────────────

void accesoDenegado() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_ROJO, HIGH);
    tone(BUZZER, 300, 100);
    delay(200);
    digitalWrite(LED_ROJO, LOW);
    delay(100);
  }
}

void errorServidor() {
  digitalWrite(LED_ROJO, HIGH);
  tone(BUZZER, 200, 500);
  delay(500);
  digitalWrite(LED_ROJO, LOW);
}

// ─────────────────────────────

void enviarHeartbeat() {
  HTTPClient http;
  http.begin(String(SERVER_URL) + "/nodo/heartbeat");

  StaticJsonDocument<100> doc;
  doc["id_nodo"] = ID_NODO;

  String body;
  serializeJson(doc, body);

  http.POST(body);
  http.end();
}

// ─────────────────────────────

void loop() {

  // Heartbeat
  if (millis() - ultimoHeartbeat > INTERVALO_HEARTBEAT) {
    enviarHeartbeat();
    ultimoHeartbeat = millis();
  }

  // Entrada
  if (rfid1.PICC_IsNewCardPresent() && rfid1.PICC_ReadCardSerial()) {

    String uid = leerUID(rfid1);

    if (esDuplicado(uid)) return;

    if (obtenerModoRegistro()) {
      registrarUID(uid);
    } else {
      verificarAcceso(uid, "entrada");
    }
  }

  // Salida
  if (rfid2.PICC_IsNewCardPresent() && rfid2.PICC_ReadCardSerial()) {

    String uid = leerUID(rfid2);

    if (esDuplicado(uid)) return;

    if (obtenerModoRegistro()) {
      registrarUID(uid);
    } else {
      verificarAcceso(uid, "salida");
    }
  }
}