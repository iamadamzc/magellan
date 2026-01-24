# How to Create Desktop Shortcut for Scanner

## Quick Launch Setup

### Option 1: Use the Batch File (Easiest)

1. **Right-click** on `Launch_Scanner.bat` (in `A:\1\scanner\`)
2. Click **"Send to" → "Desktop (create shortcut)"**
3. **Rename** the shortcut to "📊 Scanner"
4. **Double-click** the desktop icon to launch!

---

### Option 2: Create PowerShell Shortcut (Advanced)

If you want a cleaner launcher:

1. **Right-click** on Desktop → **New → Shortcut**
2. **Location**: 
   ```
   powershell.exe -WindowStyle Hidden -Command "cd 'A:\1\scanner'; Start-Process 'http://localhost:8501'; streamlit run app.py"
   ```
3. **Name**: `Scanner Pro`
4. **Icon** (optional):
   - Right-click shortcut → **Properties**
   - Click **"Change Icon"**
   - Browse to: `C:\Windows\System32\shell32.dll`
   - Choose a chart/graph icon

---

### Option 3: Create VBS Script (Silent Launch)

For completely silent background launch:

1. Create `Launch_Scanner.vbs` with this content:
   ```vbscript
   Set WshShell = CreateObject("WScript.Shell")
   WshShell.CurrentDirectory = "A:\1\scanner"
   WshShell.Run "cmd /c streamlit run app.py", 0, False
   WshShell.Run "http://localhost:8501", 1, False
   ```

2. Right-click → Send to Desktop
3. Double-click to launch (no console window!)

---

## What Happens When You Click

1. ✅ Changes to scanner directory
2. ✅ Starts Streamlit server
3. ✅ Opens browser to `http://localhost:8501`
4. ✅ Scanner UI loads automatically

---

## Stopping the Scanner

- **Close the browser tab** (scanner keeps running in background)
- **Close the command window** (stops scanner completely)
- Or press **Ctrl+C** in the terminal

---

## Recommended: Option 1 (Batch File)

The `Launch_Scanner.bat` file is already created. Just:
1. Right-click it
2. Send to Desktop
3. Done! 🎯

---

## Bonus: Auto-Start on Windows Login

To make the scanner start automatically when you log in:

1. Press **Win+R**
2. Type: `shell:startup`
3. Copy `Launch_Scanner.bat` to that folder
4. Scanner will auto-launch on every login!

---

**Status**: Desktop launcher ready! 🚀
