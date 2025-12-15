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
from kivy.core.window import Window
from kivy.utils import get_color_from_hex, platform
from plyer import tts

# --- AYARLAR ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPTfdbSV0cuDHK6hl1bnmOXUa_OzVnmYNIKhiiGvlVMMnPsUf27aN8dWqyuvkd4q84aINz5dvLoYmI/pub?output=csv"

Window.clearcolor = (0.1, 0.1, 0.1, 1)

# Yedek veriler (İnternet/Dosya yoksa devreye girer)
YEDEK_VERILER = [
    {"tr": "Merhaba", "en": "Hello", "ipa": "", "okunus": "helo", "cen": "Hello world", "ctr": "Merhaba dünya"},
    {"tr": "Gitmek", "en": "Go", "ipa": "", "okunus": "go", "cen": "Let's go", "ctr": "Hadi gidelim"}
]

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
        
        # Eğer çalışma alanında yoksa kopyalamayı dene
        if not os.path.exists(yol) and os.path.exists('kelimeler.csv'):
            try: shutil.copy('kelimeler.csv', yol)
            except: pass
        return yol

    def internetten_guncelle(self):
        try:
            if "http" not in CSV_URL: return False, "Link Hatalı!"
            response = requests.get(CSV_URL, timeout=15)
            response.raise_for_status()
            with open(self.dosya_yolu, 'wb') as f:
                f.write(response.content)
            self.yukle()
            return True, "Başarıyla Güncellendi!"
        except Exception as e:
            return False, f"Hata: {str(e)}"

    def temizle(self, metin):
        """Metindeki \n, \\n ve gereksiz karakterleri AGRESİF şekilde temizler"""
        if not metin: return ""
        # Önce string'e çevir, sonra temizle
        metin = str(metin)
        # Kelime içinde görünen '\n' yazısını sil
        metin = metin.replace("\\n", " ")
        # Gerçek satır atlamaları sil
        metin = metin.replace("\n", " ").replace("\r", " ")
        # Gereksiz boşlukları (çift boşluk) tek boşluğa düşür ve kenarları kırp
        return " ".join(metin.split())

    def yukle(self):
        self.veriler = []
        if os.path.exists(self.dosya_yolu):
            try:
                # utf-8-sig: Excel BOM karakterini temizler
                with open(self.dosya_yolu, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    if content:
                        delimiter = ';' if ';' in content.splitlines()[0] else ','
                        f.seek(0)
                        reader = csv.reader(f, delimiter=delimiter)
                        rows = list(reader)
                        
                        start_index = 0
                        # Başlık satırı kontrolü
                        if rows and len(rows[0]) > 0 and ("Sıra" in str(rows[0][0]) or "id" in str(rows[0][0]).lower()):
                            start_index = 1
                        
                        for i in range(start_index, len(rows)):
                            row = rows[i]
                            # Boş veya eksik satırları atla
                            if not row or len(row) < 3: continue
                            if not row[1].strip() or not row[2].strip(): continue

                            # Her sütunu temizleyerek al
                            def safe(idx):
                                val = row[idx] if idx < len(row) else ""
                                return self.temizle(val)
                            
                            self.veriler.append({
                                "tr": safe(1), "en": safe(2), "ipa": safe(3), 
                                "okunus": safe(4), "cen": safe(5), "ctr": safe(6)
                            })
            except Exception as e:
                print(f"Yükleme Hatası: {e}")

        if not self.veriler:
            self.veriler = YEDEK_VERILER.copy()

YONETICI = VeriYoneticisi()

class AyarlarEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="Ayarlar", font_size='32sp'))
        
        bilgi = Label(
            text="Ses hızı ayarı, telefonunuzun\n[Ayarlar > Erişilebilirlik > Metin Okuma]\nmenüsünden yapılır.", 
            font_size='18sp', color=(0.8,0.8,0.8,1), halign='center'
        )
        layout.add_widget(bilgi)
        
        btn_geri = Button(text="Ana Menüye Dön", background_color=(0.3, 0.7, 0.3, 1), size_hint=(1, 0.2))
        btn_geri.bind(on_press=self.don)
        layout.add_widget(btn_geri)
        self.add_widget(layout)

    def don(self, instance):
        self.manager.current = 'menu'

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text="İngilizce Ezber", font_size='40sp'))
        
        btn1 = Button(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), on_press=lambda x: self.gecis("kelime"))
        btn2 = Button(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), on_press=lambda x: self.gecis("cumle"))
        btn3 = Button(text="Listeyi Güncelle", background_color=(1,0.5,0,1), on_press=self.guncelle)
        
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
        p = Popup(title='İşlem', content=Label(text='İndiriliyor...'), size_hint=(0.6, 0.3))
        p.open()
        basari, msj = YONETICI.internetten_guncelle()
        p.dismiss()
        Popup(title='Durum', content=Label(text=msj), size_hint=(0.8, 0.4)).open()

    def gecis(self, mod):
        if not YONETICI.veriler:
            Popup(title='Hata', content=Label(text='Liste Boş! Lütfen güncelleyin.'), size_hint=(0.8, 0.4)).open()
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
        sayi = len(YONETICI.veriler)
        kaynak = "Yedek Veri" if YONETICI.veriler == YEDEK_VERILER else "CSV Dosyası"
        self.lbl.text = f"Kelime Sayısı:\\n{sayi}\\n\\nVeri Kaynağı:\\n{kaynak}"

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # HATA DÜZELTME: self.gec değil self.gecmis kullanıyoruz
        self.gecmis = []
        self.aktif = None
        self.yon = "tr_to_en"
        self.cevrildi = False
        self.mod = "kelime"
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.kart = Button(text="Başla", font_size='24sp', halign='center', valign='middle')
        self.kart.bind(size=self.kart.setter('text_size'))
        self.kart.bind(on_press=self.cevir)
        
        self.btn_ses = Button(text="🔊 DİNLE", size_hint=(1, 0.15), background_color=(0.5, 0.5, 0.5, 1), on_press=self.seslendir)
        
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
        if YONETICI.veriler: self.ileri(None)
    
    def seslendir(self, i):
        if self.aktif:
            try:
                text = self.aktif['en'] if self.mod == "kelime" else self.aktif['cen']
                if text: tts.speak(text)
            except: pass
            
    def guncelle(self):
        try:
            self.kart.markup = True; v = self.aktif
            if not v: return

            if not self.cevrildi:
                self.kart.background_color = get_color_from_hex('#455A64')
                soru = (v["tr"] if self.yon == "tr_to_en" else v["en"]) if self.mod == "kelime" else (v["ctr"] if self.yon == "tr_to_en" else v["cen"])
                ipucu = "(Türkçesi?)" if self.yon == "en_to_tr" else "(İngilizcesi?)"
                
                # Soru kısmında artık \n görmeyeceksin, temizledik.
                self.kart.text = f"[b]{soru}[/b]\n\n\n[size=18]{ipucu}[/size]"
            else:
                self.kart.background_color = get_color_from_hex('#FFECB3'); self.kart.color = (0,0,0,1)
                
                if self.mod == "kelime":
                    # Okunuş ve cevap
                    self.kart.text = f"[size=32][b]{v['en']}[/b][/size]\n[{v['okunus']}]\n---\n{v['tr']}"
                else:
                    self.kart.text = f"[b]{v['cen']}[/b]\n---\n{v['ctr']}"
        except Exception as e:
            self.kart.text = "Hata"

    def cevir(self, i): self.cevrildi = not self.cevrildi; self.guncelle()
    
    def ileri(self, i): 
        if not YONETICI.veriler: return
        
        # Geçmişe kaydet (Hata düzeltildi: self.gecmis kullanıldı)
        if getattr(self, 'aktif', None): 
            self.gecmis.append({"v": self.aktif, "y": self.yon})
        
        try:
            self.aktif = random.choice(YONETICI.veriler)
            self.yon = random.choice(["tr_to_en","en_to_tr"])
            self.cevrildi = False
            self.guncelle()
        except: pass

    def geri(self, i): 
        # Hata düzeltildi: self.gecmis kullanıldı
        if self.gecmis: 
            s = self.gecmis.pop()
            self.aktif = s["v"]
            self.yon = s["y"]
            self.cevrildi = False
            self.guncelle()

class AppMain(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(AnaMenu(name='menu'))
        sm.add_widget(InfoEkrani(name='info'))
        sm.add_widget(AyarlarEkrani(name='ayarlar'))
        sm.add_widget(Calisma(name='calisma'))
        return sm

if __name__ == '__main__': AppMain().run()
