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

// SG90 rotacion continua
#define SERVO_DETENIDO   90
#define SERVO_SUBE       0
#define SERVO_BAJA       180

// Tiempos de la pluma — ajusta segun tu servo
#define TIEMPO_SUBIR   600
#define TIEMPO_BAJAR   600
#define TIEMPO_ESPERA  3000

MFRC522 rfid1(SS_PIN_1, RST_PIN_1);
MFRC522 rfid2(SS_PIN_2, RST_PIN_2);

Servo servoEntrada;
Servo servoSalida;

<<<<<<< HEAD
=======
// Anti-duplicados
>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca
String ultimoUID = "";
unsigned long ultimoTiempoUID = 0;
#define BLOQUEO_UID 3000

<<<<<<< HEAD
=======
// Cache modo registro — 8 seg para no hacer peticion extra innecesaria
>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca
bool modoRegistro = false;
unsigned long ultimoCheckRegistro = 0;
#define INTERVALO_CHECK 8000

<<<<<<< HEAD
=======
// Heartbeat cada 5 seg para deteccion rapida de emergencia
>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca
unsigned long ultimoHeartbeat = 0;
#define INTERVALO_HEARTBEAT 5000

<<<<<<< HEAD
=======
String estadoEmergencia = "";

// Alarma de emergencia sin bloquear el loop
unsigned long ultimoPitidoEmergencia = 0;
#define INTERVALO_PITIDO 2500   // cada 2.5 seg — da tiempo al patron SOS completo

// ─────────────────────────────────────────
//  SETUP
// ─────────────────────────────────────────

>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca
void setup() {
  Serial.begin(115200);
  SPI.begin();

  rfid1.PCD_Init();
  rfid2.PCD_Init();

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO,  OUTPUT);
  pinMode(BUZZER,    OUTPUT);

  // Inicializar servos detenidos y soltar señal
  servoEntrada.attach(SERVO_ENTRADA_PIN);
  servoSalida.attach(SERVO_SALIDA_PIN);
  servoEntrada.write(SERVO_DETENIDO);
  servoSalida.write(SERVO_DETENIDO);
  delay(500);
  servoEntrada.detach();
  servoSalida.detach();

  // LED rojo al arrancar
  digitalWrite(LED_ROJO, HIGH);
  delay(300);
  digitalWrite(LED_ROJO, LOW);

  Serial.println("Conectando a WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nWiFi OK — IP: " + WiFi.localIP().toString());

  // Parpadeo verde = listo
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_VERDE, HIGH);
    delay(200);
    digitalWrite(LED_VERDE, LOW);
    delay(200);
  }

  enviarHeartbeat();
}

// ─────────────────────────────────────────
//  LEER UID
// ─────────────────────────────────────────

String leerUID(MFRC522 &rfid) {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

<<<<<<< HEAD
=======
// ─────────────────────────────────────────
//  ANTI-DUPLICADO
// ─────────────────────────────────────────

>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca
bool esDuplicado(String uid) {
  if (uid == ultimoUID && (millis() - ultimoTiempoUID < BLOQUEO_UID)) {
    return true;
  }
  ultimoUID = uid;
  ultimoTiempoUID = millis();
  return false;
}

<<<<<<< HEAD
=======
// ─────────────────────────────────────────
//  HEARTBEAT
// ─────────────────────────────────────────
>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca

void enviarHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/nodo/heartbeat");
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<128> doc;
  doc["id_nodo"]  = ID_NODO;
  doc["ip_local"] = WiFi.localIP().toString();
  String body;
  serializeJson(doc, body);

  int code = http.POST(body);

  if (code == 200) {
    StaticJsonDocument<200> res;
    deserializeJson(res, http.getString());
    String nueva = res["emergencia"].as<String>();

    if (nueva != estadoEmergencia) {
      Serial.println(">>> Emergencia: '" + estadoEmergencia + "' -> '" + nueva + "'");
    }

    estadoEmergencia = nueva;
    Serial.println("Heartbeat OK — emergencia: '" + estadoEmergencia + "'");
  } else {
    Serial.println("Heartbeat error: " + String(code));
  }

  http.end();
}

// ─────────────────────────────────────────
//  MODO REGISTRO
// ─────────────────────────────────────────

bool obtenerModoRegistro() {
  if (millis() - ultimoCheckRegistro < INTERVALO_CHECK) {
    return modoRegistro;
  }
  ultimoCheckRegistro = millis();
  if (WiFi.status() != WL_CONNECTED) return false;

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

<<<<<<< HEAD
=======
// ─────────────────────────────────────────
//  REGISTRAR UID
// ─────────────────────────────────────────
>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca

void registrarUID(String uid) {
  digitalWrite(BUZZER, HIGH);
  delay(80);
  digitalWrite(BUZZER, LOW);

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
    Serial.println("UID registrado: " + uid);
  } else {
    errorServidor();
  }
  http.end();
}

<<<<<<< HEAD
=======
// ─────────────────────────────────────────
//  VERIFICAR ACCESO
// ─────────────────────────────────────────

>>>>>>> d01a58c2636d719ca5cbc2675cb85b66f37385ca
void verificarAcceso(String uid, String tipo) {
  HTTPClient http;
  http.begin(String(SERVER_URL) + "/acceso/verificar");
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<150> doc;
  doc["uid_rfid"]    = uid;
  doc["tipo_evento"] = tipo;
  doc["id_nodo"]     = ID_NODO;
  String body;
  serializeJson(doc, body);

  int code = http.POST(body);

  if (code == 200) {
    StaticJsonDocument<256> res;
    deserializeJson(res, http.getString());

    if (res["permitido"]) {
      Serial.println("Permitido: " + res["nombre"].as<String>());
      accesoPermitido(tipo);
    } else {
      Serial.println("Denegado: " + res["motivo"].as<String>());
      accesoDenegado();
    }
  } else {
    Serial.println("Error servidor: " + String(code));
    errorServidor();
  }
  http.end();
}

// ─────────────────────────────────────────
//  MOVER PLUMA — sube, espera, baja
// ─────────────────────────────────────────

void moverPluma(Servo &servo, int pin) {
  servo.attach(pin);

  Serial.println("Pluma subiendo...");
  servo.write(SERVO_SUBE);
  delay(TIEMPO_SUBIR);
  servo.write(SERVO_DETENIDO);

  Serial.println("Pluma abierta — esperando...");
  delay(TIEMPO_ESPERA);

  Serial.println("Pluma bajando...");
  servo.write(SERVO_BAJA);
  delay(TIEMPO_BAJAR);
  servo.write(SERVO_DETENIDO);
  delay(200);

  servo.detach();
  Serial.println("Pluma cerrada.");
}

// ─────────────────────────────────────────
//  ACCESO PERMITIDO
// ─────────────────────────────────────────

void accesoPermitido(String tipo) {
  digitalWrite(LED_VERDE, HIGH);

  digitalWrite(BUZZER, HIGH);
  delay(200);
  digitalWrite(BUZZER, LOW);

  if (tipo == "entrada") {
    moverPluma(servoEntrada, SERVO_ENTRADA_PIN);
  } else {
    moverPluma(servoSalida, SERVO_SALIDA_PIN);
  }

  digitalWrite(LED_VERDE, LOW);
}

// ─────────────────────────────────────────
//  INDICADORES
// ─────────────────────────────────────────

void accesoDenegado() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(LED_ROJO, HIGH);
    digitalWrite(BUZZER,   HIGH);
    delay(150);
    digitalWrite(LED_ROJO, LOW);
    digitalWrite(BUZZER,   LOW);
    delay(100);
  }
}

void errorServidor() {
  digitalWrite(LED_ROJO, HIGH);
  digitalWrite(BUZZER,   HIGH);
  delay(500);
  digitalWrite(LED_ROJO, LOW);
  digitalWrite(BUZZER,   LOW);
}

// ─────────────────────────────────────────
//  MANEJO DE EMERGENCIA
//  lockdown   → patron SOS  (3 cortos + 3 largos + 3 cortos)
//  evacuacion → sirena rapida (8 pulsos muy cortos)
// ─────────────────────────────────────────

void manejarEmergencia() {

  if (estadoEmergencia == "lockdown") {
    if (servoEntrada.attached()) servoEntrada.detach();
    if (servoSalida.attached())  servoSalida.detach();

    if (millis() - ultimoPitidoEmergencia >= INTERVALO_PITIDO) {
      ultimoPitidoEmergencia = millis();

      // 3 pitidos CORTOS
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_ROJO, HIGH);
        digitalWrite(BUZZER,   HIGH);
        delay(100);
        digitalWrite(LED_ROJO, LOW);
        digitalWrite(BUZZER,   LOW);
        delay(80);
      }

      delay(150);

      // 3 pitidos LARGOS
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_ROJO, HIGH);
        digitalWrite(BUZZER,   HIGH);
        delay(300);
        digitalWrite(LED_ROJO, LOW);
        digitalWrite(BUZZER,   LOW);
        delay(80);
      }

      delay(150);

      // 3 pitidos CORTOS
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_ROJO, HIGH);
        digitalWrite(BUZZER,   HIGH);
        delay(100);
        digitalWrite(LED_ROJO, LOW);
        digitalWrite(BUZZER,   LOW);
        delay(80);
      }
    }

  } else if (estadoEmergencia == "evacuacion") {
    if (servoEntrada.attached()) servoEntrada.detach();

    if (!servoSalida.attached()) {
      servoSalida.attach(SERVO_SALIDA_PIN);
      servoSalida.write(SERVO_SUBE);
      Serial.println("Evacuacion: pluma salida abierta");
    }

    // Sirena rapida — 8 pulsos muy cortos cada 600ms
    if (millis() - ultimoPitidoEmergencia >= 600) {
      ultimoPitidoEmergencia = millis();

      for (int i = 0; i < 8; i++) {
        digitalWrite(BUZZER, HIGH);
        delay(40);
        digitalWrite(BUZZER, LOW);
        delay(30);
      }
    }
  }
}

// ─────────────────────────────────────────
//  LOOP PRINCIPAL
// ─────────────────────────────────────────

void loop() {

  // Heartbeat cada 5 segundos
  if (millis() - ultimoHeartbeat >= INTERVALO_HEARTBEAT) {
    enviarHeartbeat();
    ultimoHeartbeat = millis();
  }

  // Emergencia activa — manejar y NO procesar tarjetas
  if (estadoEmergencia == "lockdown" || estadoEmergencia == "evacuacion") {
    manejarEmergencia();
    return;
  }

  // Modo normal — servos sueltos
  if (servoEntrada.attached()) servoEntrada.detach();
  if (servoSalida.attached())  servoSalida.detach();

  // Lector 1 — ENTRADA
  if (rfid1.PICC_IsNewCardPresent() && rfid1.PICC_ReadCardSerial()) {
    String uid = leerUID(rfid1);
    rfid1.PICC_HaltA();
    rfid1.PCD_StopCrypto1();

    if (esDuplicado(uid)) return;

    if (obtenerModoRegistro()) {
      registrarUID(uid);
    } else {
      verificarAcceso(uid, "entrada");
    }
    delay(500);   // reducido de 1000 a 500ms
  }

  // Lector 2 — SALIDA
  if (rfid2.PICC_IsNewCardPresent() && rfid2.PICC_ReadCardSerial()) {
    String uid = leerUID(rfid2);
    rfid2.PICC_HaltA();
    rfid2.PCD_StopCrypto1();

    if (esDuplicado(uid)) return;

    if (obtenerModoRegistro()) {
      registrarUID(uid);
    } else {
      verificarAcceso(uid, "salida");
    }
    delay(500);   // reducido de 1000 a 500ms
  }
}