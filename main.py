import csv
import random
import os
import sys
import requests
import shutil
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.utils import get_color_from_hex, platform

# --- AYARLAR ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPTfdbSV0cuDHK6hl1bnmOXUa_OzVnmYNIKhiiGvlVMMnPsUf27aN8dWqyuvkd4q84aINz5dvLoYmI/pub?output=csv" 

Window.clearcolor = (0.1, 0.1, 0.1, 1)

# --- GLOBAL AYARLAR ---
AYARLAR = {
    "konusma_hizi": 1.0  # Varsayılan Normal (1.0)
}

# --- GELİŞMİŞ SES YÖNETİCİSİ (ANDROID NATIVE) ---
class SesYoneticisi:
    def __init__(self):
        self.tts = None
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                
                # TTS Motorunu Başlat
                self.tts = TextToSpeech(PythonActivity.mActivity, None)
                self.tts.setLanguage(Locale.US)
            except Exception as e:
                print(f"TTS Başlatma Hatası: {e}")
        else:
            # Bilgisayar için basit plyer (Hız ayarı çalışmayabilir ama ses verir)
            try:
                from plyer import tts
                self.plyer_tts = tts
            except: pass

    def oku(self, metin):
        hiz = AYARLAR["konusma_hizi"]
        
        if platform == 'android' and self.tts:
            try:
                self.tts.setSpeechRate(float(hiz))
                self.tts.speak(metin, 0, None)
            except Exception as e:
                print(f"Okuma Hatası: {e}")
        else:
            # PC Fallback
            try:
                self.plyer_tts.speak(metin)
            except: 
                print(f"Seslendiriliyor (PC): {metin} (Hız: {hiz})")

SES = SesYoneticisi()

class VeriYoneticisi:
    def __init__(self):
        self.dosya_yolu = self.dosya_yolu_bul()
        self.veriler = []
        self.yukle()

    def dosya_yolu_bul(self):
        if platform == 'android':
            from android.storage import app_storage_path
            klasor = app_storage_path()
        else:
            klasor = os.getcwd()
        
        yol = os.path.join(klasor, 'kelimeler.csv')
        
        if not os.path.exists(yol) and os.path.exists('kelimeler.csv'):
            try: shutil.copy('kelimeler.csv', yol)
            except: pass
        return yol

    def internetten_guncelle(self):
        try:
            if "http" not in CSV_URL: return False, "Link Girilmemiş!"
            response = requests.get(CSV_URL, timeout=15)
            response.raise_for_status()
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
                delimiter = ';' if ';' in content.splitlines()[0] else ','
                f.seek(0)
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                start = 1 if rows and "Sıra" in str(rows[0][0]) else 0
                
                for i in range(start, len(rows)):
                    row = rows[i]
                    if len(row) < 2: continue
                    def safe(idx): return row[idx].replace("\\n", " ").strip() if idx < len(row) else ""
                    
                    self.veriler.append({
                        "tr": safe(1), "en": safe(2), "ipa": safe(3), 
                        "okunus": safe(4), "cen": safe(5), "ctr": safe(6)
                    })
        except Exception as e:
            print(f"Hata: {e}")

YONETICI = VeriYoneticisi()

# --- AYARLAR EKRANI (YENİ) ---
class AyarlarEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        layout.add_widget(Label(text="Konuşma Hızı Ayarı", font_size='28sp', size_hint=(1, 0.2)))
        
        # Hız Seçenekleri (Toggle Buttonlar)
        grid = GridLayout(cols=3, spacing=10, size_hint=(1, 0.2))
        
        self.btn_yavas = ToggleButton(text="Yavaş\n(0.5x)", group='hiz', background_color=(0.3, 0.3, 0.3, 1))
        self.btn_normal = ToggleButton(text="Normal\n(1.0x)", group='hiz', state='down', background_color=(0.2, 0.6, 0.8, 1))
        self.btn_hizli = ToggleButton(text="Hızlı\n(1.5x)", group='hiz', background_color=(0.3, 0.3, 0.3, 1))
        
        self.btn_yavas.bind(on_press=lambda x: self.hiz_degistir(0.5))
        self.btn_normal.bind(on_press=lambda x: self.hiz_degistir(1.0))
        self.btn_hizli.bind(on_press=lambda x: self.hiz_degistir(1.5))
        
        grid.add_widget(self.btn_yavas)
        grid.add_widget(self.btn_normal)
        grid.add_widget(self.btn_hizli)
        
        layout.add_widget(grid)
        layout.add_widget(Label(text="", size_hint=(1, 0.4))) # Boşluk
        
        btn_geri = Button(text="Kaydet ve Dön", background_color=(0.3, 0.7, 0.3, 1), size_hint=(1, 0.2))
        btn_geri.bind(on_press=self.kaydet_don)
        layout.add_widget(btn_geri)
        
        self.add_widget(layout)

    def hiz_degistir(self, hiz):
        AYARLAR["konusma_hizi"] = hiz
        # Buton renklerini güncelle
        def renk_ayarla(btn, aktif_mi):
            btn.background_color = (0.2, 0.6, 0.8, 1) if aktif_mi else (0.3, 0.3, 0.3, 1)
            
        renk_ayarla(self.btn_yavas, hiz == 0.5)
        renk_ayarla(self.btn_normal, hiz == 1.0)
        renk_ayarla(self.btn_hizli, hiz == 1.5)
        
        # Test sesi
        SES.oku("Speed test")

    def kaydet_don(self, instance):
        self.manager.current = 'menu'

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text="İngilizce Ezber", font_size='40sp'))
        
        btn1 = Button(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), on_press=lambda x: self.gecis("kelime"))
        btn2 = Button(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), on_press=lambda x: self.gecis("cumle"))
        btn3 = Button(text="Listeyi Güncelle", background_color=(1,0.5,0,1), on_press=self.guncelle)
        
        # AYARLAR VE INFO YAN YANA
        alt_grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.15))
        btn_ayarlar = Button(text="⚙️ Ayarlar", background_color=(0.5, 0.5, 0.5, 1), on_press=lambda x: setattr(self.manager, 'current', 'ayarlar'))
        btn_info = Button(text="ℹ️ Info", background_color=(0,0.8,0.8,1), on_press=lambda x: setattr(self.manager, 'current', 'info'))
        alt_grid.add_widget(btn_ayarlar)
        alt_grid.add_widget(btn_info)
        
        btn5 = Button(text="Çıkış", background_color=(0.8,0.2,0.2,1), on_press=lambda x: sys.exit())
        
        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)
        layout.add_widget(alt_grid)
        layout.add_widget(btn5)
        self.add_widget(layout)

    def guncelle(self, instance):
        p = Popup(title='İşlem', content=Label(text='İndiriliyor...'), size_hint=(0.6, 0.3)); p.open()
        basari, msj = YONETICI.internetten_guncelle()
        p.dismiss()
        Popup(title='Durum', content=Label(text=msj), size_hint=(0.8, 0.4)).open()

    def gecis(self, mod):
        if not YONETICI.veriler:
            Popup(title='Hata', content=Label(text='Liste Boş!'), size_hint=(0.8, 0.4)).open()
            return
        self.manager.get_screen('calisma').baslat(mod)
        self.manager.current = 'calisma'

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
        self.lbl.text = f"Kelime Sayısı:\\n{len(YONETICI.veriler)}\\n\\nDurum: Aktif"

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gecmis, self.aktif, self.yon, self.cevrildi = [], None, "tr_to_en", False
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.kart = Button(text="Başla", font_size='24sp', halign='center', valign='middle')
        self.kart.bind(size=self.kart.setter('text_size'))
        self.kart.bind(on_press=self.cevir)
        
        self.btn_ses = Button(text="🔊 DİNLE", size_hint=(1, 0.15), background_color=(0.5, 0.5, 0.5, 1), on_press=self.seslendir)
        
        btns = BoxLayout(size_hint=(1,0.15), spacing=10)
        btns.add_widget(Button(text="Geri", on_press=self.geri))
        btns.add_widget(Button(text="Menü", on_press=lambda x: setattr(self.manager, 'current', 'menu')))
        btns.add_widget(Button(text="İleri", on_press=self.ileri))
        
        layout.add_widget(self.kart); layout.add_widget(self.btn_ses); layout.add_widget(btns); self.add_widget(layout)

    def baslat(self, mod): self.mod = mod; self.gecmis = []; self.ileri(None)
    
    def seslendir(self, i):
        if self.aktif:
            metin = self.aktif['en'] if self.mod == "kelime" else self.aktif['cen']
            SES.oku(metin)
            
    def guncelle(self):
        try:
            self.kart.markup = True; v = self.aktif
            if not self.cevrildi:
                self.kart.background_color = get_color_from_hex('#455A64')
                soru = (v["tr"] if self.yon == "tr_to_en" else v["en"]) if self.mod == "kelime" else (v["ctr"] if self.yon == "tr_to_en" else v["cen"])
                ipucu = "(Türkçesi?)" if self.yon == "en_to_tr" else "(İngilizcesi?)"
                
                # --- DÜZELTME BURADA ---
                # \n yerine tek bir satır atlama karakteri kullanıyoruz
                self.kart.text = f"[b]{soru}[/b]\n\n\n[size=18]{ipucu}[/size]"
            else:
                self.kart.background_color = get_color_from_hex('#FFECB3'); self.kart.color = (0,0,0,1)
                
                if self.mod == "kelime":
                    # --- DÜZELTME BURADA ---
                    # Gereksiz \n işaretleri temizlendi
                    self.kart.text = f"[size=32][b]{v['en']}[/b][/size]\n[{v['okunus']}]\n---\n{v['tr']}"
                else:
                    self.kart.text = f"[b]{v['cen']}[/b]\n---\n{v['ctr']}"
        except Exception as e:
            self.kart.text = "Görüntüleme Hatası"

    def cevir(self, i): self.cevrildi = not self.cevrildi; self.guncelle()
    def ileri(self, i): 
        if getattr(self,'akt',None): self.gec.append({"v":self.akt,"y":self.y})
        if YONETICI.veriler: self.akt=random.choice(YONETICI.veriler); self.y=random.choice(["tr_to_en","en_to_tr"]); self.aktif=self.akt; self.yon=self.y; self.cevrildi=False; self.guncelle()
    def geri(self, i): 
        if self.gec: s=self.gec.pop(); self.aktif=s["v"]; self.yon=s["y"]; self.cevrildi=False; self.guncelle()

class AppMain(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(AnaMenu(name='menu'))
        sm.add_widget(InfoEkrani(name='info'))
        sm.add_widget(AyarlarEkrani(name='ayarlar')) # Yeni ekran eklendi
        sm.add_widget(Calisma(name='calisma'))
        return sm

if __name__ == '__main__': AppMain().run()
