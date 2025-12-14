[app]
title = Ingilizce Ezber
package.name = ingilizce
package.domain = com.ingilizce
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,csv
version = 0.1

# GEREKSİNİMLER (Versiyonlar sabitlendi - Güvenlik İçin)
# Kivy 2.3.0 en stabil sürümdür.
requirements = python3,kivy==2.3.0,requests,openssl,plyer,pyjnius,urllib3,chardet,idna,certifi

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# ANDROID AYARLARI (GÜNCEL STANDARTLAR)
# API 33 = Android 13 (Google Play Standardı)
android.api = 33
# Min API 24 = Android 7.0 (Daha eskisi için çok fazla ayar gerekir, 7.0 idealdir)
android.minapi = 24
# NDK LTS sürümü
android.ndk = 25b
# Lisansı otomatik kabul et
android.accept_sdk_license = True

android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# P4A (Python for Android) ayarları
# Branch'i boş bırakarak buildozer'ın en uyumlu sürümü seçmesini sağlıyoruz.
# p4a.branch = master  <-- BU SATIR RİSKLİ OLDUĞU İÇİN KALDIRILDI

p4a.bootstrap = sdl2

log_level = 2
warn_on_root = 1
