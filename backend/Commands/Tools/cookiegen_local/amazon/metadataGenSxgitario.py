"""FWCIM (Amazon anti-bot fingerprint) generator — builds the `metadata1` value.

This is now the ONLY metadata1 generator in this codebase — it used to be
one of two competing implementations:

* The original `FwcimAmazonSxgitario` (retired) — six fixed
  HARDWARE_PROFILES bundling a real captured canvas hash + GPU + screen +
  math per entry, plus a log-logistic keystroke-timing model and a strict
  `__assertConsistency` self-check. More "textbook accurate" on paper, but
  live testing repeatedly showed it correlates with far more Amazon
  captcha/Arkose challenges. Leading hypothesis (see project memory): only
  5-6 possible canvas hashes existed across every account this pipeline
  ever generated (two profiles even collided on the exact same hash) —
  in a bulk-registration context that's a strong fingerprint-clustering
  signal, regardless of how accurate its other fields were.
* `generate_fingerprint_desofuscado.py` (root-level reconstruction of an
  older, retired obfuscated `generate_fingerprint.py`) — MERGED into this
  class below. Its actual algorithm is what's been empirically running in
  production: a canvas rendered fresh via Pillow on every single call
  (with real per-pixel jitter), so no two accounts this generator
  produces can ever share a canvas hash — confirmed live, 2026-07-21,
  across dozens of registrations, 0 captcha.

Pillow (PIL) is a REQUIRED dependency for the canvas step — see
`__buildCanvas` below for what happens (and why it's bad) if it's
missing. Do not remove it from requirements.txt.

Author: Vxsilisk @ Sxgitario API Gateways Service
        DEV  https://t.me/Vxsilisk
        SHOP https://t.me/Sxgitario
"""

import base64
import hashlib
import math
import json
import random
import struct
import time
import zlib


class FwcimAmazonSxgitario:
    """Builds one `metadata1` FWCIM payload per call.

    Construct with the current request's context (URL, UA, the form
    values actually being submitted) and call :meth:`generateMetadata`.
    Build a fresh instance for every request — metadata1 must never be
    cached or reused across POSTs.
    """

    __KEY_IDENTIFIER = "ECdITeCs"
    __KEY_MATERIAL   = [1888420705, 0x99971834, 0x8BE7EB3A, 874813317]
    __XXTEA_DELTA    = 0x9E3779B9

    # Chrome 109+ dropped Native Client — plugins string without it
    _CHROME_PLUGINS = "Chrome PDF Plugin Chrome PDF Viewer"

    # Browser/OS profiles — GPU/plugins/screen coherent per browser+OS
    # combination. Canvas is intentionally NOT bundled per-profile here
    # (unlike the retired generator) — it's rendered fresh in
    # __buildCanvas() on every single call instead, decoupled from the
    # profile entirely. That decoupling is the actual source of this
    # generator's low captcha rate (see module docstring) — do not
    # "fix" it by tying canvas back to a fixed per-profile value.
    __PROFILES = {
        # ── Generic fallback (kept for UA-based detection) ──────────────
        'chrome_win': {
            'gpuVendor': 'Google Inc. (NVIDIA)',
            'gpuModel': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
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
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1920-1080-1040-24-*-*-*',
            'screenInfo': '1920-1080-1040-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1040},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # ── US profiles ─────────────────────────────────────────────────
        # Laptop barata 1366×768 Intel UHD 620 — más común bulk residencial US
        'chrome_win_us': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1366-768-728-24-*-*-*',
            'screenInfo': '1366-768-728-24-*-*-*',
            'screen': {'width': 1366, 'height': 768, 'availHeight': 728},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # US 14" laptop 125% scale — Iris Xe (muy común Win11)
        'chrome_win_us_hd': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1536-864-824-24-*-*-*',
            'screenInfo': '1536-864-824-24-*-*-*',
            'screen': {'width': 1536, 'height': 864, 'availHeight': 824},
            'dpr': 1.25, 'deviceMemory': 8,
        },
        # US desktop FHD Intel UHD 630 (i5 office)
        'chrome_win_us_fhd': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1920-1080-1040-24-*-*-*',
            'screenInfo': '1920-1080-1040-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1040},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # US gamer RTX 3060 (raro en pool clean — no usar bulk)
        'chrome_win_us_nvidia': {
            'gpuVendor': 'Google Inc. (NVIDIA)',
            'gpuModel': 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Laptop GPU Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
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
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1920-1080-1040-24-*-*-*',
            'screenInfo': '1920-1080-1040-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1040},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # ── MX profiles ─────────────────────────────────────────────────
        # Laptop residencial MX: 1366×768 Intel UHD 620 (HP/Lenovo/Dell LATAM)
        'chrome_win_mx': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1366-768-728-24-*-*-*',
            'screenInfo': '1366-768-728-24-*-*-*',
            'screen': {'width': 1366, 'height': 768, 'availHeight': 728},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # MX notebook 1536×864 @125% — Iris Xe (laptops 14" Win11)
        'chrome_win_mx_hd': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1536-864-824-24-*-*-*',
            'screenInfo': '1536-864-824-24-*-*-*',
            'screen': {'width': 1536, 'height': 864, 'availHeight': 824},
            'dpr': 1.25, 'deviceMemory': 8,
        },
        # MX AMD APU (laptops Telcel/Coppel/BestBuy MX)
        'chrome_win_mx_amd': {
            'gpuVendor': 'Google Inc. (AMD)',
            'gpuModel': 'ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1366-768-728-24-*-*-*',
            'screenInfo': '1366-768-728-24-*-*-*',
            'screen': {'width': 1366, 'height': 768, 'availHeight': 728},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # MX FHD gamer/office entry — GTX 1650
        'chrome_win_mx_fhd': {
            'gpuVendor': 'Google Inc. (NVIDIA)',
            'gpuModel': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
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
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1920-1080-1040-24-*-*-*',
            'screenInfo': '1920-1080-1040-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1040},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        # ── EU profiles ─────────────────────────────────────────────────
        # EU laptop típico 1920×1080 Intel Iris Xe
        'chrome_win_eu': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1920-1080-1040-24-*-*-*',
            'screenInfo': '1920-1080-1040-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1040},
            'dpr': 1.0, 'deviceMemory': 16,
        },
        # EU 1536×864 @125% — UHD 630
        'chrome_win_eu_hd': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1536-864-824-24-*-*-*',
            'screenInfo': '1536-864-824-24-*-*-*',
            'screen': {'width': 1536, 'height': 864, 'availHeight': 824},
            'dpr': 1.25, 'deviceMemory': 8,
        },
        # JP / FE — Intel UHD 770 desktop
        'chrome_win_jp': {
            'gpuVendor': 'Google Inc. (Intel)',
            'gpuModel': 'ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
                'WEBGL_compressed_texture_s3tc', 'WEBGL_debug_renderer_info', 'OES_texture_float',
                'WEBGL_lose_context', 'WEBGL_depth_texture', 'EXT_color_buffer_half_float',
                'WEBGL_color_buffer_float', 'OES_standard_derivatives', 'OES_element_index_uint',
                'OES_texture_float_linear', 'OES_texture_half_float', 'OES_texture_half_float_linear',
                'EXT_shader_texture_lod', 'WEBGL_compressed_texture_s3tc_srgb', 'WEBGL_debug_shaders',
                'EXT_float_blend', 'WEBGL_draw_buffers',
            ],
            'css': {'textShadow': 1, 'WebkitTextStroke': 1, 'boxShadow': 1, 'borderRadius': 1,
                    'borderImage': 1, 'opacity': 1, 'transform': 1, 'transition': 1},
            'js': {'audio': True, 'geolocation': True, 'localStorage': 'supported',
                   'touch': False, 'video': True, 'webWorker': True},
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1920-1080-1040-24-*-*-*',
            'screenInfo': '1920-1080-1040-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1040},
            'dpr': 1.0, 'deviceMemory': 16,
        },
        # ── Mac / Firefox ────────────────────────────────────────────────
        'chrome_mac': {
            'gpuVendor': 'Apple', 'gpuModel': 'Apple M1',
            'gpuExtensions': [
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
            'plugins': 'Chrome PDF Plugin Chrome PDF Viewer ||1440-900-900-22-*-*-*',
            'screenInfo': '1440-900-900-22-*-*-*',
            'screen': {'width': 1440, 'height': 900, 'availHeight': 900},
            'dpr': 2.0, 'deviceMemory': 8,
        },
        'firefox_linux': {
            'gpuVendor': 'Intel', 'gpuModel': 'Intel(R) HD Graphics, or similar',
            'gpuExtensions': [
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
            'screenInfo': '1280-1024-1024-24-*-*-*',
            'screen': {'width': 1280, 'height': 1024, 'availHeight': 1024},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        'firefox_win': {
            'gpuVendor': 'Google Inc. (NVIDIA)',
            'gpuModel': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)',
            'gpuExtensions': [
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
            'screenInfo': '1920-1080-1080-24-*-*-*',
            'screen': {'width': 1920, 'height': 1080, 'availHeight': 1080},
            'dpr': 1.0, 'deviceMemory': 8,
        },
        'safari_mac': {
            'gpuVendor': 'Apple', 'gpuModel': 'Apple M2',
            'gpuExtensions': [
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
            'screenInfo': '1440-900-900-22-*-*-*',
            'screen': {'width': 1440, 'height': 900, 'availHeight': 900},
            'dpr': 2.0, 'deviceMemory': 8,
        },
    }

    # Per-marketplace behavior overrides: HW pool, form fields, TZ, canvas strategy weights
    __MARKET_HINTS = {
        "US": {
            "timezones": (-5, -5, -5, -5, -5, -6, -6, -6, -7, -8),
            "profiles": (
                "chrome_win_us", "chrome_win_us", "chrome_win_us",
                "chrome_win_us_hd", "chrome_win_us_hd",
                "chrome_win_us_fhd", "chrome_win_us_fhd",
                "chrome_win",
            ),
            "form_email_key": "ap_email_login",
            "form_name_key": "ap_customer_name",
            "key_slow": False,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "skia_soft", "skia_soft"),
            "dwell_ms": (3500, 8000),
            "paste_email": 0.20, "paste_password": 0.12, "paste_name": 0.03, "paste_otp": 0.48,
        },
        "CA": {
            "timezones": (-5, -5, -5, -6, -7, -8),
            "profiles": ("chrome_win_us_fhd", "chrome_win_us_hd", "chrome_win_us", "chrome_win_eu", "chrome_win"),
            "form_email_key": "ap_email_login",
            "form_name_key": "ap_customer_name",
            "key_slow": False,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "skia_soft", "skia_soft"),
            "dwell_ms": (3500, 8000),
            "paste_email": 0.20, "paste_password": 0.12, "paste_name": 0.03, "paste_otp": 0.48,
        },
        "MX": {
            "timezones": (-6, -6, -6, -6, -6, -6, -6, -6, -6, -6),
            "profiles": (
                "chrome_win_mx", "chrome_win_mx", "chrome_win_mx", "chrome_win_mx",
                "chrome_win_mx_hd", "chrome_win_mx_hd", "chrome_win_mx_hd",
                "chrome_win_mx_amd", "chrome_win_mx_amd",
                "chrome_win_mx_fhd",
            ),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "skia_soft", "skia_soft"),
            "dwell_ms": (4200, 9000),
            "paste_email": 0.18, "paste_password": 0.08, "paste_name": 0.03, "paste_otp": 0.50,
        },
        "BR": {
            "timezones": (-3, -3, -3, -3, -4, -5),
            "profiles": (
                "chrome_win_mx", "chrome_win_mx", "chrome_win_mx_hd",
                "chrome_win_mx_amd", "chrome_win_us",
            ),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (4000, 8500),
            "paste_email": 0.18, "paste_password": 0.08, "paste_name": 0.03, "paste_otp": 0.50,
        },
        "UK": {
            "timezones": (0, 0, 1),
            "profiles": ("chrome_win_eu", "chrome_win_eu_hd", "chrome_win"),
            "form_email_key": "ap_email_login",
            "form_name_key": "ap_customer_name",
            "key_slow": False,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "DE": {
            "timezones": (1, 1, 2),
            "profiles": ("chrome_win_eu", "chrome_win_eu_hd", "chrome_win"),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": True,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "FR": {
            "timezones": (1, 1, 2),
            "profiles": ("chrome_win_eu", "chrome_win_eu_hd", "chrome_win"),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": True,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "ES": {
            "timezones": (1, 1, 2),
            "profiles": ("chrome_win_eu", "chrome_win_eu", "chrome_win_eu_hd", "chrome_win_eu_hd", "chrome_win"),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": True,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "IT": {
            "timezones": (1, 1, 2),
            "profiles": ("chrome_win_eu", "chrome_win_eu_hd", "chrome_win"),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": True,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "NL": {
            "timezones": (1, 1, 2),
            "profiles": ("chrome_win_eu", "chrome_win_eu_hd", "chrome_win"),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": False,
            "form_dual_email": True,
            "canvas_strategies": ("skia_soft", "skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "JP": {
            "timezones": (9,),
            "profiles": ("chrome_win_jp", "chrome_win_eu", "chrome_mac"),
            "form_email_key": "ap_email",
            "form_name_key": "ap_customer_name",
            "key_slow": True,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3500, 8000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "AU": {
            "timezones": (10, 10, 11, 8),
            "profiles": ("chrome_win", "chrome_win_eu", "chrome_win_us_fhd"),
            "form_email_key": "ap_email_login",
            "form_name_key": "ap_customer_name",
            "key_slow": False,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
        "SG": {
            "timezones": (8,),
            "profiles": ("chrome_win_jp", "chrome_win_eu", "chrome_win"),
            "form_email_key": "ap_email_login",
            "form_name_key": "ap_customer_name",
            "key_slow": False,
            "form_dual_email": False,
            "canvas_strategies": ("skia_soft", "skia_soft", "pixels_linear"),
            "dwell_ms": (3200, 7000),
            "paste_email": 0.16, "paste_password": 0.08, "paste_name": 0.04, "paste_otp": 0.52,
        },
    }

    # ── Session-sticky class vars (reset between accounts) ──────────────
    _session_profile        = None
    _session_canvas         = None
    _session_canvas_strategy = None
    _session_ls_ubid        = None

    # Strategy pool (ordered by empirical quality: skia_soft best for NA)
    CANVAS_STRATEGIES: tuple = (
        "skia_soft",
        "cleartype_rgb",
        "pixels_linear",
        "entropy_layer",
    )

    def __init__(
        self,
        location:       str,
        userAgent:      str,
        referrer:       str  = "",
        dynamicUrls:    list = None,
        inlineHashes:   list = None,
        emailValue:     str  = "",
        customerName:   str  = "",
        passwordValue:  str  = "",
        otpValue:       str  = "",
        timezone:       int  = None,
        postCaptcha:    bool = False,
        marketplace:    str  = "",
        acceptLanguage: str  = "",
        canvasStrategy: str  = "",
    ) -> None:
        self.__location      = location
        self.__userAgent     = userAgent or 'Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0'
        self.__referrer      = referrer or ""
        self.__dynamicUrls   = dynamicUrls or []
        self.__inlineHashes  = inlineHashes or []
        self.__emailValue    = emailValue
        self.__customerName  = customerName
        self.__passwordValue = passwordValue
        self.__otpValue      = otpValue
        self.__postCaptcha   = postCaptcha
        self.__marketplace   = (marketplace or "").upper().strip()
        self.__hint          = dict(self.__MARKET_HINTS.get(self.__marketplace) or {})

        # TZ: prefer explicit; then marketplace pool; then system
        if timezone is not None:
            self.__timezone = int(timezone)
        elif self.__hint.get("timezones"):
            self.__timezone = int(random.choice(self.__hint["timezones"]))
        else:
            self.__timezone = -int(time.timezone / 3600)

        # Profile detection (marketplace pool first, then UA inference)
        self.__profile = self.__detectProfile(self.__userAgent)
        FwcimAmazonSxgitario._session_profile = self.__profile

        # Canvas strategy sticky per account
        strat = (canvasStrategy or "").strip() or FwcimAmazonSxgitario._session_canvas_strategy
        if not strat or strat not in FwcimAmazonSxgitario.CANVAS_STRATEGIES:
            try:
                from services.canvas_tracker import banned_strategies as _banned
                banned = _banned()
            except Exception:
                banned = set()
            pool = list(self.__hint.get("canvas_strategies") or FwcimAmazonSxgitario.CANVAS_STRATEGIES)
            pool = [s for s in pool if s in FwcimAmazonSxgitario.CANVAS_STRATEGIES and s not in banned]
            if not pool:
                pool = [s for s in FwcimAmazonSxgitario.CANVAS_STRATEGIES if s not in banned]
            if not pool:
                pool = list(FwcimAmazonSxgitario.CANVAS_STRATEGIES)
            strat = random.choice(pool)
        FwcimAmazonSxgitario._session_canvas_strategy = strat
        self.__canvasStrategy = strat
        self.last_canvas_strategy = strat

    @classmethod
    def reset_session(cls):
        """Reset all session-sticky state between accounts."""
        cls._session_profile         = None
        cls._session_canvas          = None
        cls._session_canvas_strategy = None
        cls._session_ls_ubid         = None

    @classmethod
    def current_canvas_strategy(cls) -> str:
        return cls._session_canvas_strategy or "skia_soft"


    #//! -------------------- Public API -------------------- !\\#
    def generateMetadata(self) -> dict:
        try:
            fingerprint = self.__buildFingerprint()
            md = self.__encodeMetadata1(fingerprint)
            return {
                'status':    True,
                'context':   'Amazon FWCIM Fingerprint Generator',
                'poweredBy': 'Vxsilisk @ Sxgitario API Gateways Service',
                'metadata1': md,
            }
        except Exception as error:
            return {'status': False, 'description': str(error)}


    #//! -------------------- Fingerprint builder -------------------- !\\#
    def __buildFingerprint(self) -> dict:
        now = int(time.time() * 1000)
        p   = self.__profile

        form = self.__buildForm()

        values      = (self.__customerName, self.__emailValue, self.__passwordValue,
                       self.__passwordValue, self.__otpValue)
        totalKeys   = sum(len(str(v)) for v in values if v)
        totalClicks = sum(1 for v in values if v)
        interaction = self.__buildInteraction(totalKeys, totalClicks, now)

        # Dwell time: log-normal matches real form-fill behavior (Dhakal 2018).
        # Fast markets (US/CA/UK): median ~40s. Slow (MX/BR/EU): median ~55s.
        if self.__marketplace in ("US", "CA", "UK", "AU", "SG"):
            ln_mu = 3.689  # e^3.689 ≈ 40s
        elif self.__marketplace in ("MX", "BR", "DE", "FR", "ES", "IT", "NL", "JP"):
            ln_mu = 4.007  # e^4.007 ≈ 55s
        else:
            ln_mu = 3.807  # e^3.807 ≈ 45s
        start_ago = int(max(15_000, min(300_000, random.lognormvariate(ln_mu, 0.55) * 1000)))

        mem = min(8, int(p.get("deviceMemory") or 8))
        screen_info = p.get("screenInfo") or ""
        plugins = p.get("plugins") or ""
        # Chrome 109+: strip Native Client, enforce coherent plugins||screen
        if "Chrome PDF" in (self.__userAgent or "") or "chrome" in (self.__userAgent or "").lower():
            if "||" in plugins:
                plugins = self._CHROME_PLUGINS + " ||" + screen_info
            elif "Chrome PDF" in plugins and "Native Client" in plugins:
                plugins = self._CHROME_PLUGINS + " ||" + screen_info

        return {
            'metrics': self.__buildMetrics(),
            'start': now - start_ago,
            'interaction': interaction,
            'scripts': {
                'dynamicUrls': list(self.__dynamicUrls),
                'inlineHashes': list(self.__inlineHashes),
                'elapsed': 0,
                'dynamicUrlCount': len(self.__dynamicUrls),
                'inlineHashesCount': len(self.__inlineHashes),
            },
            'history': {'length': random.choice([1, 2, 2, 2, 3])},
            # Desktop Chrome Battery API: charging=True, level=1.0 (plugged in).
            # dischargingTime=null (JSON null = JS Infinity for desktop/plugged).
            'battery': {'charging': True, 'level': 1.0, 'chargingTime': 0, 'dischargingTime': None},
            # Empty dict validated empirically — filled timing fields increased captcha rate
            'performance': {'timing': {}},
            'automation': {
                'wd': {'properties': {'document': [], 'window': [], 'navigator': []}},
                'phantom': {'properties': {'window': []}},
            },
            'end': now,
            'timeZone': self.__timezone,
            'flashVersion': None,
            'plugins': plugins,
            'dupedPlugins': plugins,
            'screenInfo': screen_info,
            'lsUbid': self.__generateLsUbid(),
            'referrer': self.__referrer,
            'userAgent': self.__userAgent,
            'location': self.__location,
            'webDriver': False,
            'capabilities': {'css': p['css'], 'js': p['js'], 'elapsed': 0},
            'gpu': {'vendor': p['gpuVendor'], 'model': p['gpuModel'], 'extensions': p['gpuExtensions']},
            'dnt': None,
            'math': {'tan': str(math.tan(1)), 'sin': str(math.sin(1)), 'cos': str(math.cos(1))},
            'form': form,
            'canvas': self.__buildCanvas(),
            'token': {'isCompatible': True, 'pageHasCaptcha': 1 if self.__postCaptcha else 0},
            'auth': {'form': {'method': 'post'}},
            'errors': [],
            'version': '4.0.0',
        }

    def __detectProfile(self, userAgent: str) -> dict:
        # Sticky: reuse same HW profile across claim/register/otp
        if FwcimAmazonSxgitario._session_profile is not None:
            return FwcimAmazonSxgitario._session_profile
        # Marketplace pool (first call)
        hinted = self.__hint.get("profiles") or ()
        if hinted:
            key = random.choice(list(hinted))
            if key in self.__PROFILES:
                return self.__PROFILES[key]
        # Infer from location URL
        loc = (self.__location or "").lower()
        if "amazon.com.mx" in loc:
            return self.__PROFILES[random.choice([
                "chrome_win_mx", "chrome_win_mx", "chrome_win_mx_hd",
                "chrome_win_mx_amd", "chrome_win_mx_fhd",
            ])]
        if "amazon.com.br" in loc:
            return self.__PROFILES[random.choice(["chrome_win_mx", "chrome_win_us", "chrome_win"])]
        if "amazon.ca" in loc:
            return self.__PROFILES[random.choice([
                "chrome_win_us_fhd", "chrome_win_us_hd", "chrome_win_us", "chrome_win",
            ])]
        if "amazon.com" in loc and not any(
            x in loc for x in (".com.mx", ".com.br", ".com.au", ".com.be", ".com.tr")
        ):
            return self.__PROFILES[random.choice([
                "chrome_win_us", "chrome_win_us", "chrome_win_us_hd",
                "chrome_win_us_fhd", "chrome_win_us_nvidia", "chrome_win",
            ])]
        if any(x in loc for x in ("amazon.de", "amazon.fr", "amazon.es", "amazon.it",
                                   "amazon.nl", "amazon.co.uk")):
            return self.__PROFILES[random.choice(["chrome_win_eu", "chrome_win_eu_hd", "chrome_win"])]
        if "amazon.co.jp" in loc:
            return self.__PROFILES[random.choice(["chrome_win_jp", "chrome_mac"])]
        if "amazon.com.au" in loc or "amazon.sg" in loc:
            return self.__PROFILES[random.choice(["chrome_win", "chrome_win_eu", "chrome_win_us_fhd"])]
        # UA-based fallback
        ua = userAgent.lower()
        if 'chrome' in ua and 'edg' not in ua:
            return self.__PROFILES['chrome_mac'] if ('mac' in ua or 'darwin' in ua) else self.__PROFILES[random.choice([
                "chrome_win_us", "chrome_win_us_hd", "chrome_win_us_fhd", "chrome_win",
            ])]
        if 'firefox' in ua:
            return self.__PROFILES['firefox_linux'] if ('linux' in ua or 'x11' in ua) else self.__PROFILES['firefox_win']
        if 'safari' in ua and 'chrome' not in ua:
            return self.__PROFILES['safari_mac']
        return self.__PROFILES['firefox_linux']


    #//! -------------------- Canvas -------------------- !\\#
    def __loadCanvasFonts(self):
        from PIL import ImageFont
        try:
            return ImageFont.truetype('arial.ttf', 14), ImageFont.truetype('arial.ttf', 18)
        except (OSError, IOError):
            try:
                p = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
                return ImageFont.truetype(p, 14), ImageFont.truetype(p, 18)
            except (OSError, IOError):
                d = ImageFont.load_default()
                return d, d

    def __drawCanvasBase(self, image, strategy: str) -> None:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        fs, fl = self.__loadCanvasFonts()
        draw.text((2, 2),  'Cwm fjordank glyphs vext quiz', fill='#0050d4', font=fs)
        draw.text((2, 20), 'mmmmmmmmmmlli',                 fill='#0050d4', font=fl)
        draw.text((2, 42), 'W',                             fill='#0050d4', font=fs)
        draw.rectangle([0, 0, 7, 7], fill=(51, 102, 153, 128))
        draw.rectangle([1, 1, 6, 6], outline='#336699')
        draw.ellipse([0, 0, 7, 7],   fill='#336699')
        draw.ellipse([1, 1, 6, 6],   outline='#336699')
        for offset, color in ((0, '#336699'), (2, '#663399'), (4, '#cc6600')):
            draw.arc([20 + offset, 0 + offset, 50 + offset, 30 + offset], 0, 360, fill=color, width=2)
        if strategy == "skia_soft":
            soft = (0, 80, 200)
            draw.text((3, 3),  'Cwm fjordank glyphs vext quiz', fill=soft, font=fs)
            draw.text((3, 21), 'mmmmmmmmmmlli',                 fill=soft, font=fl)
        elif strategy == "cleartype_rgb":
            draw.text((1, 2), 'Cwm fjordank glyphs vext quiz', fill='#c01010', font=fs)
            draw.text((3, 2), 'Cwm fjordank glyphs vext quiz', fill='#1030c0', font=fs)
            draw.text((2, 2), 'Cwm fjordank glyphs vext quiz', fill='#0050d4', font=fs)
            draw.text((1, 20), 'mmmmmmmmmmlli', fill='#b01818', font=fl)
            draw.text((3, 20), 'mmmmmmmmmmlli', fill='#1828b0', font=fl)
            draw.text((2, 20), 'mmmmmmmmmmlli', fill='#0050d4', font=fl)
        elif strategy == "entropy_layer":
            for _ in range(random.randint(4, 9)):
                x0 = random.randint(60, 250); y0 = random.randint(0, 50)
                c  = (random.randint(0, 40), random.randint(40, 120), random.randint(140, 230))
                draw.ellipse([x0, y0, x0 + random.randint(2, 6), y0 + random.randint(2, 6)], fill=c)
            draw.text((2 + random.randint(0, 1), 2), 'Cwm fjordank glyphs vext quiz', fill='#0050d4', font=fs)

    def __applyCanvasNoise(self, image, strategy: str) -> None:
        try:
            import numpy as np
            from PIL import Image as _Image
            arr  = np.asarray(image.convert("RGB"), dtype=np.int16)
            h, w = arr.shape[:2]
            rng  = np.random.default_rng()
            bw   = min(100, w); y0, y1 = 10, min(50, h)
            ys   = np.arange(y0, y1)[:, None]; xs = np.arange(bw)[None, :]
            if strategy == "skia_soft":
                r = np.clip((xs * 1.7).astype(np.int16) + rng.integers(-1, 2, size=(y1 - y0, bw)), 0, 255)
                g = np.clip((ys * 2.4).astype(np.int16) + rng.integers(-1, 2, size=(y1 - y0, bw)), 0, 255)
                b = np.clip(120 + rng.integers(-3, 4, size=(y1 - y0, bw)), 0, 255)
            elif strategy == "entropy_layer":
                r = np.clip(xs * 2 + rng.integers(-2, 3, size=(y1 - y0, bw)), 0, 255)
                g = np.clip(ys * 3 + rng.integers(-2, 3, size=(y1 - y0, bw)), 0, 255)
                b = np.clip(128 + rng.integers(-5, 6, size=(y1 - y0, bw)), 0, 255)
                n  = int(rng.integers(80, 161))
                xs2 = rng.integers(0, w, size=n); ys2 = rng.integers(0, h, size=n)
                d   = rng.integers(-12, 13, size=n)
                arr[ys2, xs2, 0] = np.clip(arr[ys2, xs2, 0] + d, 0, 255)
                arr[ys2, xs2, 1] = np.clip(arr[ys2, xs2, 1] + d // 2, 0, 255)
                arr[ys2, xs2, 2] = np.clip(arr[ys2, xs2, 2] - d // 3, 0, 255)
            else:
                r = np.clip(xs * 2 + rng.integers(-2, 3, size=(y1 - y0, bw)), 0, 255)
                g = np.clip(ys * 3 + rng.integers(-2, 3, size=(y1 - y0, bw)), 0, 255)
                b = np.clip(128 + rng.integers(-5, 6, size=(y1 - y0, bw)), 0, 255)
            arr[y0:y1, 0:bw, 0] = r; arr[y0:y1, 0:bw, 1] = g; arr[y0:y1, 0:bw, 2] = b
            image.paste(_Image.fromarray(arr.astype(np.uint8), mode="RGB"))
            return
        except Exception:
            pass
        pixels = image.load(); w2, h2 = image.size
        for x in range(min(100, w2)):
            for y in range(10, min(50, h2)):
                pixels[x, y] = (
                    max(0, min(255, x * 2 + random.randint(-2, 2))),
                    max(0, min(255, y * 3 + random.randint(-2, 2))),
                    max(0, min(255, 128 + random.randint(-5, 5))),
                )

    def __buildCanvas(self) -> dict:
        # Sticky per-account: claim/register/otp share the same hash+bins —
        # a real browser never re-renders the canvas mid-session.
        cached = FwcimAmazonSxgitario._session_canvas
        if isinstance(cached, dict) and cached.get("histogramBins"):
            return {"hash": cached["hash"], "emailHash": cached["emailHash"], "histogramBins": cached["histogramBins"]}

        strategy = self.__canvasStrategy or "skia_soft"
        try:
            from PIL import Image
            image = Image.new('RGB', (280, 60), (255, 255, 255))
            self.__drawCanvasBase(image, strategy)
            self.__applyCanvasNoise(image, strategy)

            try:
                import numpy as np
                arr  = np.asarray(image.convert("RGB"), dtype=np.uint8)
                rgba = np.empty((*arr.shape[:2], 4), dtype=np.uint8)
                rgba[..., :3] = arr; rgba[..., 3] = 255
                pixelBytes    = rgba.reshape(-1).tobytes()
                lum           = (0.299 * arr[..., 0].astype(float) + 0.587 * arr[..., 1].astype(float)
                                 + 0.114 * arr[..., 2].astype(float)).astype(int)
                histogramBins = lum.reshape(-1).tolist()
            except Exception:
                pixelBytes    = b''.join(struct.pack('BBBB', *px, 255) for px in image.getdata())
                histogramBins = [int(0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]) for px in image.getdata()]

            canvasHash = zlib.crc32(pixelBytes) & 0xFFFFFFFF
            if canvasHash >= 0x80000000:
                canvasHash -= 0x100000000
            # emailHash derived from canvasHash — unique per render, deterministic per canvas
            emailHash = struct.unpack('>i', hashlib.md5(canvasHash.to_bytes(4, 'big')).digest()[0:4])[0]
            canvas = {'hash': canvasHash, 'emailHash': emailHash, 'histogramBins': histogramBins}
        except ImportError:
            _seed = random.randint(0, 0x7FFFFFFF)
            emailHash = struct.unpack('>i', hashlib.md5(str(_seed).encode()).digest()[0:4])[0]
            canvas = {
                'hash': emailHash ^ random.randint(1, 0x7FFFFFFF),
                'emailHash': emailHash,
                'histogramBins': [random.randint(10, 80) for _ in range(280 * 60)],
            }

        FwcimAmazonSxgitario._session_canvas = canvas
        return canvas


    #//! -------------------- Metrics / interaction -------------------- !\\#
    def __buildMetrics(self) -> dict:
        # All zeroes except light input noise — filled timings increased captcha rate
        fields = ('el', 'script', 'h', 'batt', 'perf', 'auto', 'tz', 'fp2', 'lsubid',
                  'browser', 'capabilities', 'gpu', 'dnt', 'math', 'tts', 'input',
                  'canvas', 'captchainput', 'pow')
        metrics = {key: 0 for key in fields}
        metrics['input'] = random.randint(0, 2)
        return metrics

    def __buildInteraction(self, totalKeys: int, totalClicks: int, now: int) -> dict:
        cursor = now - random.randint(1500, 4000)
        keyEvents = []
        for i in range(totalKeys):
            cursor += self.__humanKeyInterval(i, totalKeys)
            dur = random.randint(40, 120)
            keyEvents.append({'start': cursor, 'end': cursor + dur})

        keyPressTimeIntervals = [keyEvents[i]['start'] - keyEvents[i - 1]['start'] for i in range(1, len(keyEvents))]
        keyCycles = [e['end'] - e['start'] for e in keyEvents]

        mouseEvents = []
        clickTime = now - random.randint(2000, 5000)
        for i in range(totalClicks):
            x, y = self.__humanMousePosition(i)
            dur = random.randint(30, 90)
            mouseEvents.append({'start': clickTime, 'end': clickTime + dur, 'x': x, 'y': y})
            clickTime += random.randint(600, 1500) if random.random() < 0.15 else random.randint(150, 500)

        mouseCycles = [e['end'] - e['start'] for e in mouseEvents]
        mouseClickPositions = [f"{e['x']},{e['y']}" for e in mouseEvents]
        pastes = 1 if random.random() < 0.15 else 0

        return {
            'clicks': totalClicks, 'touches': 0, 'keyPresses': totalKeys,
            'cuts': 0, 'copies': 0, 'pastes': pastes,
            'keyPressTimeIntervals': keyPressTimeIntervals,
            'mouseClickPositions': mouseClickPositions,
            'keyCycles': keyCycles,
            'mouseCycles': mouseCycles,
            'touchCycles': [],
        }

    @staticmethod
    def _ex_gauss(mu: float, sigma: float, tau: float) -> int:
        """Ex-Gaussian sample (Normal + Exponential). Validated model for human IKI (Dhakal CHI 2018)."""
        return max(20, int(random.gauss(mu, sigma) + random.expovariate(1.0 / tau)))

    @staticmethod
    def __humanKeyInterval(index: int, total: int) -> int:
        # Generic ex-Gaussian for top-level interaction block (mu=65, sigma=25, tau=50 → mean ~115ms)
        if index == 0:
            return max(120, FwcimAmazonSxgitario._ex_gauss(280, 90, 150))
        if random.random() < 0.07:
            return max(300, FwcimAmazonSxgitario._ex_gauss(600, 200, 350))
        return FwcimAmazonSxgitario._ex_gauss(65, 25, 50)

    @staticmethod
    def __humanMousePosition(formIndex: int) -> tuple:
        x = random.randint(150, 400) + random.randint(-5, 5)
        y = 50 + formIndex * 45 + random.randint(-10, 10) + random.randint(-3, 3)
        return (x, y)


    #//! -------------------- Form builders -------------------- !\\#
    def __buildForm(self) -> dict:
        form = {}
        name_key  = self.__hint.get("form_name_key")  or "ap_customer_name"
        email_key = self.__hint.get("form_email_key") or "ap_email_login"
        slow      = bool(self.__hint.get("key_slow"))

        sw = int(self.__profile.get("screen", {}).get("width") or 1366)
        fw = 340 if sw <= 1400 else (360 if sw <= 1600 else 380)
        fh = 31  if sw <= 1400 else 32

        if self.__customerName:
            form[name_key] = self.__buildFormField(self.__customerName, fw + 12, fh, kind="name", slow=slow)
        if self.__emailValue:
            form[email_key] = self.__buildFormField(self.__emailValue, fw, fh, kind="email", slow=slow)
            # EU marketplaces send both ap_email + ap_email_login — never random 50% (bot cluster)
            if bool(self.__hint.get("form_dual_email")):
                alt_key = "ap_email_login" if email_key == "ap_email" else "ap_email"
                form[alt_key] = self.__buildFormField(self.__emailValue, fw, fh, kind="email", slow=slow)
        if self.__passwordValue:
            form['password']         = self.__buildFormField(self.__passwordValue, fw, fh, kind="password", slow=slow)
            form['ap_password_check'] = self.__buildFormField(self.__passwordValue, fw, fh, kind="password", slow=slow)
        if self.__otpValue:
            form['cvf-input-code'] = self.__buildFormField(self.__otpValue, min(200, fw), fh, kind="otp", slow=slow)
        form['auth-credential-autofill-hint'] = self.__buildFormField('', 0, 0)
        return form

    def __buildFormField(self, value, width: int, height: int, *, kind: str = "text", slow: bool = False) -> dict:
        keyCount = len(str(value)) if value else 0

        if keyCount == 0:
            return {
                'clicks': 0, 'touches': 0, 'keyPresses': 0, 'cuts': 0, 'copies': 0, 'pastes': 0,
                'keyPressTimeIntervals': [], 'mouseClickPositions': [], 'keyCycles': [],
                'mouseCycles': [], 'touchCycles': [],
                'width': width, 'height': height,
                'totalFocusTime': 0, 'checksum': None, 'prefilled': False,
            }

        # Paste probability by kind + marketplace
        paste_key = {"email": "paste_email", "password": "paste_password",
                     "name": "paste_name", "otp": "paste_otp"}.get(kind)
        defaults  = {"email": 0.18, "password": 0.10, "name": 0.03, "otp": 0.48}
        if paste_key and self.__hint.get(paste_key) is not None:
            paste_p = float(self.__hint[paste_key])
        else:
            paste_p = defaults.get(kind, 0.10)

        sw     = int(self.__profile.get("screen", {}).get("width") or 1366)
        lo_x   = max(80,  int(sw * 0.30))
        hi_x   = max(lo_x + 40, int(sw * 0.48))
        mouseX = random.randint(lo_x, hi_x)
        mouseY = random.randint(12, 30)
        checksum = format(zlib.crc32(str(value).encode('utf-8')) & 0xFFFFFFFF, '08X')

        if random.random() < paste_p:
            return {
                'clicks': 1, 'touches': 0, 'keyPresses': 0, 'cuts': 0, 'copies': 0, 'pastes': 1,
                'keyPressTimeIntervals': [],
                'mouseClickPositions': [f"{mouseX},{mouseY}"],
                'keyCycles': [],
                'mouseCycles': [random.randint(40, 100)],
                'touchCycles': [],
                'width': width, 'height': height,
                'totalFocusTime': random.randint(400, 1600),
                'checksum': checksum,
                'prefilled': False,
            }

        # Ex-Gaussian IKI params per field kind (Dhakal CHI 2018, adapted).
        # key_slow=True scales mu+tau by 1.4 for LATAM/EU markets.
        _params = {
            "email":    (55,  22, 45),
            "password": (80,  32, 65),
            "name":     (100, 42, 70),
            "otp":      (60,  18, 30),
        }
        mu, sigma, tau = _params.get(kind, (65, 25, 50))
        if slow:
            mu  = int(mu  * 1.4)
            tau = int(tau * 1.4)

        keyIntervals, totalFocus = [], 0
        for i in range(keyCount):
            if i == 0:
                # First key: hesitation before starting to type
                interval = max(80, FwcimAmazonSxgitario._ex_gauss(mu * 3, sigma * 2, tau * 2))
            elif random.random() < (0.09 if slow else 0.06):
                # Cognitive pause (word boundary, recall hesitation)
                interval = max(300, FwcimAmazonSxgitario._ex_gauss(mu * 7, sigma * 3, tau * 5))
            else:
                interval = FwcimAmazonSxgitario._ex_gauss(mu, sigma, tau)
            keyIntervals.append(interval)
            totalFocus += interval

        _cycle_mu = 75 if slow else 60
        keyCycles = [max(20, FwcimAmazonSxgitario._ex_gauss(_cycle_mu, 18, 25)) for _ in range(keyCount)]
        return {
            'clicks': 1, 'touches': 0, 'keyPresses': keyCount, 'cuts': 0, 'copies': 0, 'pastes': 0,
            'keyPressTimeIntervals': keyIntervals,
            'mouseClickPositions': [f"{mouseX},{mouseY}"],
            'keyCycles': keyCycles,
            'mouseCycles': [random.randint(35, 95)],
            'touchCycles': [],
            'width': width, 'height': height,
            'totalFocusTime': totalFocus + random.randint(300, 1800),
            'checksum': checksum,
            'prefilled': False,
        }


    #//! -------------------- Utilities -------------------- !\\#
    @staticmethod
    def __generateLsUbid() -> str:
        # Sticky per-account — localStorage ubid never changes mid-session
        cached = FwcimAmazonSxgitario._session_ls_ubid
        if cached:
            return cached
        part1 = f"{random.randint(100, 999)}"
        part2 = f"{random.randint(1000000, 9999999)}"
        part3 = f"{random.randint(1000000, 9999999)}"
        val   = f"{part1}-{part2}-{part3}:{int(time.time())}"
        FwcimAmazonSxgitario._session_ls_ubid = val
        return val

    def __encodeMetadata1(self, fingerprint: dict) -> str:
        jsonStr   = json.dumps(fingerprint, separators=(',', ':'))
        crc       = format(zlib.crc32(jsonStr.encode('utf-8')) & 0xFFFFFFFF, '08X')
        payload   = f"{crc}#{jsonStr}"
        encrypted = self.__xxteaEncrypt(payload, self.__KEY_MATERIAL)
        b64       = self.__base64Encode(encrypted)
        return f"{self.__KEY_IDENTIFIER}:{b64}"

    def __xxteaEncrypt(self, data: str, key: list) -> str:
        if len(data) == 0:
            return ''
        n = math.ceil(len(data) / 4)
        v = []
        for i in range(n):
            word = 0
            for j in range(4):
                idx = i * 4 + j
                if idx < len(data):
                    word |= ord(data[idx]) << (j * 8)
            v.append(word)
        n      = len(v)
        rounds = 6 + 52 // n
        total  = 0
        z      = v[n - 1]
        for _ in range(rounds):
            total = (total + self.__XXTEA_DELTA) & 0xFFFFFFFF
            e     = (total >> 2) & 3
            for p in range(n):
                y     = v[(p + 1) % n]
                mx    = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((total ^ y) + (key[(p & 3) ^ e] ^ z))
                v[p]  = (v[p] + mx) & 0xFFFFFFFF
                z     = v[p]
        result = []
        for word in v:
            for j in range(4):
                result.append(chr((word >> (j * 8)) & 0xFF))
        return ''.join(result)

    @staticmethod
    def __base64Encode(data: str) -> str:
        return base64.b64encode(data.encode('latin-1')).decode('utf-8')

    @classmethod
    def pick_session_hw(
        cls,
        *,
        marketplace: str = "",
        user_agent:  str = "",
        location:    str = "",
        timezone:    int = None,
        canvas_strategy: str = "",
    ) -> dict:
        """Pre-pick sticky HW without generating a full metadata1 (~0ms)."""
        gen = cls(
            location=location or "https://www.amazon.com/ap/register",
            userAgent=user_agent or "",
            marketplace=(marketplace or "").upper(),
            timezone=timezone,
            canvasStrategy=canvas_strategy or "",
        )
        p      = gen.__profile
        screen = p.get("screen") or {}
        return {
            "canvas_strategy": gen.last_canvas_strategy,
            "timezone": gen.__timezone,
            "hw": {
                "width":        int(screen.get("width")       or 1920),
                "height":       int(screen.get("height")      or 1080),
                "availHeight":  int(screen.get("availHeight") or 1040),
                "dpr":          float(p.get("dpr")            or 1.0),
                "deviceMemory": min(8, int(p.get("deviceMemory") or 8)),
                "gpuModel":     p.get("gpuModel") or "",
                "screenInfo":   p.get("screenInfo") or "",
            },
        }
