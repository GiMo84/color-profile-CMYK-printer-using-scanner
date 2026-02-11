#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
from pathlib import Path

# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def load_cal_curve(cal_file, channel):
    """
    Reads an Argyll .cal file and extracts the device curve
    for a given channel.

    Returns:
        I: nominal input levels [0..1]
        O: output density proxy [0..1]
    """
    I = []
    O = []

    with open(cal_file, "r") as f:
        active = False
        for line in f:
            if line.startswith(f"BEGIN_DATA_{channel.upper()}"):
                active = True
                continue
            if line.startswith("END_DATA"):
                active = False
            if active:
                a, b = line.split()
                I.append(float(a))
                O.append(float(b))

    return np.array(I), np.array(O)


def gamma_fit(I, O):
    """
    Fits O = I^g in log domain.
    """
    mask = (I > 1e-4) & (O > 1e-4)
    x = np.log(I[mask])
    y = np.log(O[mask])
    g = np.polyfit(x, y, 1)[0]
    return g


def linear_slope(I, O):
    """
    Fits O = s*I + b, returns slope s.
    """
    s, _ = np.polyfit(I, O, 1)
    return s


# ------------------------------------------------------------
# Analysis per channel
# ------------------------------------------------------------

def analyze_light_channel(name, I, O, light_value, light_trans):
    """
    Analyze a channel with light ink (C/M).
    """

    T_eff = light_value * light_trans

    dark_mask = (I > 0.05) & (I < 0.6 * T_eff)
    light_mask = (I > T_eff + 0.05) & (I < 0.95)

    Id, Od = I[dark_mask], O[dark_mask]
    Il, Ol = I[light_mask], O[light_mask]

    g_dark = gamma_fit(Id, Od)
    s_dark = linear_slope(Id, Od)
    s_light = linear_slope(Il, Ol)

    light_value_est = s_light / s_dark

    return {
        "gamma_dark": g_dark,
        "s_dark": s_dark,
        "s_light": s_light,
        "light_value_est": light_value_est,
        "Id": Id,
        "Od": Od,
        "Il": Il,
        "Ol": Ol,
    }


def analyze_dark_channel(name, I, O):
    """
    Analyze Y or K (no light ink).
    """
    mask = (I > 0.05) & (I < 0.95)
    g = gamma_fit(I[mask], O[mask])
    return {"gamma": g}


# ------------------------------------------------------------
# Plotting
# ------------------------------------------------------------

def plot_channel(name, I, O, result, outdir):
    plt.figure(figsize=(6, 5))
    plt.plot(I, O, "k.", label="Measured")

    if "Id" in result:
        Id, Od = result["Id"], result["Od"]
        Il, Ol = result["Il"], result["Ol"]

        g = result["gamma_dark"]
        s_dark = result["s_dark"]
        s_light = result["s_light"]

        I_fit = np.linspace(Id.min(), Id.max(), 200)
        plt.plot(I_fit, I_fit ** g, "r-", label=f"Dark gamma fit (g={g:.2f})")

        I_fit = np.linspace(Il.min(), Il.max(), 200)
        plt.plot(I_fit, s_light * I_fit, "b-", label="Light slope fit")

    else:
        g = result["gamma"]
        I_fit = np.linspace(0.01, 1.0, 200)
        plt.plot(I_fit, I_fit ** g, "r-", label=f"Gamma fit (g={g:.2f})")

    plt.xlabel("Nominal input")
    plt.ylabel("Argyll device output")
    plt.title(name)
    plt.legend()
    plt.grid(True)

    out = Path(outdir) / f"{name}.png"
    plt.savefig(out, dpi=150)
    plt.close()


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cal", required=True, help="Argyll .cal file")
    #ap.add_argument("--params", required=True, help="JSON with current Gutenprint params")
    ap.add_argument("--out", default="diagnostics", help="Output directory")
    args = ap.parse_args()

    #with open(args.params) as f:
    #    params = json.load(f)
    params = {"LightCyanValue": 0.35, "LightCyanTrans": 0.5,
              "LightMagentaValue": 0.33, "LightMagentaTrans": 0.5}

    Path(args.out).mkdir(exist_ok=True)

    results = {}

    # Light ink channels
    for ch, light in [("C", "LightCyan"), ("M", "LightMagenta")]:
        I, O = load_cal_curve(args.cal, ch)

        res = analyze_light_channel(
            ch,
            I,
            O,
            params[f"{light}Value"],
            params[f"{light}Trans"],
        )

        results[ch] = res
        plot_channel(ch, I, O, res, args.out)

    # Y and K
    for ch in ["Y", "K"]:
        I, O = load_cal_curve(args.cal, ch)
        res = analyze_dark_channel(ch, I, O)
        results[ch] = res
        plot_channel(ch, I, O, res, args.out)

    # Print numeric summary
    print("\n=== Suggested first-run adjustments ===\n")

    for ch in ["C", "M"]:
        r = results[ch]
        print(f"{ch}:")
        print(f"  Dark gamma multiplier ≈ {1/r['gamma_dark']:.3f}")
        print(f"  LightValue estimate   ≈ {r['light_value_est']:.3f}")
        print()

    for ch in ["Y", "K"]:
        r = results[ch]
        print(f"{ch}:")
        print(f"  Gamma multiplier ≈ {1/r['gamma']:.3f}")
        print()


if __name__ == "__main__":
    main()
