import os, sys, asyncio, threading, uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from amazon_v2 import create_account, COUNTRY_CONFIG

app = Flask(__name__, static_folder="static")
CORS(app)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/countries")
def countries():
    return jsonify([
        {"code": code, "domain": cfg["domain"]}
        for code, cfg in COUNTRY_CONFIG.items()
    ])


@app.route("/api/create", methods=["POST"])
def api_create():
    data = request.get_json(silent=True) or {}
    country = data.get("country", "US").upper()
    if country not in COUNTRY_CONFIG:
        return jsonify({"error": f"Invalid country: {country}"}), 400

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {"status": "queued", "result": None, "error": None}
    threading.Thread(target=_run_job, args=(job_id, country), daemon=True).start()
    return jsonify({"job_id": job_id, "status": "queued"})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


# ── Background async loop ────────────────────────────────────────────────────

jobs = {}
_loop = asyncio.new_event_loop()
threading.Thread(target=lambda: (_loop.run_forever()), daemon=True).start()


def _run_job(job_id, country_code):
    jobs[job_id]["status"] = "running"
    devnull = open(os.devnull, "w")
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = devnull
    sys.stderr = devnull
    try:
        future = asyncio.run_coroutine_threadsafe(create_account(country_code), _loop)
        account = future.result(timeout=300)
        if account:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result"] = {
                "email": account.email,
                "password": account.password,
                "name": account.name,
                "cookie": account.cookie,
            }
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "Account creation returned None"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)[:300]
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        devnull.close()


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
