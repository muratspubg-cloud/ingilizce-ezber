[app]
# Uygulama Adı
title = Ingilizce Ezber
package.name = ingilizce
package.domain = com.ingilizce

# Dosyalar
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,csv

# Sürüm
version = 0.1

# GEREKSİNİMLER (Plyer, Requests, Pyjnius eklendi)
requirements = python3,kivy==2.3.0,requests,openssl,plyer,pyjnius,urllib3,chardet,idna,certifi

# Ekran Ayarları
orientation = portrait
fullscreen = 0

# İzinler (İnternet ve Depolama)
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# Mimariler (Modern telefonlar için)
android.archs = arm64-v8a, armeabi-v7a

# Android Ayarları
android.allow_backup = True
p4a.branch = master
p4a.bootstrap = sdl2

# Loglama
log_level = 2
warn_on_root = 1
