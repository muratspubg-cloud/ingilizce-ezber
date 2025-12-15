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
from kivy.graphics import Color, RoundedRectangle
from plyer import tts

# --- AYARLAR ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPTfdbSV0cuDHK6hl1bnmOXUa_OzVnmYNIKhiiGvlVMMnPsUf27aN8dWqyuvkd4q84aINz5dvLoYmI/pub?output=csv"

# Arka plan rengi (Koyu Gri)
Window.clearcolor = (0.15, 0.15, 0.15, 1)

# Yedek veriler
YEDEK_VERILER = [
    {"tr": "Merhaba", "en": "Hello", "ipa": "", "okunus": "helo", "cen": "Hello world", "ctr": "Merhaba dünya"},
    {"tr": "Gitmek", "en": "Go", "ipa": "", "okunus": "go", "cen": "Let's go", "ctr": "Hadi gidelim"}
]

# --- 3D GÖRÜNÜMLÜ ÖZEL BUTON SINIFI ---
class OzelButon(Button):
    def __init__(self, **kwargs):
        self.ana_renk = kwargs.get('background_color', (0.2, 0.6, 0.8, 1))
        if 'background_color' in kwargs: del kwargs['background_color']
        
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = '22sp' # Buton yazılarını da biraz büyüttük
        self.bold = True
        self.color = (1, 1, 1, 1)
        
        self.bind(pos=self.guncelle_canvas, size=self.guncelle_canvas, state=self.guncelle_canvas)

    def guncelle_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            r, g, b, a = self.ana_renk
            Color(r * 0.6, g * 0.6, b * 0.6, 1)
            offset = 6 if self.state == 'normal' else 0 # Gölge derinliğini artırdık
            RoundedRectangle(pos=(self.x, self.y - offset), size=self.size, radius=[15])

            Color(r, g, b, 1)
            y_pos = self.y if self.state == 'normal' else self.y - 6
            RoundedRectangle(pos=(self.x, y_pos), size=self.size, radius=[15])

class SesYoneticisi:
    def __init__(self):
        self.tts = None
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                self.tts = TextToSpeech(PythonActivity.mActivity, None)
                self.tts.setLanguage(Locale.US)
            except: pass
        else:
            try:
                from plyer import tts
                self.plyer_tts = tts
            except: pass

    def oku(self, metin):
        try:
            if platform == 'android' and self.tts:
                self.tts.speak(metin, 0, None)
            else:
                self.plyer_tts.speak(metin)
        except: pass

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
        if not metin: return ""
        return " ".join(str(metin).replace("\\n", " ").replace("\n", " ").replace("\r", "").split())

    def yukle(self):
        self.veriler = []
        if os.path.exists(self.dosya_yolu):
            try:
                with open(self.dosya_yolu, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    if content:
                        delimiter = ';' if ';' in content.splitlines()[0] else ','
                        f.seek(0)
                        reader = csv.reader(f, delimiter=delimiter)
                        rows = list(reader)
                        start = 1 if rows and "Sıra" in str(rows[0][0]) else 0
                        
                        for i in range(start, len(rows)):
                            row = rows[i]
                            if not row or len(row) < 3: continue
                            if not row[1].strip() or not row[2].strip(): continue
                            def safe(idx): return self.temizle(row[idx]) if idx < len(row) else ""
                            
                            self.veriler.append({
                                "tr": safe(1), "en": safe(2), "ipa": safe(3), 
                                "okunus": safe(4), "cen": safe(5), "ctr": safe(6)
                            })
            except: pass
        if not self.veriler: self.veriler = YEDEK_VERILER.copy()

YONETICI = VeriYoneticisi()

class AyarlarEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="Ayarlar", font_size='28sp', size_hint=(1, 0.3)))
        
        layout.add_widget(Label(text="Ses hızı ayarı cihazınızın\n[Ayarlar > Erişilebilirlik]\nmenüsünden yapılır.", 
                                halign='center', color=(0.8,0.8,0.8,1)))
        
        layout.add_widget(Label(size_hint=(1, 0.3)))
        
        # %50 BÜYÜTÜLMÜŞ BUTON (75 * 1.5 = 112)
        btn_geri = OzelButon(text="Ana Menüye Dön", background_color=(0.3, 0.7, 0.3, 1), size_hint=(1, None), height=112)
        btn_geri.bind(on_press=self.don)
        layout.add_widget(btn_geri)
        self.add_widget(layout)

    def don(self, instance): self.manager.current = 'menu'

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="İngilizce Ezber", font_size='40sp', bold=True, size_hint=(1, 0.2)))
        
        # BUTONLAR %50 BÜYÜTÜLDÜ (Eski: 75 -> Yeni: 112)
        HEDEF_YUKSEKLIK = 112
        
        btn1 = OzelButon(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn1.bind(on_press=lambda x: self.gecis("kelime"))
        
        btn2 = OzelButon(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn2.bind(on_press=lambda x: self.gecis("cumle"))
        
        btn3 = OzelButon(text="Listeyi Güncelle", background_color=(1,0.5,0,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn3.bind(on_press=self.guncelle)
        
        # AYARLAR VE INFO
        grid = GridLayout(cols=2, spacing=15, size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        b_ayar = OzelButon(text="Ayarlar", background_color=(0.5,0.5,0.5,1))
        b_ayar.bind(on_press=lambda x: setattr(self.manager, 'current', 'ayarlar'))
        b_info = OzelButon(text="Info", background_color=(0,0.8,0.8,1))
        b_info.bind(on_press=lambda x: setattr(self.manager, 'current', 'info'))
        grid.add_widget(b_ayar)
        grid.add_widget(b_info)
        
        btn5 = OzelButon(text="Çıkış", background_color=(0.8,0.2,0.2,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn5.bind(on_press=lambda x: sys.exit())
        
        layout.add_widget(btn1)
        layout.add_widget(btn2)
        layout.add_widget(btn3)
        layout.add_widget(grid)
        layout.add_widget(btn5)
        
        layout.add_widget(Label(size_hint=(1, 0.05))) 
        self.add_widget(layout)

    def guncelle(self, i):
        p=Popup(title='İşlem', content=Label(text='İndiriliyor...'), size_hint=(0.7, 0.3)); p.open()
        s,m = YONETICI.internetten_guncelle(); p.dismiss()
        Popup(title='Durum', content=Label(text=m), size_hint=(0.8, 0.4)).open()

    def gecis(self, m):
        if not YONETICI.veriler: 
            Popup(title='Uyarı', content=Label(text='Veri Yok!'), size_hint=(0.8,0.4)).open(); return
        self.manager.get_screen('calisma').baslat(m); self.manager.current='calisma'

class InfoEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        self.lbl = Label(text="...", font_size='22sp', halign='center')
        layout.add_widget(self.lbl)
        
        # %50 BÜYÜTÜLMÜŞ BUTON
        btn = OzelButon(text="Geri Dön", background_color=(1,0.6,0,1), size_hint=(1, None), height=112)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn)
        self.add_widget(layout)
    def on_pre_enter(self):
        s = len(YONETICI.veriler)
        k = "Yedek" if YONETICI.veriler == YEDEK_VERILER else "CSV Dosyası"
        self.lbl.text = f"Toplam Kelime:\\n[b]{s}[/b]\\n\\nKaynak:\\n{k}"
        self.lbl.markup = True

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gecmis, self.aktif, self.yon, self.cevrildi = [], None, "tr_to_en", False
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # KART AYARLARI (Yazı boyutu eşitlendi)
        self.kart = OzelButon(text="Başla", background_color=get_color_from_hex('#455A64'))
        
        # --- ÖNEMLİ DEĞİŞİKLİK: FONT SABİTLENDİ ---
        self.kart.font_size = '22sp' # Tüm kart yazıları için sabit boyut (En az 12 istendi, 22 yaptık)
        self.kart.bind(on_press=self.cevir)
        
        # SES BUTONU (60 -> 90)
        self.btn_ses = OzelButon(text="🔊 DİNLE", background_color=(0.4, 0.4, 0.4, 1), size_hint=(1, None), height=90)
        self.btn_ses.bind(on_press=self.seslendir)
        
        # NAVİGASYON BUTONLARI (70 -> 105)
        btns = GridLayout(cols=3, spacing=15, size_hint=(1, None), height=105)
        b1 = OzelButon(text="Geri", background_color=(1,0.6,0,1))
        b1.bind(on_press=self.geri)
        b2 = OzelButon(text="Menü", background_color=(0.8,0.2,0.2,1))
        b2.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        b3 = OzelButon(text="İleri", background_color=(0.2,0.8,0.2,1))
        b3.bind(on_press=self.ileri)
        
        btns.add_widget(b1); btns.add_widget(b2); btns.add_widget(b3)
        
        layout.add_widget(self.kart)
        layout.add_widget(self.btn_ses)
        layout.add_widget(btns)
        self.add_widget(layout)

    def baslat(self, m): self.mod=m; self.gecmis=[]; self.ileri(None)
    def seslendir(self, i):
        if self.aktif: SES.oku(self.aktif['en'] if self.mod=="kelime" else self.aktif['cen'])
            
    def guncelle(self):
        self.kart.markup = True; v = self.aktif
        if not v: return
        
        if not self.cevrildi:
            self.kart.ana_renk = get_color_from_hex('#37474F')
            self.kart.guncelle_canvas()
            self.kart.color = (1,1,1,1)
            soru = (v["tr"] if self.yon == "tr_to_en" else v["en"]) if self.mod == "kelime" else (v["ctr"] if self.yon == "tr_to_en" else v["cen"])
            ipucu = "(Türkçesi?)" if self.yon == "en_to_tr" else "(İngilizcesi?)"
            
            # --- FONT BOYUTU SABİT ---
            # [size=...] etiketlerini kaldırdık. Kartın kendi '22sp' ayarı geçerli olacak.
            self.kart.text = f"[b]{soru}[/b]\n\n\n{ipucu}"
        else:
            self.kart.ana_renk = get_color_from_hex('#FBC02D')
            self.kart.guncelle_canvas()
            self.kart.color = (0,0,0,1)
            
            if self.mod == "kelime":
                # [size=...] etiketleri kaldırıldı
                self.kart.text = f"[b]{v['en']}[/b]\n[{v['okunus']}]\n---\n{v['tr']}"
            else:
                self.kart.text = f"[b]{v['cen']}[/b]\n---\n{v['ctr']}"

    def cevir(self, i): self.cevrildi = not self.cevrildi; self.guncelle()
    def ileri(self, i): 
        if not YONETICI.veriler: return
        if getattr(self,'aktif',None): self.gecmis.append({"v":self.aktif,"y":self.yon})
        try:
            self.aktif=random.choice(YONETICI.veriler); self.yon=random.choice(["tr_to_en","en_to_tr"]); self.cevrildi=False; self.guncelle()
        except: pass
    def geri(self, i): 
        if self.gecmis: s=self.gecmis.pop(); self.aktif=s["v"]; self.yon=s["y"]; self.cevrildi=False; self.guncelle()

class AppMain(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(AnaMenu(name='menu'))
        sm.add_widget(InfoEkrani(name='info'))
        sm.add_widget(AyarlarEkrani(name='ayarlar'))
        sm.add_widget(Calisma(name='calisma'))
        return sm

if __name__ == '__main__': AppMain().run()
