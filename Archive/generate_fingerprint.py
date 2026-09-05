#!/usr/bin/env python3
import json, zlib, base64, time, math, random, hashlib, struct, re, os

KEY_UINT32 = [1888420705, 2576816180, 2347232058, 874813317]
IDENTIFIER = "ECdITeCs"

# CRC32 — exact Module 4
class CRC32:
    IEEE = 3988292384
    def __init__(self): self.table = None
    def _build(self):
        self.table = []
        for t in range(256):
            e = t
            for _ in range(8): e = (e >> 1) ^ (self.IEEE if e & 1 else 0)
            self.table.append(e)
    def calculate(self, data):
        if not self.table: self._build()
        e = 4294967295
        for c in range(len(data)):
            t = 255 & (e ^ ord(data[c]))
            e = (e >> 8) ^ self.table[t]
        return (4294967295 ^ e) & 0xFFFFFFFF

CRC = CRC32()

HEX_ALPHA = "0123456789ABCDEF"
def hex_encode(val):
    return ''.join(HEX_ALPHA[(val >> s) & 15] for s in [28,24,20,16,12,8,4,0])

def utf8_encode(s):
    r = []
    for ch in s:
        c = ord(ch)
        if c < 128: r.append(chr(c))
        elif c < 2048: r.append(chr((c>>6)|192)); r.append(chr((c&63)|128))
        else: r.append(chr((c>>12)|224)); r.append(chr(((c>>6)&63)|128)); r.append(chr((c&63)|128))
    return ''.join(r)

def extract_scripts(html_b64):
    start = time.time()
    html = base64.b64decode(html_b64).decode('utf-8', errors='replace')
    script_re = re.compile(r'<script[\s\S]*?>[\s\S]*?</script>', re.IGNORECASE)
    src_re = re.compile(r'src="[\s\S]*?"')
    urls, hashes = [], []
    for block in script_re.findall(html):
        m = src_re.search(block)
        if m: urls.append(m.group(0)[5:-1])
        else: hashes.append(CRC.calculate(block))
    return {"dynamicUrls": urls, "inlineHashes": hashes,
            "elapsed": int((time.time()-start)*1000),
            "dynamicUrlCount": len(urls), "inlineHashesCount": len(hashes)}

def gen_canvas():
    """Generate canvas fingerprint matching Chrome on Windows rendering.
    Uses Windows-specific fonts (Arial, Segoe UI) and ClearType-style rendering."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        # Windows Chrome canvas dimensions and background
        img = Image.new('RGB', (280, 60), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        # Try to use a font that exists on Windows (fallback to default)
        try:
            font_path = "arial.ttf"
            font_sm = ImageFont.truetype(font_path, 14)
            font_lg = ImageFont.truetype(font_path, 18)
        except (OSError, IOError):
            try:
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                font_sm = ImageFont.truetype(font_path, 14)
                font_lg = ImageFont.truetype(font_path, 18)
            except (OSError, IOError):
                font_sm = ImageFont.load_default()
                font_lg = ImageFont.load_default()
        # Text rendering — matches Chrome's canvas fillText behavior on Windows
        d.text((2, 2), 'Cwm fjordank glyphs vext quiz', fill='#0050d4', font=font_sm)
        d.text((2, 20), 'mmmmmmmmmmlli', fill='#0050d4', font=font_lg)
        d.text((2, 42), 'W', fill='#0050d4', font=font_sm)
        # Geometric shapes — matches Chrome canvas path rendering
        d.rectangle([0, 0, 7, 7], fill=(51, 102, 153, 128))
        d.rectangle([1, 1, 6, 6], outline='#336699')
        d.ellipse([0, 0, 7, 7], fill='#336699')
        d.ellipse([1, 1, 6, 6], outline='#336699')
        # Arc rendering
        for offset, color in [(0, '#336699'), (2, '#663399'), (4, '#cc6600')]:
            bbox = [20 + offset, 0 + offset, 50 + offset, 30 + offset]
            d.arc(bbox, 0, 360, fill=color, width=2)
        # Pixel noise region — Windows ClearType produces different subpixel patterns
        rnd = random.randint
        for x in range(100):
            for y in range(10, 50):
                r = min(255, x * 2 + rnd(-2, 2))
                g = min(255, y * 3 + rnd(-2, 2))
                b = 128 + rnd(-5, 5)
                d.point((x, y), fill=(max(0, r), max(0, g), max(0, min(255, b))))
        raw = img.tobytes()
        h = zlib.crc32(raw) & 0xFFFFFFFF
        if h >= 0x80000000:
            h -= 0x100000000
        bins = [0] * (img.width * img.height)
        i = 0
        for idx in range(0, len(raw), 3):
            r = raw[idx]; g = raw[idx + 1]; b = raw[idx + 2]
            bins[i] = int(0.299 * r + 0.587 * g + 0.114 * b)
            i += 1
        return {"hash": h, "emailHash": None, "histogramBins": bins}
    except ImportError:
        h = struct.unpack('>i', hashlib.md5(b'canvas-fp-win32').digest()[:4])[0]
        return {"hash": h, "emailHash": None,
                "histogramBins": [random.randint(10, 80) for _ in range(256)]}

def gen_lsubid():
    return f"X{random.randint(10,99):02d}-{random.randint(1000000,9999999)}-{random.randint(1000000,9999999)}:{int(time.time())}"


def _compute_pow(iv: str, difficulty: int):
    """Reimplementa el proof-of-work del Web Worker `fwcim-pow.js` de Amazon.

    El worker busca el nonce N tal que SHA-256( iv_bytes || N_utf8 ) empiece
    con `difficulty` bits en cero (algoritmo hashcash, mismo formato que usa
    Amazon). Devuelve la tupla ``(token_bytes, ms_elapsed)`` para que el
    fingerprint reporte tiempos consistentes con un navegador real."""
    start = time.time()
    iv_bytes = iv.encode("utf-8") if isinstance(iv, str) else iv
    nonce = 0
    while True:
        candidate = iv_bytes + str(nonce).encode("utf-8")
        digest = hashlib.sha256(candidate).digest()
        bits = 0
        for b in digest:
            if b == 0:
                bits += 8
                continue
            # leading zeros in this byte
            bits += 8 - b.bit_length()
            break
        if bits >= difficulty:
            return list(digest), int((time.time() - start) * 1000)
        nonce += 1


def gen_pow_token(session_id: str = None, difficulty: int = None,
                  page_has_captcha: int = 0, min_difficulty: int = 8,
                  max_difficulty: int = 12):
    """Genera el bloque ``data['pow']`` que espera Amazon en metadata1.

    El navegador real corre un Worker que tarda entre 200ms y 2s dependiendo
    de la difficulty. Sin este token Amazon detecta el POST como bot y
    devuelve la página de captcha en el paso 4 (``req_4``)."""
    if session_id is None:
        session_id = f"{random.randint(100,999)}-{random.randint(10000000,99999999)}-{random.randint(10000000,99999999)}"
    if difficulty is None:
        difficulty = random.randint(min_difficulty, max_difficulty)
    start_ts = int(time.time() * 1000) - random.randint(500, 1800)
    token_bytes, elapsed = _compute_pow(session_id, difficulty)
    end_ts = start_ts + elapsed
    return {
        "isCompatible": True,
        "pageHasCaptcha": page_has_captcha,
        "start": start_ts,
        "end": end_ts,
        "time": elapsed,
        "difficulty": difficulty,
        "iv": session_id,
        "token": token_bytes,
    }


PROFILES = {
    "chrome_win": {"gpu_vendor":"Google Inc. (NVIDIA)","gpu_model":"ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)","gpu_ext":["WEBGL_compressed_texture_s3tc","WEBGL_debug_renderer_info","OES_texture_float","WEBGL_lose_context","WEBGL_depth_texture","EXT_color_buffer_half_float","WEBGL_color_buffer_float","OES_standard_derivatives","OES_element_index_uint","OES_texture_float_linear","OES_texture_half_float","OES_texture_half_float_linear","EXT_shader_texture_lod","WEBGL_compressed_texture_s3tc_srgb","WEBGL_debug_shaders","EXT_float_blend","WEBGL_draw_buffers","WEBGL_compressed_texture_astc","WEBGL_compressed_texture_etc"],"css":{"textShadow":1,"WebkitTextStroke":1,"boxShadow":1,"borderRadius":1,"borderImage":1,"opacity":1,"transform":1,"transition":1},"js":{"audio":True,"geolocation":True,"localStorage":"supported","touch":False,"video":True,"webWorker":True},"plugins":"Chrome PDF Plugin Chrome PDF Viewer Native Client ||1920-1080-1080-24-*-*-*","screen":"1920-1080-1080-24-*-*-*"},
    "chrome_mac": {"gpu_vendor":"Apple","gpu_model":"Apple M1","gpu_ext":["WEBGL_compressed_texture_s3tc","WEBGL_debug_renderer_info","OES_texture_float","WEBGL_lose_context","WEBGL_depth_texture","EXT_color_buffer_half_float","WEBGL_color_buffer_float","OES_standard_derivatives","OES_element_index_uint","OES_texture_float_linear","OES_texture_half_float","OES_texture_half_float_linear","EXT_shader_texture_lod","WEBGL_compressed_texture_s3tc_srgb","WEBGL_debug_shaders","EXT_float_blend"],"css":{"textShadow":1,"WebkitTextStroke":1,"boxShadow":1,"borderRadius":1,"borderImage":1,"opacity":1,"transform":1,"transition":1},"js":{"audio":True,"geolocation":True,"localStorage":"supported","touch":False,"video":True,"webWorker":True},"plugins":"Chrome PDF Plugin Chrome PDF Viewer Native Client ||1440-900-900-22-*-*-*","screen":"1440-900-900-22-*-*-*"},
    "firefox_linux": {"gpu_vendor":"Intel","gpu_model":"Intel(R) HD Graphics, or similar","gpu_ext":["ANGLE_instanced_arrays","EXT_blend_minmax","EXT_color_buffer_half_float","EXT_depth_clamp","EXT_float_blend","EXT_frag_depth","EXT_shader_texture_lod","EXT_sRGB","EXT_texture_compression_bptc","EXT_texture_compression_rgtc","EXT_texture_filter_anisotropic","OES_element_index_uint","OES_fbo_render_mipmap","OES_standard_derivatives","OES_texture_float","OES_texture_float_linear","OES_texture_half_float","OES_texture_half_float_linear","OES_vertex_array_object","WEBGL_color_buffer_float","WEBGL_compressed_texture_astc","WEBGL_compressed_texture_etc","WEBGL_compressed_texture_s3tc","WEBGL_compressed_texture_s3tc_srgb","WEBGL_debug_renderer_info","WEBGL_debug_shaders","WEBGL_depth_texture","WEBGL_draw_buffers","WEBGL_lose_context"],"css":{"textShadow":1,"WebkitTextStroke":1,"boxShadow":1,"borderRadius":1,"borderImage":1,"opacity":1,"transform":1,"transition":1},"js":{"audio":True,"geolocation":True,"localStorage":"supported","touch":False,"video":True,"webWorker":True},"plugins":"PDF Viewer Chrome PDF Viewer Chromium PDF Viewer Microsoft Edge PDF Viewer WebKit built-in PDF ||1280-1024-1024-24-*-*-*","screen":"1280-1024-1024-24-*-*-*"},
    "firefox_win": {"gpu_vendor":"Google Inc. (NVIDIA)","gpu_model":"ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)","gpu_ext":["ANGLE_instanced_arrays","EXT_blend_minmax","EXT_color_buffer_half_float","EXT_depth_clamp","EXT_float_blend","EXT_frag_depth","EXT_shader_texture_lod","EXT_sRGB","EXT_texture_compression_bptc","EXT_texture_compression_rgtc","EXT_texture_filter_anisotropic","OES_element_index_uint","OES_fbo_render_mipmap","OES_standard_derivatives","OES_texture_float","OES_texture_float_linear","OES_texture_half_float","OES_texture_half_float_linear","OES_vertex_array_object","WEBGL_color_buffer_float","WEBGL_compressed_texture_s3tc","WEBGL_compressed_texture_s3tc_srgb","WEBGL_debug_renderer_info","WEBGL_debug_shaders","WEBGL_depth_texture","WEBGL_draw_buffers","WEBGL_lose_context"],"css":{"textShadow":1,"WebkitTextStroke":1,"boxShadow":1,"borderRadius":1,"borderImage":1,"opacity":1,"transform":1,"transition":1},"js":{"audio":True,"geolocation":True,"localStorage":"supported","touch":False,"video":True,"webWorker":True},"plugins":"PDF Viewer Chrome PDF Viewer ||1920-1080-1080-24-*-*-*","screen":"1920-1080-1080-24-*-*-*"},
    "safari_mac": {"gpu_vendor":"Apple","gpu_model":"Apple M2","gpu_ext":["WEBGL_compressed_texture_s3tc","WEBGL_debug_renderer_info","OES_texture_float","WEBGL_lose_context","WEBGL_depth_texture","EXT_color_buffer_half_float","WEBGL_color_buffer_float","OES_standard_derivatives","OES_element_index_uint","OES_texture_float_linear","OES_texture_half_float","OES_texture_half_float_linear","WEBGL_compressed_texture_s3tc_srgb","WEBGL_debug_shaders"],"css":{"textShadow":1,"WebkitTextStroke":1,"boxShadow":1,"borderRadius":1,"borderImage":1,"opacity":1,"transform":1,"transition":1},"js":{"audio":True,"geolocation":True,"localStorage":"supported","touch":False,"video":True,"webWorker":True},"plugins":"PDF Viewer ||1440-900-900-22-*-*-*","screen":"1440-900-900-22-*-*-*"},
}


def detect_profile(ua):
    u = ua.lower()
    if "chrome" in u and "edg" not in u:
        return PROFILES["chrome_mac"] if ("mac" in u or "darwin" in u) else PROFILES["chrome_win"]
    elif "firefox" in u:
        return PROFILES["firefox_linux"] if ("linux" in u or "x11" in u) else PROFILES["firefox_win"]
    elif "safari" in u and "chrome" not in u:
        return PROFILES["safari_mac"]
    return PROFILES["firefox_linux"]

# ============================================================
# Interaction — matches Module 5/16 (human-like)
# ============================================================
def _human_key_interval(index, total):
    """Realistic inter-key interval: fast in the middle, slow at start/end."""
    if index == 0:
        return random.randint(200, 500)  # pause before first key
    if index == total - 1:
        return random.randint(150, 400)  # pause before last key
    # Middle keys: realistic typing speed with occasional pauses
    if random.random() < 0.08:
        return random.randint(400, 1200)  # occasional long pause (think)
    return random.randint(60, 180)

def _human_mouse_position(form_index, total_forms):
    """Generate mouse positions that move toward form fields realistically."""
    # Start from a realistic initial position (top-left area, like mouse resting)
    base_x = random.randint(100, 300)
    base_y = random.randint(200, 400)
    # Move toward each form field area (form fields are usually centered)
    field_x = random.randint(150, 400)
    field_y = 50 + form_index * 45 + random.randint(-10, 10)
    # Add natural jitter
    return (field_x + random.randint(-5, 5), field_y + random.randint(-3, 3))

def gen_interaction(total_keys, total_clicks, start_ts, dwell):
    # Realistic start time — user arrives, looks at page, then starts. All
    # events must fit between page load (start_ts) and submit (start_ts+dwell)
    # so the interaction timeline agrees with the claimed dwell.
    lo = max(40, dwell // 6)
    hi = max(lo, min(1500, dwell // 2))
    start_delay = random.randint(lo, hi)
    end_ts = start_ts + dwell
    t = start_ts + start_delay

    # Key events with human-like intervals
    intervals = []
    for i in range(total_keys):
        intervals.append(_human_key_interval(i, total_keys))

    # Compress typing if it would overflow the submit window (very short forms)
    typing = sum(intervals)
    budget = dwell - start_delay - 100
    if total_keys and budget > 0 and typing + 100 > budget:
        factor = max(0.05, (budget - 100) / (typing + 100))
        intervals = [max(5, int(v * factor)) for v in intervals]

    key_events = []
    for i in range(total_keys):
        t += intervals[i]
        dur = random.randint(20, 100)  # key hold time
        if t + dur > end_ts - 30:
            t = max(t - intervals[i], end_ts - 30 - dur)
        key_events.append({"start": int(t), "end": int(min(end_ts, t + dur))})
        t = key_events[-1]["end"]

    key_cycles = [e["end"] - e["start"] for e in key_events]
    key_intervals = [key_events[i]["start"] - key_events[i-1]["start"] for i in range(1, len(key_events))]

    # Mouse events — click on each form field + some random exploration
    mouse_events = []
    mt = start_ts + random.randint(0, max(20, start_delay))  # mouse moves before typing
    for i in range(total_clicks):
        x, y = _human_mouse_position(i, total_clicks)
        dur = random.randint(20, 90)  # click duration
        if mt + dur > end_ts - 60:
            break
        mouse_events.append({"start": int(mt), "end": int(mt + dur), "x": x, "y": y})
        # Time between clicks: variable, with occasional pauses
        if random.random() < 0.15:
            mt += dur + random.randint(80, 300)  # long pause (looking at page)
        else:
            mt += dur + random.randint(40, 200)

    mouse_cycles = [e["end"] - e["start"] for e in mouse_events]
    click_positions = [f"{e['x']},{e['y']}" for e in mouse_events]

    # Realistic paste count — most users don't paste in forms
    paste_count = 1 if random.random() < 0.15 else 0

    return {
        "clicks": len(mouse_events), "touches": 0, "keyPresses": total_keys,
        "cuts": 0, "copies": 0, "pastes": paste_count,
        "keyPressTimeIntervals": key_intervals, "mouseClickPositions": click_positions,
        "keyCycles": key_cycles, "mouseCycles": mouse_cycles, "touchCycles": []
    }

# ============================================================
# Form telemetry — matches Module 17 (human-like)
# ============================================================
def gen_form_field(name, value, field_width=312, field_height=32):
    cc = len(str(value)) if value else 0
    if cc == 0:
        return {
            "clicks": 0, "touches": 0, "keyPresses": 0,
            "cuts": 0, "copies": 0, "pastes": 0,
            "keyPressTimeIntervals": [], "mouseClickPositions": [],
            "keyCycles": [], "mouseCycles": [], "touchCycles": [],
            "width": field_width, "height": field_height,
            "totalFocusTime": 0, "checksum": None, "prefilled": False
        }
    # Realistic typing: fast with occasional pauses
    intervals = []
    t = 0
    for i in range(cc):
        if i == 0:
            dt = random.randint(150, 400)  # pause before first char
        elif random.random() < 0.06:
            dt = random.randint(500, 1500)  # occasional think pause
        else:
            dt = random.randint(55, 175)  # normal typing speed
        intervals.append(dt)
        t += dt
    # Key hold times — realistic press durations
    key_cycles = [random.randint(40, 110) for _ in range(cc)]
    # Mouse click before typing — clicking into the field
    click_x = random.randint(80, 280)
    click_y = random.randint(5, 25)
    mouse_cycles = [random.randint(30, 80)]
    checksum = hex_encode(CRC.calculate(utf8_encode(str(value)))) if value else None

    return {
        "clicks": 1, "touches": 0, "keyPresses": cc,
        "cuts": 0, "copies": 0, "pastes": 0,
        "keyPressTimeIntervals": intervals,
        "mouseClickPositions": [f"{click_x},{click_y}"],
        "keyCycles": key_cycles,
        "mouseCycles": mouse_cycles,
        "touchCycles": [],
        "width": field_width, "height": field_height,
        "totalFocusTime": t + random.randint(200, 1500),
        "checksum": checksum,
        "prefilled": False
    }

# ============================================================
# Main collector
# ============================================================
def _gen_perf_timing(now, dwell):
    """Page-load timeline consistent with the claimed dwell.

    navigationStart sits a few hundred ms before the server served the page
    (≈ now-dwell); every milestone is pinned strictly before ``now`` and kept
    in monotonic order, so the fingerprint never reports events in the future
    or out of order — even for very short dwells (fast claim/register steps
    with the pacing sleeps removed)."""
    r = random.randint
    nav = now - dwell - r(300, 700)
    serve = now - dwell
    load_end = max(serve + 60, now - r(60, 250))
    if load_end > now - 30:
        load_end = now - r(30, 120)
    span = max(load_end - serve, 40)

    # Pre-response handshake milestones, each bounded before the server response.
    def clip(v, lo=serve):
        return max(nav, min(lo, v))

    seq = [
        ("fetchStart", nav + r(5, 60)),
        ("domainLookupStart", nav + r(20, 120)),
        ("domainLookupEnd", nav + r(40, 190)),
        ("connectStart", nav + r(60, 250)),
        ("connectEnd", nav + r(100, 360)),
        ("requestStart", nav + r(140, 450)),
    ]
    out = {}
    prev = nav
    for k, v in seq:
        v = max(prev, clip(v))
        out[k] = v
        prev = v
    c0, c1 = out["connectStart"], out["connectEnd"]
    out["secureConnectionStart"] = c0 + r(5, max(5, c1 - c0 - 10))
    out["responseStart"] = min(serve, out["requestStart"] + r(10, 70))

    # Post-response load milestones inside [serve, load_end].
    def slot(lo, hi):
        a = serve + int(span * lo)
        b = serve + int(span * hi)
        return max(a, min(load_end, a + r(0, max(0, b - a))))

    out["responseEnd"] = slot(0.02, 0.12)
    out["domLoading"] = slot(0.12, 0.25)
    out["domInteractive"] = slot(0.25, 0.45)
    out["domContentLoadedEventStart"] = slot(0.45, 0.60)
    out["domContentLoadedEventEnd"] = slot(0.60, 0.72)
    out["domComplete"] = slot(0.72, 0.86)
    out["loadEventStart"] = slot(0.86, 0.94)
    out["loadEventEnd"] = load_end
    out["navigationStart"] = nav
    out["unloadEventStart"] = 0
    out["unloadEventEnd"] = 0
    out["redirectStart"] = 0
    out["redirectEnd"] = 0

    # Final monotonic sweep — guarantee ordering even after clamping.
    order = ["fetchStart", "domainLookupStart", "domainLookupEnd",
             "connectStart", "secureConnectionStart", "connectEnd",
             "requestStart", "responseStart", "responseEnd", "domLoading",
             "domInteractive", "domContentLoadedEventStart",
             "domContentLoadedEventEnd", "domComplete", "loadEventStart",
             "loadEventEnd"]
    last = nav
    for k in order:
        if out[k] < last:
            out[k] = last
        last = out[k]
    return out

def collect_fingerprint(email=None, password=None, name=None, password_check=None,
                        otp=None, user_agent=None, referrer=None, location=None,
                        time_zone=None, html_b64=None, dwell_ms=None,
                        session_id=None):
    now = int(time.time() * 1000)
    if not user_agent: user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"
    if not referrer: referrer = ""
    if not location:
        location = ""
    if time_zone is None: time_zone = -(time.timezone // 3600)

    profile = detect_profile(user_agent)
    data = {}

    data["metrics"] = {k: 0 for k in ["el","script","h","batt","perf","auto","tz","fp2","lsubid","browser","capabilities","gpu","dnt","math","tts","input","canvas","captchainput","pow"]}
    data["metrics"]["perf"] = 1
    data["metrics"]["lsubid"] = 1
    data["metrics"]["input"] = 1
    data["metrics"]["pow"] = random.randint(800, 2200)  # ms que tarda el Web Worker real
    if otp:
        data["metrics"]["captchainput"] = 1
    # User dwells on the page before submitting. When the caller measured the
    # real elapsed time between page load and submit (dwell_ms), reuse it so
    # start/timeToSubmit are consistent with what the server observes (a bot
    # that submits ~1s after the page was served cannot claim a 10-25s dwell).
    # The floor is kept tiny so `start` never precedes the page-serve time the
    # server recorded (inflating it would be a hard contradiction).
    if dwell_ms is not None:
        dwell = max(int(dwell_ms), 50)
    else:
        dwell = random.randint(10000, 25000)
    data["start"] = now - dwell
    data["end"] = now
    # tts collector outputs timeToSubmit = submitTime - start (slightly before end)
    if dwell_ms is not None:
        data["timeToSubmit"] = max(30, dwell - random.randint(30, 150))
    else:
        data["timeToSubmit"] = max(30, dwell - random.randint(100, 900))

    # Build form fields in order — matches real fingerprint structure
    form_field_defs = []
    if name: form_field_defs.append(("ap_customer_name", name, 312, 32))
    if email: form_field_defs.append(("ap_email_login", email, 294, 32))
    if password: form_field_defs.append(("password", password, 312, 32))
    if password_check: form_field_defs.append(("ap_password_check", password_check, 312, 32))


    if email and not password and not password_check:
        form_field_defs.append(("auth-credential-autofill-hint", "", 0, 0))
    if otp:
        form_field_defs.append(("cvf-input-code", otp, 312, 32))

    # Interaction — based on actual form field keystrokes, bounded by the dwell
    total_keys = sum(len(str(v)) for _, v, _, _ in form_field_defs if v)
    total_clicks = len(form_field_defs) + random.randint(0, 3)
    data["interaction"] = gen_interaction(total_keys, total_clicks, data["start"], dwell)

    # Scripts
    hashes_list = [random.randint(-2000000000, 2000000000) for _ in range(random.randint(20, 40))]
    if html_b64:
        data["scripts"] = extract_scripts(html_b64)
    else:
        urls_list = []
        data["scripts"] = {"dynamicUrls": urls_list, "inlineHashes": [], "elapsed": 0, "dynamicUrlCount": 0, "inlineHashesCount": 0}

    data["history"] = {"length": random.randint(5, 12)}
    data["performance"] = {"timing": _gen_perf_timing(now, dwell)}
    data["automation"] = {"wd":{"properties":{"document":[],"window":[],"navigator":[]}},"phantom":{"properties":{"window":[]}}}
    data["timeZone"] = time_zone
    data["flashVersion"] = None
    data["plugins"] = profile["plugins"]
    data["dupedPlugins"] = profile["plugins"]
    data["screenInfo"] = profile["screen"]
    data["lsUbid"] = gen_lsubid()
    data["referrer"] = referrer
    data["userAgent"] = user_agent
    data["location"] = location
    data["webDriver"] = False
    data["capabilities"] = {"css": profile["css"], "js": profile["js"], "elapsed": 0}
    data["gpu"] = {"vendor": profile["gpu_vendor"], "model": profile["gpu_model"], "extensions": profile["gpu_ext"]}
    data["dnt"] = None
    constant = -1e+300
    data["math"] = {"tan": str(math.tan(constant)), "sin": str(math.sin(constant)), "cos": str(math.cos(constant))}

    # Form — ordered, matching real fingerprint structure
    data["form"] = {}
    for fname, fval, fw, fh in form_field_defs:
        data["form"][fname] = gen_form_field(fname, fval, fw, fh)

    data["canvas"] = gen_canvas()
    data["token"] = {"isCompatible": True, "pageHasCaptcha": 0}
    # Proof-of-Work: Amazon compara este token con el hash esperado en server
    # side. Sin él, el POST del paso 4 dispara el captcha FWCIM. La session-id
    # usada como IV es la misma cookie `session-id` que asigna Amazon al
    # cargar /ap/register. Si no se pasa, cae a un valor aleatorio (que Amazon
    # rechaza y dispara el captcha visual aamation).
    if session_id is None:
        session_id = gen_lsubid().split(":", 1)[0]
    data["pow"] = gen_pow_token(
        session_id=session_id,
        page_has_captcha=0,
        min_difficulty=8,
        max_difficulty=12,
    )
    data["auth"] = {"form": {"method": "post"}}
    data["errors"] = []
    data["version"] = "4.0.0"
    return data

# ============================================================
# Encoding
# ============================================================
_MASK32 = 0xFFFFFFFF
def _to_s32(x):
    x &= _MASK32
    return x - (1 << 32) if x & (1 << 31) else x

def _tea_delta(a, c, d, key, u, h):
    """f(c,a) = ((c>>>5 ^ a<<2) + (a>>>3 ^ c<<4)) ^ ((d^a) + (key[3&u^h]^c))"""
    aa = a & _MASK32; cc = c & _MASK32
    x = _to_s32(_to_s32((cc >> 5) ^ _to_s32(aa << 2)) + _to_s32((aa >> 3) ^ _to_s32(cc << 4)))
    y = _to_s32(_to_s32(d ^ _to_s32(aa)) + _to_s32(_to_s32(key[3 & u ^ h]) ^ _to_s32(cc)))
    return _to_s32(x ^ y)

def te_encrypt(pt, key):
    """Exact port of FWCIM doEncrypt (mod 70): running a/c carry, signed << / unsigned >>>.

    Takes bytes, returns bytes. Inlined + precomputed indices for speed; the
    arithmetic below must stay byte-identical to the JS (do not "simplify")."""
    if not pt: return b''
    plen = len(pt)
    n = (plen + 3) // 4
    v = [0] * n
    for i in range(n):
        idx = i << 2
        val = pt[idx]
        if idx + 1 < plen: val |= pt[idx + 1] << 8
        if idx + 2 < plen: val |= pt[idx + 2] << 16
        if idx + 3 < plen: val |= pt[idx + 3] << 24
        v[i] = val
    rounds = int(6 + 52 / n)
    MASK = 0xFFFFFFFF
    SIGN = 0x80000000
    nxt = list(range(1, n)) + [0]
    a = v[0]; c = v[n - 1]; d = 0
    for _ in range(rounds):
        d = (d + 2654435769) & MASK
        h = (d >> 2) & 3
        for u in range(n):
            a = v[nxt[u]]
            aa = a; cc = c
            t = ((aa << 2) & MASK)
            t = ((t + SIGN) & MASK) - SIGN
            x = (cc >> 5) ^ t
            x = ((x + SIGN) & MASK) - SIGN
            t = ((cc << 4) & MASK)
            t = ((t + SIGN) & MASK) - SIGN
            t = (aa >> 3) ^ t
            t = ((t + SIGN) & MASK) - SIGN
            x += t
            x = ((x + SIGN) & MASK) - SIGN
            t = d ^ aa
            t = ((t + SIGN) & MASK) - SIGN
            t2 = key[3 & u ^ h]
            t2 = ((t2 + SIGN) & MASK) - SIGN
            t2 ^= cc
            t2 = ((t2 + SIGN) & MASK) - SIGN
            t += t2
            t = ((t + SIGN) & MASK) - SIGN
            x ^= t
            x = ((x + SIGN) & MASK) - SIGN
            c = v[u] = (v[u] + x) & MASK
    out = bytearray(n << 2)
    for s in range(n):
        w = v[s]
        i = s << 2
        out[i] = w & 0xFF
        out[i + 1] = (w >> 8) & 0xFF
        out[i + 2] = (w >> 16) & 0xFF
        out[i + 3] = (w >> 24) & 0xFF
    return bytes(out)

def te_decrypt(ct, key):
    """Inverse of te_encrypt — matches server-side doDecrypt."""
    if not ct: return ''
    n=(len(ct)+3)//4; v=[]
    for i in range(n):
        idx=4*i; val=ord(ct[idx])&0xFF
        if idx+1<len(ct): val|=(ord(ct[idx+1])&0xFF)<<8
        if idx+2<len(ct): val|=(ord(ct[idx+2])&0xFF)<<16
        if idx+3<len(ct): val|=(ord(ct[idx+3])&0xFF)<<24
        v.append(val)
    rounds = int(6 + 52 / n)
    d = (rounds * 2654435769) & _MASK32
    for _ in range(rounds):
        h = (d >> 2) & 3
        for u in range(n - 1, -1, -1):
            a = v[(u + 1) % n]
            c = v[u - 1] if u > 0 else v[n - 1]
            v[u] = (v[u] - _tea_delta(a, c, d, key, u, h)) & _MASK32
        d = (d - 2654435769) & _MASK32
    return ''.join(chr(v[s]&0xFF)+chr(v[s]>>8&0xFF)+chr(v[s]>>16&0xFF)+chr(v[s]>>24&0xFF) for s in range(n))

def encode_metadata1(data):
    j=json.dumps(data,separators=(',',':')); jb=j.encode('utf-8')
    crc=zlib.crc32(jb)&0xFFFFFFFF
    return IDENTIFIER+':'+base64.b64encode(te_encrypt(format(crc,'08X').encode('latin-1')+b'#'+jb,KEY_UINT32)).decode()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description='Generate fingerprint')
    p.add_argument('--email',default=None)
    p.add_argument('--password',default=None)
    p.add_argument('--name',default=None)
    p.add_argument('--password-check',default=None)
    p.add_argument('--user-agent',default="Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0")
    p.add_argument('--referrer',default="https://www.amazon.com/")
    p.add_argument('--location',default=None)
    p.add_argument('--timezone',type=int,default=None)
    p.add_argument('--html-b64',default=None)
    args=p.parse_args()
    fp=collect_fingerprint(args.email,args.password,args.name,args.password_check,args.user_agent,args.referrer,args.location,args.timezone,args.html_b64)
    m1=encode_metadata1(fp)
    with open('generated-fingerprint.json','w') as f: 
        json.dump(fp,f,indent=2,ensure_ascii=False)
    with open('generated-metadata1.txt','w') as f: 
        f.write(m1)
    print(json.dumps(fp,indent=2,ensure_ascii=False))
    print(f"\nmetadata1: {m1[:80]}...")
