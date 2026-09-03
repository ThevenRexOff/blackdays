import io
import os
import sys


def _make_safe_write(stream):
    _orig_write = stream.write

    def _safe_write(data):
        try:
            return _orig_write(data)
        except UnicodeEncodeError:
            if isinstance(data, str):
                return _orig_write(
                    data.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                )
            return 0

    return _safe_write


def enforce_process_utf8(entry_file: str, argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    # Hard fix: relaunch with UTF-8 mode on Windows.
    if sys.platform == 'win32' and not sys.flags.utf8_mode and not os.environ.get('_SXG_UTF8_RELAUNCH'):
        _env = os.environ.copy()
        _env['_SXG_UTF8_RELAUNCH'] = '1'
        _env['PYTHONIOENCODING'] = 'utf-8:replace'
        _env['PYTHONUTF8'] = '1'
        try:
            try:
                import ctypes

                ctypes.windll.kernel32.SetConsoleOutputCP(65001)
                ctypes.windll.kernel32.SetConsoleCP(65001)
            except Exception:
                pass
            os.execve(sys.executable, [sys.executable, '-X', 'utf8', entry_file] + argv, _env)
        except Exception:
            pass

    # Soft fix: force UTF-8 environment and streams.
    os.environ['PYTHONIOENCODING'] = 'utf-8:replace'
    os.environ['PYTHONUTF8'] = '1'

    if sys.platform == 'win32':
        try:
            os.system('')
        except Exception:
            pass
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    for _stream_name in ('stdout', 'stderr'):
        _s = getattr(sys, _stream_name, None)
        if _s is None:
            continue
        try:
            _s.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
        except Exception:
            try:
                if hasattr(_s, 'buffer'):
                    setattr(
                        sys,
                        _stream_name,
                        io.TextIOWrapper(
                            _s.buffer,
                            encoding='utf-8',
                            errors='replace',
                            line_buffering=True,
                        ),
                    )
            except Exception:
                pass

    for _stream_name in ('stdout', 'stderr'):
        try:
            _s = getattr(sys, _stream_name)
            _s.write = _make_safe_write(_s)
        except Exception:
            pass
