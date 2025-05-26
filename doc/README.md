# π-Berechnung mit Leibniz-Reihe (parallel)

## Voraussetzungen
Aktiviere die virtuelle Python-Umgebung 

vom README aus: 
```shell
 cd ../ && source  venv/bin/activate
```
Vom Root aus: 
```shell
 source  venv/bin/activate
```
## Test starten
````shell
 cd ../ && source  venv/bin/activate
 pytest -v
````

## Coverage Tests starten (vorher)
````shell
 cd ../ && source  venv/bin/activate
 pip install pytest-cov
 pytest --cov-report term-missing --cov=pi code/test_pi.py
````



## Projektstruktur
```
pi-project/
├── code/           ← Python-Code und Dockeeerfiles
│   └── ....
├── doc/            ← Dokumentation & README
│   ├── ....
└── images/         ← Generierte Statistik-Images
```

## Installation
- Python 3.10+
- ssh‑Zugriff auf entfernte Hosts (für `--hosts`)

## Nutzung
```bash
cd code
python3 pi.py [Modus] --seg-size 1000000
```
**Modi**
- `--with-gil` Berechnet π mithilfe einfacher Python-Threads. (Wenig effektiv, da Python Threads wegen des GIL nicht parallel rechnen.)
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


# Aufgabenerfüllung: 
Diese Tabelle zeigt übersichtlich und nachvollziehbar, wo und wie jedes Feature im Projekt umgesetzt wurde.

| Feature                                              | Punkte | Erfüllt? | Argumente & Erläuterungen                                                                                                       |
|------------------------------------------------------|--------|----------|---------------------------------------------------------------------------------------------------------------------------------|
| calc pi with k GIL threads                           | 3.5    | Ja       | Methode `mode_gil()` nutzt Python-Threads (`threading.Thread`), erfüllt explizit die GIL-Anforderung.                           |
| calc pi with k parallel (non-GIL) threads            | 0.2    | Ja       | Methode `mode_threadpool()` nutzt `ThreadPoolExecutor` zur parallelen Thread-Ausführung.                                        |
| calc pi with k processes                             | 0.2    | Ja       | Methode `mode_process()` nutzt separate Prozesse (`multiprocessing.Process`), klare parallele Prozess-Verarbeitung.             |
| producer/consumer architecture                       | 0.5    | Ja       | Methode `producer_consumer()` realisiert Producer-Consumer-Pattern mit Queue (`queue.Queue`) und Threads.                       |
| producer/consumer architecture mit map/filter/reduce | 0.5    | Ja       | Explizite Verwendung von `map()`, `filter()`, `reduce()` in `producer_consumer()`. Sichtbar im Code: Zeilen 135–137 (`pi.py`).  |
| using a thread pool                                  | 0.2    | Ja       | Methode `mode_pool()` verwendet `multiprocessing.Pool` zur Prozessverwaltung.                                                   |
| timing and error data                                | 0.2    | Ja       | Skript `stats_pi.py` misst explizit Laufzeit, Fehler und statistische Werte und visualisiert diese mittels Matplotlib-Grafiken. |
| calc pi with k processes on n hosts                  | 1.0    | Ja       | Methode `mode_hosts()` nutzt verteilte Berechnung über SSH (Docker-Container) und subprocess (`subprocess.check_output()`).     |
| complete set of image/sketch for architecture        | 0.2    | Ja       | Statistikgrafiken durch `stats_pi.py` als PNG-Dateien generiert und gespeichert (z.B. in `doc/`).                               |
| Documentation API                                    | 0.2    | Ja       | Klar strukturierter Code mit Logging & dokumentierter Argumentparser; README-Datei mit Nutzungsanleitung.                       |


