#!/usr/bin/env python3
from generate_fingerprint import collect_fingerprint, encode_metadata1, PROFILES, detect_profile

def generate_metadata1(
    email=None,
    password=None,
    name=None,
    password_check=None,
    otp=None,
    user_agent=None,
    referrer=None,
    location=None,
    timezone=None,
    html_b64=None,
    dwell_ms=None,
    session_id=None,
):
    fp = collect_fingerprint(
        email=email,
        password=password,
        name=name,
        password_check=password_check,
        otp=otp,
        user_agent=user_agent,
        referrer=referrer,
        location=location,
        time_zone=timezone,
        html_b64=html_b64,
        dwell_ms=dwell_ms,
        session_id=session_id,
    )
    m1 = encode_metadata1(fp)
    pn = "custom"
    if user_agent:
        p = detect_profile(user_agent)
        for k, v in PROFILES.items():
            if v is p: 
                pn = k
                break
    return {"metadata1": m1, "fingerprint": fp, "profile": pn}

def generate_fingerprint(
    email=None, 
    password=None, 
    name=None, 
    password_check=None, 
    otp=None,
    user_agent=None, 
    referrer=None, 
    location=None, 
    timezone=None, 
    html_b64=None,
    dwell_ms=None
):
    return collect_fingerprint(
        email=email, 
        password=password, 
        name=name, 
        password_check=password_check, 
        otp=otp, 
        user_agent=user_agent, 
        referrer=referrer, 
        location=location, 
        time_zone=timezone, 
        html_b64=html_b64,
        dwell_ms=dwell_ms
    )
