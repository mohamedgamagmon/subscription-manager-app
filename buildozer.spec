[app]
title = Subscription Manager
package.name = subscriptionmanager
package.domain = org.subscription
source.dir = .
source.include_exts = py,png,jpg,db
version = 1.0
requirements = python3,kivy==2.2.1
orientation = portrait
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
