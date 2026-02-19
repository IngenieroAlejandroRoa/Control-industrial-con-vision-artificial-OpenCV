// Pines de solenoides
const int solA = 2;
const int solB = 3;
const int solC = 4;

// Pines de interruptores
const int startPin1 = 5;
const int startPin2 = 6;
const int stopPin1  = 7;
const int stopPin2  = 8;

// Variables de control
int stepIndex = 0;
unsigned long lastMillis = 0;
unsigned long stepDelay = 2000;

// Estados de solenoides
bool estadoSolA = true;
bool estadoSolB = true;
bool estadoSolC = true;

// Estados lógicos
bool botonesListos = false;
bool arranqueSolicitado = false;
bool enEjecucion = false;
bool emergenciaActiva = false;

// Variables recibidas por Serial
bool estadoH = false;
bool estadoS = false;

// Estado del ciclo actual
bool cicloActualEnCurso = false;

// Control de espera S1
bool esperandoS1 = false;
bool alternarA = false;

// ⭐ NUEVO: Control de espera S0
bool esperandoS0 = false;
bool alternarC = false;

// Secuencia visual
String secuenciaActual = "";

void setup() {
  pinMode(solA, OUTPUT);
  pinMode(solB, OUTPUT);
  pinMode(solC, OUTPUT);

  digitalWrite(solA, HIGH);
  digitalWrite(solB, HIGH);
  digitalWrite(solC, HIGH);

  pinMode(startPin1, INPUT_PULLUP);
  pinMode(startPin2, INPUT_PULLUP);
  pinMode(stopPin1, INPUT_PULLUP);
  pinMode(stopPin2, INPUT_PULLUP);

  Serial.begin(9600);
}

void loop() {
  bool startOn = (digitalRead(startPin1) == LOW);
  bool stopOn  = (digitalRead(stopPin1) == LOW);

  botonesListos = startOn && !stopOn;

  if (stopOn) {
    if (!emergenciaActiva) Serial.println("EMERGENCIA: ejecución congelada");
    emergenciaActiva = true;
    enEjecucion = false;
  }

  // ---- SERIAL ----
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "H1") { estadoH = true; Serial.println("H habilitado"); }
    else if (comando == "H0") { estadoH = false; Serial.println("H deshabilitado"); }
    else if (comando == "S1") { estadoS = true; Serial.println("S1 recibido"); }
    else if (comando == "S0") { estadoS = false; Serial.println("S0 recibido"); }

    else if (comando == "start") {
      if (botonesListos && estadoH) {
        if (emergenciaActiva) {
          emergenciaActiva = false;
          Serial.println("Emergencia liberada");
        }
        arranqueSolicitado = true;
        enEjecucion = true;
        cicloActualEnCurso = true;
        Serial.println("START OK");
      } else Serial.println("START rechazado");
    }

    else if (comando == "stop") {
      arranqueSolicitado = false;
      enEjecucion = false;
      cicloActualEnCurso = false;
      detenerTodo();
      stepIndex = 0;
      secuenciaActual = "";
      Serial.println("STOP");
    }

    else if (comando == "stopE") {
      Serial.println("STOP EMERGENCIA");
      emergenciaActiva = true;
      enEjecucion = false;
    }
  }

  if (emergenciaActiva) return;

  if (!botonesListos || (!arranqueSolicitado && !cicloActualEnCurso)) {
    enEjecucion = false;
    cicloActualEnCurso = false;
    detenerTodo();
    stepIndex = 0;
    secuenciaActual = "";
    return;
  }

  if (enEjecucion && (millis() - lastMillis >= stepDelay)) {
    lastMillis = millis();
    ejecutarPaso(stepIndex);

    if (!esperandoS1 && !esperandoS0) stepIndex++;

    if (stepIndex > 5) {
      Serial.println("✅ SECUENCIA COMPLETA");
      Serial.println("Secuencia final: " + secuenciaActual);
      stepIndex = 0;
      secuenciaActual = "";
      cicloActualEnCurso = false;
      if (!estadoH) arranqueSolicitado = false;
    }
  }
}

// -------- FUNCIONES --------

void detenerTodo() {
  setSolenoide(solA, estadoSolA, true, 'A');
  setSolenoide(solB, estadoSolB, true, 'B');
  setSolenoide(solC, estadoSolC, true, 'C');
}

void setSolenoide(int pin, bool &estadoActual, bool nuevoEstado, char letra) {
  if (estadoActual != nuevoEstado) {
    digitalWrite(pin, nuevoEstado ? HIGH : LOW);
    estadoActual = nuevoEstado;
    Serial.print(letra);
    if (!nuevoEstado) Serial.println("ON");
    else Serial.println("OFF");
  }
}

void ejecutarPaso(int paso) {

  // 🛑 ⭐ Esperando S1 después de A+
  if (esperandoS1) {
    if (estadoS) {
      esperandoS1 = false;
      Serial.println("S1 ✅ Continuar");
      return;
    }
    if (alternarA) setSolenoide(solA, estadoSolA, true, 'A');
    else setSolenoide(solA, estadoSolA, false, 'A');
    alternarA = !alternarA;
    Serial.println("Esperando S1 en A");
    return;
  }

  // 🛑 ⭐ Esperando S0 después de C+
  if (esperandoS0) {
    if (!estadoS) {
      esperandoS0 = false;
      Serial.println("S0 ✅ Terminar secuencia");
      return;
    }
    if (alternarC) setSolenoide(solC, estadoSolC, true, 'C'); // C-
    else setSolenoide(solC, estadoSolC, false, 'C'); // C+
    alternarC = !alternarC;
    Serial.println("Esperando S0 en C");
    return;
  }

  switch (paso) {

    case 0: setSolenoide(solA, estadoSolA, false, 'A'); secuenciaActual = "A+"; if (!estadoS) { esperandoS1 = true; alternarA = true; Serial.println("Esperando S1"); } break;
    case 1: setSolenoide(solB, estadoSolB, false, 'B'); secuenciaActual += "B+"; break;
    case 2: setSolenoide(solB, estadoSolB, true, 'B');  secuenciaActual += "B-"; break;
    case 3: setSolenoide(solA, estadoSolA, true, 'A');  secuenciaActual += "A-"; break;

    case 4:
      setSolenoide(solC, estadoSolC, false, 'C');  // C+
      secuenciaActual += "C+";

      // ⭐ Nuevo punto de control
      if (estadoS) {
        esperandoS0 = true;
        alternarC = true;
        Serial.println("Esperando S0 para terminar");
      }
      break;

    case 5:
      setSolenoide(solC, estadoSolC, true, 'C'); // C-
      secuenciaActual += "C-";
      break;
  }

  Serial.println(secuenciaActual);
}
