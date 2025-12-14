
import csv, random, os, sys, requests, shutil
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
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPTfdbSV0cuDHK6hl1bnmOXUa_OzVnmYNIKhiiGvlVMMnPsUf27aN8dWqyuvkd4q84aINz5dvLoYmI/pub?output=csv"  # Linki buraya yapıştırabilirsin

Window.clearcolor = (0.1, 0.1, 0.1, 1)

class VeriYoneticisi:
    def __init__(self):
        self.yol = self.bul()
        self.veri = []
        self.yukle()
    def bul(self):
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), 'kelimeler.csv')
        yol = os.path.join(os.getcwd(), 'kelimeler.csv')
        if not os.path.exists(yol) and os.path.exists('kelimeler.csv'):
            try: shutil.copy('kelimeler.csv', yol)
            except: pass
        return yol
    def guncelle(self):
        try:
            if "http" not in CSV_URL: return False, "Link Yok!"
            r = requests.get(CSV_URL, timeout=15); r.raise_for_status()
            with open(self.yol, 'wb') as f: f.write(r.content)
            self.yukle(); return True, "Güncellendi!"
        except Exception as e: return False, str(e)
    def yukle(self):
        self.veri = []
        if not os.path.exists(self.yol): return
        try:
            with open(self.yol, encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                for r in reader:
                    if len(r)>6 and r[0].strip().isdigit():
                        self.veri.append({"tr":r[1],"en":r[2],"ipa":r[3],"ok":r[4],"cen":r[5],"ctr":r[6]})
        except: pass
YON = VeriYoneticisi()

class AnaMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=30, spacing=15)
        l.add_widget(Label(text="İngilizce Ezber", font_size='40sp'))
        l.add_widget(Button(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), on_press=lambda x: self.g('kelime')))
        l.add_widget(Button(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), on_press=lambda x: self.g('cumle')))
        l.add_widget(Button(text="Listeyi Güncelle", background_color=(1,0.5,0,1), on_press=self.u))
        l.add_widget(Button(text="Info", background_color=(0,0.8,0.8,1), on_press=lambda x: setattr(self.manager,'current','info')))
        l.add_widget(Button(text="Çıkış", background_color=(0.8,0.2,0.2,1), on_press=lambda x: sys.exit()))
        self.add_widget(l)
    def g(self, m):
        if not YON.veri: return Popup(title='Hata', content=Label(text='Liste Boş!'), size_hint=(0.8,0.4)).open()
        self.manager.get_screen('calisma').baslat(m); self.manager.current='calisma'
    def u(self, i):
        p=Popup(title='İşlem', content=Label(text='İndiriliyor...'), size_hint=(0.6,0.3)); p.open()
        s,m=YON.guncelle(); p.dismiss(); Popup(title='Durum', content=Label(text=m), size_hint=(0.8,0.4)).open()

class Info(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l=BoxLayout(orientation='vertical', padding=40); self.lbl=Label(font_size='22sp', halign='center'); l.add_widget(self.lbl)
        l.add_widget(Button(text="Geri", size_hint=(1,0.2), background_color=(1,0.6,0,1), on_press=lambda x: setattr(self.manager,'current','menu')))
        self.add_widget(l)
    def on_pre_enter(self): self.lbl.text=f"Kelime Sayısı:\n{len(YON.veri)}\nVeritabanı: Aktif"

class Calisma(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l=BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.k=Button(font_size='22sp', on_press=self.cev)
        self.ses=Button(text="🔊 DİNLE", size_hint=(1,0.15), background_color=(0.5,0.5,0.5,1), on_press=self.oku)
        b=BoxLayout(size_hint=(1,0.15), spacing=10)
        b.add_widget(Button(text="Geri", on_press=self.ger)); b.add_widget(Button(text="Menü", on_press=lambda x: setattr(self.manager,'current','menu')))
        b.add_widget(Button(text="İleri", on_press=self.ile)); l.add_widget(self.k); l.add_widget(self.ses); l.add_widget(b); self.add_widget(l)
    def baslat(self, m): self.mod=m; self.gec=[]; self.ile(None)
    def gun(self):
        self.k.markup=True; v=self.akt
        if not self.cv:
            self.k.background_color=get_color_from_hex('#455A64')
            t=(v["tr"] if self.y=="tr_to_en" else v["en"]) if self.mod=="kelime" else (v["ctr"] if self.y=="tr_to_en" else v["cen"])
            self.k.text=f"[b]{t}[/b]"
        else:
            self.k.background_color=get_color_from_hex('#FFECB3'); self.k.color=(0,0,0,1)
            self.k.text=f"{v['en']}\n{v['ok']}\n---\n{v['tr']}" if self.mod=="kelime" else f"{v['cen']}\n---\n{v['ctr']}"
    def oku(self, i):
        if self.akt:
            try: tts.speak(self.akt['en'] if self.mod=="kelime" else self.akt['cen'])
            except: pass
    def cev(self,i): self.cv=not self.cv; self.gun()
    def ile(self,i): 
        if getattr(self,'akt',None): self.gec.append({"v":self.akt,"y":self.y})
        self.akt=random.choice(YON.veri); self.y=random.choice(["tr_to_en","en_to_tr"]); self.cv=False; self.gun()
    def ger(self,i): 
        if self.gec: s=self.gec.pop(); self.akt=s["v"]; self.y=s["y"]; self.cv=False; self.gun()

class A(App):
    def build(self):
        s=ScreenManager(); [s.add_widget(x) for x in [AnaMenu(name='menu'),Info(name='info'),Calisma(name='calisma')]]; return s
if __name__=='__main__': A().run()
