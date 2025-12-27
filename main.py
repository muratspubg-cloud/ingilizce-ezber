import csv
import random
import os
import sys
import requests
import shutil
import re
import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.dropdown import DropDown
from kivy.core.window import Window
from kivy.utils import get_color_from_hex, platform
from kivy.graphics import Color, RoundedRectangle
from kivy.storage.jsonstore import JsonStore
from plyer import tts

# --- AYARLAR ---
# 1. Ana Kelime Listesi
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRPTfdbSV0cuDHK6hl1bnmOXUa_OzVnmYNIKhiiGvlVMMnPsUf27aN8dWqyuvkd4q84aINz5dvLoYmI/pub?output=csv"

# 2. Dil Kursu Listesi
CSV_URL_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTT6HjmaATaFYx7ahx4vG5lOfOzVnUEUwjaGZqSVnCPU36oggWBLqW5zoFP4C9t8IVMRg1jYez9rwB7/pub?output=csv"

# 3. English - English Listesi
CSV_URL_3 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFXYrFIbxrULpqPNYSks0xFVT2lfFrpuIU1eXJoNPg9CXzB126Nb7eVXQ7kirHLz_Xj7CiYGbBnBBK/pub?output=csv"

Window.clearcolor = (0.15, 0.15, 0.15, 1)
AYARLAR = {"hiz": 1.0}
STORE = JsonStore('user_data.json')

# --- YEDEK VERİLER ---
YEDEK_VERILER = [
    {"tr": "Merhaba", "en": "Hello", "ipa": "", "okunus": "helo", "cen": "Hello world", "ctr": "Merhaba dünya"},
    {"tr": "Gitmek", "en": "Go", "ipa": "", "okunus": "go", "cen": "Let's go", "ctr": "Hadi gidelim"}
]

DIL_KURSU_YEDEK = [
    {"tr": "Araba", "en": "Car", "ipa": "/kɑːr/", "okunus": "kar", "cen": "My father has a red car", "ctr": "Babamın kırmızı bir arabası var"},
    {"tr": "Öğretmen", "en": "Teacher", "ipa": "/ˈtiːtʃər/", "okunus": "tiiçır", "cen": "She is a good teacher", "ctr": "O iyi bir öğretmendir"}
]

ENG_ENG_YEDEK = [
    {"word": "Diligent", "def": "Having or showing care and conscientiousness in one's work or duties.", "tr": "Çalışkan", "ex": "Many caves are located only after a diligent search."},
    {"word": "Obscure", "def": "Not discovered or known about; uncertain.", "tr": "Belirsiz", "ex": "His origins and parentage are obscure."},
    {"word": "Resilient", "def": "Able to withstand or recover quickly from difficult conditions.", "tr": "Dirençli", "ex": "Babies are generally far more resilient than new parents realize."}
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
        self.bind(pos=self.guncelle_canvas, size=self.guncelle_canvas, state=self.guncelle_canvas)

    def guncelle_canvas(self, *args):
        self.text_size = (self.width - 20, None)
        self.canvas.before.clear()
        with self.canvas.before:
            r, g, b, a = self.ana_renk
            Color(r * 0.6, g * 0.6, b * 0.6, 1)
            offset = 8 if self.state == 'normal' else 0
            RoundedRectangle(pos=(self.x, self.y - offset), size=self.size, radius=[15])
            Color(r, g, b, 1)
            y_pos = self.y if self.state == 'normal' else self.y - 8
            RoundedRectangle(pos=(self.x, y_pos), size=self.size, radius=[15])

# --- SPINNER AYARLARI ---
class BuyukSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = '22sp'
        self.height = 100
        self.background_normal = ''
        self.background_color = (0.2, 0.3, 0.4, 1)
        self.color = (1, 1, 1, 1)

class KaydirilabilirDropDown(DropDown):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_height = 800 

# --- KELİME PARÇASI ---
class KelimeParcasi(Button):
    def __init__(self, metin, **kwargs):
        super().__init__(**kwargs)
        self.text = metin
        self.font_size = '20sp'
        self.bold = True
        self.size_hint = (None, None)
        self.height = 80
        self.width = max(130, len(metin) * 24 + 50)
        self.background_normal = ''
        self.background_color = (0.25, 0.35, 0.45, 1) 
        self.color = (1, 1, 1, 1)
        self.bind(pos=self.ciz, size=self.ciz)

    def ciz(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])

# --- HARF PARÇASI ---
class HarfParcasi(Button):
    def __init__(self, harf, **kwargs):
        super().__init__(**kwargs)
        self.text = harf
        self.font_size = '28sp'
        self.bold = True
        self.size_hint = (None, None)
        self.size = (70, 70)
        self.background_normal = ''
        self.background_color = (0.8, 0.5, 0.2, 1)
        self.color = (1, 1, 1, 1)
        self.bind(pos=self.ciz, size=self.ciz)

    def ciz(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

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
        self.ana_dosya = 'kelimeler.csv'
        self.dil_dosya = 'dilkursu.csv'
        self.eng_dosya = 'eng_eng.csv'
        
        self.dosya_yolu_1 = self.yol_bul(self.ana_dosya)
        self.dosya_yolu_2 = self.yol_bul(self.dil_dosya)
        self.dosya_yolu_3 = self.yol_bul(self.eng_dosya)
        
        self.veriler = []
        self.dil_kursu_veriler = []
        self.eng_eng_veriler = []
        
        # Yüklemeler
        self.veriler = self.yukle(self.dosya_yolu_1, YEDEK_VERILER, tip="standart")
        self.dil_kursu_veriler = self.yukle(self.dosya_yolu_2, DIL_KURSU_YEDEK, tip="standart")
        self.eng_eng_veriler = self.yukle(self.dosya_yolu_3, ENG_ENG_YEDEK, tip="eng_eng")

    def yol_bul(self, dosya_adi):
        if platform == 'android':
            from android.storage import app_storage_path
            klasor = app_storage_path()
        else:
            klasor = os.getcwd()
        
        yol = os.path.join(klasor, dosya_adi)
        if not os.path.exists(yol) and os.path.exists(dosya_adi):
            try: shutil.copy(dosya_adi, yol)
            except: pass
        if not os.path.exists(yol):
            self.ornek_dosya_olustur(yol, dosya_adi)
        return yol

    def ornek_dosya_olustur(self, yol, ad):
        try:
            with open(yol, 'w', encoding='utf-8-sig') as f:
                if ad == 'eng_eng.csv':
                    f.write("Sıra;Word;Definition;TR;Example\n")
                    for v in ENG_ENG_YEDEK:
                        f.write(f"1;{v['word']};{v['def']};{v['tr']};{v['ex']}\n")
                else:
                    veri = DIL_KURSU_YEDEK if ad == 'dilkursu.csv' else YEDEK_VERILER
                    f.write("Sıra;TR;EN;IPA;Okunuş;CümleEN;CümleTR\n")
                    for v in veri:
                        f.write(f"1;{v['tr']};{v['en']};{v.get('ipa','')};{v['okunus']};{v.get('cen','')};{v.get('ctr','')}\n")
        except: pass

    def internetten_guncelle(self):
        try:
            if "http" in CSV_URL:
                r1 = requests.get(CSV_URL, timeout=15)
                r1.raise_for_status()
                with open(self.dosya_yolu_1, 'wb') as f: f.write(r1.content)
            
            if "http" in CSV_URL_2:
                r2 = requests.get(CSV_URL_2, timeout=15)
                r2.raise_for_status()
                with open(self.dosya_yolu_2, 'wb') as f: f.write(r2.content)
            
            if "http" in CSV_URL_3:
                r3 = requests.get(CSV_URL_3, timeout=15)
                r3.raise_for_status()
                with open(self.dosya_yolu_3, 'wb') as f: f.write(r3.content)
            
            self.veriler = self.yukle(self.dosya_yolu_1, YEDEK_VERILER, tip="standart")
            self.dil_kursu_veriler = self.yukle(self.dosya_yolu_2, DIL_KURSU_YEDEK, tip="standart")
            self.eng_eng_veriler = self.yukle(self.dosya_yolu_3, ENG_ENG_YEDEK, tip="eng_eng")
            return True, "Tüm Listeler Güncellendi!"
        except Exception as e:
            return False, f"Hata: {str(e)}"

    def temizle(self, metin):
        if not metin: return ""
        return " ".join(str(metin).replace("\\n", " ").replace("\n", " ").replace("\r", "").split())

    def yukle(self, yol, yedek_veri, tip="standart"):
        liste = []
        if os.path.exists(yol):
            try:
                with open(yol, 'r', encoding='utf-8-sig') as f:
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
                            def safe(idx): return self.temizle(row[idx]) if idx < len(row) else ""
                            
                            if tip == "standart":
                                liste.append({
                                    "tr": safe(1), "en": safe(2), "ipa": safe(3), 
                                    "okunus": safe(4), "cen": safe(5), "ctr": safe(6)
                                })
                            elif tip == "eng_eng":
                                liste.append({
                                    "word": safe(1), "def": safe(2), "tr": safe(3), "ex": safe(4)
                                })
            except: pass
        return liste if liste else yedek_veri.copy()

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
        
        btn_geri = OzelButon(text="Kaydet ve Dön", background_color=(0.3, 0.7, 0.3, 1), size_hint=(1, None), height=125)
        btn_geri.bind(on_press=self.don)
        layout.add_widget(btn_geri)
        self.add_widget(layout)

    def on_pre_enter(self):
        hiz = AYARLAR["hiz"]
        self.gorsel_guncelle(hiz)

    def gorsel_guncelle(self, hiz):
        self.btn_yavas.state = 'down' if hiz == 0.75 else 'normal'
        self.btn_normal.state = 'down' if hiz == 1.0 else 'normal'
        self.btn_hizli.state = 'down' if hiz == 1.25 else 'normal'
        def renk(btn, aktif): btn.background_color = (0.2, 0.6, 0.8, 1) if aktif else (0.3, 0.3, 0.3, 1)
        renk(self.btn_yavas, hiz == 0.75)
        renk(self.btn_normal, hiz == 1.0)
        renk(self.btn_hizli, hiz == 1.25)

    def hiz_set(self, deger):
        AYARLAR["hiz"] = deger
        STORE.put('ayarlar', hiz=deger)
        self.gorsel_guncelle(deger)
        SES.oku("Test speed")

    def don(self, instance): self.manager.current = 'menu'

class AnaMenu(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_box = BoxLayout(orientation='vertical', padding=0, spacing=0)
        
        baslik_kutusu = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.15)
        lbl_baslik = Label(text="İngilizce Ezber", font_size='40sp', bold=True)
        baslik_kutusu.add_widget(lbl_baslik)
        self.main_box.add_widget(baslik_kutusu)
        
        orta_alan = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.85)
        self.scroll = ScrollView(size_hint=(0.9, None), do_scroll_x=False)
        self.grid_menu = GridLayout(cols=1, spacing=20, size_hint_y=None, padding=[0, 20, 0, 20])
        self.grid_menu.bind(minimum_height=self.grid_menu.setter('height'))
        
        # --- BUTON BOYUTU %10 BÜYÜTÜLDÜ (110 -> 125) ---
        HEDEF_YUKSEKLIK = 125
        
        btn1 = OzelButon(text="Kelime Çalış", background_color=(0.2,0.6,0.8,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn1.bind(on_press=lambda x: self.level_sec("kelime"))
        
        btn2 = OzelButon(text="Cümle Çalış", background_color=(0.3,0.7,0.3,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn2.bind(on_press=lambda x: self.level_sec("cumle"))
        
        btn_kelime_etkinlik = OzelButon(text="Kelime Kurma (Etkinlik)", background_color=(0.9, 0.5, 0.1, 1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn_kelime_etkinlik.bind(on_press=lambda x: self.level_sec("etkinlik_kelime"))

        btn_cumle_etkinlik = OzelButon(text="Cümle Kurma (Etkinlik)", background_color=(0.6, 0.2, 0.8, 1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn_cumle_etkinlik.bind(on_press=lambda x: self.level_sec("etkinlik_cumle"))
        
        btn_dil_kursu = OzelButon(text="Dil Kursu Kelimeleri", background_color=(0.9, 0.3, 0.3, 1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn_dil_kursu.bind(on_press=self.dil_kursu_baslat_kelime)

        btn_dil_kursu_cumle = OzelButon(text="Dil Kursu Cümleleri", background_color=(0.8, 0.4, 0.2, 1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn_dil_kursu_cumle.bind(on_press=self.dil_kursu_baslat_cumle)
        
        # English - English Butonu
        btn_eng_eng = OzelButon(text="English - English", background_color=(0.0, 0.7, 0.7, 1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn_eng_eng.bind(on_press=lambda x: self.level_sec("eng_eng"))
        
        btn3 = OzelButon(text="Listeyi Güncelle", background_color=(1,0.5,0,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn3.bind(on_press=self.guncelle)
        
        alt_grid = GridLayout(cols=2, spacing=15, size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        b_ayar = OzelButon(text="Ayarlar", background_color=(0.5,0.5,0.5,1))
        b_ayar.bind(on_press=lambda x: setattr(self.manager, 'current', 'ayarlar'))
        b_info = OzelButon(text="Info", background_color=(0,0.8,0.8,1))
        b_info.bind(on_press=lambda x: setattr(self.manager, 'current', 'info'))
        alt_grid.add_widget(b_ayar); alt_grid.add_widget(b_info)
        
        btn5 = OzelButon(text="Çıkış", background_color=(0.8,0.2,0.2,1), size_hint=(1, None), height=HEDEF_YUKSEKLIK)
        btn5.bind(on_press=lambda x: sys.exit())
        
        self.grid_menu.add_widget(btn1)
        self.grid_menu.add_widget(btn2)
        self.grid_menu.add_widget(btn_kelime_etkinlik)
        self.grid_menu.add_widget(btn_cumle_etkinlik)
        self.grid_menu.add_widget(btn_dil_kursu)
        self.grid_menu.add_widget(btn_dil_kursu_cumle)
        self.grid_menu.add_widget(btn_eng_eng)
        self.grid_menu.add_widget(btn3)
        self.grid_menu.add_widget(alt_grid)
        self.grid_menu.add_widget(btn5)
        
        self.grid_menu.bind(height=self.update_scroll_height)
        Window.bind(height=self.update_scroll_height)
        self.scroll.add_widget(self.grid_menu)
        orta_alan.add_widget(self.scroll)
        self.main_box.add_widget(orta_alan)
        self.add_widget(self.main_box)

    def update_scroll_height(self, *args):
        max_h = Window.height * 0.85
        content_h = self.grid_menu.height
        self.scroll.height = min(max_h, content_h)

    def guncelle(self, i):
        p=Popup(title='İşlem', content=Label(text='Tüm Listeler İndiriliyor...'), size_hint=(0.7, 0.3)); p.open()
        s,m = YONETICI.internetten_guncelle(); p.dismiss()
        Popup(title='Durum', content=Label(text=m), size_hint=(0.8, 0.4)).open()

    def level_sec(self, mod_tipi):
        if mod_tipi == "eng_eng" and not YONETICI.eng_eng_veriler:
             Popup(title='Uyarı', content=Label(text='Eng-Eng Verisi Yok!'), size_hint=(0.8,0.4)).open(); return
        elif mod_tipi != "eng_eng" and not YONETICI.veriler:
             Popup(title='Uyarı', content=Label(text='Veri Yok!'), size_hint=(0.8,0.4)).open(); return

        ekran = self.manager.get_screen('level')
        ekran.modu_ayarla(mod_tipi)
        self.manager.current = 'level'

    def dil_kursu_baslat_kelime(self, instance):
        self.baslat_calisma("kelime", YONETICI.dil_kursu_veriler)
    
    def dil_kursu_baslat_cumle(self, instance):
        self.baslat_calisma("cumle", YONETICI.dil_kursu_veriler)

    def eng_eng_baslat(self, instance):
        pass

    def baslat_calisma(self, mod, liste):
        if not liste:
            Popup(title='Uyarı', content=Label(text='Liste Boş!'), size_hint=(0.8, 0.4)).open()
            return
        ekran = self.manager.get_screen('calisma')
        ekran.baslat_ozel(mod, liste)
        self.manager.current = 'calisma'

    def gecis(self, m):
        if not YONETICI.veriler: 
            Popup(title='Uyarı', content=Label(text='Veri Yok!'), size_hint=(0.8,0.4)).open(); return
        if m == "etkinlik":
            self.manager.get_screen('etkinlik').baslat()
            self.manager.current = 'etkinlik'

class LevelEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hedef_mod = "kelime"
        self.govde = BoxLayout(orientation='vertical', padding=30, spacing=30)
        self.lbl_baslik = Label(text="Level Seçin", font_size='32sp', size_hint=(1, 0.2))
        self.govde.add_widget(self.lbl_baslik)
        
        self.spinner = Spinner(
            text='Level Seçiniz',
            values=(),
            size_hint=(1, 0.15),
            pos_hint={'center_x': .5, 'center_y': .5},
            background_color=(0.2, 0.6, 0.8, 1),
            font_size='24sp',
            option_cls=BuyukSpinnerOption,
            dropdown_cls=KaydirilabilirDropDown
        )
        self.spinner.bind(text=self.level_secildi)
        self.govde.add_widget(self.spinner)
        self.govde.add_widget(Label(size_hint=(1, 0.3)))
        self.lbl_son_level = Label(text="Son Çalışılan: Yok", font_size='20sp', color=(0.6, 0.8, 1, 1), size_hint=(1, 0.1))
        self.govde.add_widget(self.lbl_son_level)
        btn_geri = OzelButon(text="Geri", background_color=(1,0.6,0,1), size_hint=(1, 0.15))
        btn_geri.bind(on_press=self.geri_don)
        self.govde.add_widget(btn_geri)
        self.add_widget(self.govde)

    def on_pre_enter(self):
        if self.hedef_mod == "eng_eng":
            aktif_liste = YONETICI.eng_eng_veriler
        else:
            aktif_liste = YONETICI.veriler

        toplam_kelime = len(aktif_liste)
        kelime_basi = 25
        toplam_level = math.ceil(toplam_kelime / kelime_basi)
        level_listesi = [f"Level {i+1}" for i in range(toplam_level)]
        self.spinner.values = level_listesi
        self.spinner.text = 'Level Seçiniz'
        
        if STORE.exists('ilerleme'):
            son = STORE.get('ilerleme')['son_level']
            self.lbl_son_level.text = f"Son Çalışılan: {son}"

    def modu_ayarla(self, mod):
        self.hedef_mod = mod
        if mod == "kelime": self.lbl_baslik.text = "Kelime Kartları"
        elif mod == "cumle": self.lbl_baslik.text = "Cümle Kartları"
        elif mod == "etkinlik_cumle": self.lbl_baslik.text = "Cümle Kurmaca"
        elif mod == "etkinlik_kelime": self.lbl_baslik.text = "Kelime Kurmaca"
        elif mod == "eng_eng": self.lbl_baslik.text = "Eng-Eng Leveller"

    def level_secildi(self, spinner, text):
        if not text.startswith("Level"): return
        try:
            level_num = int(text.split()[1])
            kelime_basi = 25
            baslangic = (level_num - 1) * kelime_basi
            bitis = baslangic + kelime_basi
            STORE.put('ilerleme', son_level=text)
            
            if self.hedef_mod == "eng_eng":
                secili_liste = YONETICI.eng_eng_veriler[baslangic:bitis]
            else:
                secili_liste = YONETICI.veriler[baslangic:bitis]

            if not secili_liste:
                Popup(title='Hata', content=Label(text='Bu Level Boş!'), size_hint=(0.6, 0.3)).open(); return

            if self.hedef_mod in ["kelime", "cumle", "eng_eng"]:
                ekran = self.manager.get_screen('calisma')
                ekran.baslat_ozel(self.hedef_mod, secili_liste)
                self.manager.current = 'calisma'
            elif self.hedef_mod == "etkinlik_cumle":
                ekran = self.manager.get_screen('etkinlik_cumle')
                ekran.baslat(secili_liste)
                self.manager.current = 'etkinlik_cumle'
            elif self.hedef_mod == "etkinlik_kelime":
                ekran = self.manager.get_screen('etkinlik_kelime')
                ekran.baslat(secili_liste)
                self.manager.current = 'etkinlik_kelime'
        except Exception as e: print(f"Hata: {e}")

    def geri_don(self, instance): self.manager.current = 'menu'

class InfoEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        self.lbl = Label(text="...", font_size='22sp', halign='center', size_hint=(1, 0.6))
        layout.add_widget(self.lbl)
        imza = Label(text="Hazırlayan: Murat SERT", font_size='20sp', bold=True, color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.1))
        layout.add_widget(imza)
        btn = OzelButon(text="Geri Dön", background_color=(1,0.6,0,1), size_hint=(1, None), height=125)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn)
        self.add_widget(layout)
    def on_pre_enter(self):
        s = len(YONETICI.veriler)
        s2 = len(YONETICI.dil_kursu_veriler)
        s3 = len(YONETICI.eng_eng_veriler)
        self.lbl.text = f'Ana Liste: "{s}"\nDil Kursu: "{s2}"\nEng-Eng: "{s3}"'

class KelimeEtkinlikEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aktif_veri = None
        self.dogru_siralama = []
        self.kullanici_siralama = []
        self.calisma_listesi = []
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        self.lbl_ipucu = Label(text="Kelimeyi Yazın", font_size='24sp', size_hint=(1, 0.15))
        main_layout.add_widget(self.lbl_ipucu)
        
        self.cevap_kutusu = StackLayout(padding=20, spacing=15, size_hint=(1, 0.20))
        with self.cevap_kutusu.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.rect = RoundedRectangle(pos=self.cevap_kutusu.pos, size=self.cevap_kutusu.size, radius=[10])
        self.cevap_kutusu.bind(pos=self.guncelle_rect, size=self.guncelle_rect)
        main_layout.add_widget(self.cevap_kutusu)
        
        self.harf_havuzu = StackLayout(padding=20, spacing=25, size_hint=(1, 0.45))
        main_layout.add_widget(self.harf_havuzu)
        
        HEDEF_BTN = 100
        btns = GridLayout(cols=2, spacing=10, size_hint=(1, None), height=HEDEF_BTN)
        b_kontrol = OzelButon(text="Kontrol Et", background_color=(0.2, 0.8, 0.2, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_kontrol.bind(on_press=self.kontrol_et)
        b_goster = OzelButon(text="Kelimeyi Gör", background_color=(1, 0.6, 0, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_goster.bind(on_press=self.dogruyu_goster)
        btns.add_widget(b_kontrol); btns.add_widget(b_goster)
        main_layout.add_widget(btns)
        
        nav = GridLayout(cols=2, spacing=10, size_hint=(1, None), height=HEDEF_BTN)
        b_menu = OzelButon(text="Menü", background_color=(0.5, 0.5, 0.5, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_menu.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        b_ileri = OzelButon(text="İleri", background_color=(0.2, 0.6, 0.8, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_ileri.bind(on_press=lambda x: self.yeni_soru())
        nav.add_widget(b_menu); nav.add_widget(b_ileri)
        main_layout.add_widget(nav)
        
        self.add_widget(main_layout)

    def guncelle_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def baslat(self, liste):
        self.calisma_listesi = liste
        self.yeni_soru()

    def yeni_soru(self):
        self.cevap_kutusu.clear_widgets()
        self.harf_havuzu.clear_widgets()
        self.kullanici_siralama = []
        if not self.calisma_listesi: return
        self.aktif_veri = random.choice(self.calisma_listesi)
        self.lbl_ipucu.text = f"[b]{self.aktif_veri['tr']}[/b]"
        self.lbl_ipucu.markup = True
        
        kelime = self.aktif_veri['en']
        kelime_temiz = re.sub(r"\(.*?\)", "", kelime) 
        temiz_kelime = re.sub(r'[^a-zA-Z]', '', kelime_temiz).lower()
        self.dogru_siralama = list(temiz_kelime)
        
        karisik_harfler = self.dogru_siralama.copy()
        random.shuffle(karisik_harfler)
        
        for harf in karisik_harfler:
            btn = HarfParcasi(harf=harf.upper())
            btn.bind(on_press=self.harf_tasima)
            self.harf_havuzu.add_widget(btn)

    def harf_tasima(self, btn):
        if btn.parent == self.harf_havuzu:
            self.harf_havuzu.remove_widget(btn)
            self.cevap_kutusu.add_widget(btn)
            self.kullanici_siralama.append(btn.text.lower())
        else:
            self.cevap_kutusu.remove_widget(btn)
            self.harf_havuzu.add_widget(btn)
            if btn.text.lower() in self.kullanici_siralama:
                self.kullanici_siralama.remove(btn.text.lower())

    def kontrol_et(self, instance):
        if self.kullanici_siralama == self.dogru_siralama:
            Popup(title='Tebrikler!', content=Label(text='✅ Doğru Yazdınız!', font_size='24sp'), size_hint=(0.6, 0.3)).open()
            SES.oku("Correct!")
        else:
            Popup(title='Hata', content=Label(text='❌ Yanlış Harfler\nTekrar Dene', font_size='20sp', halign='center'), size_hint=(0.6, 0.3)).open()

    def dogruyu_goster(self, instance):
        if self.aktif_veri:
            kelime = self.aktif_veri['en']
            temiz = re.sub(r"\(.*?\)", "", kelime).strip()
            Popup(title='Doğru Kelime', content=Label(text=kelime, font_size='24sp'), size_hint=(0.8, 0.4)).open()
            SES.oku(temiz)

class EtkinlikEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aktif_veri = None
        self.dogru_siralama = []
        self.kullanici_siralama = []
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        self.lbl_ipucu = Label(text="Cümleyi Oluşturun", font_size='20sp', size_hint=(1, 0.15), halign='center', valign='middle')
        self.lbl_ipucu.bind(size=lambda *x: setattr(self.lbl_ipucu, 'text_size', (self.lbl_ipucu.width - 20, None)))
        main_layout.add_widget(self.lbl_ipucu)
        
        self.cevap_kutusu = StackLayout(padding=20, spacing=25, size_hint=(1, 0.30))
        with self.cevap_kutusu.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.rect = RoundedRectangle(pos=self.cevap_kutusu.pos, size=self.cevap_kutusu.size, radius=[10])
        self.cevap_kutusu.bind(pos=self.guncelle_rect, size=self.guncelle_rect)
        main_layout.add_widget(self.cevap_kutusu)
        
        self.kelime_havuzu = StackLayout(padding=20, spacing=25, size_hint=(1, 0.35))
        main_layout.add_widget(self.kelime_havuzu)
        
        HEDEF_BTN = 100
        btns = GridLayout(cols=2, spacing=10, size_hint=(1, None), height=HEDEF_BTN)
        b_kontrol = OzelButon(text="Kontrol Et", background_color=(0.2, 0.8, 0.2, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_kontrol.bind(on_press=self.kontrol_et)
        b_goster = OzelButon(text="Doğruyu Gör", background_color=(1, 0.6, 0, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_goster.bind(on_press=self.dogruyu_goster)
        btns.add_widget(b_kontrol); btns.add_widget(b_goster)
        main_layout.add_widget(btns)
        
        nav = GridLayout(cols=2, spacing=10, size_hint=(1, None), height=HEDEF_BTN)
        b_menu = OzelButon(text="Menü", background_color=(0.5, 0.5, 0.5, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_menu.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        b_ileri = OzelButon(text="İleri", background_color=(0.2, 0.6, 0.8, 1), size_hint=(1, None), height=HEDEF_BTN)
        b_ileri.bind(on_press=lambda x: self.baslat())
        nav.add_widget(b_menu); nav.add_widget(b_ileri)
        main_layout.add_widget(nav)
        
        self.add_widget(main_layout)

    def guncelle_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def baslat(self, liste=None):
        if liste:
            self.calisma_listesi = liste
        elif not self.calisma_listesi and YONETICI.veriler:
            self.calisma_listesi = YONETICI.veriler
        self.yeni_soru()

    def yeni_soru(self):
        self.cevap_kutusu.clear_widgets()
        self.kelime_havuzu.clear_widgets()
        self.kullanici_siralama = []
        if not self.calisma_listesi: return
        self.aktif_veri = random.choice([v for v in self.calisma_listesi if v.get('cen')])
        self.lbl_ipucu.text = f"[b]{self.aktif_veri['ctr']}[/b]"
        self.lbl_ipucu.markup = True
        cumle = self.aktif_veri['cen']
        temiz_cumle = re.sub(r'[^\w\s]', '', cumle) 
        self.dogru_siralama = temiz_cumle.split()
        karisik_kelimeler = self.dogru_siralama.copy()
        random.shuffle(karisik_kelimeler)
        for kelime in karisik_kelimeler:
            btn = KelimeParcasi(metin=kelime)
            btn.bind(on_press=self.kelime_tasima)
            self.kelime_havuzu.add_widget(btn)

    def kelime_tasima(self, btn):
        if btn.parent == self.kelime_havuzu:
            self.kelime_havuzu.remove_widget(btn)
            self.cevap_kutusu.add_widget(btn)
            self.kullanici_siralama.append(btn.text)
        else:
            self.cevap_kutusu.remove_widget(btn)
            self.kelime_havuzu.add_widget(btn)
            if btn.text in self.kullanici_siralama:
                self.kullanici_siralama.remove(btn.text)

    def kontrol_et(self, instance):
        if self.kullanici_siralama == self.dogru_siralama:
            Popup(title='Tebrikler!', content=Label(text='✅ Doğru Cevap!', font_size='24sp'), size_hint=(0.6, 0.3)).open()
            SES.oku("Correct!")
        else:
            Popup(title='Hata', content=Label(text='❌ Yanlış Sıralama\nTekrar Dene', font_size='20sp', halign='center'), size_hint=(0.6, 0.3)).open()

    def dogruyu_goster(self, instance):
        if self.aktif_veri:
            lbl = Label(text=self.aktif_veri['cen'], font_size='20sp', halign='center', valign='middle')
            lbl.bind(size=lambda *x: setattr(lbl, 'text_size', (lbl.width - 20, None)))
            Popup(title='Doğru Cümle', content=lbl, size_hint=(0.8, 0.4)).open()
            SES.oku(self.aktif_veri['cen'])

class Calisma(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gecmis, self.aktif, self.yon, self.cevrildi = [], None, "tr_to_en", False
        self.calisma_listesi = [] 
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.kart = OzelButon(text="Başla", background_color=get_color_from_hex('#455A64'))
        self.kart.font_size = '22sp'
        self.kart.bind(on_press=self.cevir)
        self.btn_ses = OzelButon(text="🔊  DİNLE", background_color=(0.4, 0.4, 0.4, 1), size_hint=(1, None), height=90)
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

    def baslat_ozel(self, mod, liste):
        self.mod = mod
        self.calisma_listesi = liste
        self.gecmis = []
        if self.calisma_listesi: self.ileri(None)
        else: self.kart.text = "Bu levelda veri yok!"

    def seslendir(self, i):
        if self.aktif: 
            if self.mod == "eng_eng":
                metin = f"{self.aktif['word']}. {self.aktif['ex']}"
                SES.oku(metin)
            else:
                ham_metin = self.aktif['en'] if self.mod=="kelime" else self.aktif['cen']
                temiz_metin = re.sub(r"\(.*?\)", "", ham_metin).strip()
                SES.oku(temiz_metin)
            
    def guncelle(self):
        self.kart.markup = True; v = self.aktif
        if not v: return
        
        # --- FONT EŞİTLEME (İSTEK ÜZERİNE GÜNCELLENDİ) ---
        if self.mod == "eng_eng":
            if not self.cevrildi:
                self.kart.ana_renk = get_color_from_hex('#008080')
                self.kart.guncelle_canvas()
                self.kart.color = (1,1,1,1)
                
                # --- YAZI BOYUTU EŞİTLENDİ ---
                # Diğer bölümlerle aynı (22sp) ancak başlık kalın, örnek italik.
                # [size=...] etiketleri kaldırıldı.
                self.kart.text = f"[b]{v['word']}[/b]\n\n{v['def']}\n\n[i]\"{v['ex']}\"[/i]"
            else:
                self.kart.ana_renk = get_color_from_hex('#FBC02D')
                self.kart.guncelle_canvas()
                self.kart.color = (0,0,0,1)
                self.kart.text = f"[b]{v['tr']}[/b]"
            return

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
        if not self.calisma_listesi: return
        if getattr(self,'aktif',None): self.gecmis.append({"v":self.aktif,"y":self.yon})
        try:
            self.aktif=random.choice(self.calisma_listesi)
            if self.mod == "eng_eng":
                self.yon = "eng_eng"
            else:
                self.yon=random.choice(["tr_to_en","en_to_tr"])
            self.cevrildi=False; self.guncelle()
        except: pass
    def geri(self, i): 
        if self.gecmis: s=self.gecmis.pop(); self.aktif=s["v"]; self.yon=s["y"]; self.cevrildi=False; self.guncelle()

class AppMain(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(AnaMenu(name='menu'))
        sm.add_widget(LevelEkrani(name='level'))
        sm.add_widget(InfoEkrani(name='info'))
        sm.add_widget(AyarlarEkrani(name='ayarlar'))
        sm.add_widget(Calisma(name='calisma'))
        sm.add_widget(EtkinlikEkrani(name='etkinlik_cumle'))
        sm.add_widget(KelimeEtkinlikEkrani(name='etkinlik_kelime'))
        return sm

if __name__ == '__main__': AppMain().run()
