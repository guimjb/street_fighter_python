# Buildozer Spec Reference (`buildozer.spec`)

This documents every parameter currently set in `buildozer.spec` and how to build an Android APK using WSL + Python virtualenv.

## [app] section
- `title = Retro Fighter`: App display name.
- `package.name = retrofighter`: Package name component.
- `package.domain = org.retro.fighter`: Reverse-domain used with `package.name` to form the app id.
- `source.dir = .`: Project root to package.
- `source.include_exts = py,png,kv,atlas,json,wav,ogg,ttf`: File extensions included in the app bundle.
- `version = 1.0.0`: App version string.
- `requirements = python3,kivy==2.2.1,pillow`: Python modules bundled into the build.
- `android.archs = arm64-v8a`: Target ABI (Android requires 64-bit; Python 3.11 build).
- `android.accept_sdk_license = True`: Auto-accept Android SDK license.
- `orientation = landscape`: Force landscape.
- `fullscreen = 1`: Request fullscreen.
- `supported.orientation = landscape`: Declares supported orientations.
- `presplash.filename = assets/Menu/project_logo.png`: Splash image.
- `icon.filename = assets/Menu/project_logo.png`: App icon.
- `entrypoint = main.py`: Entry script (calls `FighterApp`).
- `android.python_debuggable = False`: Disable Python debug build.
- `android.hide_cursor = 1`: Hide mouse cursor.
- `android.disable_window_title = 1`: Removes window title.
- `android.allow_backup = False`: Disable Android backup.
- `android.copy_libs = 1`: Bundle Python libs into APK.
- `android.api = 33`: Target Android API level.
- `android.minapi = 21`: Minimum Android API level.
- `android.permissions = INTERNET`: Declares INTERNET permission (for any remote assets/logging).
- `log_level = 2`: Buildozer log verbosity.

## [app.p4a] section
- `bootstrap = sdl2`: Use SDL2 bootstrap for Kivy.
- `local_cmake = True`: Use a local CMake to speed/ensure build.
- `p4a.extra_args = --disable-remote-debugging --no-compile-pymodule=_remote_debugging`: Disable remote debugging module to avoid compile issues.
- `p4a.branch = master`: Use master branch of python-for-android.

## [buildozer] section
- `log_level = 2`: Buildozer verbosity during commands.
- `warn_on_root = 1`: Warn if running as root.

## [app.android] section
- `android.python_debuggable = False`: Duplicate explicit setting for Android debug flag (kept empty otherwise).

## Building for Android (WSL + venv)
1) **Set up WSL Ubuntu** (if on Windows): Install Ubuntu from the Store, update packages (`sudo apt update && sudo apt upgrade`).
2) **Install system deps** (inside WSL):
   - `sudo apt install build-essential git python3 python3-venv python3-pip pkg-config libffi-dev libssl-dev libsqlite3-dev zlib1g-dev libbz2-dev libreadline-dev libncurses5-dev libncursesw5-dev libgdbm-dev libnss3-dev liblzma-dev openjdk-17-jdk unzip zip`
   - For SDL2/Kivy build requirements: `sudo apt install libgl1-mesa-dev libgles2-mesa-dev libmtdev-dev libzbar-dev libjpeg-dev libfreetype6-dev`
   - Android SDK/NDK tools are handled by buildozer; ensure `openjdk-17` is present.
3) **Create/activate a Python venv**:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
4) **Install Python build deps in venv**:
   - `pip install --upgrade pip cython==0.29.36 virtualenv`
   - `pip install buildozer`
5) **Install project requirements in venv** (for local runs/tests): `pip install -r requirements.txt` (or `pip install kivy==2.2.1 pillow`).
6) **Build the APK**:
   - From the project root in WSL with the venv active: `buildozer -v android debug`
   - First run downloads the Android SDK/NDK/gradle into `~/.buildozer`.

7) **APK to Phone**
    - Send the APK file to your Android device and install/run it.
    - Use adb for debugging the APK on the phone.

Notes:
- Keep `arm64-v8a` for 64-bit compliance.
- If you change Python/Kivy versions, update `requirements` and ensure compatible NDK/SDK via buildozer logs.
- Use `buildozer android clean` if builds get stuck after config changes.
