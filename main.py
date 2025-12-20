import csv
import random
import os
import sys
import requests
import shutil
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
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

# Global Ayarlar
AYARLAR = {
    "hiz": 1.0
}

# Yedek veriler
YEDEK_VERILER = [
    {"tr": "Merhaba", "en": "Hello", "ipa": "", "okunus": "helo", "cen": "Hello world", "ctr": "Merhaba dünya"},
    {"tr": "Gitmek", "en": "Go", "ipa": "", "okunus": "go", "cen": "Let's go", "ctr": "Hadi gidelim"}
]

# --- 3D GÖRÜNÜMLÜ ÖZEL BUTON ---
class OzelButon(Button):
    def __init__(self, **kwargs):
        self.ana_renk = kwargs.get('background_color', (0.2, 0.6, 0.8, 1))
        if 'background_color' in kwargs: del kwargs['background_color']
        
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = '22sp'
        self.bold = True
        self.color = (1, 1, 1, 1)
        
        self.halign = 'center'
        self.valign = 'middle'
        self.text_size = (self.width, None)
        
        self.bind(pos=self.guncelle_canvas, size=self.guncelle_canvas, state=self.guncelle_canvas)

    def guncelle_canvas(self, *args):
        self.text_size = (self.width - 10, None)
        self.canvas.before.clear()
        with self.canvas.before:
            r, g, b, a = self.ana_renk
            # Gölge
            Color(r * 0.6, g * 0.6, b * 0.6, 1)
            offset = 6 if self.state == 'normal' else 0
            RoundedRectangle(pos=(self.x, self.y - offset), size=self.size, radius=[15])
            # Ana Yüzey
            Color(r, g, b, 1)
            y_pos = self.y if self.state == 'normal' else self.y - 6
            RoundedRectangle(pos=(self.x, y_pos), size=self.size, radius=[15])

# --- KELİME PARÇASI BUTONU (Etkinlik İçin) ---
class KelimeParcasi(Button):
    def __init__(self, metin, **kwargs):
        super().__init__(**kwargs)
        self.text = metin
        self.font_size = '18sp'
        self.size_hint = (None, None)
        self.height = 60
        # Genişliği metne göre ayarla (min 100)
        self.width = max(100, len(metin) * 15)
        self.background_normal = ''
        self.background_color = (0.3, 0.3, 0.3, 1) # Gri
        self.color = (1, 1, 1, 1)

class SesYoneticisi:
    def __init__(self):
        self.android_tts = None
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                Locale = autoclass('java.util.Locale')
                self.android_tts = TextToSpeech(PythonActivity.mActivity, None)
                self.android_tts.setLanguage(Locale.US)
            except: pass

    def oku(self, metin):
        hiz = AYARLAR["hiz"]
        try:
            if platform == 'android' and self.android_tts:
                self.android_tts.setSpeechRate(float(hiz))
                self.android_tts.speak(metin, 0, None)
            else:
                tts.speak(metin)
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
        layout.add_widget(Label(text="Konuşma Hızı", font_size='32sp', size_hint=(1, 0.2)))
        
        grid = GridLayout(cols=3, spacing=10, size_hint=(1, 0.2))
        self.btn_yavas = ToggleButton(text="Yavaş\n(0.75x)", group='hiz', background_color=(0.3, 0.3, 0.3, 1))
        self.btn_normal = ToggleButton(text="Normal\n(1.0x)", group='hiz', state='down', background_color=(0.2, 0.6, 0.8, 1))
        self.btn_hizli = ToggleButton(text="Hızlı\n(1.25x)", group='hiz', background_color=(0.3, 0.3, 0.3, 1))
        
        self.btn_yavas.bind(on_press=lambda x: self.hiz_set(0.75))
        self.btn_normal.bind(on_press=lambda x: self.hiz_set(1.0))
        self.btn_hizli.bind(on_press=lambda x: self.hiz_set(1.25))
        
        grid.add_widget(self.btn_yavas); grid.add_widget(self.btn_normal); grid.add_widget(self.btn_hizli)
        layout.add_widget(grid)
        layout.add_widget(Label(size_hint=(1, 0.4))) 
        
        btn_geri = OzelButon(text="Kaydet ve Dön", background_color=(0.3, 0.7, 0.3, 1), size_hint=(1, None), height=112)
        btn_geri.bind(on_press=self.don)
        layout.add_widget(btn_geri)
        self.add_widget(layout)

    def hiz_set(self, deger):
        AYARLAR["hiz"] = deger
        def renk(btn, aktif): btn.background_color = (0.2, 0.6, 0.8, 1) if aktif else (0.3, 0.3, 0.3, 1)
        renk(self.btn_yavas, deger == 0.75); renk(self.btn_normal, deger == 1.0); renk(self.btn_hizli, deger == 1.25)
        SES.oku("Test speed")
    def don(self, instance): self.manager.current = 'menu'

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        layout.add_widget(Label(text="İngilizce Ezber", font_size='40sp', bold=True, size_hint=(1, 0.2)))
        
        HEDEF_YUKSEKLIK = 112
        
        btn1 = OzelButon(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn1.bind(on_press=lambda x: self.gecis("kelime"))
        
        btn2 = OzelButon(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn2.bind(on_press=lambda x: self.gecis("cumle"))
        
        # --- YENİ ETKİNLİK BUTONU ---
        btn_etkinlik = OzelButon(text="Cümle Kurma (Etkinlik)", background_color=(0.6, 0.2, 0.8, 1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn_etkinlik.bind(on_press=lambda x: self.gecis("etkinlik"))
        
        btn3 = OzelButon(text="Listeyi Güncelle", background_color=(1,0.5,0,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn3.bind(on_press=self.guncelle)
        
        grid = GridLayout(cols=2, spacing=15, size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        b_ayar = OzelButon(text="Ayarlar", background_color=(0.5,0.5,0.5,1))
        b_ayar.bind(on_press=lambda x: setattr(self.manager, 'current', 'ayarlar'))
        b_info = OzelButon(text="Info", background_color=(0,0.8,0.8,1))
        b_info.bind(on_press=lambda x: setattr(self.manager, 'current', 'info'))
        grid.add_widget(b_ayar); grid.add_widget(b_info)
        
        btn5 = OzelButon(text="Çıkış", background_color=(0.8,0.2,0.2,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn5.bind(on_press=lambda x: sys.exit())
        
        layout.add_widget(btn1); layout.add_widget(btn2); layout.add_widget(btn_etkinlik); layout.add_widget(btn3)
        layout.add_widget(grid); layout.add_widget(btn5)
        self.add_widget(layout)

    def guncelle(self, i):
        p=Popup(title='İşlem', content=Label(text='İndiriliyor...'), size_hint=(0.7, 0.3)); p.open()
        s,m = YONETICI.internetten_guncelle(); p.dismiss()
        Popup(title='Durum', content=Label(text=m), size_hint=(0.8, 0.4)).open()

    def gecis(self, m):
        if not YONETICI.veriler: 
            Popup(title='Uyarı', content=Label(text='Veri Yok!'), size_hint=(0.8,0.4)).open(); return
        
        if m == "etkinlik":
            self.manager.get_screen('etkinlik').baslat()
            self.manager.current = 'etkinlik'
        else:
            self.manager.get_screen('calisma').baslat(m)
            self.manager.current = 'calisma'

class InfoEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        self.lbl = Label(text="...", font_size='22sp', halign='center', size_hint=(1, 0.6))
        layout.add_widget(self.lbl)
        imza = Label(text="Hazırlayan: Murat SERT", font_size='16sp', color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.1))
        layout.add_widget(imza)
        btn = OzelButon(text="Geri Dön", background_color=(1,0.6,0,1), size_hint=(1, None), height=112)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn)
        self.add_widget(layout)
    def on_pre_enter(self):
        s = len(YONETICI.veriler)
        self.lbl.text = f'Toplam Kelime: "{s}"'

# --- YENİ ETKİNLİK EKRANI (CÜMLE KURMA) ---
class EtkinlikEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aktif_veri = None
        self.dogru_siralama = []
        self.kullanici_siralama = []
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # 1. ÜST BİLGİ (İpucu)
        self.lbl_ipucu = Label(text="Cümleyi Oluşturun", font_size='20sp', size_hint=(1, 0.15))
        main_layout.add_widget(self.lbl_ipucu)
        
        # 2. CEVAP ALANI (Kullanıcının kelimeleri taşıdığı yer)
        self.cevap_kutusu = StackLayout(padding=10, spacing=10, size_hint=(1, 0.25))
        # Arka plan rengi için canvas ekleyelim
        with self.cevap_kutusu.canvas.before:
            Color(0.2, 0.2, 0.2, 1) # Koyu zemin
            self.rect = RoundedRectangle(pos=self.cevap_kutusu.pos, size=self.cevap_kutusu.size, radius=[10])
        self.cevap_kutusu.bind(pos=self.guncelle_rect, size=self.guncelle_rect)
        main_layout.add_widget(self.cevap_kutusu)
        
        # 3. KELİME HAVUZU (Karışık kelimelerin durduğu yer)
        self.kelime_havuzu = StackLayout(padding=10, spacing=10, size_hint=(1, 0.35))
        main_layout.add_widget(self.kelime_havuzu)
        
        # 4. KONTROL BUTONLARI
        btns = GridLayout(cols=2, spacing=10, size_hint=(1, None), height=112)
        
        b_kontrol = OzelButon(text="Kontrol Et", background_color=(0.2, 0.8, 0.2, 1))
        b_kontrol.bind(on_press=self.kontrol_et)
        
        b_goster = OzelButon(text="Doğruyu Gör", background_color=(1, 0.6, 0, 1))
        b_goster.bind(on_press=self.dogruyu_goster)
        
        btns.add_widget(b_kontrol)
        btns.add_widget(b_goster)
        main_layout.add_widget(btns)
        
        # 5. ALT NAVİGASYON
        nav = GridLayout(cols=2, spacing=10, size_hint=(1, None), height=80)
        b_menu = OzelButon(text="Menü", background_color=(0.5, 0.5, 0.5, 1))
        b_menu.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        b_ileri = OzelButon(text="İleri", background_color=(0.2, 0.6, 0.8, 1))
        b_ileri.bind(on_press=lambda x: self.baslat())
        
        nav.add_widget(b_menu)
        nav.add_widget(b_ileri)
        main_layout.add_widget(nav)
        
        self.add_widget(main_layout)

    def guncelle_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def baslat(self):
        self.cevap_kutusu.clear_widgets()
        self.kelime_havuzu.clear_widgets()
        self.kullanici_siralama = []
        
        if not YONETICI.veriler: return
        
        # Rastgele cümle seç (Sadece İngilizce cümlesi dolu olanlar)
        self.aktif_veri = random.choice([v for v in YONETICI.veriler if v.get('cen')])
        
        # İpucu (Türkçesi)
        self.lbl_ipucu.text = f"[b]{self.aktif_veri['ctr']}[/b]"
        self.lbl_ipucu.markup = True
        
        # Cümleyi kelimelere ayır ve temizle
        cumle = self.aktif_veri['cen']
        # Noktalama işaretlerini ayır veya temizle (Basit tutmak için temizliyoruz)
        temiz_cumle = re.sub(r'[^\w\s]', '', cumle) 
        self.dogru_siralama = temiz_cumle.split()
        
        karisik_kelimeler = self.dogru_siralama.copy()
        random.shuffle(karisik_kelimeler)
        
        for kelime in karisik_kelimeler:
            btn = KelimeParcasi(metin=kelime)
            btn.bind(on_press=self.kelime_tasima)
            self.kelime_havuzu.add_widget(btn)

    def kelime_tasima(self, btn):
        # Eğer havuzdaysa -> Cevaba taşı
        if btn.parent == self.kelime_havuzu:
            self.kelime_havuzu.remove_widget(btn)
            self.cevap_kutusu.add_widget(btn)
            self.kullanici_siralama.append(btn.text)
        # Eğer cevaptaysa -> Havuza geri taşı
        else:
            self.cevap_kutusu.remove_widget(btn)
            self.kelime_havuzu.add_widget(btn)
            if btn.text in self.kullanici_siralama:
                self.kullanici_siralama.remove(btn.text)

    def kontrol_et(self, instance):
        if self.kullanici_siralama == self.dogru_siralama:
            # DOĞRU: Yeşil Tik Sesi ve Popup
            Popup(title='Tebrikler!', content=Label(text='✅ Doğru Cevap!', font_size='24sp'), size_hint=(0.6, 0.3)).open()
            SES.oku("Correct!")
        else:
            # YANLIŞ
            Popup(title='Hata', content=Label(text='❌ Yanlış Sıralama\nTekrar Dene', font_size='20sp', halign='center'), size_hint=(0.6, 0.3)).open()

    def dogruyu_goster(self, instance):
        if self.aktif_veri:
            Popup(title='Doğru Cümle', content=Label(text=self.aktif_veri['cen'], font_size='20sp', halign='center'), size_hint=(0.8, 0.4)).open()
            SES.oku(self.aktif_veri['cen'])

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gecmis, self.aktif, self.yon, self.cevrildi = [], None, "tr_to_en", False
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.kart = OzelButon(text="Başla", background_color=get_color_from_hex('#455A64'))
        self.kart.font_size = '22sp'
        self.kart.bind(on_press=self.cevir)
        
        self.btn_ses = OzelButon(text="🔊 DİNLE", background_color=(0.4, 0.4, 0.4, 1), size_hint=(1, None), height=90)
        self.btn_ses.bind(on_press=self.seslendir)
        
        btns = GridLayout(cols=3, spacing=15, size_hint=(1, None), height=105)
        b1 = OzelButon(text="Geri", background_color=(1,0.6,0,1))
        b1.bind(on_press=self.geri)
        b2 = OzelButon(text="Menü", background_color=(0.8,0.2,0.2,1))
        b2.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        b3 = OzelButon(text="İleri", background_color=(0.2,0.8,0.2,1))
        b3.bind(on_press=self.ileri)
        
        btns.add_widget(b1); btns.add_widget(b2); btns.add_widget(b3)
        layout.add_widget(self.kart); layout.add_widget(self.btn_ses); layout.add_widget(btns)
        self.add_widget(layout)

    def baslat(self, m): self.mod=m; self.gecmis=[]; self.ileri(None)
    
    def seslendir(self, i):
        if self.aktif: 
            ham_metin = self.aktif['en'] if self.mod=="kelime" else self.aktif['cen']
            temiz_metin = re.sub(r"\(.*?\)", "", ham_metin).strip()
            SES.oku(temiz_metin)
            
    def guncelle(self):
        self.kart.markup = True; v = self.aktif
        if not v: return
        
        if not self.cevrildi:
            self.kart.ana_renk = get_color_from_hex('#37474F')
            self.kart.guncelle_canvas()
            self.kart.color = (1,1,1,1)
            soru = (v["tr"] if self.yon == "tr_to_en" else v["en"]) if self.mod == "kelime" else (v["ctr"] if self.yon == "tr_to_en" else v["cen"])
            ipucu = "(Türkçesi?)" if self.yon == "en_to_tr" else "(İngilizcesi?)"
            self.kart.text = f"[b]{soru}[/b]\n\n\n{ipucu}"
        else:
            self.kart.ana_renk = get_color_from_hex('#FBC02D')
            self.kart.guncelle_canvas()
            self.kart.color = (0,0,0,1)
            
            if self.mod == "kelime":
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
        sm.add_widget(EtkinlikEkrani(name='etkinlik')) # Etkinlik eklendi
        return sm

if __name__ == '__main__': AppMain().run()
