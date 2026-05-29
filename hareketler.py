import sqlite3

def yeni_hareketleri_ekle():
    conn = sqlite3.connect('spor_salonu.db')
    cursor = conn.cursor()

    # Ekleyeceğimiz yeni hareketler listesi (Hareket Adı, Kas Grubu, Açıklama)
    yeni_egzersizler = [
        ('Bench Press', 'Göğüs', 'Temel serbest ağırlık göğüs itme hareketi.'),
        ('Lateral Raise', 'Omuz', 'Orta omuz kaslarını izole eden dambıl yana açış hareketi.'),
        ('Shoulder Press Machine', 'Omuz', 'Omuz kaslarını çalıştıran temel itme makinesi.'),
        ('Leg Extension', 'Ön Bacak', 'Ön bacak (quadriceps) kaslarını izole eden makine hareketi.'),
        ('Leg Curl', 'Arka Bacak', 'Arka bacak (hamstring) kaslarını izole eden makine hareketi.'),
        ('Hammer Curl', 'Biceps', 'Biceps ve brachialis (ön kol) kaslarını çalıştıran dambıl hareketi.'),
        ('Reverse Fly', 'Omuz', 'Arka omuz kaslarını çalıştıran makine veya dambıl açış hareketi.'),
        ('Peck Deck (Fly Machine)', 'Göğüs', 'İç göğüs kaslarını sıkıştırmaya yarayan makine hareketi.'),
        ('Incline Dumbbell Press', 'Göğüs', 'Üst göğüs kaslarını hedefleyen eğimli sehpada itme hareketi.'),
        ('Push Down', 'Triceps', 'Triceps (arka kol) kaslarını çalıştıran kablolu aşağı itme hareketi.')
    ]

    eklenen_sayisi = 0
    for egzersiz in yeni_egzersizler:
        cursor.execute("SELECT COUNT(*) FROM Egzersizler WHERE hareket_adi = ?", (egzersiz[0],))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Egzersizler (hareket_adi, kas_grubu, aciklama) VALUES (?, ?, ?)", egzersiz)
            eklenen_sayisi += 1

    conn.commit()
    conn.close()
    
    print(f"İşlem tamamlandı! Veritabanına {eklenen_sayisi} yeni hareket başarıyla eklendi.")

if __name__ == "__main__":
    yeni_hareketleri_ekle()