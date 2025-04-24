# Wildlife Audio Player GUI

This GUI application allows users to connect to STM32-based audio devices via UART or Bluetooth to control playback, volume, schedules, and download logs. It supports macOS and Windows, and can be packaged into standalone applications.

## Features
- Bluetooth and UART selection and connection
- Volume and duty cycle control
- Schedule configuration with overlap validation
- Log downloading and saving
- Real-time UART debug display

---



## If want a mini standalone Python environment that just runs
### MacOS `.app` Bundle

#### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

#### Step 2: Generate `.spec` file (only once)

```bash
pyi-makespec WAP_GUI.py
```

#### Step 3: Modify the generated `WAP_GUI.spec`
You can open it using TextEdit and then replace:
```python
exe = EXE(...)
```
with:
```python
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WAP_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
```
Then **append** this after the `coll = COLLECT(...)` block to create the `.app` bundle:

```python
app = BUNDLE(
    coll,
    name='WildlifeAudioPlayer.app',
    icon='wildlife.icns'
)
```

Make sure `wildlife.icns` is in the project folder.

---
#### Step 4: Build the App

```bash
pyinstaller WAP_GUI.spec
```

Find your `.app` inside the `dist/` folder.

---
#### Step 5: Clean up build artifacts

After building, clean the unnecessary folders:

**macOS or Linux:**
```bash
rm -rf build/ __pycache__/ *.spec
```

### Windows `.exe` Executable

#### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

#### Step 2: Create Windows Executable

```bash
pyinstaller --onefile --noconsole --icon=wildlife.ico WAP_GUI.py
```

The output `.exe` file will be found in the `dist/` directory.

---
#### Step 5: Clean up build artifacts

After building, clean the unnecessary folders:

**Windows (CMD):**
```cmd
rmdir /s /q build
del /q *.spec
```

---

## If want tp run/modify the .py script
### Requirements

To install the dependencies:

```bash
pip install -r requirements.txt
```

#### `requirements.txt` contains:
```txt
pyserial
bleak
tk
```

---

### Running from Source

To run the GUI manually (Python 3.10+ required):

```bash
python WAP_GUI.py
```

---

## Author
**Jaspreet Singh**  
Developer of the Wildlife Audio Player GUI  
[https://github.com/jsingh08](https://github.com/jsingh08)
