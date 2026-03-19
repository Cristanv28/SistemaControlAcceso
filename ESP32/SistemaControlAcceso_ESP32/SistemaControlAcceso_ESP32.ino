#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

#define WIFI_SSID     "MEGACABLE-3326_2.4G"
#define WIFI_PASSWORD "Nolas1128C.@"

#define SERVER_URL "https://acceso-universitario-api-production.up.railway.app"
#define ID_NODO 1

#define SS_PIN_1  5
#define RST_PIN_1 22
#define SS_PIN_2  21
#define RST_PIN_2 4

#define LED_VERDE   33
#define LED_ROJO    32
#define LED_NARANJA 25
#define BUZZER      13

#define SERVO_ENTRADA_PIN 26
#define SERVO_SALIDA_PIN  27

#define SERVO_CERRADO 0
#define SERVO_ABIERTO 90

MFRC522 rfid1(SS_PIN_1, RST_PIN_1);
MFRC522 rfid2(SS_PIN_2, RST_PIN_2);

Servo servoEntrada;
Servo servoSalida;

String estadoEmergencia = "";
unsigned long ultimoHeartbeat = 0;
#define INTERVALO_HEARTBEAT 30000

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid1.PCD_Init();
  rfid2.PCD_Init();

  pinMode(LED_VERDE,   OUTPUT);
  pinMode(LED_ROJO,    OUTPUT);
  pinMode(LED_NARANJA, OUTPUT);

  servoEntrada.attach(SERVO_ENTRADA_PIN);
  servoSalida.attach(SERVO_SALIDA_PIN);
  servoEntrada.write(SERVO_CERRADO);
  servoSalida.write(SERVO_CERRADO);

  digitalWrite(LED_ROJO, HIGH);
  delay(300);
  digitalWrite(LED_ROJO, LOW);

  Serial.println("Conectando a WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
  Serial.println("IP: " + WiFi.localIP().toString());

  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_VERDE, HIGH);
    delay(200);
    digitalWrite(LED_VERDE, LOW);
    delay(200);
  }

  enviarHeartbeat();
}

String leerUID(MFRC522 &rfid) {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

void enviarHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/nodo/heartbeat");
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<100> doc;
  doc["id_nodo"]  = ID_NODO;
  doc["ip_local"] = WiFi.localIP().toString();
  String body;
  serializeJson(doc, body);

  int code = http.POST(body);
  if (code == 200) {
    String resp = http.getString();
    StaticJsonDocument<200> res;
    deserializeJson(res, resp);
    estadoEmergencia = res["emergencia"].as<String>();
    Serial.println("Heartbeat OK — emergencia: " + estadoEmergencia);

    bool hayEmergencia = (estadoEmergencia == "lockdown" || estadoEmergencia == "evacuacion");

    if (!hayEmergencia) {
      digitalWrite(LED_NARANJA, LOW);
      digitalWrite(LED_ROJO, LOW);
      digitalWrite(LED_VERDE, LOW);
      servoEntrada.write(SERVO_CERRADO);
      servoSalida.write(SERVO_CERRADO);
    }
  }
  http.end();
}

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
      String nombre  = res["nombre"].as<String>();
      String control = res["numero_control"].as<String>();
      Serial.println("Permitido: " + nombre + " (" + control + ")");
      accesoPermitido(tipoEvento);
    } else {
      String motivo = res["motivo"].as<String>();
      Serial.println("Denegado: " + motivo);
      accesoDenegado();
    }
  } else {
    Serial.println("Error servidor: " + String(httpCode));
    errorServidor();
  }
  http.end();
}

void accesoPermitido(String tipoEvento) {
  digitalWrite(LED_VERDE, HIGH);
  tone(BUZZER, 1000, 200);

  if (tipoEvento == "entrada") {
    servoEntrada.write(SERVO_ABIERTO);
  } else {
    servoSalida.write(SERVO_ABIERTO);
  }

  delay(1500);

  if (tipoEvento == "entrada") {
    servoEntrada.write(SERVO_CERRADO);
  } else {
    servoSalida.write(SERVO_CERRADO);
  }

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

void manejarEmergencia() {
  if (estadoEmergencia == "lockdown") {
    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_NARANJA, HIGH);
    digitalWrite(LED_ROJO, HIGH);
    tone(BUZZER, 800, 100);
    delay(150);
    digitalWrite(LED_NARANJA, LOW);
    digitalWrite(LED_ROJO, LOW);
    delay(150);
  } else if (estadoEmergencia == "evacuacion") {
    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_ROJO, LOW);
    digitalWrite(LED_NARANJA, HIGH);
    tone(BUZZER, 1200, 100);
    delay(150);
    digitalWrite(LED_NARANJA, LOW);
    delay(150);
    servoSalida.write(SERVO_ABIERTO);
    servoEntrada.write(SERVO_CERRADO);
  }
}

void loop() {
  if (millis() - ultimoHeartbeat >= INTERVALO_HEARTBEAT) {
    enviarHeartbeat();
    ultimoHeartbeat = millis();
  }

  if (estadoEmergencia == "lockdown" || estadoEmergencia == "evacuacion") {
    manejarEmergencia();
    return;
  }

  if (rfid1.PICC_IsNewCardPresent() && rfid1.PICC_ReadCardSerial()) {
    String uid = leerUID(rfid1);
    verificarAcceso(uid, "entrada");
    rfid1.PICC_HaltA();
    rfid1.PCD_StopCrypto1();
    delay(2000);
  }

  if (rfid2.PICC_IsNewCardPresent() && rfid2.PICC_ReadCardSerial()) {
    String uid = leerUID(rfid2);
    verificarAcceso(uid, "salida");
    rfid2.PICC_HaltA();
    rfid2.PCD_StopCrypto1();
    delay(2000);
  }
}