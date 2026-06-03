import sys
import sqlite3
import requests
from deep_translator import GoogleTranslator
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
                             QMessageBox, QComboBox, QAbstractItemView, QFileDialog, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QTextDocument, QPainter
from PyQt5.QtPrintSupport import QPrinter

# GRAFİK KÜTÜPHANELERİ
from PyQt5.QtChart import QChart, QChartView, QPieSeries

class SporSalonuApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 1. YENİ İSİM
        self.setWindowTitle("TRAIN-LIFE")
        self.setGeometry(100, 100, 1200, 750) 
        self.aktif_kullanici_id = None # Giriş yapana kadar None olacak
        
        self.gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.off_gunler = set()
        self.koyu_mod = True
        
        self.hedef_kas_gruplari = [
            "Göğüs (Üst Göğüs)", "Göğüs (Alt Göğüs)", "Göğüs (Orta/Genel)",
            "Omuz (Ön Omuz)", "Omuz (Orta Omuz)", "Omuz (Arka Omuz)",
            "Sırt (Kanat / Genişlik)", "Sırt (Orta Sırt / Kalınlık)", "Sırt (Alt Sırt)", "Sırt (Trapez)",
            "Biceps (Ön Kol)", "Triceps (Arka Kol)",
            "Ön Bacak (Quadriceps)", "Arka Bacak (Hamstring)", "Alt Bacak (Kalf)", "Kalça", "Karın (Core)"
        ]

        self.veritabani_kur()

        merkez_widget = QWidget()
        self.setCentralWidget(merkez_widget)
        
        ana_dikey_layout = QVBoxLayout(merkez_widget)
        ana_dikey_layout.setContentsMargins(15, 10, 15, 15)
        ana_dikey_layout.setSpacing(10)

        self.ust_bar_layout = QHBoxLayout()
        self.ust_bar_layout.addStretch()
        
        self.btn_tema = QPushButton("☀️") 
        self.btn_tema.setFixedSize(45, 45)
        self.btn_tema.setCursor(Qt.PointingHandCursor)
        self.btn_tema.clicked.connect(self.tema_degistir)
        self.btn_tema.hide() # Giriş yapılana kadar gizli
        self.ust_bar_layout.addWidget(self.btn_tema)
        
        ana_dikey_layout.addLayout(self.ust_bar_layout)

        icerik_layout = QHBoxLayout()
        ana_dikey_layout.addLayout(icerik_layout)

        self.menu_widget = QWidget()
        self.menu_widget.setObjectName("SolMenu")
        self.menu_widget.hide() # Giriş yapılana kadar gizli
        menu_layout = QVBoxLayout(self.menu_widget)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(12)

        self.btn_profil = QPushButton("Profil Bilgileri")
        self.btn_havuz = QPushButton("Egzersiz Kütüphanesi") 
        self.btn_takvim = QPushButton("Haftalık Programım")
        self.btn_analiz = QPushButton("Program Analizi")
        self.btn_grafik = QPushButton("Bölge Dağılım Grafiği") 

        self.menu_butonlari = [self.btn_profil, self.btn_havuz, self.btn_takvim, self.btn_analiz, self.btn_grafik]
        for btn in self.menu_butonlari:
            btn.setMinimumHeight(45)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            menu_layout.addWidget(btn)
        
        self.btn_profil.setChecked(True)
        menu_layout.addStretch()

        self.ekranlar = QStackedWidget()
        
        # Ekranları oluştur ve ekle (Sıralama Değişti)
        self.ekran_giris = self.giris_ekrani_olustur() # 0
        self.ekran_profil = self.profil_ekrani_olustur() # 1
        self.ekran_havuz = self.egzersiz_havuzu_ekrani_olustur() # 2
        self.ekran_takvim = self.takvim_ekrani_olustur() # 3
        self.ekran_analiz = self.analiz_ekrani_olustur() # 4
        self.ekran_grafik = self.grafik_ekrani_olustur() # 5

        self.ekranlar.addWidget(self.ekran_giris)
        self.ekranlar.addWidget(self.ekran_profil)
        self.ekranlar.addWidget(self.ekran_havuz)
        self.ekranlar.addWidget(self.ekran_takvim)
        self.ekranlar.addWidget(self.ekran_analiz)
        self.ekranlar.addWidget(self.ekran_grafik) 

        icerik_layout.addWidget(self.menu_widget, 1)
        icerik_layout.addWidget(self.ekranlar, 4)

        # Menü yönlendirmeleri (İndeksler güncellendi)
        self.btn_profil.clicked.connect(lambda: self.ekranlar.setCurrentIndex(1))
        self.btn_havuz.clicked.connect(lambda: self.ekranlar.setCurrentIndex(2))
        self.btn_takvim.clicked.connect(lambda: self.ekranlar.setCurrentIndex(3))
        self.btn_takvim.clicked.connect(self.takvime_gec) 
        self.btn_analiz.clicked.connect(lambda: self.ekranlar.setCurrentIndex(4))
        self.btn_analiz.clicked.connect(self.analiz_yap) 
        self.btn_grafik.clicked.connect(lambda: self.ekranlar.setCurrentIndex(5))
        self.btn_grafik.clicked.connect(self.grafik_guncelle)

        self.stil_sablonlarini_hazirla()
        
        if self.koyu_mod:
            self.setStyleSheet(self.dark_qss)
        else:
            self.setStyleSheet(self.light_qss)

    def veritabani_kur(self):
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Kullanicilar 
                          (kullanici_id INTEGER PRIMARY KEY, kullanici_adi TEXT, sifre TEXT, boy REAL, kilo REAL)''')
        
        # Email sütunu yoksa ekle (Hata verirse zaten vardır, pas geçeriz)
        try:
            cursor.execute("ALTER TABLE Kullanicilar ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass
            
        cursor.execute('''CREATE TABLE IF NOT EXISTS Egzersizler 
                          (egzersiz_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           hareket_adi TEXT UNIQUE, 
                           ana_kas TEXT, 
                           yan_kas TEXT, 
                           aciklama TEXT)''')
                           
        cursor.execute('''CREATE TABLE IF NOT EXISTS Programlar 
                          (program_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           kullanici_id INTEGER, 
                           egzersiz_id INTEGER, 
                           gun TEXT, 
                           set_sayisi INTEGER, 
                           tekrar_sayisi INTEGER)''')
                           
        cursor.execute('''CREATE TABLE IF NOT EXISTS OffGunler 
                          (kullanici_id INTEGER, gun TEXT, UNIQUE(kullanici_id, gun))''')
                           
        # Varsayılan kullanıcıyı ve şifresini ekle/güncelle
        cursor.execute("INSERT OR IGNORE INTO Kullanicilar (kullanici_id, kullanici_adi, sifre, email) VALUES (1, 'Sarp Yüksel', 'password', 'deneme@gmail.com')")
        cursor.execute("UPDATE Kullanicilar SET email = 'deneme@gmail.com' WHERE kullanici_id = 1 AND email IS NULL")
        conn.commit()
        conn.close()

    def off_gunleri_yukle(self):
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT gun FROM OffGunler WHERE kullanici_id = ?", (self.aktif_kullanici_id,))
        gunler = cursor.fetchall()
        self.off_gunler = {g[0] for g in gunler}
        conn.close()

    def stil_sablonlarini_hazirla(self):
        # Karanlık Tema ve Beyaz Kalan Köşeler / Scrollbar Düzeltmeleri
        self.dark_qss = """
            QMainWindow, QDialog, QMessageBox { background-color: #14151f; color: #ffffff; }
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: #ffffff; }
            QMessageBox QLabel { color: #ffffff; font-size: 14px; }
            QMessageBox QPushButton { background-color: #000BE3; color: #ffffff; padding: 6px 15px; border-radius: 4px; font-weight: bold; border: none; }
            QMessageBox QPushButton:hover { background-color: #242636; }
            QWidget#SolMenu { background-color: #1b1c26; border-radius: 12px; border: 1px solid #262837; }
            QWidget#SolMenu QPushButton { background-color: transparent; color: #a1a2b3; border: none; border-radius: 8px; padding-left: 15px; text-align: left; font-size: 14px; font-weight: 500; }
            QWidget#SolMenu QPushButton:hover { background-color: #242636; color: #ffffff; }
            QWidget#SolMenu QPushButton:checked { background-color: #000BE3; color: #ffffff; font-weight: bold; }
            QPushButton#ThemeButton { background-color: #1b1c26; border: 1px solid #262837; border-radius: 22px; font-size: 18px; }
            QPushButton#ThemeButton:hover { background-color: #242636; }
            QPushButton { background-color: #242636; border: 1px solid #2d3047; border-radius: 6px; padding: 6px 12px; font-size: 13px; color: #ffffff; }
            QPushButton:hover { background-color: #2d3047; }
            QLineEdit { background-color: #1b1c26; border: 1px solid #262837; border-radius: 6px; padding: 8px; color: #ffffff; }
            QLineEdit:focus { border: 1px solid #000BE3; }
            QComboBox { background-color: #1b1c26; border: 1px solid #262837; border-radius: 6px; padding: 5px; color: #ffffff; }
            QComboBox QAbstractItemView { background-color: #1b1c26; color: #ffffff; selection-background-color: #000BE3; }
            QLabel#Baslik { font-size: 22px; font-weight: bold; color: #ffffff; margin-bottom: 10px; }
            QLabel#AltYazi { font-size: 14px; color: #a1a2b3; }
            
            /* Tablo ve Köşe Kutucuğu Düzeltmesi */
            QTableWidget { background-color: #1b1c26; border: 1px solid #262837; gridline-color: #262837; border-radius: 8px; alternate-background-color: #1f202e; color: #ffffff; selection-background-color: #000BE3; selection-color: #ffffff; }
            QHeaderView::section { background-color: #242636; color: #ffffff; padding: 8px; border: 1px solid #14151f; font-weight: bold; }
            QTableWidget::item { padding: 5px; }
            QTableCornerButton::section { background-color: #242636; border: 1px solid #14151f; }
            
            /* Scrollbar (Kaydırma Çubuğu) Düzeltmesi */
            QScrollBar:vertical { border: none; background: #14151f; width: 12px; margin: 0px 0 0px 0; }
            QScrollBar::handle:vertical { background-color: #2d3047; min-height: 30px; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background-color: #000BE3; }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { border: none; background: none; height: 0px; }
            
            QScrollBar:horizontal { border: none; background: #14151f; height: 12px; margin: 0px 0 0px 0; }
            QScrollBar::handle:horizontal { background-color: #2d3047; min-width: 30px; border-radius: 6px; }
            QScrollBar::handle:horizontal:hover { background-color: #000BE3; }
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal { border: none; background: none; width: 0px; }
            
            QAbstractScrollArea::corner { background: #14151f; }
            QFrame#Ayrac { background-color: #262837; }
        """
        
        self.light_qss = """
            QMainWindow, QDialog, QMessageBox { background-color: #f4f5f8; color: #000000; }
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50; }
            QMessageBox QLabel { color: #000000; font-size: 14px; }
            QMessageBox QPushButton { background-color: #000BE3; color: #ffffff; padding: 6px 15px; border-radius: 4px; font-weight: bold; border: none; }
            QMessageBox QPushButton:hover { background-color: #242636; }
            QWidget#SolMenu { background-color: #ffffff; border-radius: 12px; border: 1px solid #dcdde1; }
            QWidget#SolMenu QPushButton { background-color: transparent; color: #7f8c8d; border: none; border-radius: 8px; padding-left: 15px; text-align: left; font-size: 14px; font-weight: 500; }
            QWidget#SolMenu QPushButton:hover { background-color: #f5f6fa; color: #2c3e50; }
            QWidget#SolMenu QPushButton:checked { background-color: #000BE3; color: #ffffff; font-weight: bold; }
            QPushButton#ThemeButton { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 22px; font-size: 18px; }
            QPushButton#ThemeButton:hover { background-color: #f5f6fa; }
            QPushButton { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 6px 12px; color: #2c3e50; font-size: 13px; }
            QPushButton:hover { background-color: #f5f6fa; }
            QLineEdit { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 8px; color: #000000; }
            QLineEdit:focus { border: 1px solid #000BE3; }
            QComboBox { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 5px; color: #000000; }
            QComboBox QAbstractItemView { background-color: #ffffff; color: #000000; selection-background-color: #000BE3; selection-color: #ffffff; }
            QLabel#Baslik { font-size: 22px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
            QLabel#AltYazi { font-size: 14px; color: #7f8c8d; }
            
            QTableWidget { background-color: #ffffff; border: 1px solid #dcdde1; gridline-color: #f5f6fa; border-radius: 8px; alternate-background-color: #fbfbfc; color: #000000; selection-background-color: #000BE3; selection-color: #ffffff; }
            QHeaderView::section { background-color: #f5f6fa; color: #2c3e50; padding: 8px; border: 1px solid #dcdde1; font-weight: bold; }
            QTableWidget::item { padding: 5px; }
            QTableCornerButton::section { background-color: #f5f6fa; border: 1px solid #dcdde1; }
            
            QScrollBar:vertical { border: none; background: #f4f5f8; width: 12px; margin: 0px 0 0px 0; }
            QScrollBar::handle:vertical { background-color: #dcdde1; min-height: 30px; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background-color: #000BE3; }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { border: none; background: none; height: 0px; }
            
            QScrollBar:horizontal { border: none; background: #f4f5f8; height: 12px; margin: 0px 0 0px 0; }
            QScrollBar::handle:horizontal { background-color: #dcdde1; min-width: 30px; border-radius: 6px; }
            QScrollBar::handle:horizontal:hover { background-color: #000BE3; }
            QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal { border: none; background: none; width: 0px; }
            
            QAbstractScrollArea::corner { background: #f4f5f8; }
            QFrame#Ayrac { background-color: #dcdde1; }
        """
        self.btn_tema.setObjectName("ThemeButton")

    def tema_degistir(self):
        self.koyu_mod = not self.koyu_mod
        if self.koyu_mod:
            self.btn_tema.setText("☀️")
            self.setStyleSheet(self.dark_qss)
        else:
            self.btn_tema.setText("🌙")
            self.setStyleSheet(self.light_qss)
        
        if self.aktif_kullanici_id:
            self.takvimi_guncelle()
            if self.ekranlar.currentIndex() == 5:
                self.grafik_guncelle()

    # --- EKRAN 0: LOGİN EKRANI (YENİ) ---
    def giris_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)
        layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel("TRAIN-LIFE")
        logo_label.setStyleSheet("font-size: 42px; font-weight: 900; color: #000BE3; letter-spacing: 2px;")
        logo_label.setAlignment(Qt.AlignCenter)

        altyazi = QLabel("Fitness Planlayıcınıza Hoş Geldiniz")
        altyazi.setStyleSheet("font-size: 16px; color: #a1a2b3; margin-bottom: 30px;")
        altyazi.setAlignment(Qt.AlignCenter)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("E-posta Adresi")
        self.input_email.setStyleSheet("font-size: 14px; padding: 12px; margin-bottom: 10px; max-width: 350px;")
        self.input_email.setText("sarp@trainlife.com") # Kolay giriş için hazır

        self.input_sifre = QLineEdit()
        self.input_sifre.setPlaceholderText("Şifre")
        self.input_sifre.setEchoMode(QLineEdit.Password)
        self.input_sifre.setStyleSheet("font-size: 14px; padding: 12px; margin-bottom: 20px; max-width: 350px;")
        self.input_sifre.returnPressed.connect(self.giris_yap)

        btn_giris = QPushButton("Sisteme Giriş Yap")
        btn_giris.setCursor(Qt.PointingHandCursor)
        btn_giris.setStyleSheet("background-color: #000BE3; color: white; padding: 12px; font-size: 16px; font-weight: bold; border:none; border-radius: 6px; max-width: 350px;")
        btn_giris.clicked.connect(self.giris_yap)

        layout.addStretch()
        layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        layout.addWidget(altyazi, alignment=Qt.AlignCenter)
        layout.addWidget(self.input_email, alignment=Qt.AlignCenter)
        layout.addWidget(self.input_sifre, alignment=Qt.AlignCenter)
        layout.addWidget(btn_giris, alignment=Qt.AlignCenter)
        layout.addStretch()

        return sayfa

    def giris_yap(self):
        email = self.input_email.text().strip()
        sifre = self.input_sifre.text().strip()
        
        if not email or not sifre:
            QMessageBox.warning(self, "Uyarı", "Lütfen E-posta ve şifrenizi girin!")
            return

        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT kullanici_id FROM Kullanicilar WHERE email = ? AND sifre = ?", (email, sifre))
        sonuc = cursor.fetchone()
        conn.close()

        if sonuc:
            self.aktif_kullanici_id = sonuc[0]
            self.off_gunleri_yukle()
            self.profil_verilerini_yukle()
            
            # Menüyü ve Tema butonunu göster
            self.menu_widget.show()
            self.btn_tema.show()
            
            # Profil sekmesine atla
            self.ekranlar.setCurrentIndex(1)
            self.takvimi_guncelle()
        else:
            QMessageBox.critical(self, "Giriş Başarısız", "E-posta adresi veya şifre hatalı!")

    # --- EKRAN 1: PROFİL ---
    def profil_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)
        baslik = QLabel("Profil Bilgileriniz")
        baslik.setObjectName("Baslik")
        baslik.setAlignment(Qt.AlignCenter)
        
        self.input_ad_soyad = QLineEdit()
        self.input_ad_soyad.setPlaceholderText("Adınız Soyadınız")
        self.input_ad_soyad.setStyleSheet("font-size: 14px; margin-left: 200px; margin-right: 200px; margin-bottom: 10px;")
        
        self.input_boy = QLineEdit()
        self.input_boy.setPlaceholderText("Boyunuz (Örn: 180 cm)")
        self.input_boy.setStyleSheet("font-size: 14px; margin-left: 200px; margin-right: 200px; margin-bottom: 10px;")
        
        self.input_kilo = QLineEdit()
        self.input_kilo.setPlaceholderText("Kilonuz (Örn: 75 kg)")
        self.input_kilo.setStyleSheet("font-size: 14px; margin-left: 200px; margin-right: 200px; margin-bottom: 20px;")
        
        btn_kaydet = QPushButton("Kaydet ve Programa Başla")
        btn_kaydet.setCursor(Qt.PointingHandCursor)
        btn_kaydet.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 16px; font-weight: bold; margin-left: 250px; margin-right: 250px; border:none;")
        btn_kaydet.clicked.connect(self.profil_kaydet)
        
        layout.addStretch()
        layout.addWidget(baslik)
        layout.addWidget(self.input_ad_soyad)
        layout.addWidget(self.input_boy)
        layout.addWidget(self.input_kilo)
        layout.addWidget(btn_kaydet)
        layout.addStretch()
        return sayfa

    def profil_kaydet(self):
        try:
            ad = self.input_ad_soyad.text().strip()
            if not ad: raise Exception("Ad Soyad boş bırakılamaz!")
            boy = float(self.input_boy.text().replace(',', '.'))
            kilo = float(self.input_kilo.text().replace(',', '.'))
            
            conn = sqlite3.connect('spor_salonu.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE Kullanicilar SET kullanici_adi = ?, boy = ?, kilo = ? WHERE kullanici_id = ?", (ad, boy, kilo, self.aktif_kullanici_id))
            conn.commit()
            conn.close()
            
            self.bmi_guncelle(boy, kilo)
            QMessageBox.information(self, "Başarılı", "Bilgileriniz kaydedildi!")
            
            self.ekranlar.setCurrentIndex(2) 
            self.btn_havuz.setChecked(True)
        except ValueError:
            QMessageBox.warning(self, "Hata", "Lütfen boy ve kilo için sadece sayı giriniz!")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def profil_verilerini_yukle(self):
        if not self.aktif_kullanici_id: return
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT kullanici_adi, boy, kilo FROM Kullanicilar WHERE kullanici_id = ?", (self.aktif_kullanici_id,))
        sonuc = cursor.fetchone()
        conn.close()
        
        if sonuc:
            if sonuc[0]: self.input_ad_soyad.setText(sonuc[0])
            if sonuc[1] and sonuc[2]:
                self.input_boy.setText(str(sonuc[1]))
                self.input_kilo.setText(str(sonuc[2]))
                self.bmi_guncelle(sonuc[1], sonuc[2])

    def bmi_guncelle(self, boy_cm, kilo):
        boy_m = boy_cm / 100
        bmi = kilo / (boy_m * boy_m)
        durum = "Zayıf" if bmi < 18.5 else "Normal" if bmi < 24.9 else "Fazla Kilolu" if bmi < 29.9 else "Obez"
        metin = f"👤 {self.input_ad_soyad.text()}  |  📏 {boy_cm} cm  |  ⚖️ {kilo} kg  |  🔥 BMI: {bmi:.1f} ({durum})"
        
        if not hasattr(self, 'lbl_bmi'):
            self.lbl_bmi = QLabel(metin)
        self.lbl_bmi.setText(metin)

    # --- EKRAN 2: EGZERSİZ KÜTÜPHANESİ ---
    def egzersiz_havuzu_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)

        baslik = QLabel("Egzersiz Kütüphanesi")
        baslik.setObjectName("Baslik")
        layout.addWidget(baslik)

        # 1. BÖLÜM: API ARAMA
        arama_layout = QHBoxLayout()
        self.input_arama = QLineEdit()
        self.input_arama.setPlaceholderText("İngilizce terimlerle aratın (Örn: press, row)...")
        self.input_arama.setStyleSheet("padding: 8px; font-size: 14px;")
        self.input_arama.returnPressed.connect(lambda: self.egzersizleri_api_den_cek())
        
        btn_ara = QPushButton("🔍 İnternette Ara")
        btn_ara.setCursor(Qt.PointingHandCursor)
        btn_ara.setStyleSheet("background-color: #000BE3; color: white; padding: 8px; font-weight: bold; border:none;")
        btn_ara.clicked.connect(lambda: self.egzersizleri_api_den_cek()) 

        arama_layout.addWidget(self.input_arama)
        arama_layout.addWidget(btn_ara)
        layout.addLayout(arama_layout)

        self.tablo_egzersizler = QTableWidget()
        self.tablo_egzersizler.setColumnCount(5) 
        self.tablo_egzersizler.setHorizontalHeaderLabels(["Hareket Adı", "Ana Kas (1.0 Puan)", "Yardımcı Kaslar (0.5 Puan)", "Tür/Zorluk", "Talimat"])
        
        header = self.tablo_egzersizler.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Stretch) 
        self.tablo_egzersizler.setColumnWidth(0, 150)
        self.tablo_egzersizler.setColumnWidth(1, 150) 
        self.tablo_egzersizler.setColumnWidth(2, 200)
        self.tablo_egzersizler.setColumnWidth(3, 150)

        self.tablo_egzersizler.setWordWrap(True) 
        self.tablo_egzersizler.verticalHeader().setVisible(False) 
        self.tablo_egzersizler.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablo_egzersizler.setSelectionBehavior(QAbstractItemView.SelectRows) 
        self.tablo_egzersizler.setEditTriggers(QAbstractItemView.NoEditTriggers) 
        layout.addWidget(self.tablo_egzersizler)

        ekleme_layout = QHBoxLayout()
        self.combo_gun = QComboBox()
        self.combo_gun.addItems(self.gunler)

        btn_ekle = QPushButton("Listeden Seçili Hareketi Ekle ➕")
        btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; border:none;")
        btn_ekle.clicked.connect(self.programa_ekle)

        ekleme_layout.addWidget(QLabel("Hangi Güne Eklensin? :"))
        ekleme_layout.addWidget(self.combo_gun)
        ekleme_layout.addWidget(btn_ekle)
        layout.addLayout(ekleme_layout)

        # --- 2. BÖLÜM: MANUEL HAREKET YARATMA ---
        ayrac = QFrame()
        ayrac.setFrameShape(QFrame.HLine)
        ayrac.setObjectName("Ayrac")
        layout.addWidget(ayrac)

        manuel_baslik = QLabel("API'de Bulamadığın Hareketi Kendin Yarat:")
        manuel_baslik.setStyleSheet("color: #a1a2b3; font-weight: bold; margin-top: 5px;")
        layout.addWidget(manuel_baslik)

        manuel_layout = QHBoxLayout()
        self.input_manuel_hareket = QLineEdit()
        self.input_manuel_hareket.setPlaceholderText("Hareketin Adı (Örn: Peck Deck Fly)")
        
        self.combo_manuel_kas = QComboBox()
        self.combo_manuel_kas.addItems(self.hedef_kas_gruplari)
        
        btn_manuel_ekle = QPushButton("🛠️ Kendi Hareketimi Yarat ve Ekle")
        btn_manuel_ekle.setCursor(Qt.PointingHandCursor)
        btn_manuel_ekle.setStyleSheet("background-color: #8E44AD; color: white; padding: 8px; font-weight: bold; border:none; border-radius: 5px;")
        btn_manuel_ekle.clicked.connect(self.manuel_hareket_programa_ekle)

        manuel_layout.addWidget(self.input_manuel_hareket)
        manuel_layout.addWidget(self.combo_manuel_kas)
        manuel_layout.addWidget(btn_manuel_ekle)
        layout.addLayout(manuel_layout)
        
        return sayfa

    def egzersizleri_api_den_cek(self, varsayilan_kelime=None):
        if varsayilan_kelime: arama_metni = varsayilan_kelime
        else:
            arama_metni = self.input_arama.text().strip()
            if not arama_metni:
                QMessageBox.warning(self, "Uyarı", "Lütfen aramak için bir kelime girin.")
                return

        API_KEY = "9Yezy8z9BZZGRQzW6Sh13Q5xYLNe7PR8ACO2TzeE"
        api_url = f"https://api.api-ninjas.com/v1/exercises?name={arama_metni}"

        try:
            response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
            if response.status_code == requests.codes.ok:
                veriler = response.json()
                self.tablo_egzersizler.setRowCount(0)
                
                if len(veriler) == 0:
                    if not varsayilan_kelime: QMessageBox.information(self, "Bulunamadı", "Uygun hareket bulunamadı.")
                    return

                tip_ceviri = {"strength": "Güç", "stretching": "Esneme", "plyometrics": "Patlayıcı", "powerlifting": "Powerlift", "cardio": "Kardiyo", "olympic_weightlifting": "Olimpik"}
                zorluk_ceviri = {"beginner": "Başlangıç", "intermediate": "Orta", "advanced": "İleri"}

                satir_indeksi = 0
                for egzersiz in veriler:
                    self.tablo_egzersizler.insertRow(satir_indeksi)
                    hareket_adi = egzersiz.get('name', 'Bilinmiyor')
                    ingilizce_kas = egzersiz.get('muscle', '')
                    name_lower = hareket_adi.lower()
                    
                    ana_kas = ""
                    yan_kaslar = []
                    
                    if ingilizce_kas == "chest":
                        if "incline" in name_lower: ana_kas = "Göğüs (Üst Göğüs)"
                        elif "decline" in name_lower: ana_kas = "Göğüs (Alt Göğüs)"
                        else: ana_kas = "Göğüs (Orta/Genel)"
                        if "press" in name_lower or "bench" in name_lower or "push" in name_lower: yan_kaslar.extend(["Triceps (Arka Kol)", "Omuz (Ön Omuz)"])
                        elif "fly" in name_lower or "peck" in name_lower or "cable" in name_lower: yan_kaslar.append("Omuz (Ön Omuz)")
                    elif ingilizce_kas == "shoulders":
                        if "lateral" in name_lower or "side" in name_lower: ana_kas = "Omuz (Orta Omuz)"
                        elif "rear" in name_lower or "reverse" in name_lower or "deltoid" in name_lower: ana_kas = "Omuz (Arka Omuz)"
                        else: ana_kas = "Omuz (Ön Omuz)"
                        if "press" in name_lower: yan_kaslar.append("Triceps (Arka Kol)")
                    elif ingilizce_kas in ["lats", "middle_back", "lower_back", "traps"]:
                        if ingilizce_kas == "lats": ana_kas = "Sırt (Kanat / Genişlik)"
                        elif ingilizce_kas == "middle_back": ana_kas = "Sırt (Orta Sırt / Kalınlık)"
                        elif ingilizce_kas == "lower_back": ana_kas = "Sırt (Alt Sırt)"
                        elif ingilizce_kas == "traps": ana_kas = "Sırt (Trapez)"
                        if "row" in name_lower or "pull" in name_lower or "chin" in name_lower or "lat" in name_lower: yan_kaslar.extend(["Biceps (Ön Kol)", "Omuz (Arka Omuz)"])
                    elif ingilizce_kas == "biceps": ana_kas = "Biceps (Ön Kol)"
                    elif ingilizce_kas == "triceps": ana_kas = "Triceps (Arka Kol)"
                    elif ingilizce_kas in ["quadriceps", "hamstrings", "calves", "glutes"]:
                        if ingilizce_kas == "quadriceps": ana_kas = "Ön Bacak (Quadriceps)"
                        elif ingilizce_kas == "hamstrings": ana_kas = "Arka Bacak (Hamstring)"
                        elif ingilizce_kas == "calves": ana_kas = "Alt Bacak (Kalf)"
                        elif ingilizce_kas == "glutes": ana_kas = "Kalça"
                        if "squat" in name_lower or "press" in name_lower or "lunge" in name_lower or "deadlift" in name_lower:
                            if ana_kas != "Kalça": yan_kaslar.append("Kalça")
                            if ana_kas != "Arka Bacak (Hamstring)": yan_kaslar.append("Arka Bacak (Hamstring)")
                            if ana_kas != "Ön Bacak (Quadriceps)" and ("squat" in name_lower or "press" in name_lower): yan_kaslar.append("Ön Bacak (Quadriceps)")
                    elif ingilizce_kas == "abdominals": ana_kas = "Karın (Core)"
                    else: ana_kas = ingilizce_kas.capitalize()
                        
                    yan_kaslar_str = ", ".join(yan_kaslar) if yan_kaslar else "-"
                    ham_tip = egzersiz.get('type', 'strength')
                    turkce_tip = tip_ceviri.get(ham_tip, ham_tip.capitalize())
                    ham_zorluk = egzersiz.get('difficulty', 'beginner')
                    turkce_zorluk = zorluk_ceviri.get(ham_zorluk, ham_zorluk.capitalize())
                    kunye_metni = f"Tür: {turkce_tip}\nSeviye: {turkce_zorluk}"
                    
                    talimat_ing = egzersiz.get('instructions', 'Talimat bulunmuyor.')
                    try: talimat_tr = GoogleTranslator(source='en', target='tr').translate(talimat_ing)
                    except Exception: talimat_tr = talimat_ing

                    self.tablo_egzersizler.setItem(satir_indeksi, 0, QTableWidgetItem(hareket_adi))
                    self.tablo_egzersizler.setItem(satir_indeksi, 1, QTableWidgetItem(ana_kas))
                    
                    item_yan = QTableWidgetItem(yan_kaslar_str)
                    if yan_kaslar_str != "-": item_yan.setForeground(QColor("#a1a2b3") if self.koyu_mod else QColor("#7f8c8d"))
                    self.tablo_egzersizler.setItem(satir_indeksi, 2, item_yan)
                    self.tablo_egzersizler.setItem(satir_indeksi, 3, QTableWidgetItem(kunye_metni))
                    self.tablo_egzersizler.setItem(satir_indeksi, 4, QTableWidgetItem(talimat_tr))
                    
                    satir_indeksi += 1
                self.tablo_egzersizler.resizeRowsToContents()
            else:
                if not varsayilan_kelime: QMessageBox.critical(self, "API Hatası", f"API Hatası (Kod {response.status_code})")
        except requests.exceptions.RequestException as e:
            if not varsayilan_kelime: QMessageBox.critical(self, "Bağlantı Hatası", f"Bağlantı kesildi: {str(e)}")

    def programa_ekle(self):
        secilen_gun = self.combo_gun.currentText()
        if secilen_gun in self.off_gunler:
            QMessageBox.warning(self, "İşlem Engellendi", f"Dikkat: {secilen_gun} günü Off Day!")
            return

        satir = self.tablo_egzersizler.currentRow()
        if satir < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce tablodan bir hareket seçin!")
            return

        secilen_hareket = self.tablo_egzersizler.item(satir, 0).text()
        secilen_ana_kas = self.tablo_egzersizler.item(satir, 1).text() 
        secilen_yan_kas = self.tablo_egzersizler.item(satir, 2).text()
        secilen_aciklama = self.tablo_egzersizler.item(satir, 4).text() 

        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT egzersiz_id FROM Egzersizler WHERE hareket_adi = ?", (secilen_hareket,))
        sonuc = cursor.fetchone()
        
        if sonuc: yerel_egzersiz_id = sonuc[0]
        else:
            cursor.execute('INSERT INTO Egzersizler (hareket_adi, ana_kas, yan_kas, aciklama) VALUES (?, ?, ?, ?)', 
                           (secilen_hareket, secilen_ana_kas, secilen_yan_kas, secilen_aciklama))
            yerel_egzersiz_id = cursor.lastrowid

        cursor.execute("INSERT INTO Programlar (kullanici_id, egzersiz_id, gun, set_sayisi, tekrar_sayisi) VALUES (?, ?, ?, ?, ?)", 
                       (self.aktif_kullanici_id, yerel_egzersiz_id, secilen_gun, 4, 10))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Başarılı", f"'{secilen_hareket}' başarıyla {secilen_gun} gününe eklendi!")
        self.takvimi_guncelle()

    def manuel_hareket_programa_ekle(self):
        secilen_gun = self.combo_gun.currentText()
        if secilen_gun in self.off_gunler:
            QMessageBox.warning(self, "İşlem Engellendi", f"Dikkat: {secilen_gun} günü Off Day!")
            return

        hareket_adi = self.input_manuel_hareket.text().strip().title()
        if not hareket_adi:
            QMessageBox.warning(self, "Uyarı", "Lütfen eklemek istediğiniz özel hareketin adını yazın!")
            return

        ana_kas = self.combo_manuel_kas.currentText()
        yan_kas = "-"
        aciklama = "Bu hareket kullanıcı tarafından manuel olarak eklenmiştir."

        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT egzersiz_id FROM Egzersizler WHERE hareket_adi = ?", (hareket_adi,))
        sonuc = cursor.fetchone()
        
        if sonuc: yerel_egzersiz_id = sonuc[0]
        else:
            cursor.execute('INSERT INTO Egzersizler (hareket_adi, ana_kas, yan_kas, aciklama) VALUES (?, ?, ?, ?)', 
                           (hareket_adi, ana_kas, yan_kas, aciklama))
            yerel_egzersiz_id = cursor.lastrowid

        cursor.execute("INSERT INTO Programlar (kullanici_id, egzersiz_id, gun, set_sayisi, tekrar_sayisi) VALUES (?, ?, ?, ?, ?)", 
                       (self.aktif_kullanici_id, yerel_egzersiz_id, secilen_gun, 4, 10))
        conn.commit()
        conn.close()

        self.input_manuel_hareket.clear()
        QMessageBox.information(self, "Başarılı", f"Özel hareket '{hareket_adi}' başarıyla {secilen_gun} gününe eklendi!")
        self.takvimi_guncelle()

    # --- EKRAN 3: HAFTALIK PROGRAMIM ---
    def takvim_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)
        
        baslik = QLabel("Haftalık Çalışma Programım")
        baslik.setObjectName("Baslik")
        layout.addWidget(baslik)
        altyazi = QLabel("Ekleme yapmak için BOŞ kutuya, silmek için DOLU kutuya çift tıklayınız.\nDinlenme günü ilan etmek için gün başlığına (Örn: Pazar) tıklayınız.")
        altyazi.setObjectName("AltYazi")
        layout.addWidget(altyazi)

        self.tablo_takvim = QTableWidget()
        self.tablo_takvim.setColumnCount(7)
        self.tablo_takvim.setRowCount(10) 
        self.tablo_takvim.setHorizontalHeaderLabels(self.gunler)
        self.tablo_takvim.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_takvim.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo_takvim.horizontalHeader().sectionClicked.connect(self.off_gun_belirle)
        self.tablo_takvim.cellDoubleClicked.connect(self.takvim_hucre_etkilesim)
        layout.addWidget(self.tablo_takvim)

        alt_layout = QHBoxLayout()
        btn_pdf = QPushButton("📄 Programı PDF Olarak İndir")
        btn_pdf.setCursor(Qt.PointingHandCursor)
        btn_pdf.setStyleSheet("background-color: #000BE3; color: white; padding: 8px; font-weight: bold; border-radius: 5px; border:none;")
        btn_pdf.clicked.connect(self.pdf_olarak_indir)
        alt_layout.addWidget(btn_pdf)
        alt_layout.addStretch() 
        
        sag_alt_kutu = QVBoxLayout()
        btn_temizle = QPushButton("🗑️ Programı Temizle")
        btn_temizle.setCursor(Qt.PointingHandCursor)
        btn_temizle.setStyleSheet("background-color: #E74C3C; color: white; padding: 6px 12px; font-weight: bold; border-radius: 5px; border:none;")
        btn_temizle.clicked.connect(self.programi_temizle)
        
        self.lbl_bmi = QLabel("Boy ve Kilo bilgisi henüz girilmedi.")
        self.lbl_bmi.setStyleSheet("font-size: 14px; font-weight: bold; padding: 3px;")
        self.lbl_bmi.setAlignment(Qt.AlignRight)
        
        sag_alt_kutu.addWidget(btn_temizle)
        sag_alt_kutu.addWidget(self.lbl_bmi)
        alt_layout.addLayout(sag_alt_kutu)
        layout.addLayout(alt_layout)
        return sayfa

    def programi_temizle(self):
        cevap = QMessageBox.question(self, "Programı Sıfırla", "TÜM egzersizleri silmek istediğinize emin misiniz?\nBu işlem geri alınamaz!", QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            conn = sqlite3.connect('spor_salonu.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Programlar WHERE kullanici_id = ?", (self.aktif_kullanici_id,))
            conn.commit()
            conn.close()
            self.takvimi_guncelle()
            QMessageBox.information(self, "Temizlendi", "Haftalık programınız tamamen sıfırlandı.")

    def takvim_hucre_etkilesim(self, satir, sutun):
        item = self.tablo_takvim.item(satir, sutun)
        secilen_gun = self.gunler[sutun]
        
        if secilen_gun in self.off_gunler:
            QMessageBox.warning(self, "İşlem Engellendi", f"Dikkat: {secilen_gun} günü Off Day olarak ayarlanmış!")
            return

        if not item or not item.text().strip() or "OFF DAY" in item.text():
            self.combo_gun.setCurrentText(secilen_gun)
            self.btn_havuz.setChecked(True)
            self.ekranlar.setCurrentIndex(2)
            return

        hareket_adi = item.text().split('\n')[0] 
        cevap = QMessageBox.question(self, "Hareketi Sil", f"{secilen_gun} günündeki '{hareket_adi}' hareketini silmek istiyor musun?", QMessageBox.Yes | QMessageBox.No)
        
        if cevap == QMessageBox.Yes:
            conn = sqlite3.connect('spor_salonu.db')
            cursor = conn.cursor()
            sorgu = "DELETE FROM Programlar WHERE kullanici_id = ? AND gun = ? AND egzersiz_id = (SELECT egzersiz_id FROM Egzersizler WHERE hareket_adi = ?)"
            cursor.execute(sorgu, (self.aktif_kullanici_id, secilen_gun, hareket_adi))
            conn.commit()
            conn.close()
            self.takvimi_guncelle()

    def pdf_olarak_indir(self):
        dosya_yolu, _ = QFileDialog.getSaveFileName(self, "PDF Olarak Kaydet", "Haftalik_Fitness_Programi.pdf", "PDF Dosyaları (*.pdf)")
        if dosya_yolu:
            html = f"<html><head><meta charset='utf-8'></head><body><h1 style='text-align:center; color:#2C3E50;'>Haftalık Fitness Programı</h1><h3 style='text-align:center; color:#7F8C8D;'>{self.lbl_bmi.text()}</h3><hr><table border='1' width='100%' cellspacing='0' cellpadding='10' style='border-collapse: collapse; text-align: center; font-family: Arial; font-size: 14px;'><tr style='background-color: #000BE3; color: white;'>"
            for gun in self.gunler: html += f"<th style='padding: 10px; font-size: 16px;'>{gun}</th>"
            html += "</tr>"
            
            for satir in range(self.tablo_takvim.rowCount()):
                bos_satir = True
                satir_html = "<tr>"
                for sutun in range(7):
                    item = self.tablo_takvim.item(satir, sutun)
                    if item and item.text():
                        bos_satir = False
                        metin = item.text().replace('\n', '<br>')
                        if "OFF DAY" in metin: satir_html += f"<td style='background-color: #FFCCCC; font-weight: bold; color: black; font-size: 13px; padding: 8px;'>{metin}</td>"
                        else: satir_html += f"<td style='color: black; font-size: 13px; padding: 8px;'>{metin}</td>"
                    else: satir_html += "<td></td>"
                satir_html += "</tr>"
                if not bos_satir: html += satir_html
                    
            html += "</table></body></html>"
            belge = QTextDocument()
            belge.setHtml(html)
            yazici = QPrinter(QPrinter.ScreenResolution)
            yazici.setOutputFormat(QPrinter.PdfFormat)
            yazici.setOutputFileName(dosya_yolu)
            yazici.setOrientation(QPrinter.Landscape)
            belge.print_(yazici)
            QMessageBox.information(self, "Başarılı", f"Programınız başarıyla kaydedildi!")

    def off_gun_belirle(self, sutun_indeksi):
        secilen_gun = self.gunler[sutun_indeksi]
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        
        if secilen_gun in self.off_gunler:
            cevap = QMessageBox.question(self, "Off Day İptali", f"{secilen_gun} gününü dinlenme günü olmaktan çıkarmak istiyor musun?", QMessageBox.Yes | QMessageBox.No)
            if cevap == QMessageBox.Yes:
                self.off_gunler.remove(secilen_gun)
                cursor.execute("DELETE FROM OffGunler WHERE kullanici_id = ? AND gun = ?", (self.aktif_kullanici_id, secilen_gun))
                conn.commit()
                self.takvimi_guncelle()
        else:
            cevap = QMessageBox.question(self, "Dinlenme Günü (Off Day)", f"{secilen_gun} gününü Off Day yapmak istiyor musun?", QMessageBox.Yes | QMessageBox.No)
            if cevap == QMessageBox.Yes:
                self.off_gunler.add(secilen_gun)
                cursor.execute("INSERT OR IGNORE INTO OffGunler (kullanici_id, gun) VALUES (?, ?)", (self.aktif_kullanici_id, secilen_gun))
                cursor.execute("DELETE FROM Programlar WHERE kullanici_id = ? AND gun = ?", (self.aktif_kullanici_id, secilen_gun))
                conn.commit()
                self.takvimi_guncelle()
                
        conn.close()

    def takvime_gec(self):
        self.takvimi_guncelle()

    def takvimi_guncelle(self):
        if not self.aktif_kullanici_id: return
        
        self.tablo_takvim.clearContents() 
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT p.gun, e.hareket_adi, e.ana_kas FROM Programlar p JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id WHERE p.kullanici_id = ?", (self.aktif_kullanici_id,))
        programlar = cursor.fetchall()
        conn.close()
        
        gun_indeksleri = {"Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4, "Cumartesi": 5, "Pazar": 6}
        gun_satir_sayaci = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        for gun, hareket_adi, ana_kas in programlar:
            sutun = gun_indeksleri.get(gun)
            if sutun is not None:
                satir = gun_satir_sayaci[sutun]
                if satir < self.tablo_takvim.rowCount():
                    item = QTableWidgetItem(f"{hareket_adi}\n({ana_kas})")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tablo_takvim.setItem(satir, sutun, item)
                    gun_satir_sayaci[sutun] += 1
        
        off_renk = QColor(90, 25, 25) if self.koyu_mod else QColor(255, 220, 220)
        
        for sutun, gun in enumerate(self.gunler):
            if gun in self.off_gunler:
                for satir in range(self.tablo_takvim.rowCount()):
                    item = self.tablo_takvim.item(satir, sutun)
                    if not item:
                        item = QTableWidgetItem()
                        self.tablo_takvim.setItem(satir, sutun, item)
                    item.setBackground(off_renk) 
                    if self.koyu_mod: item.setForeground(QColor(255, 255, 255))
                    else: item.setForeground(QColor(0, 0, 0))

                    if satir == 0:
                        item.setText("OFF DAY\n(Dinlenme)")
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignCenter)

    # --- EKRAN 4: HAFTALIK KAS ANALİZİ ---
    def analiz_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)
        
        baslik = QLabel("Haftalık Detaylı Kas Analiz Raporu")
        baslik.setObjectName("Baslik")
        layout.addWidget(baslik)
        
        altyazi = QLabel("Hangi hareketlerin bu kası etkilediğini görmek için fareyi satırın üzerine getirip bekleyiniz (Hover/Tooltip).\nAna bölgeler 1.0 Puan, Yardımcı bölgeler 0.5 Puan olarak hesaplanır.")
        altyazi.setObjectName("AltYazi")
        layout.addWidget(altyazi)

        self.tablo_analiz = QTableWidget()
        self.tablo_analiz.setColumnCount(3)
        self.tablo_analiz.setHorizontalHeaderLabels(["Durum Analizi", "Kas Grubu / Alt Kırılım", "Katsayılı Hacim Puanı"])
        self.tablo_analiz.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_analiz.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo_analiz.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo_analiz.verticalHeader().setVisible(False)
        layout.addWidget(self.tablo_analiz)
        
        return sayfa

    def analiz_yap(self):
        if not self.aktif_kullanici_id: return
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT e.hareket_adi, e.ana_kas, e.yan_kas FROM Programlar p JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id WHERE p.kullanici_id = ?", (self.aktif_kullanici_id,))
        programlar = cursor.fetchall()
        conn.close()
        
        kas_hacim_puanlari = {bolge: 0.0 for bolge in self.hedef_kas_gruplari}
        kas_hareket_eslesmesi = {bolge: [] for bolge in self.hedef_kas_gruplari}
        ana_kas_olarak_secildi_mi = {bolge: False for bolge in self.hedef_kas_gruplari}
        
        for hareket_adi, ana_kas, yan_kas_str in programlar:
            if ana_kas in kas_hacim_puanlari:
                kas_hacim_puanlari[ana_kas] += 1.0
                kas_hareket_eslesmesi[ana_kas].append(f"{hareket_adi} (Ana: 1 Puan)")
                ana_kas_olarak_secildi_mi[ana_kas] = True 
                
            if yan_kas_str and yan_kas_str != "-":
                yan_bolgeler = [b.strip() for b in yan_kas_str.split(",")]
                for b in yan_bolgeler:
                    if b in kas_hacim_puanlari:
                        kas_hacim_puanlari[b] += 0.5
                        kas_hareket_eslesmesi[b].append(f"{hareket_adi} (Yan: 0.5 Puan)")
                    
        self.tablo_analiz.setRowCount(0)
        
        if self.koyu_mod:
            renk_eksik = QColor(70, 30, 30)
            renk_asiri = QColor(80, 40, 20) 
            renk_yetersiz = QColor(85, 75, 25) 
            renk_denge = QColor(25, 55, 35)
            yazi_rengi = QColor(255, 255, 255)
        else:
            renk_eksik = QColor(255, 225, 225)
            renk_asiri = QColor(255, 200, 180)
            renk_yetersiz = QColor(255, 250, 200) 
            renk_denge = QColor(220, 245, 220)
            yazi_rengi = QColor(0, 0, 0)

        for satir_indeksi, bolge in enumerate(self.hedef_kas_gruplari):
            self.tablo_analiz.insertRow(satir_indeksi)
            
            puan = kas_hacim_puanlari[bolge]
            etkileyen_hareketler = kas_hareket_eslesmesi[bolge]
            
            if puan == 0.0:
                durum_metni = "❌ Çalışmıyor"
                arka_plan_renk = renk_eksik
                tooltip_metni = f"Dikkat: {bolge} bölgesini tetikleyen hiçbir hareket bulunmuyor!"
                
            elif not ana_kas_olarak_secildi_mi[bolge]:
                durum_metni = "⚠️ İzole Edilmemiş (Yetersiz)"
                arka_plan_renk = renk_yetersiz
                liste_metni = "\n• ".join(etkileyen_hareketler)
                tooltip_metni = f"UYARI: {bolge} sadece başka hareketlerde yardımcı kas olarak uyarılıyor. Gelişim için doğrudan hedefleyen bir 'Ana Hareket' eklemelisin!\n\nHareketleriniz:\n• {liste_metni}"
                
            elif puan > 2.0:
                durum_metni = "🔥 Aşırı Çalışma"
                arka_plan_renk = renk_asiri
                liste_metni = "\n• ".join(etkileyen_hareketler)
                tooltip_metni = f"UYARI: {bolge} için 2 puanlık hacim sınırı aşıldı! Overtraining riskine dikkat edin.\n\nHareketleriniz:\n• {liste_metni}"
                
            else:
                durum_metni = "✅ Dengeli"
                arka_plan_renk = renk_denge
                liste_metni = "\n• ".join(etkileyen_hareketler)
                tooltip_metni = f"Tebrikler! {bolge} için ideal hacimdesiniz.\n\nHareketler:\n• {liste_metni}"

            item_durum = QTableWidgetItem(durum_metni)
            item_bolge = QTableWidgetItem(bolge)
            item_sayi = QTableWidgetItem(f"{puan} Puan")
            
            item_durum.setTextAlignment(Qt.AlignCenter)
            item_sayi.setTextAlignment(Qt.AlignCenter)
            
            for item in [item_durum, item_bolge, item_sayi]:
                item.setBackground(arka_plan_renk)
                item.setForeground(yazi_rengi)
                item.setToolTip(tooltip_metni) 
                
            self.tablo_analiz.setItem(satir_indeksi, 0, item_durum)
            self.tablo_analiz.setItem(satir_indeksi, 1, item_bolge)
            self.tablo_analiz.setItem(satir_indeksi, 2, item_sayi)

    # --- EKRAN 5: SADELEŞTİRİLMİŞ VE KATSAYILI PASTA GRAFİĞİ ---
    def grafik_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)

        baslik = QLabel("Bölge Dağılım Grafiği (Tüm Vücut Oranı)")
        baslik.setObjectName("Baslik")
        layout.addWidget(baslik)
        
        altyazi = QLabel("Haftalık programınızın ana kas gruplarına göre sadeleştirilmiş, puan bazlı (Ana: 1.0, Yan: 0.5) yüzdelik dağılımı.")
        altyazi.setObjectName("AltYazi")
        layout.addWidget(altyazi)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignRight)

        self.chart_view.setChart(self.chart)
        layout.addWidget(self.chart_view)

        return sayfa

    def grafik_guncelle(self):
        if not self.aktif_kullanici_id: return
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT e.hareket_adi, e.ana_kas, e.yan_kas FROM Programlar p JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id WHERE p.kullanici_id = ?", (self.aktif_kullanici_id,))
        programlar = cursor.fetchall()
        conn.close()

        grup_haritasi = {
            "Göğüs (Üst Göğüs)": "Göğüs", "Göğüs (Alt Göğüs)": "Göğüs", "Göğüs (Orta/Genel)": "Göğüs",
            "Omuz (Ön Omuz)": "Omuz", "Omuz (Orta Omuz)": "Omuz", "Omuz (Arka Omuz)": "Omuz",
            "Sırt (Kanat / Genişlik)": "Sırt", "Sırt (Orta Sırt / Kalınlık)": "Sırt", "Sırt (Alt Sırt)": "Sırt", "Sırt (Trapez)": "Sırt",
            "Ön Bacak (Quadriceps)": "Bacak", "Arka Bacak (Hamstring)": "Bacak", "Alt Bacak (Kalf)": "Bacak",
            "Biceps (Ön Kol)": "Biceps", "Triceps (Arka Kol)": "Triceps", "Kalça": "Kalça", "Karın (Core)": "Karın"
        }

        ana_kas_puanlari = {"Göğüs": 0.0, "Sırt": 0.0, "Omuz": 0.0, "Bacak": 0.0, "Kalça": 0.0, "Biceps": 0.0, "Triceps": 0.0, "Karın": 0.0}
        toplam_puan = 0.0

        for hareket_adi, ana_kas, yan_kas_str in programlar:
            basit_ana_grup = grup_haritasi.get(ana_kas, ana_kas)
            if basit_ana_grup in ana_kas_puanlari:
                ana_kas_puanlari[basit_ana_grup] += 1.0
                toplam_puan += 1.0
            else:
                ana_kas_puanlari[basit_ana_grup] = 1.0
                toplam_puan += 1.0

            if yan_kas_str and yan_kas_str != "-":
                yan_bolgeler = [b.strip() for b in yan_kas_str.split(",")]
                for b in yan_bolgeler:
                    basit_yan_grup = grup_haritasi.get(b, b)
                    if basit_yan_grup in ana_kas_puanlari:
                        ana_kas_puanlari[basit_yan_grup] += 0.5
                        toplam_puan += 0.5
                    else:
                        ana_kas_puanlari[basit_yan_grup] = 0.5
                        toplam_puan += 0.5

        self.chart.removeAllSeries()
        series = QPieSeries()

        renk_paleti = ["#E74C3C", "#3498DB", "#F1C40F", "#2ECC71", "#9B59B6", "#E67E22", "#1ABC9C", "#95A5A6"]

        if toplam_puan == 0.0:
            dilim = series.append("Program Boş", 1)
            dilim.setColor(QColor("#7f8c8d"))
            dilim.setLabelVisible(True)
            dilim.setLabelColor(QColor("#ffffff") if self.koyu_mod else QColor("#000000"))
        else:
            renk_indeksi = 0
            for bolge, puan in ana_kas_puanlari.items():
                if puan > 0:
                    yuzde = (puan / toplam_puan) * 100
                    dilim = series.append(f"{bolge} ({yuzde:.1f}%)", puan)
                    dilim.setLabelVisible(True)
                    dilim.setColor(QColor(renk_paleti[renk_indeksi % len(renk_paleti)]))
                    if self.koyu_mod: dilim.setLabelColor(QColor("#ffffff"))
                    else: dilim.setLabelColor(QColor("#000000"))
                    renk_indeksi += 1

        self.chart.addSeries(series)

        if self.koyu_mod:
            self.chart.setBackgroundBrush(QColor("#14151f")) 
            self.chart.legend().setLabelColor(QColor("#ffffff"))
        else:
            self.chart.setBackgroundBrush(QColor("#f4f5f8"))
            self.chart.legend().setLabelColor(QColor("#2c3e50"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pencere = SporSalonuApp()
    pencere.show()
    sys.exit(app.exec_())