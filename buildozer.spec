[app]
title = Ingilizce Ezber
package.name = ingilizce
package.domain = com.ingilizce
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,csv
version = 0.1

# GEREKSİNİMLER TAM LİSTE
requirements = python3,kivy==2.3.0,requests,openssl,plyer,pyjnius,urllib3,chardet,idna,certifi

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Android ayarları
p4a.branch = master
p4a.bootstrap = sdl2

log_level = 2
warn_on_root = 1
