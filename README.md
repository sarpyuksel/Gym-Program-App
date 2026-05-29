# Fitness Planner 🏋️‍♂️

Fitness Planner, **Python (PyQt5)** ve **SQLite** kullanılarak geliştirilmiş, kapsamlı ve ticari standartlarda bir masaüstü uygulamasıdır. Kullanıcıların haftalık antrenman rutinlerini oluşturmalarına, yönetmelerine ve gelişmiş biyomekanik takiple analiz etmelerine yardımcı olmak için tasarlanmıştır.

### 🌟 Temel Özellikler

* **🌍 Canlı API Entegrasyonu ve Gerçek Zamanlı Çeviri:** *API-Ninjas* veritabanı üzerinden binlerce egzersizi dinamik olarak çeker. Karmaşık İngilizce egzersiz talimatlarını otomatik olarak Türkçeye çeviren asenkron bir çeviri motoruna (`deep-translator`) sahiptir.
* **🧠 Akıllı Biyomekanik Analiz Motoru:** **17 spesifik alt kas grubunu** (Örn: Üst Göğüs, Arka Omuz) analiz ederek temel kas takibinin ötesine geçer. Birleşik/hibrit (compound) hareketleri otomatik olarak algılar ve eksik kas grupları veya olası aşırı çalışma (overtraining) durumlarında kullanıcıyı uyarır.
* **📄 Dinamik PDF Raporlama:** Haftalık programı tek tıkla şık bir yatay HTML/PDF belgesine dönüştüren yerleşik bir işleme motoru içerir.
* **🎨 Premium UI/UX ve Bağlamsal Yönlendirme:** Özel **Koyu ve Açık modlara** sahip, son derece optimize edilmiş, tam duyarlı (responsive) bir arayüz sunar. Boş takvim hücrelerine çift tıklayarak egzersiz kütüphanesinde o güne otomatik yönlendirme gibi sezgisel etkileşimler içerir.
* **🗄️ İlişkisel Veritabanı Yönetimi:** Kullanıcı profillerini, özel egzersiz önbelleklerini ve haftalık programları güçlü bir SQLite mimarisi kullanarak güvenle saklar.

### 🚀 Kurulum ve Çalıştırma

1. Repoyu klonlayın:
`git clone https://github.com/sarpyuksel/Fitness-Planner-Pro.git`

2. Gerekli kütüphaneleri yükleyin:
`pip install PyQt5 requests deep-translator`

3. Uygulamayı çalıştırın:
`python main_api.py`

