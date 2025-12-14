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

# LINK YOKSA BOŞ BIRAKIN
CSV_URL = "LINK_YOK" 

Window.clearcolor = (0.1, 0.1, 0.1, 1)

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
        
        # APK içindeki dosyayı çalışma alanına kopyala (İlk açılış)
        if not os.path.exists(yol) and os.path.exists('kelimeler.csv'):
            try: shutil.copy('kelimeler.csv', yol)
            except: pass
        return yol

    def internetten_guncelle(self):
        try:
            if "http" not in CSV_URL: return False, "Link Girilmemiş!"
            
            # Timeout ekledik ki sonsuza kadar beklemesin
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
                
                start_index = 1 if rows and len(rows[0]) > 0 and "Sıra" in str(rows[0][0]) else 0
                
                for i in range(start_index, len(rows)):
                    row = rows[i]
                    if len(row) < 7: continue
                    
                    self.veriler.append({
                        "tr": row[1], "en": row[2], "ipa": row[3], 
                        "okunus": row[4], "cen": row[5], "ctr": row[6]
                    })
        except Exception as e:
            print(f"Veri hatası: {e}")

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
        self.lbl.text = f"Kelime Sayısı:\\n{len(YONETICI.veriler)}\\n\\nVeritabanı: Aktif"

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text="İngilizce Ezber", font_size='40sp'))
        
        btn1 = Button(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), on_press=lambda x: self.gecis("kelime"))
        btn2 = Button(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), on_press=lambda x: self.gecis("cumle"))
        btn3 = Button(text="Listeyi Güncelle", background_color=(1,0.5,0,1), on_press=self.guncelle)
        btn4 = Button(text="Info / Bilgi", background_color=(0,0.8,0.8,1), on_press=lambda x: setattr(self.manager, 'current', 'info'))
        btn5 = Button(text="Çıkış", background_color=(0.8,0.2,0.2,1), on_press=lambda x: sys.exit())
        
        for b in [btn1,btn2,btn3,btn4,btn5]: layout.add_widget(b)
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

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gecmis, self.aktif, self.yon, self.cevrildi = [], None, "tr_to_en", False
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.kart = Button(text="Başla", font_size='24sp', on_press=self.cevir)
        self.btn_ses = Button(text="🔊 DİNLE", size_hint=(1, 0.15), background_color=(0.5, 0.5, 0.5, 1), on_press=self.seslendir)
        
        btns = BoxLayout(size_hint=(1,0.15), spacing=10)
        btns.add_widget(Button(text="Geri", on_press=self.geri))
        btns.add_widget(Button(text="Menü", on_press=lambda x: setattr(self.manager, 'current', 'menu')))
        btns.add_widget(Button(text="İleri", on_press=self.ileri))
        
        layout.add_widget(self.kart); layout.add_widget(self.btn_ses); layout.add_widget(btns); self.add_widget(layout)

    def baslat(self, mod): self.mod = mod; self.gecmis = []; self.ileri(None)
    
    def seslendir(self, i):
        if self.aktif:
            try: tts.speak(self.aktif['en'] if self.mod == "kelime" else self.aktif['cen'])
            except: pass
            
    def guncelle(self):
        self.kart.markup = True; v = self.aktif
        if not self.cevrildi:
            self.kart.background_color = get_color_from_hex('#455A64')
            soru = (v["tr"] if self.yon == "tr_to_en" else v["en"]) if self.mod == "kelime" else (v["ctr"] if self.yon == "tr_to_en" else v["cen"])
            ipucu = "(Türkçesi?)" if self.yon == "en_to_tr" else "(İngilizcesi?)"
            self.kart.text = f"[b]{soru}[/b]\\n\\n\\n[size=18]{ipucu}[/size]"
        else:
            self.kart.background_color = get_color_from_hex('#FFECB3'); self.kart.color = (0,0,0,1)
            self.kart.text = f"[size=32][b]{v['en']}[/b][/size]\\n/{v['ipa']}/\\n[{v['okunus']}]\\n---\\n{v['tr']}" if self.mod=="kelime" else f"[b]{v['cen']}[/b]\\n---\\n{v['ctr']}"
            
    def cevir(self, i): self.cevrildi = not self.cevrildi; self.guncelle()
    def ileri(self, i): 
        if getattr(self,'akt',None): self.gec.append({"v":self.akt,"y":self.y})
        if YONETICI.veriler: self.akt=random.choice(YONETICI.veriler); self.y=random.choice(["tr_to_en","en_to_tr"]); self.aktif=self.akt; self.yon=self.y; self.cevrildi=False; self.guncelle()
    def geri(self, i): 
        if self.gec: s=self.gec.pop(); self.aktif=s["v"]; self.yon=s["y"]; self.cevrildi=False; self.guncelle()

class AppMain(App):
    def build(self):
        sm = ScreenManager()
        for s in [AnaMenu(name='menu'), InfoEkrani(name='info'), Calisma(name='calisma')]: sm.add_widget(s)
        return sm

if __name__ == '__main__': AppMain().run()
