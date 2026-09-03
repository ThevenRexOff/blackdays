import os
import sys
import shutil
import subprocess


CRITICAL_MODULES = [
    "generate_password",
    "fingerprint",
    "generate_fingerprint",
]

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SOURCE_DIR, "dist")

IS_WINDOWS = os.name == "nt"


def get_python():
    if IS_WINDOWS:
        win = os.path.join(SOURCE_DIR, ".venv", "Scripts", "python.exe")
        if os.path.exists(win):
            return win
    else:
        unix = os.path.join(SOURCE_DIR, ".venv", "bin", "python")
        if os.path.exists(unix):
            return unix
    return sys.executable


def clean_dist():
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    print("  Cleaned dist/")


def copy_unprotected():
    files = ["amazon_v2.py", "telegram_bot.py", "log.py", "tempmail.py", "requirements.txt", "index.html", "app.py"]
    if IS_WINDOWS:
        files.append("run_bot.bat")
    else:
        files.append("run_bot.sh")
    for f in files:
        src = os.path.join(SOURCE_DIR, f)
        if os.path.exists(src):
            shutil.copy2(src, DIST_DIR)
            print(f"  Copied: {f}")
    env = os.path.join(SOURCE_DIR, ".env")
    if os.path.exists(env):
        shutil.copy2(env, DIST_DIR)
        print(f"  Copied: .env")


def compile_with_nuitka(module_name: str) -> bool:
    python = get_python()
    input_path = os.path.join(SOURCE_DIR, f"{module_name}.py")

    if not os.path.exists(input_path):
        print(f"    Skip: {module_name}.py (not found)")
        return False

    print(f"    Compiling: {module_name}.py → native extension")

    cmd = [
        python, "-m", "nuitka",
        "--mode=module",
        f"--output-dir={DIST_DIR}",
        "--remove-output",
        "--python-flag=no_asserts",
        "--python-flag=no_docstrings",
        input_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"    OK: {module_name}")
            return True
        else:
            print(f"    FAIL: {module_name}")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-3:]:
                    print(f"      {line}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT: {module_name}")
        return False
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def create_stubs():
    for module_name in CRITICAL_MODULES:
        stub_path = os.path.join(DIST_DIR, f"{module_name}.py")

        if os.path.exists(stub_path):
            continue

        source_path = os.path.join(SOURCE_DIR, f"{module_name}.py")
        if not os.path.exists(source_path):
            continue

        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()

        compiled = compile(source, f"{module_name}.py", "exec")
        has_all = any(
            isinstance(c, tuple) and len(c) >= 2 and c[0] == "__all__"
            for c in compiled.co_consts
        )

        if has_all:
            stub = f"""
import importlib.util as _iu
import os as _os
import sys as _sys

_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ext in ('.so', '.pyd', '.cpython-*.so'):
    import glob as _g
    for _f in _g.glob(_os.path.join(_dir, '{module_name}*' + _ext)):
        _spec = _iu.spec_from_file_location('{module_name}', _f)
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _sys.modules[__name__] = _mod
        for _k in dir(_mod):
            if not _k.startswith('_'):
                globals()[_k] = getattr(_mod, _k)
        break
"""
        else:
            stub = f"""
import importlib.util as _iu
import os as _os
import sys as _sys

_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ext in ('.so', '.pyd', '.cpython-*.so'):
    import glob as _g
    for _f in _g.glob(_os.path.join(_dir, '{module_name}*' + _ext)):
        _spec = _iu.spec_from_file_location('{module_name}', _f)
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _sys.modules[__name__] = _mod
        for _k in dir(_mod):
            if not _k.startswith('_'):
                globals()[_k] = getattr(_mod, _k)
        break
"""
        with open(stub_path, "w", encoding="utf-8") as f:
            f.write(stub)


def verify_dist():
    print("\n  Verifying distribution...")

    required = ["amazon_v2.py", "log.py", "requirements.txt"]
    missing = [f for f in required if not os.path.exists(os.path.join(DIST_DIR, f))]

    for module in CRITICAL_MODULES:
        has_py = os.path.exists(os.path.join(DIST_DIR, f"{module}.py"))
        has_ext = any(
            f.startswith(module) and (f.endswith(".so") or f.endswith(".pyd"))
            for f in os.listdir(DIST_DIR)
        )
        if has_ext:
            print(f"    {module}: native extension")
        elif has_py:
            print(f"    {module}: stub only (Nuitka may have failed)")
        else:
            missing.append(f"{module}.py")

    if missing:
        print(f"    Missing: {', '.join(missing)}")
        return False

    total_size = sum(
        os.path.getsize(os.path.join(DIST_DIR, f))
        for f in os.listdir(DIST_DIR)
    )
    print(f"    Total size: {total_size / 1024:.1f} KB")
    return True


def main():
    print("=" * 50)
    print("  AMAZON FP - Nuitka Build Pipeline")
    print("=" * 50)

    print("\n[1/4] Cleaning dist/")
    clean_dist()

    print("\n[2/4] Copying unprotected files")
    copy_unprotected()

    print("\n[3/4] Compiling with Nuitka")
    success = 0
    for module in CRITICAL_MODULES:
        if compile_with_nuitka(module):
            success += 1
    print(f"\n  Compiled: {success}/{len(CRITICAL_MODULES)} modules")

    print("\n[3b] Creating Python stubs for fallback")
    create_stubs()

    print("\n[4/4] Verifying distribution")
    ok = verify_dist()

    print("\n" + "=" * 50)
    if ok:
        launcher = "run_bot.bat" if IS_WINDOWS else "run_bot.sh"
        print("  Build complete: dist/")
        print(f"  Launch with: {launcher}  (Linux/macOS: sh {launcher})")
        if not IS_WINDOWS:
            print("  NOTE: this dist/ contains .so (Linux). For Windows run build.py there.")
    else:
        print("  Build had issues - check above")
    print("=" * 50)


if __name__ == "__main__":
    main()
