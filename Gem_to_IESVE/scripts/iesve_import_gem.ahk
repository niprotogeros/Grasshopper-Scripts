#Requires AutoHotkey v2.0+
; iesve_import_gem.ahk
; Usage: AutoHotkey.exe iesve_import_gem.ahk "C:\path\to\model.gem"
; This script assumes IESVE is already running. It focuses the window,
; navigates to ModelIT, opens File > Import > GEM File, selects the GEM,
; and confirms quarantine. You may need to tweak hotkeys for your VE build.

#SingleInstance Force
#Warn
SendMode("Event")
SetTitleMatchMode 2  ; partial title match

if A_Args.Length < 1 {
    MsgBox "No GEM path provided.`nUsage: AutoHotkey.exe iesve_import_gem.ahk ""C:\path\model.gem""", "IESVE", "Iconx"
    ExitApp
}
gem := A_Args[0]
if !FileExist(gem) {
    MsgBox "GEM file not found:`n" gem, "IESVE", "Iconx"
    ExitApp
}

; Wait for VE main window (process name is VE.exe)
if !WinWait("ahk_exe VE.exe",, 30) {
    MsgBox "Could not find a running IESVE window (VE.exe).", "IESVE", "Iconx"
    ExitApp
}
WinActivate("ahk_exe VE.exe")
Sleep 300

; ---- Navigate to ModelIT (Alt+M) ----
Send("!m")
Sleep 400

; ---- File > Import > GEM File... ----
; Note: The exact menu accelerators may vary by version. If this sequence doesn't
; work on your machine, run once and use Alt key to verify letters, then edit below.
Send("!f")     ; File
Sleep 150
Send("i")      ; Import...
Sleep 150
Send("g")      ; GEM File...
Sleep 400

; ---- File Open dialog ----
if !WinWaitActive("Open",, 10) {
    MsgBox "File Open dialog did not appear. Adjust menu accelerator keys in the script.", "IESVE", "Iconx"
    ExitApp
}

; Type the path into the file name box
; Common control name for the path edit is Edit1
ControlSetText("Edit1", gem, "Open")
Sleep 250
Send("{Enter}")

; ---- Quarantine dialog (optional) ----
; Some builds show a Quarantine or Import dialog with an OK/Import button.
; We try to accept it if it appears; otherwise continue silently.
if WinWait("Quarantine",, 20) {
    WinActivate("Quarantine")
    Sleep 150
    ; Press Alt+O for OK (adjust mnemonic if the button differs)
    Send("!o")
}

; Script ends here. VE will proceed with the GEM import.
ExitApp
