import sys
import sqlite3
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
        self.setWindowTitle("Haftalık Fitness Programlayıcı")
        self.setGeometry(100, 100, 1050, 650)
        self.aktif_kullanici_id = 1 
        
        self.gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.off_gunler = set()

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
        ana_layout = QHBoxLayout(merkez_widget)

        menu_layout = QVBoxLayout()
        self.btn_profil = QPushButton("1. Profil Bilgileri")
        self.btn_havuz = QPushButton("2. Egzersiz Arama & Ekle")
        self.btn_takvim = QPushButton("3. Haftalık Programım")
        self.btn_analiz = QPushButton("4. Program Analizi (Kas Kontrolü)")

        butonlar = [self.btn_profil, self.btn_havuz, self.btn_takvim, self.btn_analiz]
        for btn in butonlar:
            btn.setMinimumHeight(40)
            menu_layout.addWidget(btn)
        
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

        ana_layout.addLayout(menu_layout, 1)
        ana_layout.addWidget(self.ekranlar, 4)

        self.btn_profil.clicked.connect(lambda: self.ekranlar.setCurrentIndex(0))
        self.btn_havuz.clicked.connect(lambda: self.ekranlar.setCurrentIndex(1))
        self.btn_takvim.clicked.connect(self.takvime_gec) 
        self.btn_analiz.clicked.connect(self.analiz_yap) 

        self.egzersizleri_veritabanindan_cek()
        self.profil_verilerini_yukle() 

    # --- EKRAN 1: PROFIL BİLGİLERİ ---
    def profil_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)

        baslik = QLabel("Profil Bilgileriniz")
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")

        # YENİ: Ad Soyad Alanı eklendi
        self.input_ad_soyad = QLineEdit()
        self.input_ad_soyad.setText("Sarp Yüksel") # Varsayılan olarak ismin eklendi
        self.input_ad_soyad.setPlaceholderText("Adınız Soyadınız")
        self.input_ad_soyad.setStyleSheet("padding: 8px; font-size: 14px; margin-left: 200px; margin-right: 200px; margin-bottom: 10px;")

        self.input_boy = QLineEdit()
        self.input_boy.setPlaceholderText("Boyunuz (Örn: 180 cm)")
        self.input_boy.setStyleSheet("padding: 8px; font-size: 14px; margin-left: 200px; margin-right: 200px; margin-bottom: 10px;")

        self.input_kilo = QLineEdit()
        self.input_kilo.setPlaceholderText("Kilonuz (Örn: 75 kg)")
        self.input_kilo.setStyleSheet("padding: 8px; font-size: 14px; margin-left: 200px; margin-right: 200px; margin-bottom: 20px;")

        btn_kaydet = QPushButton("Kaydet ve Programa Başla")
        btn_kaydet.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 16px; font-weight: bold; margin-left: 250px; margin-right: 250px;")
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
            cursor.execute("UPDATE Kullanicilar SET kullanici_adi = ?, boy = ?, kilo = ? WHERE kullanici_id = ?", 
                           (ad, boy, kilo, self.aktif_kullanici_id))
            conn.commit()
            conn.close()

            self.bmi_guncelle(boy, kilo)
            QMessageBox.information(self, "Başarılı", "Bilgileriniz kaydedildi!")
            self.ekranlar.setCurrentIndex(1) 
            
        except ValueError:
            QMessageBox.warning(self, "Hata", "Lütfen boy ve kilo için sadece sayı giriniz! (Örn: Boy: 180, Kilo: 75.5)")
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def profil_verilerini_yukle(self):
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
        durum = ""
        if bmi < 18.5: durum = "Zayıf"
        elif 18.5 <= bmi < 24.9: durum = "Normal"
        elif 25 <= bmi < 29.9: durum = "Fazla Kilolu"
        else: durum = "Aşırı"

        # Kişinin ismini de alt bilgiye ekledik
        metin = f"👤 {self.input_ad_soyad.text()}  |  📏 {boy_cm} cm  |  ⚖️ {kilo} kg  |  🔥 BMI: {bmi:.1f} ({durum})"
        self.lbl_bmi.setText(metin)

    # --- EKRAN 2: EGZERSİZ HAVUZU ---
    def egzersiz_havuzu_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)

        arama_layout = QHBoxLayout()
        self.input_arama = QLineEdit()
        self.input_arama.setPlaceholderText("Hareket ara (Örn: chest press)...")
        self.input_arama.setStyleSheet("padding: 8px; font-size: 14px;")
        self.input_arama.textChanged.connect(self.egzersiz_ara) 
        
        arama_layout.addWidget(QLabel("🔍 Arama:"))
        arama_layout.addWidget(self.input_arama)
        layout.addLayout(arama_layout)

        self.tablo_egzersizler = QTableWidget()
        self.tablo_egzersizler.setColumnCount(4)
        self.tablo_egzersizler.setHorizontalHeaderLabels(["ID", "Hareket Adı", "Çalışan Bölge", "Açıklama"])
        self.tablo_egzersizler.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_egzersizler.setColumnHidden(0, True) 
        self.tablo_egzersizler.setSelectionBehavior(QAbstractItemView.SelectRows) 
        self.tablo_egzersizler.setEditTriggers(QAbstractItemView.NoEditTriggers) 
        layout.addWidget(self.tablo_egzersizler)

        ekleme_layout = QHBoxLayout()
        self.combo_gun = QComboBox()
        self.combo_gun.addItems(self.gunler)
        self.combo_gun.setStyleSheet("padding: 5px; font-size: 14px;")

        btn_ekle = QPushButton("Seçili Hareketi Programa Ekle ➕")
        btn_ekle.setStyleSheet("background-color: #008CBA; color: white; padding: 8px; font-weight: bold;")
        btn_ekle.clicked.connect(self.programa_ekle)

        ekleme_layout.addWidget(QLabel("Hangi Güne Eklensin? :"))
        ekleme_layout.addWidget(self.combo_gun)
        ekleme_layout.addWidget(btn_ekle)
        layout.addLayout(ekleme_layout)
        return sayfa

    def egzersizleri_veritabanindan_cek(self, arama_metni=""):
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT egzersiz_id, hareket_adi, kas_grubu, aciklama FROM Egzersizler")
        tum_sonuclar = cursor.fetchall()
        conn.close()

        def tr_kucult(metin): return metin.replace("I", "ı").replace("İ", "i").lower()
        arama_metni_kucuk = tr_kucult(arama_metni)

        self.tablo_egzersizler.setRowCount(0)
        satir_indeksi = 0
        for satir_verisi in tum_sonuclar:
            hareket_adi = str(satir_verisi[1])
            if arama_metni_kucuk in tr_kucult(hareket_adi):
                self.tablo_egzersizler.insertRow(satir_indeksi)
                for sutun_indeksi, veri in enumerate(satir_verisi):
                    self.tablo_egzersizler.setItem(satir_indeksi, sutun_indeksi, QTableWidgetItem(str(veri)))
                satir_indeksi += 1

    def egzersiz_ara(self):
        self.egzersizleri_veritabanindan_cek(self.input_arama.text())

    def programa_ekle(self):
        secilen_gun = self.combo_gun.currentText()
        if secilen_gun in self.off_gunler:
            QMessageBox.warning(self, "İşlem Engellendi", f"Dikkat: {secilen_gun} gününü Off Day (Dinlenme) olarak belirlediniz!\n\nDinlenme gününe egzersiz ekleyemezsiniz.")
            return

        satir = self.tablo_egzersizler.currentRow()
        if satir < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce tablodan bir hareket seçin!")
            return

        secilen_id = self.tablo_egzersizler.item(satir, 0).text()
        secilen_hareket = self.tablo_egzersizler.item(satir, 1).text()

        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Programlar (kullanici_id, egzersiz_id, gun, set_sayisi, tekrar_sayisi) VALUES (?, ?, ?, ?, ?)", 
                       (self.aktif_kullanici_id, int(secilen_id), secilen_gun, 4, 10))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Başarılı", f"'{secilen_hareket}' başarıyla {secilen_gun} gününe eklendi!")
        self.takvimi_guncelle()

    # --- EKRAN 3: TAKVİM VE PDF İNDİRME ---
    def takvim_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)
        
        baslik = QLabel("Haftalık Çalışma Programım\n(Silmek istediğiniz hareketin üzerine ÇİFT TIKLAYIN)")
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #555;")
        layout.addWidget(baslik)

        self.tablo_takvim = QTableWidget()
        self.tablo_takvim.setColumnCount(7)
        self.tablo_takvim.setRowCount(10) 
        self.tablo_takvim.setHorizontalHeaderLabels(self.gunler)
        self.tablo_takvim.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablo_takvim.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.tablo_takvim.horizontalHeader().sectionClicked.connect(self.off_gun_belirle)
        self.tablo_takvim.cellDoubleClicked.connect(self.hareketi_sil)
        layout.addWidget(self.tablo_takvim)

        # ALT BİLGİ VE PDF BUTONU
        alt_layout = QHBoxLayout()
        
        # YENİ: PDF Çıktı Butonu
        btn_pdf = QPushButton("📄 Programı PDF Olarak İndir")
        btn_pdf.setStyleSheet("background-color: #E74C3C; color: white; padding: 8px; font-weight: bold; border-radius: 5px;")
        btn_pdf.clicked.connect(self.pdf_olarak_indir)
        
        alt_layout.addWidget(btn_pdf)
        alt_layout.addStretch() 
        
        self.lbl_bmi = QLabel("Boy ve Kilo bilgisi henüz girilmedi.")
        self.lbl_bmi.setStyleSheet("font-size: 14px; font-weight: bold; color: #00796b; padding: 5px;")
        alt_layout.addWidget(self.lbl_bmi)
        
        layout.addLayout(alt_layout)
        return sayfa

    def pdf_olarak_indir(self):
        """Tablodaki programı HTML tablosuna çevirip QPrinter ile PDF'e basar."""
        dosya_yolu, _ = QFileDialog.getSaveFileName(self, "PDF Olarak Kaydet", "Haftalik_Fitness_Programi.pdf", "PDF Dosyaları (*.pdf)")
        
        if dosya_yolu:
            # 1. HTML Şablonunu Oluştur
            html = f"""
            <h1 style='text-align:center; color:#2C3E50;'>Haftalık Fitness Programı</h1>
            <h3 style='text-align:center; color:#7F8C8D;'>{self.lbl_bmi.text()}</h3>
            <hr>
            <table border='1' width='100%' cellspacing='0' cellpadding='10' style='border-collapse: collapse; text-align: center; font-family: Arial;'>
                <tr style='background-color: #34495E; color: white;'>
            """
            
            # Gün başlıklarını ekle
            for gun in self.gunler:
                html += f"<th>{gun}</th>"
            html += "</tr>"
            
            # Tablodaki dolu satırları HTML'e aktar
            for satir in range(self.tablo_takvim.rowCount()):
                bos_satir = True
                satir_html = "<tr>"
                
                for sutun in range(7):
                    item = self.tablo_takvim.item(satir, sutun)
                    if item and item.text():
                        bos_satir = False
                        # PyQt tablosundaki \n karakterlerini HTML'deki <br> ile değiştiriyoruz
                        metin = item.text().replace('\n', '<br>')
                        
                        # Eğer hücre OFF DAY ise arka planı kırmızı yap
                        if "OFF DAY" in metin:
                            satir_html += f"<td style='background-color: #FFCCCC; font-weight: bold;'>{metin}</td>"
                        else:
                            satir_html += f"<td>{metin}</td>"
                    else:
                        satir_html += "<td></td>"
                satir_html += "</tr>"
                
                # Sadece içinde veri olan satırları PDF'e ekle
                if not bos_satir:
                    html += satir_html
                    
            html += "</table>"
            
            # 2. QPrinter ile PDF oluştur
            belge = QTextDocument()
            belge.setHtml(html)
            
            yazici = QPrinter(QPrinter.HighResolution)
            yazici.setOutputFormat(QPrinter.PdfFormat)
            yazici.setOutputFileName(dosya_yolu)
            yazici.setOrientation(QPrinter.Landscape) # Tablo sığsın diye yatay çıktı veriyoruz
            
            belge.print_(yazici)
            
            QMessageBox.information(self, "Başarılı", f"Programınız başarıyla '{dosya_yolu}' konumuna kaydedildi!")

    def hareketi_sil(self, satir, sutun):
        item = self.tablo_takvim.item(satir, sutun)
        if not item or not item.text() or "OFF DAY" in item.text():
            return

        secilen_gun = self.gunler[sutun]
        hareket_adi = item.text().split('\n')[0] 

        cevap = QMessageBox.question(self, "Hareketi Sil", 
                                     f"{secilen_gun} günündeki '{hareket_adi}' hareketini programdan silmek istiyor musun?", 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if cevap == QMessageBox.Yes:
            conn = sqlite3.connect('spor_salonu.db')
            cursor = conn.cursor()
            sorgu = '''
                DELETE FROM Programlar 
                WHERE kullanici_id = ? AND gun = ? 
                AND egzersiz_id = (SELECT egzersiz_id FROM Egzersizler WHERE hareket_adi = ?)
            '''
            cursor.execute(sorgu, (self.aktif_kullanici_id, secilen_gun, hareket_adi))
            conn.commit()
            conn.close()
            self.takvimi_guncelle()

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
        cursor.execute('''
            SELECT p.gun, e.hareket_adi, e.kas_grubu 
            FROM Programlar p
            JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id
            WHERE p.kullanici_id = ?
        ''', (self.aktif_kullanici_id,))
        programlar = cursor.fetchall()
        conn.close()

        gun_indeksleri = {"Pazartesi": 0, "Salı": 1, "Çarşamba": 2, "Perşembe": 3, "Cuma": 4, "Cumartesi": 5, "Pazar": 6}
        gun_satir_sayaci = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        for gun, hareket_adi, kas_grubu in programlar:
            sutun = gun_indeksleri.get(gun)
            if sutun is not None:
                satir = gun_satir_sayaci[sutun]
                if satir < self.tablo_takvim.rowCount():
                    hucre_metni = f"{hareket_adi}\n({kas_grubu})"
                    item = QTableWidgetItem(hucre_metni)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.tablo_takvim.setItem(satir, sutun, item)
                    gun_satir_sayaci[sutun] += 1

        for sutun, gun in enumerate(self.gunler):
            if gun in self.off_gunler:
                for satir in range(self.tablo_takvim.rowCount()):
                    item = self.tablo_takvim.item(satir, sutun)
                    if not item:
                        item = QTableWidgetItem()
                        self.tablo_takvim.setItem(satir, sutun, item)
                    item.setBackground(QColor(255, 153, 153)) 
                    if satir == 0:
                        item.setText("OFF DAY\n(Dinlenme)")
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                        item.setTextAlignment(Qt.AlignCenter) 

    # --- EKRAN 4: ANALİZ ALGORİTMASI ---
    def analiz_ekrani_olustur(self):
        sayfa = QWidget()
        layout = QVBoxLayout(sayfa)
        
        baslik = QLabel("📊 Haftalık Program Analizi")
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 20px; color: #2C3E50;")
        layout.addWidget(baslik)

        self.lbl_analiz_sonuc = QLabel("Analiz için butona basınız...")
        self.lbl_analiz_sonuc.setStyleSheet("font-size: 16px; line-height: 1.5; padding: 20px; background-color: #f9f9f9; border-radius: 10px;")
        self.lbl_analiz_sonuc.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        layout.addWidget(self.lbl_analiz_sonuc)
        layout.addStretch()
        return sayfa

    def analiz_yap(self):
        hedef_kas_gruplari = ["Göğüs", "Sırt", "Omuz", "Triceps", "Biceps", "Ön Bacak", "Arka Bacak"]
        conn = sqlite3.connect('spor_salonu.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT e.kas_grubu 
            FROM Programlar p
            JOIN Egzersizler e ON p.egzersiz_id = e.egzersiz_id
            WHERE p.kullanici_id = ?
        ''', (self.aktif_kullanici_id,))
        calisilan_bolgeler = [row[0].strip() for row in cursor.fetchall()]
        conn.close()

        sonuc_metni = "<b>Haftalık Kas Grubu Kapsamı:</b><br><br>"
        eksik_sayisi = 0

        for bolge in hedef_kas_gruplari:
            if any(bolge.lower() in b.lower() or b.lower() in bolge.lower() for b in calisilan_bolgeler):
                sonuc_metni += f"<span style='color: green;'>✅ {bolge} (Programa Eklenmiş)</span><br>"
            else:
                sonuc_metni += f"<span style='color: red;'>❌ {bolge} (EKSİK!)</span><br>"
                eksik_sayisi += 1
        
        if eksik_sayisi == 0:
            sonuc_metni += "<br>🎉 <b>Mükemmel!</b> Tüm kas gruplarını kapsayan dengeli bir program hazırladın."
        else:
            sonuc_metni += f"<br>⚠️ <b>Dikkat:</b> Programında eksik kalan {eksik_sayisi} bölge var. Simetrik bir gelişim için bu bölgelere hareket eklemelisin."

        self.lbl_analiz_sonuc.setText(sonuc_metni)
        self.ekranlar.setCurrentIndex(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = SporSalonuApp()
    pencere.show()
    sys.exit(app.exec_())