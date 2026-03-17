from PySide6.QtWidgets import QCheckBox, QApplication, QLineEdit, QWidget, QPushButton, QVBoxLayout, QSlider, QLabel
from PySide6.QtCore import QTimer, Qt
import sys
import json
import os
from Main import start_monitoring, stop_monitoring, set_threshold, set_webhook, set_record_video
import threading


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Audio Monitor")
        self.setGeometry(100, 100, 300, 250)

        # UI elements
        self.label = QLabel("Status: Idle")

        self.start_btn = QPushButton("Start Listening")
        self.stop_btn = QPushButton("Stop")

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(100)
        self.slider.setValue(25)
        self.video_checkbox = QCheckBox("Record video")
        self.video_checkbox.setChecked(True)  # default ON

        self.threshold_label = QLabel("Sensitivity: 0.25")

        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText("Enter Discord Webhook URL")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.webhook_input)
        layout.addWidget(self.video_checkbox)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.slider)

        self.setLayout(layout)

        # Connections
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.slider.valueChanged.connect(self.update_threshold)
        self.webhook_input.editingFinished.connect(self.apply_webhook)
        self.video_checkbox.stateChanged.connect(self.toggle_video)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(200)

        # Load saved settings AFTER creating UI
        self.load_settings()

    def start(self):
        self.label.setText("Status: Listening...")
        self.thread = threading.Thread(target=start_monitoring)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.label.setText("Status: Stopped")
        stop_monitoring()

    def update_ui(self):
        try:
            from Main import current_volume
            self.label.setText(f"Volume: {current_volume:.3f}")
        except:
            pass

    def update_threshold(self, value):
        threshold = value / 100
        set_threshold(threshold)
        self.threshold_label.setText(f"Sensitivity: {threshold:.2f} ({value}%)")

    def save_settings(self):
        data = {
            "webhook": self.webhook_input.text()
        }
        with open("settings.json", "w") as f:
            json.dump(data, f)

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                data = json.load(f)
                webhook = data.get("webhook", "")
                self.webhook_input.setText(webhook)
                set_webhook(webhook)

    def apply_webhook(self):
        url = self.webhook_input.text()
        set_webhook(url)
        self.save_settings()
    def toggle_video(self, state):
        enabled = state == 2
        set_record_video(enabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
