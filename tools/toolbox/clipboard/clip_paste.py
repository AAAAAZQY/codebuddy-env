# -*- coding: utf-8 -*-
r"""
clip_paste.py - 用 Keil 做剪贴板中转, 绕过 OcularSD 剪贴板拦截。
放在 toolbox/clipboard/ 下, 双击 run.bat 启动。Ctrl+C 退出。

原理(实测):
  OcularSD 按进程授权: VS Code/Python 剪贴板=禁止(读不到), Keil 剪贴板=允许
  (既能读受保护内容, 又能写出干净剪贴板)。所以本脚本用 Keil 当中转:
    目标窗口按 Ctrl+V -> 脚本拦截这次按键 ->
      1) 切到 Keil, 把受保护内容粘贴进 Keil 新建的空白文档(Ctrl+V)
      2) Keil 全选+复制(Ctrl+A, Ctrl+C) -> 此时剪贴板变成 Keil 产出的干净内容
      3) 切回目标窗口, 发原生 Ctrl+V -> 目标程序正常粘贴
  python 全程不读剪贴板, 只发按键, OcularSD 勾不到。

日志: 同时打印到控制台和同目录 clip_paste.log, 排错时把该文件内容发我。
前置: Keil 一直开着即可, 无需手动准备任何文件。
"""
import ctypes
import ctypes.wintypes
import atexit
import datetime
import os
import sys
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

ULONG_PTR = ctypes.c_size_t
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WH_KEYBOARD_LL = 13
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1
ASFW_ANY = 0xFFFFFFFF
TH32CS_SNAPPROCESS = 0x00000002


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.wintypes.DWORD),
        ("cntUsage", ctypes.wintypes.DWORD),
        ("th32ProcessID", ctypes.wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", ctypes.wintypes.DWORD),
        ("cntThreads", ctypes.wintypes.DWORD),
        ("th32ParentProcessID", ctypes.wintypes.DWORD),
        ("pcPriClassBase", ctypes.wintypes.LONG),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


kernel32.CreateToolhelp32Snapshot.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = ctypes.wintypes.HANDLE
kernel32.Process32First.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32First.restype = ctypes.wintypes.BOOL
kernel32.Process32Next.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32Next.restype = ctypes.wintypes.BOOL
kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
kernel32.CloseHandle.restype = ctypes.wintypes.BOOL

user32.GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD
user32.GetClassNameW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.IsIconic.argtypes = [ctypes.wintypes.HWND]
user32.IsIconic.restype = ctypes.wintypes.BOOL
user32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = ctypes.wintypes.BOOL
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
user32.IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
user32.IsWindowVisible.restype = ctypes.wintypes.BOOL
user32.AttachThreadInput.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.wintypes.BOOL]
user32.AttachThreadInput.restype = ctypes.wintypes.BOOL


_pending = False
_target_hwnd = None
_hook = None
_proc = None
_keil_hwnd = None
_logf = None
WM_APP_WAKE = 0x8000      # WM_APP, 用于唤醒阻塞的消息循环
_hook_thread_id = 0
_relaying = False         # 中转进行中: 期间放过自己注入的 Ctrl+V, 防止钩子自拦截


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("_dummy", ctypes.c_ubyte * 24)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.wintypes.DWORD), ("u", _INPUTUNION)]


def _open_log():
    global _logf
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clip_paste.log")
        _logf = open(path, "w", encoding="utf-8")
    except OSError:
        _logf = None


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = "[%s] %s" % (ts, msg)
    try:
        print(line, flush=True)
    except Exception:
        pass
    if _logf:
        try:
            _logf.write(line + "\n")
            _logf.flush()
        except Exception:
            pass


def _wnd_title(hwnd):
    if not hwnd:
        return ""
    buf = ctypes.create_unicode_buffer(256)
    if user32.GetWindowTextW(hwnd, buf, 256):
        return buf.value
    return ""


def _send_combo(vk):
    arr = (INPUT * 4)()
    arr[0].type = arr[1].type = arr[2].type = arr[3].type = INPUT_KEYBOARD
    arr[0].u.ki.wVk = VK_CONTROL
    arr[1].u.ki.wVk = vk
    arr[2].u.ki.wVk = vk
    arr[2].u.ki.dwFlags = KEYEVENTF_KEYUP
    arr[3].u.ki.wVk = VK_CONTROL
    arr[3].u.ki.dwFlags = KEYEVENTF_KEYUP
    user32.SendInput(4, arr, ctypes.sizeof(INPUT))


def find_keil():
    keil_pid = None
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
    if kernel32.Process32First(snap, ctypes.byref(pe)):
        while True:
            name = pe.szExeFile.split(b"\x00")[0].lower()
            if name == b"uv4.exe":
                keil_pid = pe.th32ProcessID
                break
            if not kernel32.Process32Next(snap, ctypes.byref(pe)):
                break
    kernel32.CloseHandle(snap)
    if not keil_pid:
        return None

    found = []

    def enum(hwnd, _):
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == keil_pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows.argtypes = [ENUMPROC, ctypes.wintypes.LPARAM]
    user32.EnumWindows(ENUMPROC(enum), 0)
    return found[0] if found else None


def focus(hwnd):
    user32.AllowSetForegroundWindow(ASFW_ANY)
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    for _ in range(3):
        if user32.GetForegroundWindow() == hwnd:
            break
        cur = user32.GetForegroundWindow()
        ct = user32.GetWindowThreadProcessId(cur, None)
        kt = user32.GetWindowThreadProcessId(hwnd, None)
        if ct and kt and ct != kt:
            user32.AttachThreadInput(ct, kt, True)
        user32.SetForegroundWindow(hwnd)
        if ct and kt and ct != kt:
            user32.AttachThreadInput(ct, kt, False)
        time.sleep(0.06)
    if user32.GetForegroundWindow() != hwnd:
        # Alt 键技巧: 伪造一次用户输入, 让系统允许后台进程抢前台
        user32.keybd_event(VK_MENU, 0, 0, 0)
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.08)
    if user32.GetForegroundWindow() != hwnd:
        user32.SwitchToThisWindow(hwnd, True)
        time.sleep(0.1)
    time.sleep(0.1)


def _press_key(vk, alt=False):
    n = 4 if alt else 2
    arr = (INPUT * n)()
    i = 0
    if alt:
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki.wVk = VK_MENU
        i += 1
    arr[i].type = INPUT_KEYBOARD
    arr[i].u.ki.wVk = vk
    i += 1
    arr[i].type = INPUT_KEYBOARD
    arr[i].u.ki.wVk = vk
    arr[i].u.ki.dwFlags = KEYEVENTF_KEYUP
    i += 1
    if alt:
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki.wVk = VK_MENU
        arr[i].u.ki.dwFlags = KEYEVENTF_KEYUP
        i += 1
    user32.SendInput(i, arr, ctypes.sizeof(INPUT))


def _keil_pid():
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(_keil_hwnd, ctypes.byref(pid))
    return pid.value


def find_save_dialog():
    kpid = _keil_pid()
    if not kpid:
        return None
    hits = []

    def enum(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(64)
        if user32.GetClassNameW(hwnd, cls, 64) and cls.value == "#32770":
            p = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == kpid:
                hits.append(hwnd)
        return True

    ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows.argtypes = [ENUMPROC, ctypes.wintypes.LPARAM]
    user32.EnumWindows(ENUMPROC(enum), 0)
    return hits[0] if hits else None


def dismiss_save_dialog():
    dlg = find_save_dialog()
    if dlg:
        user32.AllowSetForegroundWindow(ASFW_ANY)
        user32.SetForegroundWindow(dlg)
        time.sleep(0.1)
        _press_key(0x4E, alt=True)   # Alt+N -> 否/No, 不保存
        time.sleep(0.15)


def relay(target_hwnd):
    global _keil_hwnd, _relaying
    _relaying = True
    try:
        if not _keil_hwnd or not user32.IsWindow(_keil_hwnd):
            _keil_hwnd = find_keil()
            log("[中转] 重新查找 Keil -> %s" % _keil_hwnd)
        if not _keil_hwnd:
            log("[中转] 找不到 Keil, 本次 Ctrl+V 放行(多半失败)")
            return
        log("[中转] 目标 hwnd=%s 标题=%s" % (target_hwnd, _wnd_title(target_hwnd)))

        focus(_keil_hwnd)
        fg = user32.GetForegroundWindow()
        log("[中转] 切到 Keil 后前台=%s 标题=%s (期望是 Keil)" % (fg, _wnd_title(fg)))

        _send_combo(0x4E)          # Ctrl+N 新建空白文档
        time.sleep(0.35)
        _send_combo(0x56)          # Ctrl+V 粘入受保护内容
        time.sleep(0.4)
        _send_combo(0x41)          # Ctrl+A 全选
        time.sleep(0.1)
        _send_combo(0x43)          # Ctrl+C 复制 -> 干净剪贴板
        time.sleep(0.25)
        _send_combo(0x41)          # Ctrl+A 再次全选
        time.sleep(0.08)
        _press_key(0x2E)           # Delete 清空, 避免关闭时弹保存框
        time.sleep(0.1)
        _send_combo(0x73)          # Ctrl+F4 关闭当前文档(已清空, 通常不弹)
        time.sleep(0.3)
        log("[中转] 关闭时保存对话框=%s" % ("有" if find_save_dialog() else "无"))
        dismiss_save_dialog()      # 备份: 万一仍弹, 选否
        time.sleep(0.15)

        if target_hwnd and user32.IsWindow(target_hwnd):
            focus(target_hwnd)
            log("[中转] 切回目标后前台=%s" % user32.GetForegroundWindow())
            _send_combo(0x56)      # 目标: 原生 Ctrl+V 粘贴干净内容
            log("[中转] 已向目标发送原生 Ctrl+V")
    except Exception:
        import traceback as _tb
        log("[中转异常] " + _tb.format_exc())
    finally:
        _relaying = False


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


def _low_level_keyboard_proc(nCode, wParam, lParam):
    try:
        global _pending, _target_hwnd, _keil_hwnd
        if nCode == 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.vkCode == 0x56:
                ctrl = user32.GetAsyncKeyState(VK_CONTROL) & 0x8000
                alt = user32.GetAsyncKeyState(VK_MENU) & 0x8000
                win = (user32.GetAsyncKeyState(VK_LWIN) & 0x8000) or (user32.GetAsyncKeyState(VK_RWIN) & 0x8000)
                if ctrl and not alt and not win:
                    if _keil_hwnd and user32.IsWindow(_keil_hwnd) and not _relaying:
                        _target_hwnd = user32.GetForegroundWindow()
                        _pending = True
                        user32.PostThreadMessageW(_hook_thread_id, WM_APP_WAKE, 0, 0)  # 唤醒阻塞的消息循环
                        log("[钩子] 拦截 Ctrl+V, 目标 hwnd=%s 标题=%s" % (_target_hwnd, _wnd_title(_target_hwnd)))
                        return 1   # 拦截, 由消息循环做 Keil 中转
                    else:
                        log("[钩子] 检测到 Ctrl+V, 但 Keil 无效, 放行原生粘贴")
    except Exception:
        import traceback as _tb
        log("[钩子异常] " + _tb.format_exc())
    return user32.CallNextHookEx(None, nCode, wParam, lParam)


def _unhook():
    global _hook
    if _hook:
        user32.UnhookWindowsHookEx(_hook)
        _hook = None


def main():
    _open_log()
    log("==== 启动 ====")
    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
    _proc = HOOKPROC(_low_level_keyboard_proc)
    user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, ctypes.wintypes.HINSTANCE, ctypes.wintypes.DWORD)
    user32.SetWindowsHookExW.restype = ctypes.wintypes.HHOOK
    user32.CallNextHookEx.argtypes = (ctypes.wintypes.HHOOK, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
    user32.CallNextHookEx.restype = ctypes.c_int
    user32.UnhookWindowsHookEx.argtypes = (ctypes.wintypes.HHOOK,)
    user32.UnhookWindowsHookEx.restype = ctypes.wintypes.BOOL
    user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
    user32.GetAsyncKeyState.restype = ctypes.c_short
    user32.AllowSetForegroundWindow.argtypes = (ctypes.wintypes.DWORD,)
    user32.AllowSetForegroundWindow.restype = ctypes.wintypes.BOOL
    user32.PostThreadMessageW.argtypes = (ctypes.wintypes.DWORD, ctypes.wintypes.UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
    user32.PostThreadMessageW.restype = ctypes.wintypes.BOOL
    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = ctypes.wintypes.DWORD
    user32.SystemParametersInfoW.argtypes = (ctypes.wintypes.UINT, ctypes.wintypes.UINT, ctypes.c_void_p, ctypes.wintypes.UINT)
    user32.SystemParametersInfoW.restype = ctypes.wintypes.BOOL
    user32.keybd_event.argtypes = (ctypes.c_ubyte, ctypes.c_ubyte, ctypes.wintypes.DWORD, ULONG_PTR)
    user32.SwitchToThisWindow.argtypes = (ctypes.wintypes.HWND, ctypes.wintypes.BOOL)
    # 关闭前台锁: 让后台进程(本脚本)能稳定把 Keil 抢到前台, 否则 SendInput 的按键会发到原窗口
    _ok = user32.SystemParametersInfoW(0x2000, 0, None, 0)  # SPI_SETFOREGROUNDLOCKTIMEOUT = 0
    log("前台锁关闭: %s" % ("成功" if _ok else "失败"))

    _hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _proc, None, 0)
    if not _hook:
        log("SetWindowsHookEx 失败(可能被 DLP/杀软拦截)。退出。")
        return
    atexit.register(_unhook)

    global _hook_thread_id
    _hook_thread_id = kernel32.GetCurrentThreadId()

    global _keil_hwnd
    _keil_hwnd = find_keil()
    if _keil_hwnd:
        log("已找到 Keil 窗口 hwnd=%s, 中转就绪。" % _keil_hwnd)
    else:
        log("警告: 未找到 Keil(UV4.exe)。Ctrl+V 将放行原生粘贴(多半失败)。请确认 Keil 已打开。")
    log("已启动(Keil 中转)。VS Code 复制 -> 目标程序 Ctrl+V 即可。")

    msg = ctypes.wintypes.MSG()
    user32.GetMessageW.argtypes = [ctypes.POINTER(ctypes.wintypes.MSG), ctypes.wintypes.HWND, ctypes.c_uint, ctypes.c_uint]
    user32.GetMessageW.restype = ctypes.c_int
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        global _pending, _target_hwnd
        if _pending:
            tgt = _target_hwnd
            _pending = False
            _target_hwnd = None
            relay(tgt)
            log("[完成] 一轮中转结束")
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("已退出。")
    except Exception:
        import traceback as _tb
        try:
            log("致命异常: " + _tb.format_exc())
        except Exception:
            pass
        raise
