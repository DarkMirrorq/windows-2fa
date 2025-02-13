import sys
import requests
import keyboard
import pyotp  # TOTP için gerekli
import qrcode  # QR kodu oluşturmak için gerekli
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QLineEdit, QPushButton, QDialog
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon, QImage, QPixmap

SERVER_URL = "http://IP-ADRESS:3005"
DEVICE_NAME = "PC Name"
TOTP_SECRET = "16 Digit Random String"  # Google Authenticator için önceden belirlenen gizli anahtar

def pil_image_to_qimage(pil_image):
    """Convert a PIL Image to QImage"""
    # PIL görüntüsünü RGBA formatına dönüştür
    pil_image = pil_image.convert("RGBA")
    # Verileri al
    width, height = pil_image.size
    data = pil_image.tobytes("raw", "RGBA")

    # QImage nesnesini oluştur
    q_image = QImage(data, width, height, QImage.Format_RGBA8888)
    return q_image

class TotpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter TOTP Code")
        self.setGeometry(500, 300, 400, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()

        self.label = QLabel("Enter your TOTP code:", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.code_input = QLineEdit(self)
        self.code_input.setPlaceholderText("TOTP Code")
        self.code_input.setStyleSheet("font-size: 24px;")
        self.code_input.setMaxLength(6)
        self.layout.addWidget(self.code_input)

        self.submit_button = QPushButton("Verify", self)
        self.submit_button.clicked.connect(self.verify_totp)
        self.layout.addWidget(self.submit_button)

        self.setLayout(self.layout)

    def verify_totp(self):
        """Girilen kodu kontrol et"""
        totp = pyotp.TOTP(TOTP_SECRET)
        entered_code = self.code_input.text()
        if totp.verify(entered_code):
            self.accept()  # Dialogu kapat ve başarılı olduğunda ana pencereye geri dön
        else:
            self.label.setText("Invalid code. Try again.")

class QrCodeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code")
        self.setGeometry(600, 300, 300, 300)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()
        
        self.qr_label = QLabel(self)
        self.layout.addWidget(self.qr_label)

        self.setLayout(self.layout)
        self.generate_qr_code()

    def generate_qr_code(self):
        """QR kodunu oluştur ve göster"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(TOTP_SECRET)
        qr.make(fit=True)

        # PIL ile QR kodunu oluştur
        qr_image = qr.make_image(fill='black', back_color='white')

        # PIL görüntüsünü QImage'e dönüştür
        qr_qimage = pil_image_to_qimage(qr_image)

        # QPixmap nesnesine dönüştür
        qr_pixmap = QPixmap.fromImage(qr_qimage)

        # QLabel üzerinde göster
        self.qr_label.setPixmap(qr_pixmap)

class LockScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Two-Factor Authentication")
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Arka plan rengini siyah yap
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(0, 0, 0))
        self.setPalette(palette)

        self.layout = QVBoxLayout()

        # Bekleme mesajını büyütüp beyaz yap
        self.label = QLabel("Waiting for authentication...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white;")
        self.label.setFont(QFont('Arial', 40))
        self.layout.addWidget(self.label)

        # Küçültülmüş TOTP butonu
        self.totp_button = QPushButton(self)  # Yeni buton
        self.totp_button.setIcon(QIcon("key.png"))  # Anahtar simgesinin yolu
        self.totp_button.setIconSize(QSize(50, 50))  # İkon boyutu
        self.totp_button.setStyleSheet("background-color: white; color: white;")
        self.totp_button.clicked.connect(self.show_totp_dialog)
        self.totp_button.setFixedSize(60, 60)  # Buton boyutu
        self.totp_button.move(1860, 1020)  # Sağ alt köşeye yerleştirme
        self.totp_button.setToolTip("Enter TOTP Code")  # Araç ipucu
        self.totp_button.setVisible(True)  # Butonu görünür yap



        self.setLayout(self.layout)
        self.showFullScreen()

        self.check_approval()

        self.block_keys()

    def block_keys(self):
        keyboard.block_key('esc')
        keyboard.block_key('windows')
        keyboard.block_key('alt')
        keyboard.block_key('ctrl')
        keyboard.block_key('shift')
        keyboard.block_key('tab')
        keyboard.add_hotkey('alt+tab', lambda: None)
        keyboard.add_hotkey('alt+f4', lambda: None)

    def check_approval(self):
        try:
            response = requests.get(f"{SERVER_URL}/active_devices", timeout=5)
            if response.status_code == 200:
                devices = response.json().get("devices", [])
                for device in devices:
                    if device["device_name"] == DEVICE_NAME and device["status"] == "approved":
                        self.label.setText("Authentication successful! Closing...")
                        QTimer.singleShot(1000, self.close_application)
                        return
        except requests.exceptions.RequestException:
            self.enable_totp_mode()

        QTimer.singleShot(5000, self.check_approval)

    def show_totp_dialog(self):
        """TOTP giriş penceresini göster"""
        dialog = TotpDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.label.setText("Authentication successful! Closing...")
            QTimer.singleShot(1000, self.close_application)

    def enable_totp_mode(self):
        """İnternet yoksa TOTP moduna geç"""
        self.label.setText("No internet. Enter TOTP code:")
        self.show_totp_dialog()

    def close_application(self):
        self.close()
        QTimer.singleShot(100, QApplication.quit)

    def closeEvent(self, event):
        event.ignore()

if __name__ == "__main__":
    try:
        requests.post(f"{SERVER_URL}/register", json={"device_name": DEVICE_NAME}, timeout=5)
    except requests.exceptions.RequestException:
        print("Sunucuya kaydolunamadı. İnternet bağlantısı yok.")

    app = QApplication(sys.argv)
    lock_screen = LockScreen()
    lock_screen.show()
    sys.exit(app.exec_())
