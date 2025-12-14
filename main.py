import csv
import random
import os
import sys
import requests
import shutil
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex, platform
from plyer import tts

# --- AYARLAR ---
# Google Sheets CSV linkini buraya yapıştır (Tırnak içine)
CSV_URL = "LINK_YOK" 

# Göz yormayan koyu arka plan
Window.clearcolor = (0.1, 0.1, 0.1, 1)

class VeriYoneticisi:
    def __init__(self):
        self.dosya_yolu = self.dosya_yolu_bul()
        self.veriler = []
        self.yukle()

    def dosya_yolu_bul(self):
        # Android ve Bilgisayar ayrımı
        if platform == 'android':
            from android.storage import app_storage_path
            klasor = app_storage_path()
        else:
            klasor = os.getcwd()
        
        yol = os.path.join(klasor, 'kelimeler.csv')
        
        # Eğer çalışma alanında dosya yoksa, APK içinden kopyala
        if not os.path.exists(yol) and os.path.exists('kelimeler.csv'):
            try: shutil.copy('kelimeler.csv', yol)
            except: pass
        return yol

    def internetten_guncelle(self):
        try:
            if "http" not in CSV_URL: return False, "Link Girilmemiş!"
            
            response = requests.get(CSV_URL, timeout=15)
            response.raise_for_status()
            
            # Dosyayı binary modda yaz (Karakter hatası olmasın diye)
            with open(self.dosya_yolu, 'wb') as f:
                f.write(response.content)
            
            self.yukle()
            return True, "Başarıyla Güncellendi!"
        except Exception as e:
            return False, f"Hata: {str(e)}"

    def yukle(self):
        self.veriler = []
        if not os.path.exists(self.dosya_yolu): return
        
        try:
            with open(self.dosya_yolu, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content: return
                
                # Ayırıcıyı otomatik tespit et
                delimiter = ';' if ';' in content.splitlines()[0] else ','
                f.seek(0)
                
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                
                # Başlık satırını atlama kontrolü
                start_index = 0
                if rows and len(rows[0]) > 0 and "Sıra" in str(rows[0][0]):
                    start_index = 1
                
                for i in range(start_index, len(rows)):
                    row = rows[i]
                    # Eksik sütun varsa o satırı atla (Çökme önleyici)
                    if len(row) < 2: continue
                    
                    # Güvenli veri alma (Index hatası vermez)
                    def safe_get(idx): return row[idx] if idx < len(row) else ""
                    
                    self.veriler.append({
                        "tr": safe_get(1), 
                        "en": safe_get(2), 
                        "ipa": safe_get(3), 
                        "okunus": safe_get(4), 
                        "cen": safe_get(5), 
                        "ctr": safe_get(6)
                    })
        except Exception as e:
            print(f"Yükleme Hatası: {e}")

YONETICI = VeriYoneticisi()

class InfoEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        self.lbl = Label(text="...", font_size='22sp', halign='center')
        layout.add_widget(self.lbl)
        
        btn = Button(text="Geri Dön", background_color=(1,0.6,0,1), size_hint=(1,0.2))
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn)
        self.add_widget(layout)
        
    def on_pre_enter(self):
        sayi = len(YONETICI.veriler)
        durum = "Aktif" if sayi > 0 else "Boş / Hatalı"
        self.lbl.text = f"Kelime Sayısı:\\n{sayi}\\n\\nVeritabanı Durumu:\\n{durum}"

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text="İngilizce Ezber", font_size='40sp'))
        
        # Butonlar
        btn1 = Button(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), on_press=lambda x: self.gecis("kelime"))
        btn2 = Button(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), on_press=lambda x: self.gecis("cumle"))
        btn3 = Button(text="Listeyi Güncelle", background_color=(1,0.5,0,1), on_press=self.guncelle)
        btn4 = Button(text="Info / Bilgi", background_color=(0,0.8,0.8,1), on_press=lambda x: setattr(self.manager, 'current', 'info'))
        btn5 = Button(text="Çıkış", background_color=(0.8,0.2,0.2,1), on_press=lambda x: sys.exit())
        
        for b in [btn1,btn2,btn3,btn4,btn5]: layout.add_widget(b)
        self.add_widget(layout)

    def guncelle(self, instance):
        p = Popup(title='İşlem', content=Label(text='İndiriliyor...'), size_hint=(0.6, 0.3))
        p.open()
        basari, msj = YONETICI.internetten_guncelle()
        p.dismiss()
        Popup(title='Durum', content=Label(text=msj), size_hint=(0.8, 0.4)).open()

    def gecis(self, mod):
        # LİSTE BOŞSA ÇÖKMESİN, UYARI VERSİN
        if not YONETICI.veriler:
            Popup(title='Uyarı', content=Label(text='Kelime listesi boş!\\nLütfen güncelleyin.'), size_hint=(0.8, 0.4)).open()
            return
        
        self.manager.get_screen('calisma').baslat(mod)
        self.manager.current = 'calisma'

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gecmis, self.aktif, self.yon, self.cevrildi = [], None, "tr_to_en", False
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # KART BUTONU (text_size ve halign ile metin taşmasını önledik)
        self.kart = Button(text="Başla", font_size='24sp', halign='center', valign='middle')
        self.kart.bind(size=self.kart.setter('text_size')) 
        self.kart.bind(on_press=self.cevir)
        
        # SES BUTONU
        self.btn_ses = Button(text="🔊 DİNLE", size_hint=(1, 0.15), background_color=(0.5, 0.5, 0.5, 1))
        self.btn_ses.bind(on_press=self.seslendir)
        
        # NAVİGASYON
        btns = BoxLayout(size_hint=(1,0.15), spacing=10)
        btns.add_widget(Button(text="Geri", on_press=self.geri))
        btns.add_widget(Button(text="Menü", on_press=lambda x: setattr(self.manager, 'current', 'menu')))
        btns.add_widget(Button(text="İleri", on_press=self.ileri))
        
        layout.add_widget(self.kart)
        layout.add_widget(self.btn_ses)
        layout.add_widget(btns)
        self.add_widget(layout)

    def baslat(self, mod):
        self.mod = mod
        self.gecmis = []
        self.ileri(None)

    def seslendir(self, i):
        if self.aktif:
            try:
                # İngilizce metni bul ve oku
                metin = self.aktif['en'] if self.mod == "kelime" else self.aktif['cen']
                if metin: tts.speak(metin)
            except: pass

    def guncelle(self):
        try:
            self.kart.markup = True
            v = self.aktif
            
            if not self.cevrildi:
                # ÖN YÜZ
                self.kart.background_color = get_color_from_hex('#455A64') # Koyu Gri
                soru = (v["tr"] if self.yon == "tr_to_en" else v["en"]) if self.mod == "kelime" else (v["ctr"] if self.yon == "tr_to_en" else v["cen"])
                ipucu = "(Türkçesi?)" if self.yon == "en_to_tr" else "(İngilizcesi?)"
                self.kart.text = f"[b]{soru}[/b]\\n\\n\\n[size=18]{ipucu}[/size]"
            else:
                # ARKA YÜZ
                self.kart.background_color = get_color_from_hex('#FFECB3') # Açık Sarı
                self.kart.color = (0,0,0,1) # Siyah Yazı
                
                # --- KRİTİK DEĞİŞİKLİK: IPA KALDIRILDI ---
                # Fonetik semboller bazı telefonlarda çökme yapar. Sadece okunuşu gösteriyoruz.
                if self.mod == "kelime":
                    # Örn: apple [epıl] --- Elma
                    self.kart.text = f"[size=32][b]{v['en']}[/b][/size]\\n[{v['okunus']}]\\n---\\n{v['tr']}"
                else:
                    self.kart.text = f"[b]{v['cen']}[/b]\\n---\\n{v['ctr']}"
        except Exception as e:
            self.kart.text = "Görüntüleme Hatası"

    def cevir(self, i):
        self.cevrildi = not self.cevrildi
        self.guncelle()

    def ileri(self, i):
        # Listede veri yoksa işlem yapma (Çökme Koruması)
        if not YONETICI.veriler: return

        if getattr(self, 'aktif', None):
            self.gecmis.append({"v": self.aktif, "y": self.yon})
        
        self.aktif = random.choice(YONETICI.veriler)
        self.yon = random.choice(["tr_to_en", "en_to_tr"])
        self.cevrildi = False
        self.guncelle()

    def geri(self, i):
        if self.gecmis:
            son = self.gecmis.pop()
            self.aktif = son["v"]
            self.yon = son["y"]
            self.cevrildi = False
            self.guncelle()

class AppMain(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(AnaMenu(name='menu'))
        sm.add_widget(InfoEkrani(name='info'))
        sm.add_widget(Calisma(name='calisma'))
        return sm

if __name__ == '__main__':
    AppMain().run()
