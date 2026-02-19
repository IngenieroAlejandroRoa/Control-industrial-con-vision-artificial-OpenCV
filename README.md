# Control Industrial con Vision Artificial - OpenCV

Sistema de automatización y control industrial para máquina selladora de cajas utilizando Python, OpenCV y Arduino Nano. Implementa visión artificial en tiempo real para supervisión del proceso y control de solenoides mediante comunicación serial, integrando una interfaz gráfica para operación y monitoreo.

## Descripción del Proyecto

Este sistema integra visión artificial con control industrial para automatizar una máquina selladora de cajas. La solución combina procesamiento de imágenes en tiempo real con control secuencial de solenoides, permitiendo la detección automática de cajas en estaciones de carga y sellado, así como la gestión del ciclo de trabajo de la máquina.

## Características Principales

- **Visión Artificial en Tiempo Real**: Detección de cajas mediante análisis de color en espacio HSV
- **Control de Solenoides**: Gestión de 3 solenoides (A, B, C) con secuencia automatizada
- **Interfaz Gráfica Moderna**: Panel de control desarrollado con PyQt6 con diseño oscuro profesional
- **Comunicación Serial**: Sincronización bidireccional entre Python y Arduino
- **Seguridad**: Sistema de parada de emergencia y control por botones físicos
- **Monitoreo Visual**: Visualización de secuencia de proceso y estado de solenoides
- **Detección en Dos Zonas**: ROI (Región de Interés) para estación de carga y sellado

## Arquitectura del Sistema

### Hardware
- **Microcontrolador**: Arduino Nano
- **Cámara**: Cámara USB compatible con OpenCV
- **Solenoides**: 3 solenoides neumáticos
- **Botones**: 2 botones de inicio, 2 botones de parada/emergencia
- **Comunicación**: USB Serial (9600 baudios)

### Software
- **Python 3.x**: Procesamiento de visión y GUI
- **OpenCV**: Análisis de imagen y detección
- **PyQt6**: Interfaz gráfica de usuario
- **NumPy**: Procesamiento numérico
- **PySerial**: Comunicación serial
- **Arduino IDE**: Programación del microcontrolador

## Funcionamiento del Sistema

### Detección de Cajas

El sistema utiliza dos regiones de interés (ROI) en el flujo de video:
1. **Estación de Carga**: (260, 145, 25x30 px) - Detección de caja entrante
2. **Estación de Sellado**: (305, 180, 40x50 px) - Detección de caja en sellado

La detección se basa en:
- Conversión del frame a espacio de color HSV
- Rango de detección amarillo: [20, 100, 100] a [35, 255, 255]
- Umbral de detección: >10% de píxeles amarillos en ROI

### Secuencia de Control

El proceso sigue una secuencia de 6 pasos:

1. **A+**: Activación del solenoide A (espera hasta S1)
2. **B+**: Activación del solenoide B
3. **B-**: Desactivación del solenoide B
4. **A-**: Desactivación del solenoide A
5. **C+**: Activación del solenoide C (espera hasta S0)
6. **C-**: Desactivación del solenoide C

### Protocolo de Comunicación Serial

**De Python a Arduino**:
- `start`: Inicia la secuencia automática
- `stop`: Detiene la secuencia
- `stopE`: Parada de emergencia
- `H1`: Habilita sensor de carga
- `H0`: Deshabilita sensor de carga
- `S1`: Caja detectada en sellado
- `S0`: Sin caja en sellado
- `Solenoid [A|B|C]_ON/OFF`: Control manual

**De Arduino a Python**:
- `AON/AOFF`, `BON/BOFF`, `CON/COFF`: Estados de solenoides
- `A+`, `A+B+`, `A+B+B-`, etc.: Progreso de secuencia
- `H habilitado/deshabilitado`: Confirmación de sensor H
- `S1/S0 recibido`: Confirmación de sensor S

## Instalación

### Requisitos

```bash
pip install opencv-python pyqt6 pyserial numpy
```

### Configuración de Hardware

1. **Conexiones Arduino Nano**:
   - Pin 2: Solenoide A
   - Pin 3: Solenoide B
   - Pin 4: Solenoide C
   - Pin 5-6: Botones de inicio (INPUT_PULLUP)
   - Pin 7-8: Botones de parada (INPUT_PULLUP)

2. **Configuración de Cámara**:
   - Conectar cámara USB
   - Modificar `cv2.VideoCapture(1)` si es necesario (0 para cámara predeterminada)

3. **Puerto Serial**:
   - Ajustar puerto en línea 76 del código Python (`COM5` o `/dev/ttyUSB0`)

## Uso

### Carga del Firmware Arduino

```bash
# Abrir Microcontrolador.ino en Arduino IDE
# Seleccionar placa: Arduino Nano
# Seleccionar puerto COM correspondiente
# Cargar el programa
```

### Ejecución de la Aplicación

```bash
python "Control por vision artificial.py"
```

### Operación

1. **Inicio del Sistema**:
   - Presionar botones físicos de inicio
   - Hacer clic en "Start" en la interfaz
   - Verificar detección de caja en estación de carga (H)

2. **Monitoreo**:
   - Visualización en tiempo real de la cámara
   - Indicadores de secuencia de proceso
   - Estados de solenoides con colores

3. **Control Manual**:
   - Botones ON/OFF para cada solenoide
   - Independientes del modo automático

4. **Parada de Emergencia**:
   - Botón físico de emergencia
   - Botón "Emergency Stop" en interfaz
   - Congela ejecución inmediatamente

## Estructura del Código

### Control por vision artificial.py

```
MachineInterface (QWidget)
├── __init__(): Inicialización de GUI y hardware
├── toggle_solenoid(): Control manual de solenoides
├── read_serial(): Lectura y procesamiento de mensajes Arduino
├── start/stop/emergency_stop(): Control del ciclo
├── update_frame(): Procesamiento de visión y detección
└── closeEvent(): Limpieza de recursos
```

### Microcontrolador.ino

```
Variables Globales
├── Estados de solenoides
├── Control de secuencia
└── Flags de sensores

loop()
├── Lectura de botones físicos
├── Procesamiento de comandos serial
├── Control de emergencia
└── Ejecución de secuencia

ejecutarPaso()
├── Lógica de secuencia paso a paso
├── Espera condicional S1 (caja en sellado)
└── Espera condicional S0 (sin caja)
```

## Personalización

### Ajuste de ROI

Modificar en línea 90 del código Python:
```python
self.rectangulos = [(305, 180, 40, 50), (260, 145, 25, 30)]
```

### Ajuste de Detección de Color

Modificar rangos HSV en líneas 91-92:
```python
self.amarillo_bajo = np.array([20, 100, 100])
self.amarillo_alto = np.array([35, 255, 255])
```

### Tiempos de Secuencia

Modificar en línea 15 del código Arduino:
```cpp
unsigned long stepDelay = 2000; // milisegundos
```

## Video de Demostración

Ver `Maquina automatizada.mp4` para observar el sistema en funcionamiento.

## Solución de Problemas

**Cámara no detectada**:
- Verificar índice de cámara (0, 1, 2)
- Confirmar permisos de acceso

**Puerto serial no disponible**:
- Verificar drivers CH340/FTDI
- Comprobar puerto correcto en administrador de dispositivos

**Detección errónea**:
- Ajustar iluminación del área
- Calibrar rangos HSV según color real
- Modificar porcentaje de umbral (línea 364)

**Solenoides no responden**:
- Verificar conexiones físicas
- Comprobar alimentación de solenoides
- Revisar lógica invertida (HIGH = OFF)

## Mejoras Futuras

- Registro de ciclos y estadísticas de producción
- Configuración de parámetros desde GUI
- Múltiples perfiles de detección
- Integración con sistemas SCADA
- Base de datos para trazabilidad
- Alertas y notificaciones automáticas

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## Autor

Proyecto de control industrial con visión artificial desarrollado para automatización de procesos industriales.

## Notas Técnicas

- Los solenoides operan con lógica invertida (HIGH = apagado, LOW = encendido)
- El sistema requiere detección de caja (H1) antes de iniciar ciclo
- La secuencia incluye esperas inteligentes en A+ (hasta S1) y C+ (hasta S0)
- La comunicación serial es asíncrona y no bloqueante
- Los timers de Qt operan a 30ms (video) y 100ms (serial)
