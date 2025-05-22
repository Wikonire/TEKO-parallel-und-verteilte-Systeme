import subprocess
import numpy as np
import argparse
import re
import matplotlib
matplotlib.use('Agg')  # nicht-interaktives Backend
import matplotlib.pyplot as plt

def run_pi_script(args, runs):
    pi_estimates, times, errors = [], [], []

    cmd = ["python", "code/pi.py"] + args

    for i in range(runs):
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = (result.stdout + result.stderr).strip()
        print(f"Run {i+1}: {output}")

        match = re.search(r"π≈(\d+\.\d+), Fehler=([\deE\-\+\.]+), Zeit=(\d+\.\d+)s", output)
        if match:
            pi_estimates.append(float(match.group(1)))
            errors.append(float(match.group(2)))
            times.append(float(match.group(3)))
        else:
            print(f"⚠️ Unerwartetes Ausgabeformat im Lauf {i+1}: {output}")

    return np.array(pi_estimates), np.array(errors), np.array(times)

def print_statistics(data, label):
    if data.size == 0:
        print(f"\n⚠️ Keine gültigen Daten für {label}.")
        return
    print(f"\nStatistiken für {label}:")
    print(f"  Mittelwert: {np.mean(data):.12f}")
    print(f"  Standardabweichung: {np.std(data):.12f}")
    print(f"  Minimum: {np.min(data):.12f}")
    print(f"  Maximum: {np.max(data):.12f}")

def plot_data(data, label, ylabel):
    plt.figure(figsize=(8, 4))
    plt.plot(data, marker='o', linestyle='-', color='b')
    plt.title(f'{label} über mehrere Läufe')
    plt.xlabel('Laufnummer')
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{label.replace(' ', '_').lower()}.png")

def main():
    parser = argparse.ArgumentParser(description="Statistiken für mehrfache π-Berechnung")
    parser.add_argument("--runs", type=int, default=10, help="Anzahl Durchläufe")
    parser.add_argument("--pi-args", type=str, default="--with-gil -i 1000000", help="Argumente für pi.py")
    args = parser.parse_args()

    pi_args_list = args.pi_args.split()

    pi_estimates, errors, times = run_pi_script(pi_args_list, args.runs)

    print_statistics(pi_estimates, "π-Schätzung")
    print_statistics(errors, "Fehler")
    print_statistics(times, "Ausführungszeit")

    if pi_estimates.size > 0:
        plot_data(pi_estimates, "Pi Schätzung", "π-Wert")
    if errors.size > 0:
        plot_data(errors, "Fehler", "Abweichung")
    if times.size > 0:
        plot_data(times, "Ausführungszeit", "Zeit (s)")

if __name__ == "__main__":
    main()
