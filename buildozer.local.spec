[app]
title = Retro Fighter
package.name = retrofighter
package.domain = org.retro.fighter

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,wav,ogg,ttf
source.include_patterns = assets/*, assets/**/*

version = 1.0.0

requirements = python3,kivy==2.2.1

# Architecture: Android only runs Python 3.11 on 64-bit
android.archs = arm64-v8a

orientation = landscape
fullscreen = 1
supported.orientation = landscape

presplash.filename = assets/Menu/project_logo.png
icon.filename = assets/Menu/project_logo.png

entrypoint = main.py

android.python_debuggable = False
android.hide_cursor = 1
android.disable_window_title = 1
android.allow_backup = False
android.copy_libs = 1

# Android versions
android.api = 33
android.minapi = 21

# Permissions
android.permissions = INTERNET

log_level = 2



[app.p4a]
bootstrap = sdl2
local_cmake = True
p4a.extra_args = --disable-remote-debugging --no-compile-pymodule=_remote_debugging

# No remote debugging module (fixes compile errors)
p4a.branch = master
local_recipes = recipes
blacklist_recipes = jpeg



[buildozer]
log_level = 2
warn_on_root = 1


# This section should be empty except python_debuggable (optional)
[app.android]
android.python_debuggable = False


[android]
android.sdk_path = /Users/guimachado/.buildozer/android/platform/android-sdk
android.ndk_path = /Users/guimachado/.buildozer/android/platform/android-ndk-r25b
