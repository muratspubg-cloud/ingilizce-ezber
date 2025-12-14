[app]
title = Ingilizce Ezber
package.name = ingilizce
package.domain = com.ingilizce
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,csv
version = 0.1
requirements = python3,kivy,requests,openssl,plyer,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
# Android özel ayarları
p4a.branch = master
# Log seviyesi
log_level = 2
warn_on_root = 1