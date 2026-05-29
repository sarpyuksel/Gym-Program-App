import sqlite3

def veritabani_olustur():
    
    conn = sqlite3.connect('spor_salonu.db')
    cursor = conn.cursor()

    # 1. Kullanıcılar Tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Kullanicilar (
        kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT UNIQUE NOT NULL,
        sifre TEXT NOT NULL,
        hedef TEXT,
        kilo REAL
    )
    ''')

    # 2. Egzersizler Tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Egzersizler (
        egzersiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hareket_adi TEXT NOT NULL,
        kas_grubu TEXT NOT NULL,
        aciklama TEXT
    )
    ''')

    # 3. Programlar Tablosu (İlişkisel Tablo)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Programlar (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_id INTEGER,
        egzersiz_id INTEGER,
        gun TEXT NOT NULL,
        set_sayisi INTEGER,
        tekrar_sayisi INTEGER,
        durum TEXT DEFAULT 'Bekliyor', -- Antrenman yapıldı mı yapılmadı mı takibi için
        FOREIGN KEY(kullanici_id) REFERENCES Kullanicilar(kullanici_id),
        FOREIGN KEY(egzersiz_id) REFERENCES Egzersizler(egzersiz_id)
    )
    ''')

    # Başlangıç için birkaç temel egzersiz ekleyelim (Eğer tablo boşsa)
    cursor.execute("SELECT COUNT(*) FROM Egzersizler")
    if cursor.fetchone()[0] == 0:
        ornek_egzersizler = [
            ('Chest Press Machine', 'Göğüs', 'Göğüs kaslarını izole eden temel makine hareketi.'),
            ('Lat Pulldown', 'Sırt', 'Sırt kaslarını ve kanatları çalıştıran çekme hareketi.'),
            ('Leg Press', 'Bacak', 'Üst bacak ve kalça kaslarını çalıştıran itme hareketi.'),
            ('Dumbbell Curl', 'Biceps', 'Ön kol kaslarını çalıştıran temel hareket.'),
            ('Triceps Pushdown', 'Triceps', 'Arka kol kaslarını çalıştıran kablolu itme hareketi.')
        ]
        cursor.executemany("INSERT INTO Egzersizler (hareket_adi, kas_grubu, aciklama) VALUES (?, ?, ?)", ornek_egzersizler)

    conn.commit()
    conn.close()
    print("Veritabanı ve 3 tablo başarıyla oluşturuldu. Örnek egzersizler eklendi.")

if __name__ == "__main__":
    veritabani_olustur()