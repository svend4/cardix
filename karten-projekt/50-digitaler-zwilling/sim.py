#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Digitaler Zwilling v0.2 — Lieferung aus Vending-Automaten.

Nur Python-Standardbibliothek. Läuft auch in Termux.
Alle Zahlen sind ANNAHMEN und müssen mit einem echten Pilot abgeglichen werden.

Aufruf:
    python3 sim.py                # Standardszenarien
    python3 sim.py --rate 6 --base 1 --extra 1 --trigger 3 --hold 5 --rain
"""
import argparse
import random
import statistics


def run(seed, rate_min=12, rain=True, base=1, extra=1, trigger=3, hold=5,
        batch=3, hours=8, p_late=0.10, p_forgot=0.05, p_empty=0.03):
    rnd = random.Random(seed)

    # 1. Bestellungen
    t, ok = 0.0, []
    while t < hours * 60:
        t += rnd.expovariate(1 / rate_min)
        if rnd.random() >= p_empty:          # Fach leer -> Bestellung fällt aus
            ok.append(t)

    # 2. Roboter legt die Ware ins Ausgabefach
    robot_free, ready = 0.0, []
    for ot in ok:
        start = max(ot, robot_free)
        robot_free = start + rnd.uniform(0.5, 1.5)
        ready.append((ot, robot_free))

    # 3. Kuriere (Basis + Abruf bei Warteschlange)
    free = [0.0] * (base + extra)
    waits, trips, called, i = [], 0, 0, 0
    while i < len(ready):
        first = ready[i][1]
        depart_base = max(first, min(free[:base]))
        queue = sum(1 for _, rd in ready[i:] if rd <= depart_base)
        pool = list(range(base))
        if extra and queue >= trigger:
            pool = list(range(base + extra))
            called += 1
        c = min(pool, key=lambda j: free[j])
        depart = max(first, free[c])

        group, j = [ready[i]], i + 1          # Bündeln bis 'batch', max. 'hold' Minuten warten
        while j < len(ready) and len(group) < batch and ready[j][1] <= depart + hold:
            group.append(ready[j])
            j += 1
        depart = max(depart, group[-1][1])

        if rnd.random() < p_late:             # Störung: Kurier verspätet
            depart += rnd.uniform(5, 12)
        if rnd.random() < p_forgot:           # Störung: Code vergessen
            depart += 3

        ride = rnd.uniform(8, 15) * (1.4 if rain else 1.0)
        for ot, _ in group:
            waits.append(depart + ride - ot)
        free[c] = depart + ride * 2
        trips += 1
        i = j

    return {
        "orders": len(ok),
        "wait_mean": statistics.mean(waits) if waits else 0.0,
        "wait_max": max(waits) if waits else 0.0,
        "trips": trips,
        "called": called,
    }


def summary(label, runs=40, **kw):
    res = [run(s, **kw) for s in range(runs)]
    avg = lambda k: statistics.mean(r[k] for r in res)
    print(f"{label}: Wartezeit Ø {avg('wait_mean'):.0f} min, max {avg('wait_max'):.0f} min, "
          f"Fahrten {avg('trips'):.0f} für {avg('orders'):.0f} Bestellungen, "
          f"Zweiter gerufen {avg('called'):.0f}x")


def main():
    p = argparse.ArgumentParser(description="Digitaler Zwilling Vending-Lieferung")
    p.add_argument("--rate", type=float, help="Minuten zwischen Bestellungen")
    p.add_argument("--base", type=int, default=1)
    p.add_argument("--extra", type=int, default=1)
    p.add_argument("--trigger", type=int, default=3)
    p.add_argument("--hold", type=float, default=5)
    p.add_argument("--rain", action="store_true")
    a = p.parse_args()

    if a.rate:
        summary("Eigenes Szenario", rate_min=a.rate, base=a.base, extra=a.extra,
                trigger=a.trigger, hold=a.hold, rain=a.rain)
        return

    print("--- normal, alle 12 min, Regen ---")
    summary("1 Kurier", extra=0)
    summary("1 + Abruf ab 3", extra=1, trigger=3)
    print("--- Spitze, alle 6 min, Regen ---")
    summary("1 Kurier", rate_min=6, extra=0)
    summary("1 + Abruf ab 3", rate_min=6, extra=1, trigger=3)
    summary("2 fest", rate_min=6, base=2, extra=0)


if __name__ == "__main__":
    main()
