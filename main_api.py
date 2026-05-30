import sys
import sqlite3
import requests
from deep_translator import GoogleTranslator
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
                             QMessageBox, QComboBox, QAbstractItemView, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QTextDocument
from PyQt5.QtPrintSupport import QPrinter

class SporSalonuApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fitness Planner Pro")
        self.setGeometry(100, 100, 1200, 750) 
        self.aktif_kullanici_id = 1 
        
        self.gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.off_gunler = set()
        self.koyu_mod = True

        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO Kullanicilar (kullanici_id, kullanici_adi, sifre) VALUES (1, 'Sarp Yüksel', 'password')")
        
        try:
            cursor.execute("ALTER TABLE Kullanicilar ADD COLUMN boy REAL")
        except sqlite3.OperationalError:
            pass 
            
        conn.commit()
        conn.close()

        merkez_widget = QWidget()
        self.setCentralWidget(merkez_widget)
        
        ana_dikey_layout = QVBoxLayout(merkez_widget)
        ana_dikey_layout.setContentsMargins(15, 10, 15, 15)
        ana_dikey_layout.setSpacing(10)

        ust_bar_layout = QHBoxLayout()
        ust_bar_layout.addStretch()
        
        self.btn_tema = QPushButton("☀️") 
        self.btn_tema.setFixedSize(45, 45)
        self.btn_tema.setCursor(Qt.PointingHandCursor)
        self.btn_tema.clicked.connect(self.tema_degistir)
        ust_bar_layout.addWidget(self.btn_tema)
        
        ana_dikey_layout.addLayout(ust_bar_layout)

        icerik_layout = QHBoxLayout()
        ana_dikey_layout.addLayout(icerik_layout)

        self.menu_widget = QWidget()
        self.menu_widget.setObjectName("SolMenu")
        menu_layout = QVBoxLayout(self.menu_widget)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(12)

        self.btn_profil = QPushButton("Profil Bilgileri")
        self.btn_havuz = QPushButton("Egzersiz Kütüphanesi") 
        self.btn_takvim = QPushButton("Haftalık Programım")
        self.btn_analiz = QPushButton("Program Analizi")

        self.menu_butonlari = [self.btn_profil, self.btn_havuz, self.btn_takvim, self.btn_analiz]
        for btn in self.menu_butonlari:
            btn.setMinimumHeight(45)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            menu_layout.addWidget(btn)
        
        self.btn_profil.setChecked(True)
        menu_layout.addStretch()

        self.ekranlar = QStackedWidget()
        self.ekran_profil = self.profil_ekrani_olustur()
        self.ekran_havuz = self.egzersiz_havuzu_ekrani_olustur()
        self.ekran_takvim = self.takvim_ekrani_olustur()
        self.ekran_analiz = self.analiz_ekrani_olustur()

        self.ekranlar.addWidget(self.ekran_profil)
        self.ekranlar.addWidget(self.ekran_havuz)
        self.ekranlar.addWidget(self.ekran_takvim)
        self.ekranlar.addWidget(self.ekran_analiz)

        icerik_layout.addWidget(self.menu_widget, 1)
        icerik_layout.addWidget(self.ekranlar, 4)

        self.btn_profil.clicked.connect(lambda: self.ekranlar.setCurrentIndex(0))
        self.btn_havuz.clicked.connect(lambda: self.ekranlar.setCurrentIndex(1))
        self.btn_takvim.clicked.connect(self.takvime_gec) 
        self.btn_analiz.clicked.connect(self.analiz_yap) 

        self.stil_sablonlarini_hazirla()
        
        if self.koyu_mod:
            self.setStyleSheet(self.dark_qss)
        else:
            self.setStyleSheet(self.light_qss)

        self.profil_verilerini_yukle() 
        self.egzersizleri_api_den_cek(varsayilan_kelime="press")

    def stil_sablonlarini_hazirla(self):
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
            
            QTableWidget { background-color: #1b1c26; border: 1px solid #262837; gridline-color: #262837; border-radius: 8px; alternate-background-color: #1f202e; color: #ffffff; selection-background-color: #000BE3; selection-color: #ffffff; }
            QHeaderView::section { background-color: #242636; color: #ffffff; padding: 8px; border: 1px solid #14151f; font-weight: bold; }
            QTableWidget::item { padding: 5px; }
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
        
        self.takvimi_guncelle()

    def profil_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)

        baslik = QLabel("Profil Bilgileriniz")
        baslik.setObjectName("Baslik")
        baslik.setAlignment(Qt.AlignCenter)

        self.input_ad_soyad = QLineEdit()
        self.input_ad_soyad.setText("Sarp Yüksel")
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
            if not ad:
                raise Exception("Ad Soyad boş bırakılamaz!")
            
            boy = float(self.input_boy.text().replace(',', '.'))
            kilo = float(self.input_kilo.text().replace(',', '.'))
            
            conn = sqlite3.connect('spor_salonu.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE Kullanicilar SET kullanici_adi = ?, boy = ?, kilo = ? WHERE kullanici_id = ?", (ad, boy, kilo, self.aktif_kullanici_id))
            conn.commit()
            conn.close()

            self.bmi_guncelle(boy, kilo)
            QMessageBox.information(self, "Başarılı", "Bilgileriniz kaydedildi!")
            
            self.ekranlar.setCurrentIndex(1) 
            self.btn_havuz.setChecked(True)
        except ValueError:
            QMessageBox.warning(self, "Hata", "Lütfen boy ve kilo için sadece sayı giriniz!")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def profil_verilerini_yukle(self):
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT kullanici_adi, boy, kilo FROM Kullanicilar WHERE kullanici_id = ?", (self.aktif_kullanici_id,))
        sonuc = cursor.fetchone()
        conn.close()
        
        if sonuc:
            if sonuc[0]:
                self.input_ad_soyad.setText(sonuc[0])
            if sonuc[1] and sonuc[2]:
                self.input_boy.setText(str(sonuc[1]))
                self.input_kilo.setText(str(sonuc[2]))
                self.bmi_guncelle(sonuc[1], sonuc[2])

    def bmi_guncelle(self, boy_cm, kilo):
        boy_m = boy_cm / 100
        bmi = kilo / (boy_m * boy_m)
        durum = ""
        if bmi < 18.5:
            durum = "Zayıf"
        elif 18.5 <= bmi < 24.9:
            durum = "Normal"
        elif 25 <= bmi < 29.9:
            durum = "Fazla Kilolu"
        else:
            durum = "Obez"
            
        metin = f"👤 {self.input_ad_soyad.text()}  |  📏 {boy_cm} cm  |  ⚖️ {kilo} kg  |  🔥 BMI: {bmi:.1f} ({durum})"
        self.lbl_bmi.setText(metin)

    # --- EKRAN 2: EGZERSİZ KÜTÜPHANESİ ---
    def egzersiz_havuzu_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)

        baslik = QLabel("Egzersiz Kütüphanesi")
        baslik.setObjectName("Baslik")
        layout.addWidget(baslik)

        arama_layout = QHBoxLayout()
        self.input_arama = QLineEdit()
        self.input_arama.setPlaceholderText("İngilizce terimlerle aratın (Örn: press, dumbbell, row)...")
        self.input_arama.setStyleSheet("padding: 8px; font-size: 14px;")
        
        # Enter Tuşu ile arama
        self.input_arama.returnPressed.connect(lambda: self.egzersizleri_api_den_cek())
        
        btn_ara = QPushButton("🔍 İnternette Ara")
        btn_ara.setCursor(Qt.PointingHandCursor)
        btn_ara.setStyleSheet("background-color: #000BE3; color: white; padding: 8px; font-weight: bold; border:none;")
        btn_ara.clicked.connect(lambda: self.egzersizleri_api_den_cek()) 

        arama_layout.addWidget(self.input_arama)
        arama_layout.addWidget(btn_ara)
        layout.addLayout(arama_layout)

        self.tablo_egzersizler = QTableWidget()
        self.tablo_egzersizler.setColumnCount(4) 
        self.tablo_egzersizler.setHorizontalHeaderLabels(["Hareket Adı", "Çalışan Hibrit Bölgeler", "Tür / Ekipman / Zorluk", "Yapılış Talimatı (Türkçe)"])
        
        header = self.tablo_egzersizler.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch) 
        self.tablo_egzersizler.setColumnWidth(0, 180)
        self.tablo_egzersizler.setColumnWidth(1, 240) 
        self.tablo_egzersizler.setColumnWidth(2, 220)

        self.tablo_egzersizler.setWordWrap(True) 
        self.tablo_egzersizler.verticalHeader().setVisible(False) 
        self.tablo_egzersizler.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.tablo_egzersizler.setSelectionBehavior(QAbstractItemView.SelectRows) 
        self.tablo_egzersizler.setEditTriggers(QAbstractItemView.NoEditTriggers) 
        layout.addWidget(self.tablo_egzersizler)

        ekleme_layout = QHBoxLayout()
        self.combo_gun = QComboBox()
        self.combo_gun.addItems(self.gunler)

        btn_ekle = QPushButton("Seçili Hareketi Programa Ekle ➕")
        btn_ekle.setCursor(Qt.PointingHandCursor)
        btn_ekle.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold; border:none;")
        btn_ekle.clicked.connect(self.programa_ekle)

        ekleme_layout.addWidget(QLabel("Hangi Güne Eklensin? :"))
        ekleme_layout.addWidget(self.combo_gun)
        ekleme_layout.addWidget(btn_ekle)
        layout.addLayout(ekleme_layout)
        
        return sayfa

    def egzersizleri_api_den_cek(self, varsayilan_kelime=None):
        if varsayilan_kelime:
            arama_metni = varsayilan_kelime
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
                    if not varsayilan_kelime:
                        QMessageBox.information(self, "Bulunamadı", "Uygun hareket bulunamadı.")
                    return

                tip_ceviri = {"strength": "Güç Geliştirme", "stretching": "Esneme", "plyometrics": "Patlayıcı Güç", "powerlifting": "Powerlifting", "cardio": "Kardiyo", "olympic_weightlifting": "Olimpik Halter"}
                zorluk_ceviri = {"beginner": "Başlangıç", "intermediate": "Orta Seviye", "advanced": "İleri Düzey"}

                satir_indeksi = 0
                for egzersiz in veriler:
                    self.tablo_egzersizler.insertRow(satir_indeksi)
                    
                    hareket_adi = egzersiz.get('name', 'Bilinmiyor')
                    ingilizce_kas = egzersiz.get('muscle', '')
                    name_lower = hareket_adi.lower()
                    
                    aktif_bolgeler = []
                    
                    if ingilizce_kas == "chest":
                        if "incline" in name_lower:
                            aktif_bolgeler.append("Göğüs (Üst Göğüs)")
                        elif "decline" in name_lower:
                            aktif_bolgeler.append("Göğüs (Alt Göğüs)")
                        else:
                            aktif_bolgeler.append("Göğüs (Orta/Genel)")
                        
                        if "press" in name_lower or "bench" in name_lower or "push" in name_lower:
                            aktif_bolgeler.append("Triceps (Arka Kol)")
                            aktif_bolgeler.append("Omuz (Ön Omuz)")
                        elif "fly" in name_lower or "peck" in name_lower or "cable" in name_lower:
                            aktif_bolgeler.append("Omuz (Ön Omuz)")
                            
                    elif ingilizce_kas == "shoulders":
                        if "lateral" in name_lower or "side" in name_lower:
                            aktif_bolgeler.append("Omuz (Orta Omuz)")
                        elif "rear" in name_lower or "reverse" in name_lower or "deltoid" in name_lower:
                            aktif_bolgeler.append("Omuz (Arka Omuz)")
                        else:
                            aktif_bolgeler.append("Omuz (Ön Omuz)")
                            
                        if "press" in name_lower:
                            aktif_bolgeler.append("Triceps (Arka Kol)")
                            
                    elif ingilizce_kas in ["lats", "middle_back", "lower_back", "traps"]:
                        if ingilizce_kas == "lats":
                            aktif_bolgeler.append("Sırt (Kanat / Genişlik)")
                        elif ingilizce_kas == "middle_back":
                            aktif_bolgeler.append("Sırt (Orta Sırt / Kalınlık)")
                        elif ingilizce_kas == "lower_back":
                            aktif_bolgeler.append("Sırt (Alt Sırt)")
                        elif ingilizce_kas == "traps":
                            aktif_bolgeler.append("Sırt (Trapez)")
                            
                        if "row" in name_lower or "pull" in name_lower or "chin" in name_lower or "lat" in name_lower:
                            aktif_bolgeler.append("Biceps (Ön Kol)")
                            aktif_bolgeler.append("Omuz (Arka Omuz)")
                            
                    elif ingilizce_kas == "biceps":
                        aktif_bolgeler.append("Biceps (Ön Kol)")
                    elif ingilizce_kas == "triceps":
                        aktif_bolgeler.append("Triceps (Arka Kol)")
                        
                    elif ingilizce_kas in ["quadriceps", "hamstrings", "calves", "glutes"]:
                        if ingilizce_kas == "quadriceps":
                            aktif_bolgeler.append("Ön Bacak (Quadriceps)")
                        elif ingilizce_kas == "hamstrings":
                            aktif_bolgeler.append("Arka Bacak (Hamstring)")
                        elif ingilizce_kas == "calves":
                            aktif_bolgeler.append("Alt Bacak (Kalf)")
                        elif ingilizce_kas == "glutes":
                            aktif_bolgeler.append("Kalça")
                            
                        if "squat" in name_lower or "press" in name_lower or "lunge" in name_lower or "deadlift" in name_lower:
                            if "Kalça" not in aktif_bolgeler:
                                aktif_bolgeler.append("Kalça")
                            if "Arka Bacak (Hamstring)" not in aktif_bolgeler:
                                aktif_bolgeler.append("Arka Bacak (Hamstring)")
                            if "Ön Bacak (Quadriceps)" not in aktif_bolgeler and ("squat" in name_lower or "press" in name_lower):
                                aktif_bolgeler.append("Ön Bacak (Quadriceps)")
                                
                    elif ingilizce_kas == "abdominals":
                        aktif_bolgeler.append("Karın (Core)")
                    
                    if not aktif_bolgeler:
                        aktif_bolgeler.append(ingilizce_kas.capitalize())
                        
                    turkce_kas = ", ".join(aktif_bolgeler)

                    ham_tip = egzersiz.get('type', 'strength')
                    turkce_tip = tip_ceviri.get(ham_tip, ham_tip.capitalize())
                    ekipman = egzersiz.get('equipment', 'body_only').replace('_', ' ').capitalize()
                    ham_zorluk = egzersiz.get('difficulty', 'beginner')
                    turkce_zorluk = zorluk_ceviri.get(ham_zorluk, ham_zorluk.capitalize())
                    
                    kunye_metni = f"🎯 Tür: {turkce_tip}\n🛠️ Araç: {ekipman}\n📈 Seviye: {turkce_zorluk}"

                    talimat_ing = egzersiz.get('instructions', 'Talimat bulunmuyor.')
                    try:
                        talimat_tr = GoogleTranslator(source='en', target='tr').translate(talimat_ing)
                    except Exception:
                        talimat_tr = talimat_ing

                    self.tablo_egzersizler.setItem(satir_indeksi, 0, QTableWidgetItem(hareket_adi))
                    self.tablo_egzersizler.setItem(satir_indeksi, 1, QTableWidgetItem(turkce_kas))
                    self.tablo_egzersizler.setItem(satir_indeksi, 2, QTableWidgetItem(kunye_metni))
                    self.tablo_egzersizler.setItem(satir_indeksi, 3, QTableWidgetItem(talimat_tr))
                    
                    satir_indeksi += 1
            else:
                if not varsayilan_kelime:
                    QMessageBox.critical(self, "API Hatası", "API anahtarını kontrol edin.")
        except requests.exceptions.RequestException as e:
            if not varsayilan_kelime:
                QMessageBox.critical(self, "Bağlantı Hatası", f"Bağlantı kesildi: {str(e)}")

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
        secilen_kas_grubu = self.tablo_egzersizler.item(satir, 1).text() 
        secilen_aciklama = self.tablo_egzersizler.item(satir, 2).text() 

        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT egzersiz_id FROM Egzersizler WHERE hareket_adi = ?", (secilen_hareket,))
        sonuc = cursor.fetchone()
        
        if sonuc:
            yerel_egzersiz_id = sonuc[0]
        else:
            cursor.execute('INSERT INTO Egzersizler (hareket_adi, kas_grubu, aciklama) VALUES (?, ?, ?)', 
                           (secilen_hareket, secilen_kas_grubu, secilen_aciklama))
            yerel_egzersiz_id = cursor.lastrowid

        cursor.execute("INSERT INTO Programlar (kullanici_id, egzersiz_id, gun, set_sayisi, tekrar_sayisi) VALUES (?, ?, ?, ?, ?)", 
                       (self.aktif_kullanici_id, yerel_egzersiz_id, secilen_gun, 4, 10))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Başarılı", f"'{secilen_hareket}' başarıyla {secilen_gun} gününe eklendi!")
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

        # Alt Butonlar
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
            self.ekranlar.setCurrentIndex(1)
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
            html = f"<html><head><meta charset='utf-8'></head><body><h1 style='text-align:center; color:#2C3E50;'>Haftalık Fitness Programı</h1><h3 style='text-align:center; color:#7F8C8D;'>{self.lbl_bmi.text()}</h3><hr><table border='1' width='100%' cellspacing='0' cellpadding='10' style='border-collapse: collapse; text-align: center; font-family: Arial; font-size: 11px;'><tr style='background-color: #000BE3; color: white;'>"
            
            for gun in self.gunler:
                html += f"<th>{gun}</th>"
            html += "</tr>"
            
            for satir in range(self.tablo_takvim.rowCount()):
                bos_satir = True
                satir_html = "<tr>"
                for sutun in range(7):
                    item = self.tablo_takvim.item(satir, sutun)
                    if item and item.text():
                        bos_satir = False
                        metin = item.text().replace('\n', '<br>')
                        if "OFF DAY" in metin:
                            satir_html += f"<td style='background-color: #FFCCCC; font-weight: bold; color: black;'>{metin}</td>"
                        else:
                            satir_html += f"<td style='color: black;'>{metin}</td>"
                    else:
                        satir_html += "<td></td>"
                satir_html += "</tr>"
                
                if not bos_satir:
                    html += satir_html
                    
            html += "</table></body></html>"
            
            belge = QTextDocument()
            belge.setHtml(html)
            yazici = QPrinter(QPrinter.HighResolution)
            yazici.setOutputFormat(QPrinter.PdfFormat)
            yazici.setOutputFileName(dosya_yolu)
            yazici.setOrientation(QPrinter.Landscape)
            belge.print_(yazici)
            
            QMessageBox.information(self, "Başarılı", f"Programınız başarıyla kaydedildi!")

    def off_gun_belirle(self, sutun_indeksi):
        secilen_gun = self.gunler[sutun_indeksi]
        if secilen_gun in self.off_gunler:
            cevap = QMessageBox.question(self, "Off Day İptali", f"{secilen_gun} gününü dinlenme günü olmaktan çıkarmak istiyor musun?", QMessageBox.Yes | QMessageBox.No)
            if cevap == QMessageBox.Yes:
                self.off_gunler.remove(secilen_gun)
                self.takvimi_guncelle()
        else:
            cevap = QMessageBox.question(self, "Dinlenme Günü (Off Day)", f"{secilen_gun} gününü Off Day yapmak istiyor musun?", QMessageBox.Yes | QMessageBox.No)
            if cevap == QMessageBox.Yes:
                self.off_gunler.add(secilen_gun)
                conn = sqlite3.connect('spor_salonu.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Programlar WHERE kullanici_id = ? AND gun = ?", (self.aktif_kullanici_id, secilen_gun))
                conn.commit()
                conn.close()
                self.takvimi_guncelle()

    def takvime_gec(self):
        self.takvimi_guncelle()
        self.ekranlar.setCurrentIndex(2)

    def takvimi_guncelle(self):
        self.tablo_takvim.clearContents() 
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT p.gun, e.hareket_adi, e.kas_grubu FROM Programlar p JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id WHERE p.kullanici_id = ?", (self.aktif_kullanici_id,))
        programlar = cursor.fetchall()
        conn.close()
        
        gun_indeksleri = {"Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4, "Cumartesi": 5, "Pazar": 6}
        gun_satir_sayaci = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        for gun, hareket_adi, kas_grubu in programlar:
            sutun = gun_indeksleri.get(gun)
            if sutun is not None:
                satir = gun_satir_sayaci[sutun]
                if satir < self.tablo_takvim.rowCount():
                    birincil_kas = kas_grubu.split(',')[0].strip()
                    item = QTableWidgetItem(f"{hareket_adi}\n({birincil_kas})")
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
                    
                    if self.koyu_mod:
                        item.setForeground(QColor(255, 255, 255))
                    else:
                        item.setForeground(QColor(0, 0, 0))

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
        
        altyazi = QLabel("Hangi hareketlerin bu kası etkilediğini görmek için fareyi satırın üzerine getirip bekleyiniz (Hover/Tooltip).")
        altyazi.setObjectName("AltYazi")
        layout.addWidget(altyazi)

        self.tablo_analiz = QTableWidget()
        self.tablo_analiz.setColumnCount(3)
        self.tablo_analiz.setHorizontalHeaderLabels(["Durum Analizi", "Kas Grubu / Alt Kırılım", "Toplam Hareket Hacmi"])
        self.tablo_analiz.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_analiz.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo_analiz.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo_analiz.verticalHeader().setVisible(False)
        layout.addWidget(self.tablo_analiz)
        
        return sayfa

    def analiz_yap(self):
        hedef_kas_gruplari = [
            "Göğüs (Üst Göğüs)", "Göğüs (Alt Göğüs)", "Göğüs (Orta/Genel)",
            "Omuz (Ön Omuz)", "Omuz (Orta Omuz)", "Omuz (Arka Omuz)",
            "Sırt (Kanat / Genişlik)", "Sırt (Orta Sırt / Kalınlık)", "Sırt (Alt Sırt)", "Sırt (Trapez)",
            "Biceps (Ön Kol)", "Triceps (Arka Kol)",
            "Ön Bacak (Quadriceps)", "Arka Bacak (Hamstring)", "Alt Bacak (Kalf)", "Kalça", "Karın (Core)"
        ]
        
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT e.hareket_adi, e.kas_grubu FROM Programlar p JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id WHERE p.kullanici_id = ?", (self.aktif_kullanici_id,))
        programlar = cursor.fetchall()
        conn.close()
        
        kas_hareket_eslesmesi = {bolge: [] for bolge in hedef_kas_gruplari}
        
        for hareket_adi, kas_grubu_str in programlar:
            bolgeler = [b.strip() for b in kas_grubu_str.split(",")]
            for b in bolgeler:
                if b in kas_hareket_eslesmesi and hareket_adi not in kas_hareket_eslesmesi[b]:
                    kas_hareket_eslesmesi[b].append(hareket_adi)
                    
        self.tablo_analiz.setRowCount(0)
        
        if self.koyu_mod:
            renk_eksik = QColor(70, 30, 30)
            renk_asiri = QColor(80, 60, 20)
            renk_denge = QColor(25, 55, 35)
            yazi_rengi = QColor(255, 255, 255)
        else:
            renk_eksik = QColor(255, 225, 225)
            renk_asiri = QColor(255, 240, 190)
            renk_denge = QColor(220, 245, 220)
            yazi_rengi = QColor(0, 0, 0)

        for satir_indeksi, bolge in enumerate(hedef_kas_gruplari):
            self.tablo_analiz.insertRow(satir_indeksi)
            
            etkileyen_hareketler = kas_hareket_eslesmesi[bolge]
            hareket_sayisi = len(etkileyen_hareketler)
            
            if hareket_sayisi == 0:
                durum_metni = "❌ Bölge Çalıştırılmıyor"
                arka_plan_renk = renk_eksik
                tooltip_metni = f"Dikkat: {bolge} bölgesini tetikleyen hiçbir hareket bulunmuyor!"
            elif hareket_sayisi > 2:
                durum_metni = "⚠️ Aşırı Çalışma"
                arka_plan_renk = renk_asiri
                liste_metni = "\n• ".join(etkileyen_hareketler)
                tooltip_metni = f"UYARI: {bolge} için sınır aşıldı!\n\nHareketleriniz:\n• {liste_metni}"
            else:
                durum_metni = "✅ Dengeli"
                arka_plan_renk = renk_denge
                liste_metni = "\n• ".join(etkileyen_hareketler)
                tooltip_metni = f"Tebrikler! {bolge} için ideal hacim.\n\nHareketler:\n• {liste_metni}"

            item_durum = QTableWidgetItem(durum_metni)
            item_bolge = QTableWidgetItem(bolge)
            item_sayi = QTableWidgetItem(f"{hareket_sayisi} Hareket")
            
            item_durum.setTextAlignment(Qt.AlignCenter)
            item_sayi.setTextAlignment(Qt.AlignCenter)
            
            for item in [item_durum, item_bolge, item_sayi]:
                item.setBackground(arka_plan_renk)
                item.setForeground(yazi_rengi)
                item.setToolTip(tooltip_metni) 
                
            self.tablo_analiz.setItem(satir_indeksi, 0, item_durum)
            self.tablo_analiz.setItem(satir_indeksi, 1, item_bolge)
            self.tablo_analiz.setItem(satir_indeksi, 2, item_sayi)
            
        self.ekranlar.setCurrentIndex(3)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pencere = SporSalonuApp()
    pencere.show()
    sys.exit(app.exec_())