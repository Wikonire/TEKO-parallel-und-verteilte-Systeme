# π-Berechnung mit Leibniz-Reihe (parallel)

## Projektstruktur
```
pi-project/
├── code/           ← Python-Code
│   └── pi.py
├── doc/            ← Dokumentation & Diagramme
│   ├── README.md
│   └── architecture.puml
└── images/         ← (optionale PNGs)
```

## Installation
- Python 3.8+
- ssh‑Zugriff auf entfernte Hosts (für `--hosts`)

## Nutzung
```bash
cd code
python3 pi.py [Modus] --seg-size 1000000
```
**Modi**
- `--with-gil`
- `--with-thread`
- `--with-proces`
- `--pool N`
- `--hosts host1,host2,...`

Beispiel, 4‑Prozess-Pool mit Seggröße 500 000:
```bash
python3 pi.py --pool 4 --seg-size 500000
```

Verteilte Ausführung:
```bash
python3 pi.py --hosts a.example.com,b.example.com --seg-size 1000000
```

## Architektur
Siehe `architecture.puml` im PlantUML‑Format im `doc/`‑Ordner.

## Tipps zur Optimierung
- Erhöhe `--seg-size`, um Overhead zu reduzieren.
- Pool‑Variante in der Regel am schnellsten.
- SSH‑Modus abhängig von Netzwerk‑Latenz.
