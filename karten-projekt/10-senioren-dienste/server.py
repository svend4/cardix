#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Bestell-Server v0.1 fuer 10-senioren-dienste.

Nur Python-Standardbibliothek. Laeuft lokal, in Termux und auf Google Cloud Run.

Endpunkte:
  GET  /health                -> {"ok": true}
  GET  /katalog               -> der Katalog (nur aktive/draft Karten)
  POST /bestellung            -> {"kunde": "K-1234", "karten": ["sen-0001", "sen-0006"]}

Datenschutz: Es werden KEINE Namen, Adressen oder Gesundheitsdaten angenommen.
"kunde" ist ein Pseudonym-Code (K-0000 .. K-9999), die Zuordnung zur Person liegt
ausserhalb dieses Servers beim Pflegedienst.

ACHTUNG Cloud Run: Das Dateisystem ist fluechtig. bestellungen.jsonl ist nur fuer
lokale Tests. Fuer echten Betrieb: Firestore / Cloud Storage (Region europe-west3).
"""
import json
import os
import re
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
KATALOG_PATH = os.environ.get("KATALOG", os.path.join(HERE, "katalog-sen.json"))
STORE_PATH = os.environ.get("STORE", os.path.join(HERE, "bestellungen.jsonl"))
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")   # im Betrieb: eigene Domain
MAX_BODY = 4096
MAX_KARTEN = 10
RATE_WINDOW = 60          # Sekunden
RATE_MAX = 10             # Bestellungen pro Kunde und Fenster

KUNDE_RE = re.compile(r"^K-\d{4}$")


def load_katalog(path):
    with open(path, encoding="utf-8") as f:
        k = json.load(f)
    if k.get("format") != "karten-katalog":
        raise ValueError("format ist nicht karten-katalog")
    if str(k.get("version", "")).split(".")[0] != "0":
        raise ValueError("unbekannte Version")
    return k


KATALOG = load_katalog(KATALOG_PATH)
AKTIV = {c["id"]: c for c in KATALOG["cards"] if c.get("status") != "retired"}
_rate = {}


def rate_ok(kunde):
    now = time.time()
    hits = [t for t in _rate.get(kunde, []) if now - t < RATE_WINDOW]
    if len(hits) >= RATE_MAX:
        _rate[kunde] = hits
        return False
    hits.append(now)
    _rate[kunde] = hits
    return True


def validate(data):
    if not isinstance(data, dict):
        return "JSON-Objekt erwartet"
    extra = set(data) - {"kunde", "karten"}
    if extra:
        return "unbekannte Felder: " + ", ".join(sorted(extra))
    kunde = data.get("kunde")
    if not isinstance(kunde, str) or not KUNDE_RE.match(kunde):
        return "kunde muss K-0000 bis K-9999 sein"
    karten = data.get("karten")
    if not isinstance(karten, list) or not karten:
        return "karten muss eine nicht leere Liste sein"
    if len(karten) > MAX_KARTEN:
        return "zu viele Karten"
    for k in karten:
        if k not in AKTIV:
            return "unbekannte oder ausgemusterte Karte: " + str(k)
    if len(set(karten)) != len(karten):
        return "Karte doppelt"
    # Regeln aus dem Kern: excludes / requires
    for k in karten:
        rel = AKTIV[k].get("relations", {})
        for x in rel.get("excludes", []):
            if x in karten:
                return f"{k} und {x} schliessen sich aus"
        for r in rel.get("requires", []):
            if r not in karten:
                return f"{k} braucht {r}"
    return None


def notify(order):
    # Platzhalter: hier spaeter E-Mail / Messenger an den Dienst.
    print("NEUE BESTELLUNG", json.dumps(order, ensure_ascii=False), file=sys.stderr, flush=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "KartenServer/0.1"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):   # keine IP-Adressen ins Log
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})
        if self.path == "/katalog":
            k = dict(KATALOG)
            k["cards"] = list(AKTIV.values())
            return self._send(200, k)
        self._send(404, {"error": "nicht gefunden"})

    def do_POST(self):
        if self.path != "/bestellung":
            return self._send(404, {"error": "nicht gefunden"})
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            return self._send(415, {"error": "Content-Type application/json erwartet"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send(400, {"error": "Content-Length ungueltig"})
        if n <= 0 or n > MAX_BODY:
            return self._send(413, {"error": "Anfrage zu gross oder leer"})
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._send(400, {"error": "kein gueltiges JSON"})
        err = validate(data)
        if err:
            return self._send(422, {"error": err})
        if not rate_ok(data["kunde"]):
            return self._send(429, {"error": "zu viele Bestellungen, bitte warten"})
        order = {
            "bestellung": uuid.uuid4().hex[:12],
            "zeit": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "kunde": data["kunde"],
            "karten": data["karten"],
            "nummern": [AKTIV[k]["n"] for k in data["karten"]],
            "woerter": [AKTIV[k]["word"] for k in data["karten"]],
        }
        try:
            with open(STORE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(order, ensure_ascii=False) + "\n")
        except OSError:
            return self._send(500, {"error": "speichern fehlgeschlagen"})
        notify(order)
        self._send(201, {"ok": True, "bestellung": order["bestellung"], "nummern": order["nummern"]})


def main():
    port = int(os.environ.get("PORT", "8080"))   # Cloud Run setzt PORT
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Karten-Server auf Port {port}, {len(AKTIV)} Karten", file=sys.stderr, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
