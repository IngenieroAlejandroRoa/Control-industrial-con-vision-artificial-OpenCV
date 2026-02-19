import sys, time, cv2, serial, numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap


class MachineInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vision Machine Control")
        self.setStyleSheet("""
            QWidget {
                background-color: #0e0a1a;
                color: #d0bfff;
                font-family: 'Segoe UI';
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
                color: #c9aaff;
            }
            QLabel#subtitle {
                font-size: 24px;
                color: #a185ff;
            }
            QLabel.section_title {
                font-size: 18px;
                font-weight: bold;
                color: #d0bfff;
            }
            QPushButton {
                padding: 14px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#start {
                background-color: #a259ff;
                color: white;
            }
            QPushButton#stop {
                background-color: #2e223f;
                color: #aaa;
            }
            QPushButton#emergency {
                background-color: #3b0f16;
                color: #ff4c4c;
            }
            QPushButton#toggle_off {
                background-color: #2e3a44;
                color: white;
                padding: 4px 12px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 11px;
            }
            QPushButton#toggle_on {
                background-color: #00d26a;
                color: black;
                padding: 4px 12px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 11px;
            }
            QFrame#panel {
                background-color: #1a132e;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        self.resize(1000, 800)

        try:
            self.ser = serial.Serial('COM5', 9600)
            time.sleep(2)
        except Exception as e:
            print(f"No se pudo abrir el puerto serial: {e}")
            self.ser = None

        self.previous_carga_state = None  # Track last state
        self.previous_carga_state2 = None  # Track last state
        self.sequence_labels = []
        self.cap = cv2.VideoCapture(1)
        if not self.cap.isOpened():
            print("No se pudo abrir la cámara.")
            sys.exit()

        self.rectangulos = [(305, 180, 40, 50), (260, 145, 25, 30)]
        self.amarillo_bajo = np.array([20, 100, 100])
        self.amarillo_alto = np.array([35, 255, 255])

        title = QLabel("Vision Machine Control")
        title.setObjectName("title")
        subtitle = QLabel("Automated Solenoid Control System")
        subtitle.setObjectName("subtitle")

        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setFixedSize(800, 500)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("color: #9b80ff;")

        camera_panel = QFrame()
        camera_panel.setObjectName("panel")
        camera_layout = QVBoxLayout()
        camera_title = QLabel("Camera View")
        camera_title.setProperty("class", "section_title")
        camera_layout.addWidget(camera_title)
        camera_layout.addWidget(self.camera_label)
        camera_panel.setLayout(camera_layout)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("start")
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("stop")
        self.emergency_btn = QPushButton("❗ Emergency Stop")
        self.emergency_btn.setObjectName("emergency")

        control_panel = QFrame()
        control_panel.setObjectName("panel")
        control_layout = QVBoxLayout()
        control_title = QLabel("Control Panel")
        control_title.setProperty("class", "section_title")
        control_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(control_title)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.emergency_btn)
        control_panel.setLayout(control_layout)

        process_panel = QFrame()
        process_panel.setObjectName("panel")
        process_layout = QVBoxLayout()
        process_title = QLabel("Process Sequence")
        process_title.setProperty("class", "section_title")
        process_layout.addWidget(process_title)

        step_layout = QHBoxLayout()
        steps = ["A+", "B+", "B-", "A-", "C+", "C-"]
        self.sequence_buttons = []
        for i, step in enumerate(steps):
            btn = QPushButton(step)
            btn.setEnabled(False)
            btn.setStyleSheet("""
                background-color: #1a0e2d;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                color: #c084fc;
                border: 1px solid #6a0dad;
            """)
            self.sequence_buttons.append(btn)
            step_layout.addWidget(btn)
            if i < len(steps) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #a285ff; font-size: 18px;")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                step_layout.addWidget(arrow)
        process_layout.addLayout(step_layout)
        process_panel.setLayout(process_layout)

        solenoid_panel = QFrame()
        solenoid_panel.setObjectName("panel")
        solenoid_layout = QVBoxLayout()
        solenoid_title = QLabel("Solenoid Status")
        solenoid_title.setProperty("class", "section_title")
        solenoid_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        solenoid_layout.addWidget(solenoid_title)

        solenoid_grid = QHBoxLayout()
        self.solenoids = {}
        for name in ["Solenoid A", "Solenoid B", "Solenoid C"]:
            box = QVBoxLayout()

            solenoid_label = QLabel(name)
            solenoid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            solenoid_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d0bfff;")

            indicator = QLabel()
            indicator.setFixedSize(80, 80)
            indicator.setStyleSheet("""
                background-color: #100823;
                border: 2px solid #6a0dad;
                border-radius: 10px;
            """)

            btn = QPushButton("OFF")
            btn.setObjectName("toggle_off")
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.clicked.connect(lambda checked, n=name, i=indicator, b=btn: self.toggle_solenoid(n, i, b))

            box.addWidget(solenoid_label)
            box.addWidget(indicator, alignment=Qt.AlignmentFlag.AlignCenter)
            box.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            solenoid_grid.addLayout(box)
            self.solenoids[name] = {"indicator": indicator, "button": btn}
        solenoid_layout.addLayout(solenoid_grid)
        solenoid_panel.setLayout(solenoid_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        mid_layout = QHBoxLayout()
        mid_layout.addWidget(camera_panel)
        right_layout = QVBoxLayout()
        right_layout.addWidget(control_panel)
        mid_layout.addLayout(right_layout)

        main_layout.addLayout(mid_layout)
        main_layout.addWidget(process_panel)
        main_layout.addWidget(solenoid_panel)
        self.setLayout(main_layout)

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.emergency_btn.clicked.connect(self.emergency_stop)

        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.serial_timer = QTimer()
        self.serial_timer.timeout.connect(self.read_serial)
        self.serial_timer.start(100)

    def toggle_solenoid(self, name, indicator, button):
        if button.isChecked():
            indicator.setStyleSheet("""
                background-color: #00d26a;
                border: 2px solid #6a0dad;
                border-radius: 10px;
            """)
            button.setText("ON")
            button.setObjectName("toggle_on")
            button.setStyleSheet("""
                background-color: #00d26a;
                color: black;
                padding: 4px 12px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 11px;
            """)
            if self.ser:
                self.ser.write(f"{name}_ON\n".encode())
        else:
            indicator.setStyleSheet("""
                background-color: #100823;
                border: 2px solid #6a0dad;
                border-radius: 10px;
            """)
            button.setText("OFF")
            button.setObjectName("toggle_off")
            button.setStyleSheet("""
                background-color: #2e3a44;
                color: white;
                padding: 4px 12px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 11px;
            """)
            if self.ser:
                self.ser.write(f"{name}_OFF\n".encode())

    def read_serial(self):
        if self.ser and self.ser.in_waiting:
            try:
                line = self.ser.readline().decode().strip()
                print(f"[Serial] Recibido: {line}")
                mapping = {
                    "AON": "Solenoid A",
                    "AOFF": "Solenoid A",
                    "BON": "Solenoid B",
                    "BOFF": "Solenoid B",
                    "CON": "Solenoid C",
                    "COFF": "Solenoid C",
                }
                if line in mapping:
                    solenoid_name = mapping[line]
                    button = self.solenoids[solenoid_name]["button"]
                    indicator = self.solenoids[solenoid_name]["indicator"]
                    if "ON" in line:
                        if not button.isChecked():
                            button.setChecked(True)
                            self.toggle_solenoid(solenoid_name, indicator, button)
                    elif "OFF" in line:
                        if button.isChecked():
                            button.setChecked(False)
                            self.toggle_solenoid(solenoid_name, indicator, button)

                sequence_combinations = [
                    "A+",
                    "A+B+",
                    "A+B+B-",
                    "A+B+B-A-",
                    "A+B+B-A-C+",
                    "A+B+B-A-C+C-"
                ]
                if line in sequence_combinations:
                    count = line.count("+") + line.count("-")
                    for i, btn in enumerate(self.sequence_buttons):
                        if i < count:
                            btn.setStyleSheet("""
                                background-color: #00d26a;
                                padding: 10px 20px;
                                border-radius: 6px;
                                font-weight: bold;
                                color: black;
                                border: 1px solid #00ff99;
                            """)
                        else:
                            btn.setStyleSheet("""
                                background-color: #1a0e2d;
                                padding: 10px 20px;
                                border-radius: 6px;
                                font-weight: bold;
                                color: #c084fc;
                                border: 1px solid #6a0dad;
                            """)
            except Exception as e:
                print(f"[Error] leyendo serial: {e}")

    def start(self):
        self.running = True
        if self.ser:
            self.ser.write(b"start\n")

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.write(b"stop\n")

        for btn in self.sequence_buttons:
            btn.setStyleSheet("""
                background-color: #1a0e2d;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                color: #c084fc;
                border: 1px solid #6a0dad;
            """)

    def emergency_stop(self):
        self.running = False
        if self.ser:
            self.ser.write(b"stopE\n")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        resultados = []

        for (x, y, w, h) in self.rectangulos:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            roi = hsv[y:y + h, x:x + w]
            mask = cv2.inRange(roi, self.amarillo_bajo, self.amarillo_alto)
            amarillo_pct = (cv2.countNonZero(mask) / (w * h)) * 100
            detectado = 1 if amarillo_pct > 10 else 0
            resultados.append(detectado)
            texto = f"Caja: {detectado}"
            cv2.putText(frame, texto, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if self.running and len(resultados) == 2 and self.ser:
            mensaje = f"Carga: {resultados[1]}, Sellado: {resultados[0]}\n"
            self.ser.write(mensaje.encode("utf-8"))

            # Enviar H1 o H0 en función del estado de Carga
            if self.previous_carga_state != resultados[1]:
                self.previous_carga_state = resultados[1]
                estado = "H1" if resultados[1] == 1 else "H0"
                self.ser.write((estado + "\n").encode("utf-8"))
            
            if self.previous_carga_state2 != resultados[0]:
                self.previous_carga_state2 = resultados[0]
                estado2 = "S1" if resultados[0] == 1 else "S0"
                self.ser.write((estado2 + "\n").encode("utf-8"))

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.camera_label.setPixmap(QPixmap.fromImage(qt_img))

    def closeEvent(self, event):
        print("Cerrando aplicación...")
        self.cap.release()
        if self.ser and self.ser.is_open:
            self.ser.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MachineInterface()
    window.show()
    sys.exit(app.exec())
