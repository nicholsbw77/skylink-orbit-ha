#!/usr/bin/env python3
"""
Standalone test for the Skylink Orbit API.
Tests different request formats to find what the server accepts.
"""

import hashlib
import json
import re
import ssl
import sys
import urllib.request
import urllib.parse
import time


BASE_URL = "https://iot.skyhm.net:8444/skylinkhub_crm/skyhm_api_s.jsp"
SIGNING_SECRET = "+8uHDSF77ueRmLlKkl67"


def make_signature(cmd, data, timestamp):
    raw = f"{timestamp}+{cmd}+{data}{SIGNING_SECRET}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().lower()


def api_request(cmd, body, req_data):
    """POST with JSON body. Returns (status, raw_body)."""
    timestamp = str(int(time.time() * 1000))
    signature = make_signature(cmd, req_data, timestamp)
    url = f"{BASE_URL}?cmd={cmd}"
    body_bytes = json.dumps(body).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "User-Agent": "Orbit/3.4 (iPhone; iOS 18.3; Scale/3.00)",
        "REQ-CMD": cmd,
        "REQ-DATA": req_data,
        "REQ-TIMESTAMP": timestamp,
        "REQ-SIGNATURE": signature,
    }

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            raw = resp.read()
            return resp.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, raw
    except Exception as e:
        return -1, str(e)


def api_request_form(cmd, form_data, req_data):
    """POST with form-encoded body. Returns (status, raw_body)."""
    timestamp = str(int(time.time() * 1000))
    signature = make_signature(cmd, req_data, timestamp)
    url = f"{BASE_URL}?cmd={cmd}"
    body_bytes = urllib.parse.urlencode(form_data).encode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "User-Agent": "Orbit/3.4 (iPhone; iOS 18.3; Scale/3.00)",
        "REQ-CMD": cmd,
        "REQ-DATA": req_data,
        "REQ-TIMESTAMP": timestamp,
        "REQ-SIGNATURE": signature,
    }

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            raw = resp.read()
            return resp.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, raw
    except Exception as e:
        return -1, str(e)


def parse_response(body):
    cleaned = body.strip().lstrip("\ufeff").strip()
    cleaned = re.sub(r':(0\d+)([,}\]\s])', r':"\1"\2', cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def test(label, cmd, body, req_data, form=False):
    print(f"  [{label}]")
    print(f"    REQ-DATA: {req_data}")
    print(f"    Body:     {json.dumps(body)}")
    if form:
        status, raw = api_request_form(cmd, body, req_data)
    else:
        status, raw = api_request(cmd, body, req_data)
    data = parse_response(raw)
    result = str(data.get("result", "")) if data else "?"
    hub_id = data.get("hub_id", "") if data else ""
    if hub_id or (result in ("0", "00")):
        print(f"    >>> SUCCESS! result={result}")
        print(f"    Response: {json.dumps(data, indent=6)}")
    else:
        msg = data.get("message", raw[:80]) if data else raw[:80]
        print(f"    FAILED result={result}: {msg}")
    print()
    return data


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <email> <password> [hub_ids]")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    hub_ids = sys.argv[3].split(",") if len(sys.argv) > 3 else []

    print("=" * 60)
    print("Skylink Orbit API Test v2")
    print("=" * 60)

    # --- Login ---
    print("\n--- act_login ---")
    login_body = {"app_sys": "apns", "username": email, "password": password, "app_brand": "00"}
    data = test("login", "act_login", login_body, email)
    if not data or str(data.get("result", "")) not in ("0", "00"):
        print("Login failed.")
        sys.exit(1)

    acc_no = data.get("acc_no", "")
    print(f"  acc_no={acc_no}  alias={data.get('alias_name', '')}\n")

    hub_id = hub_ids[0].strip() if hub_ids else ""
    if not hub_id:
        print("No hub IDs provided.")
        sys.exit(0)

    # --- hub_add: try different REQ-DATA values ---
    print("=" * 60)
    print(f"hub_add tests for: {hub_id}")
    print("=" * 60)

    body_basic = {"hub_id": hub_id, "username": email}
    body_full = {"hub_id": hub_id, "username": email, "acc_no": acc_no}
    body_app = {"hub_id": hub_id, "username": email, "app_sys": "apns", "app_brand": "00"}
    body_min = {"hub_id": hub_id}

    # Vary REQ-DATA
    print("\n--- Vary REQ-DATA header ---")
    test("REQ-DATA=email, body=hub_id+username", "hub_add", body_basic, email)
    test("REQ-DATA=hub_id, body=hub_id+username", "hub_add", body_basic, hub_id)
    test("REQ-DATA=acc_no, body=hub_id+username", "hub_add", body_basic, acc_no)
    test("REQ-DATA=hub_id, body=hub_id only", "hub_add", body_min, hub_id)
    test("REQ-DATA=hub_id, body=full", "hub_add", body_full, hub_id)
    test("REQ-DATA=acc_no, body=full", "hub_add", body_full, acc_no)
    test("REQ-DATA=email, body=app-style", "hub_add", body_app, email)
    test("REQ-DATA=hub_id, body=app-style", "hub_add", body_app, hub_id)

    # Try form-encoded instead of JSON
    print("--- Try form-encoded body ---")
    test("FORM: REQ-DATA=email", "hub_add", body_basic, email, form=True)
    test("FORM: REQ-DATA=hub_id", "hub_add", body_basic, hub_id, form=True)

    # Try with password in body
    print("--- Try with password ---")
    body_pwd = {"hub_id": hub_id, "username": email, "password": password}
    test("REQ-DATA=email, +password", "hub_add", body_pwd, email)
    test("REQ-DATA=hub_id, +password", "hub_add", body_pwd, hub_id)

    # Try hub_event_log (might give us hub info)
    print("--- hub_event_log ---")
    test("REQ-DATA=email", "hub_event_log", {"hub_id": hub_id, "username": email}, email)
    test("REQ-DATA=hub_id", "hub_event_log", {"hub_id": hub_id, "username": email}, hub_id)

    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
