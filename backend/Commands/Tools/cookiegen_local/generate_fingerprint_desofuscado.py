#!/usr/bin/env python3
"""Recovered source of the old (Pyarmor-obfuscated) generate_fingerprint.py.

Reconstructed from static analysis (Pyarmor-Static-Unpack-1shot v0.4.0 +
manual bytecode tracing of the .das disassembly for the parts the
decompiler couldn't fully reconstruct). Cross-referenced against the
current amazon/metadataGenSxgitario.py to see what changed between
versions — see the comparison notes at the bottom of this file.

Confidence per function:
  - CRC32, hex_encode, utf8_encode, extract_scripts, gen_lsubid, PROFILES,
    detect_profile, _human_key_interval, _human_mouse_position,
    gen_interaction, gen_form_field, gen_canvas: fully traced from
    bytecode, high confidence.
  - collect_fingerprint: reconstructed from strong structural evidence
    (field names/widths, call graph) but not fully opcode-by-opcode
    verified — treat the overall shape as reliable, exact field wiring as
    best-effort. TWO EXCEPTIONS, fully bytecode-verified after the initial
    pass guessed wrong by analogy with the current generator:
      - `metrics['input']` — assumed 0 like every other metric field;
        bytecode shows random.randint(0, 2) instead.
      - `capabilities['elapsed']` — assumed random.choice([0, 0, 1]);
        bytecode shows a hardcoded literal 0, no random call nearby.
  - te_encrypt / encode_metadata1: same KEY_UINT32/IDENTIFIER constants as
    the current generator's __xxtea_encrypt/__base64_encode — written here
    as the equivalent working implementation rather than re-derived from
    scratch, since the algorithm is already confirmed identical.

Validated by generating 30 samples with this file and decoding them back:
metrics.input lands on {0,1,2} roughly evenly (37% / 47% / 17% across one
30-sample run) — i.e. ~63% of every payload this script ever produced had
a nonzero metric, concentrated in the SAME field every time. Real captures
(57 samples, this session) show ~37% nonzero spread across 9 DIFFERENT
fields, never concentrated in one. So the old script's metrics behavior is
a distinctive, consistent tell of its own — not evidence of anything
stealthier than the current generator.
"""
import base64
import hashlib
import json
import math
import os
import random
import re
import struct
import time
import zlib

KEY_UINT32 = [1888420705, 0x99971834, 0x8BE7EB3A, 874813317]
IDENTIFIER = 'ECdITeCs'
HEX_ALPHA = '0123456789ABCDEF'


class CRC32:
    """Custom CRC32 table implementation (current version just uses zlib.crc32 directly)."""
    IEEE = 0xEDB88320

    def __init__(self):
        self.table = None

    def _build(self):
        self.table = []
        for i in range(256):
            v = i
            for _ in range(8):
                v = (v >> 1) ^ self.IEEE if v & 1 else v >> 1
            self.table.append(v)

    def calculate(self, data):
        if not self.table:
            self._build()
        crc = 0xFFFFFFFF
        for ch in data:
            idx = 255 & (crc ^ ord(ch))
            crc = (crc >> 8) ^ self.table[idx]
        return (0xFFFFFFFF ^ crc) & 0xFFFFFFFF


CRC = CRC32()


def hex_encode(val):
    """32-bit int -> 8-char uppercase hex. Equivalent to format(val, '08X')."""
    return ''.join(HEX_ALPHA[(val >> shift) & 15] for shift in (28, 24, 20, 16, 12, 8, 4, 0))


def utf8_encode(s):
    out = []
    for ch in s:
        cp = ord(ch)
        if cp < 128:
            out.append(chr(cp))
        elif cp < 2048:
            out.append(chr(cp >> 6 | 192))
            out.append(chr(cp & 63 | 128))
        else:
            out.append(chr(cp >> 12 | 224))
            out.append(chr(cp >> 6 & 63 | 128))
            out.append(chr(cp & 63 | 128))
    return ''.join(out)


def extract_scripts(html_b64):
    start = time.time()
    html = base64.b64decode(html_b64).decode('utf-8', errors='replace')
    script_re = re.compile(r'<script[\s\S]*?>[\s\S]*?</script>', re.IGNORECASE)
    src_re = re.compile(r'src="[\s\S]*?"')
    dynamic_urls, inline_hashes = [], []
    for tag in script_re.findall(html):
        m = src_re.search(tag)
        if m:
            dynamic_urls.append(m.group(0)[5:-1])
        else:
            inline_hashes.append(CRC.calculate(tag))
    return {
        'dynamicUrls': dynamic_urls,
        'inlineHashes': inline_hashes,
        'elapsed': int((time.time() - start) * 1000),
        'dynamicUrlCount': len(dynamic_urls),
        'inlineHashesCount': len(inline_hashes),
    }


def gen_canvas():
    """Generate canvas fingerprint matching Chrome on Windows rendering.
    Uses Windows-specific fonts (Arial, Segoe UI) and ClearType-style rendering.

    *** BUG (confirmed by bytecode trace, this is why it was likely
    abandoned) ***: in the success path (PIL available), `histogramBins`
    is built as ONE GRAYSCALE VALUE PER PIXEL of the 280x60 canvas
    (~16800 entries) — NOT a proper 256-bucket histogram. Every real
    Amazon capture (57 samples, this session) and the current generator
    both show `histogramBins` as an exactly-256-length array. Submitting
    this old version's real output would have been a glaring, trivially
    detectable structural mismatch. Only the ImportError (no PIL at all)
    fallback happens to produce the right length — via pure random noise,
    not a real fingerprint.

    *** CRITICAL, empirically confirmed 2026-07-21: despite the "wrong
    shape" above, the PIL success path is the one that must run — Pillow
    is a REQUIRED dependency, not optional. A venv missing Pillow silently
    takes the ImportError fallback below (structurally "correct" 256 bins,
    but constant/non-unique across every account) and produces a payload
    ~13x smaller (~7KB vs ~92KB base64). That smaller payload is BYTE-SIZE
    IDENTICAL to `metadataGenSxgitario.py`'s FwcimAmazonSxgitario output —
    the OTHER generator already confirmed (see project memory) to trigger
    far more Amazon captcha/Arkose challenges. Root-caused live: one Python
    environment with Pillow installed ran captcha-free; a fresh venv
    matching requirements.txt (before Pillow was added to it) failed with
    Arkose captcha on nearly every attempt — same code, same machine, only
    difference was whether `import PIL` succeeded. `Pillow` is now listed
    in requirements.txt; do not remove it as a "just for canvas" nice-to-have.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new('RGB', (280, 60), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        try:
            font_small = ImageFont.truetype('arial.ttf', 14)
            font_large = ImageFont.truetype('arial.ttf', 18)
        except (OSError, IOError):
            try:
                font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
                font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
            except (OSError, IOError):
                font_small = ImageFont.load_default()
                font_large = ImageFont.load_default()

        draw.text((2, 2), 'Cwm fjordank glyphs vext quiz', fill='#0050d4', font=font_small)
        draw.text((2, 20), 'mmmmmmmmmmlli', fill='#0050d4', font=font_large)
        draw.text((2, 42), 'W', fill='#0050d4', font=font_small)
        draw.rectangle([0, 0, 7, 7], fill=(51, 102, 153, 128))
        draw.rectangle([1, 1, 6, 6], outline='#336699')
        draw.ellipse([0, 0, 7, 7], fill='#336699')
        draw.ellipse([1, 1, 6, 6], outline='#336699')
        for offset, color in ((0, '#336699'), (2, '#663399'), (4, '#cc6600')):
            draw.arc([20 + offset, 0 + offset, 50 + offset, 30 + offset], 0, 360, fill=color, width=2)
        for x in range(100):
            for y in range(10, 50):
                r = min(255, x * 2 + random.randint(-2, 2))
                g = min(255, y * 3 + random.randint(-2, 2))
                b = 128 + random.randint(-5, 5)
                draw.point((x, y), fill=(max(0, r), max(0, g), max(0, min(255, b))))

        pixel_bytes = b''.join(struct.pack('BBB', *px) for px in image.getdata())
        canvas_hash = zlib.crc32(pixel_bytes) & 0xFFFFFFFF
        if canvas_hash >= 0x80000000:
            canvas_hash -= 0x100000000

        # BUG: one entry per pixel (~16800), not binned to 256.
        histogram_bins = [int(0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]) for px in image.getdata()]

        # emailHash: NOT actually derived from the submitted email — just a
        # second hash of a fixed salt string, effectively a constant.
        email_hash = struct.unpack('>i', hashlib.md5(b'canvas-fp-win32').digest()[0:4])[0]

        return {'hash': canvas_hash, 'emailHash': email_hash, 'histogramBins': histogram_bins}

    except ImportError:
        # No PIL at all -> pure random noise, correctly shaped (256 bins)
        # but not a real fingerprint of anything.
        email_hash = struct.unpack('>i', hashlib.md5(b'canvas-fp-win32').digest()[0:4])[0]
        return {
            'hash': email_hash,
            'emailHash': email_hash,
            'histogramBins': [random.randint(10, 80) for _ in range(256)],
        }


def gen_lsubid():
    return f'X{random.randint(10, 99):02d}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}:{int(time.time())}'


# Browser/OS profiles — broader coverage than the current generator
# (Chrome/Firefox/Safari x Win/Mac/Linux vs. current: Chrome/Windows only),
# but canvas and GPU are NOT correlated per-profile here (canvas is always
# freshly generated by gen_canvas(), decoupled from whichever profile was
# picked) — the current generator's HARDWARE_PROFILES bundles real
# captured canvas+GPU+screen+math together per entry, which is more
# internally consistent even though it covers fewer browsers.
PROFILES = {
    'chrome_win': {
        'gpu_vendor': 'Google Inc. (NVIDIA)',
        'gpu_model': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'gpu_ext': [
            'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
            'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
            'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
            'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
            'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
            'EXT_float_blend', 'WEBGL_draw_buffers', 'WEBGL_compressed_texture_astc',
            'WEBGL_compressed_texture_etc',
        ],
        'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
        'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
               'touch': False, 'video': True, 'webWorker': True},
        'plugins': 'Chrome PDF Plugin Chrome PDF Viewer Native Client ||1920-1080-1080-24-*-*-*',
        'screen': '1920-1080-1080-24-*-*-*',
    },
    'chrome_mac': {
        'gpu_vendor': 'Apple', 'gpu_model': 'Apple M1',
        'gpu_ext': [
            'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
            'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
            'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
            'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
            'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
            'EXT_float_blend',
        ],
        'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
        'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
               'touch': False, 'video': True, 'webWorker': True},
        'plugins': 'Chrome PDF Plugin Chrome PDF Viewer Native Client ||1440-900-900-22-*-*-*',
        'screen': '1440-900-900-22-*-*-*',
    },
    'firefox_linux': {
        'gpu_vendor': 'Intel', 'gpu_model': 'Intel(R) HD Graphics, or similar',
        'gpu_ext': [
            'ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float',
            'EXT_depth_clamp', 'EXT_float_blend', 'EXT_frag_depth', 'EXT_shader_texture_lod',
            'EXT_sRGB', 'EXT_texture_compression_bptc', 'EXT_texture_compression_rgtc',
            'EXT_texture_filter_anisotropic', 'OES_element_index_uint', 'OES_fbo_render_mipmap',
            'OES_standard_derivatives', 'OES_texture_float', 'OES_texture_float_linear',
            'OES_texture_half_float', 'OES_texture_half_float_linear', 'OES_vertex_array_object',
            'WEBGL_color_buffer_float', 'WEBGL_compressed_texture_astc', 'WEBGL_compressed_texture_etc',
            'WEBGL_compressed_texture_s3tc', 'WEBGL_compressed_texture_s3tc_srgb',
            'WEBGL_debug_renderer_info', 'WEBGL_debug_shaders', 'WEBGL_depth_texture',
            'WEBGL_draw_buffers', 'WEBGL_lose_context',
        ],
        'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
        'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
               'touch': False, 'video': True, 'webWorker': True},
        'plugins': 'PDF Viewer Chrome PDF Viewer Chromium PDF Viewer Microsoft Edge PDF Viewer WebKit built-in PDF ||1280-1024-1024-24-*-*-*',
        'screen': '1280-1024-1024-24-*-*-*',
    },
    'firefox_win': {
        'gpu_vendor': 'Google Inc. (NVIDIA)',
        'gpu_model': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)',
        'gpu_ext': [
            'ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float',
            'EXT_depth_clamp', 'EXT_float_blend', 'EXT_frag_depth', 'EXT_shader_texture_lod',
            'EXT_sRGB', 'EXT_texture_compression_bptc', 'EXT_texture_compression_rgtc',
            'EXT_texture_filter_anisotropic', 'OES_element_index_uint', 'OES_fbo_render_mipmap',
            'OES_standard_derivatives', 'OES_texture_float', 'OES_texture_float_linear',
            'OES_texture_half_float', 'OES_texture_half_float_linear', 'OES_vertex_array_object',
            'WEBGL_color_buffer_float', 'WEBGL_compressed_texture_s3tc',
            'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_renderer_info', 'WEBGL_debug_shaders',
            'WEBGL_depth_texture', 'WEBGL_draw_buffers', 'WEBGL_lose_context',
        ],
        'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
        'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
               'touch': False, 'video': True, 'webWorker': True},
        'plugins': 'PDF Viewer Chrome PDF Viewer ||1920-1080-1080-24-*-*-*',
        'screen': '1920-1080-1080-24-*-*-*',
    },
    'safari_mac': {
        'gpu_vendor': 'Apple', 'gpu_model': 'Apple M2',
        'gpu_ext': [
            'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
            'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
            'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
            'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
            'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
        ],
        'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
        'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
               'touch': False, 'video': True, 'webWorker': True},
        'plugins': 'PDF Viewer ||1440-900-900-22-*-*-*',
        'screen': '1440-900-900-22-*-*-*',
    },
}


def detect_profile(ua):
    ua_l = ua.lower()
    if 'chrome' in ua_l and 'edg' not in ua_l:
        return PROFILES['chrome_mac'] if ('mac' in ua_l or 'darwin' in ua_l) else PROFILES['chrome_win']
    if 'firefox' in ua_l:
        return PROFILES['firefox_linux'] if ('linux' in ua_l or 'x11' in ua_l) else PROFILES['firefox_win']
    if 'safari' in ua_l and 'chrome' not in ua_l:
        return PROFILES['safari_mac']
    return PROFILES['firefox_linux']


def _human_key_interval(index, total):
    """Realistic inter-key interval: fast in the middle, slow at start/end."""
    if index == 0:
        return random.randint(200, 500)
    if index == total - 1:
        return random.randint(150, 400)
    if random.random() < 0.08:
        return random.randint(400, 1200)
    return random.randint(60, 180)


def _human_mouse_position(form_index, total_forms):
    """Generate mouse positions that move toward form fields realistically."""
    x = random.randint(150, 400) + random.randint(-5, 5)
    y = 50 + form_index * 45 + random.randint(-10, 10) + random.randint(-3, 3)
    return (x, y)


def gen_interaction(total_keys, total_clicks, now):
    cursor = now - random.randint(1500, 4000)
    key_events = []
    for i in range(total_keys):
        cursor += _human_key_interval(i, total_keys)
        dur = random.randint(40, 120)
        key_events.append({'start': cursor, 'end': cursor + dur})

    # inter-keystroke gaps (consecutive start-time deltas)
    key_press_time_intervals = [key_events[i]['start'] - key_events[i - 1]['start'] for i in range(1, len(key_events))]
    # per-key hold duration
    key_cycles = [e['end'] - e['start'] for e in key_events]

    mouse_events = []
    click_time = now - random.randint(2000, 5000)
    for i in range(total_clicks):
        x, y = _human_mouse_position(i, total_clicks)
        dur = random.randint(30, 90)
        mouse_events.append({'start': click_time, 'end': click_time + dur, 'x': x, 'y': y})
        click_time += random.randint(600, 1500) if random.random() < 0.15 else random.randint(150, 500)

    mouse_cycles = [e['end'] - e['start'] for e in mouse_events]
    mouse_click_positions = [f"{e['x']},{e['y']}" for e in mouse_events]
    pastes = 1 if random.random() < 0.15 else 0

    return {
        'clicks': total_clicks, 'touches': 0, 'keyPresses': total_keys,
        'cuts': 0, 'copies': 0, 'pastes': pastes,
        'keyPressTimeIntervals': key_press_time_intervals,
        'mouseClickPositions': mouse_click_positions,
        'keyCycles': key_cycles,
        'mouseCycles': mouse_cycles,
        'touchCycles': [],
    }


def gen_form_field(name, value, field_width, field_height):
    key_count = len(str(value)) if value else 0

    if key_count == 0:
        return {
            'clicks': 0, 'touches': 0, 'keyPresses': 0, 'cuts': 0, 'copies': 0, 'pastes': 0,
            'keyPressTimeIntervals': [], 'mouseClickPositions': [], 'keyCycles': [],
            'mouseCycles': [], 'touchCycles': [],
            'width': field_width, 'height': field_height,
            'totalFocusTime': 0, 'checksum': None, 'prefilled': False,
        }

    key_intervals, total_focus = [], 0
    for i in range(key_count):
        if i == 0:
            iv = random.randint(150, 400)
        elif random.random() < 0.06:
            iv = random.randint(500, 1500)
        else:
            iv = random.randint(55, 175)
        key_intervals.append(iv)
        total_focus += iv

    key_cycles = [random.randint(40, 110) for _ in range(key_count)]
    mouse_x = random.randint(80, 280)
    mouse_y = random.randint(5, 25)
    mouse_cycles = [random.randint(30, 80)]

    checksum = hex_encode(CRC.calculate(utf8_encode(str(value)))) if value else None

    return {
        'clicks': 1, 'touches': 0, 'keyPresses': key_count, 'cuts': 0, 'copies': 0, 'pastes': 0,
        'keyPressTimeIntervals': key_intervals,
        'mouseClickPositions': [f"{mouse_x},{mouse_y}"],
        'keyCycles': key_cycles,
        'mouseCycles': mouse_cycles,
        'touchCycles': [],
        'width': field_width, 'height': field_height,
        # BUG (vs. real data): always sum(intervals) + random(200,1500) —
        # i.e. NEVER zero when text was typed. 57 real captures show the
        # opposite majority: 75% ARE zero even with ~22 real keypresses.
        'totalFocusTime': total_focus + random.randint(200, 1500),
        'checksum': checksum,
        'prefilled': False,
    }


# --- collect_fingerprint: reconstructed from strong structural evidence  ---
# (field names/widths/call graph fully visible in the disassembly), but the
# exact top-level dict wiring is best-effort, not opcode-verified line by
# line like the functions above.
def collect_fingerprint(email, password, name, password_check, otp, user_agent,
                         referrer, location, time_zone, html_b64):
    now = int(time.time() * 1000)
    user_agent = user_agent or 'Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0'
    referrer = referrer or ''
    location = location or ''
    if time_zone is None:
        time_zone = -int(time.timezone / 3600)

    profile = detect_profile(user_agent)
    scripts = extract_scripts(html_b64)

    form = {}
    if name:
        form['ap_customer_name'] = gen_form_field('ap_customer_name', name, 312, 32)
    if email:
        form['ap_email_login'] = gen_form_field('ap_email_login', email, 294, 32)
    if password:
        form['password'] = gen_form_field('password', password, 294, 32)
    if password_check:
        form['ap_password_check'] = gen_form_field('ap_password_check', password_check, 294, 32)
    if otp:
        form['cvf-input-code'] = gen_form_field('cvf-input-code', otp, 294, 32)
    form['auth-credential-autofill-hint'] = gen_form_field('auth-credential-autofill-hint', '', 0, 0)

    total_keys = sum(len(str(v)) for v in (name, email, password, password_check, otp) if v)
    total_clicks = sum(1 for v in (name, email, password, password_check, otp) if v)
    interaction = gen_interaction(total_keys, total_clicks, now)

    metrics_fields = ('el', 'script', 'h', 'batt', 'perf', 'auto', 'tz', 'fp2', 'lsubid',
                       'browser', 'capabilities', 'gpu', 'dnt', 'math', 'tts', 'input',
                       'canvas', 'captchainput', 'pow')
    metrics = {k: 0 for k in metrics_fields}
    # CORRECTED (verified via bytecode trace, offsets 218-278 of collect_fingerprint):
    # 'input' is NOT always 0 like the other 18 fields — it's ALWAYS
    # random.randint(0, 2), so 2/3 of every payload has metrics.input != 0.
    # This is a MUCH higher and more concentrated nonzero rate than the 37%
    # (spread across 9 different fields) that 57 real captures show — this
    # is arguably a more distinctive/detectable tell than the current
    # generator's calibrated behavior, not a stealth advantage.
    metrics['input'] = random.randint(0, 2)

    return {
        'metrics': metrics,
        'start': now - random.randint(3000, 6000),
        'interaction': interaction,
        'scripts': scripts,
        'history': {'length': 2},
        'battery': {},
        'performance': {'timing': {}},   # not traced — likely a similarly-built timing dict
        'automation': {'wd': {'properties': {'document': [], 'window': [], 'navigator': []}},
                       'phantom': {'properties': {'window': []}}},
        'end': now,
        'timeZone': time_zone,
        'flashVersion': None,
        'plugins': profile['plugins'],
        'dupedPlugins': profile['plugins'],
        'screenInfo': profile['screen'],
        'lsUbid': gen_lsubid(),
        'referrer': referrer,
        'userAgent': user_agent,
        'location': location,
        'webDriver': False,
        # CORRECTED (verified via bytecode trace, offsets 2094-2114 of
        # collect_fingerprint): 'elapsed' is a hardcoded literal 0 — no
        # random call anywhere near it. An earlier reconstruction pass
        # wrongly copied the current generator's random.choice([0,0,1])
        # here by analogy, without checking. Real captures show 86% zero /
        # 14% one — so this is always the majority value, never the 14%
        # case, unlike metrics.input which over-represents its rare value.
        'capabilities': {'css': profile['css'], 'js': profile['js'], 'elapsed': 0},
        'gpu': {'vendor': profile['gpu_vendor'], 'model': profile['gpu_model'], 'extensions': profile['gpu_ext']},
        'dnt': None,
        'math': {'tan': str(math.tan(1)), 'sin': str(math.sin(1)), 'cos': str(math.cos(1))},
        'form': form,
        'canvas': gen_canvas(),
        'token': {'isCompatible': True, 'pageHasCaptcha': 0},
        'auth': {'form': {'method': 'post'}},
        'errors': [],
        'version': '4.0.0',
    }


def te_encrypt(pt, key):
    """Same XXTEA scheme as the current generator's __xxtea_encrypt (confirmed
    via identical KEY_UINT32/IDENTIFIER constants) — reused here rather than
    re-derived, since the algorithm itself is already validated."""
    if len(pt) == 0:
        return ''
    n = math.ceil(len(pt) / 4)
    v = []
    for i in range(n):
        word = 0
        for j in range(4):
            idx = i * 4 + j
            if idx < len(pt):
                word |= ord(pt[idx]) << (j * 8)
        v.append(word)
    n = len(v)
    rounds = 6 + 52 // n
    total = 0
    z = v[n - 1]
    DELTA = 0x9E3779B9
    for _ in range(rounds):
        total = (total + DELTA) & 0xFFFFFFFF
        e = (total >> 2) & 3
        for p in range(n):
            y = v[(p + 1) % n]
            mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((total ^ y) + (key[(p & 3) ^ e] ^ z))
            v[p] = (v[p] + mx) & 0xFFFFFFFF
            z = v[p]
    out = []
    for word in v:
        for j in range(4):
            out.append(chr((word >> (j * 8)) & 0xFF))
    return ''.join(out)


def encode_metadata1(data):
    json_str = json.dumps(data, separators=(',', ':'))
    crc = format(zlib.crc32(json_str.encode('utf-8')) & 0xFFFFFFFF, '08X')
    payload = f"{crc}#{json_str}"
    encrypted = te_encrypt(payload, KEY_UINT32)
    b64 = base64.b64encode(encrypted.encode('latin-1')).decode('utf-8')
    return f"{IDENTIFIER}:{b64}"


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON NOTES vs. current amazon/metadataGenSxgitario.py
# ═══════════════════════════════════════════════════════════════════════
#
# The old version is NOT better — it has at least two confirmed structural
# bugs that the current version doesn't have:
#
# 1. canvas.histogramBins is the WRONG SHAPE in the success path (~16800
#    grayscale pixel values instead of a 256-bucket histogram). Every real
#    Amazon capture and the current generator both produce exactly 256
#    entries. Submitting this would have been a glaring, trivial-to-detect
#    mismatch.
#
# 2. form field totalFocusTime is NEVER zero once there's a value typed
#    (always sum(intervals) + random(200,1500)). 57 real captures show the
#    opposite: 75% of the time it's zero even with ~22 real keypresses.
#    The current generator (after this session's fix) correctly models
#    both cases.
#
# 3. metrics['input'] is ALWAYS random.randint(0, 2) — every single payload
#    this script ever produced had a ~63% chance of a nonzero metric,
#    concentrated in the SAME field ('input') every time. 57 real captures
#    show ~37% nonzero spread across 9 different fields, never the same one
#    twice in a row. A field that spikes way more often than reality, and
#    always the same one, is arguably a MORE consistent/detectable tell
#    than the current generator's calibrated, varied behavior — not less.
#
# 4. capabilities.elapsed is a HARDCODED literal 0 (verified: offsets
#    2094-2114, no random call anywhere nearby) — an earlier reconstruction
#    pass wrongly guessed random.choice([0,0,1]) here by analogy with the
#    current generator, without checking. Real captures show 86% zero / 14%
#    one — so unlike metrics.input (which over-represents its rare value),
#    this one just never shows the minority case. Less wrong than the other
#    three bugs, but still not what a real browser produces 14% of the time.
#
# What the old version did that's arguably nicer:
#   - Broader browser/OS coverage (Chrome/Firefox/Safari x Win/Mac/Linux,
#     5 profiles) vs. current (Chrome/Windows only, 6 profiles) — but
#     canvas/GPU aren't correlated per-profile here, whereas the current
#     HARDWARE_PROFILES bundles real captured canvas+GPU+screen+math
#     together, which is more internally consistent — a real trade-off,
#     not a clear win either way.
#   - Nothing else stood out as an improvement over the current version;
#     the human-timing model here (_human_key_interval: hardcoded ranges)
#     is simpler than the current log-logistic sampler.
