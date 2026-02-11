import click
import numpy as np
from pathlib import Path

EPS = 1e-6


# ------------------------------------------------------------
# Parsing
# ------------------------------------------------------------

def parse_cal_blocks(path):
    blocks = {}
    current = None
    data = []

    with open(path) as f:
        for line in f:
            line = line.strip()

            if line.startswith("DESCRIPTOR"):
                current = line.split('"')[1]
                blocks[current] = []
                data = []

            elif line == "BEGIN_DATA":
                data = []

            elif line == "END_DATA":
                blocks[current] = np.array(data, dtype=float)

            elif current and line and not line.startswith("#"):
                try:
                    data.append([float(x) for x in line.split()])
                except ValueError:
                    pass

    return blocks


# ------------------------------------------------------------
# Estimators
# ------------------------------------------------------------

def estimate_gamma(I, O, weights=None):
    mask = (I > 0.05) & (I < 0.95)
    x = np.log(I[mask] + EPS)
    y = np.log(O[mask] + EPS)

    if weights is not None:
        w = weights[mask]
        return np.polyfit(x, y, 1, w=w)[0]
    return np.polyfit(x, y, 1)[0]


def estimate_density(O):
    return np.clip(1.0 / max(O[-1], EPS), 0.8, 1.2)


def estimate_transition(I, O):
    d2 = np.gradient(np.gradient(O))
    return float(I[np.argmax(d2)])


def estimate_light_scale(I, O, T):
    mask = (I > 0.05) & (I < T)
    return np.mean(O[mask] / (I[mask] + EPS))


def estimate_light_value(I, O, T):
    idx = np.argmin(np.abs(I - T))
    return O[idx] / (I[idx] + EPS)


def smooth(prev, new, alpha):
    return alpha * new + (1 - alpha) * prev


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

@click.command()
@click.argument("cal_files", type=click.Path(exists=True), nargs=-1)
@click.option("--alpha", default=0.4, help="Smoothing factor between runs")
def main(cal_files, alpha):
    params = {
        "LightCyanValue": 1.0,
        "LightCyanScale": 1.0,
        "LightCyanTrans": 0.5,
        "CyanGamma": 1.0,
        "CyanDensity": 1.0,

        "LightMagentaValue": 1.0,
        "LightMagentaScale": 1.0,
        "LightMagentaTrans": 0.5,
        "MagentaGamma": 1.0,
        "MagentaDensity": 1.0,

        "YellowGamma": 1.0,
        "YellowDensity": 1.0,

        "BlackGamma": 1.0,
        "BlackDensity": 1.0,

        "CompositeGamma": 1.0,
    }

    for run, cal in enumerate(cal_files, 1):
        blocks = parse_cal_blocks(cal)

        curves = blocks["Argyll Device Calibration Curves"]
        de = blocks["Argyll Output Calibration Expected DE Response"]

        I = curves[:, 0]

        weights = 1 / (1 + de[:, 1])  # cyan DE as proxy

        # Cyan
        C = curves[:, 1]
        T = estimate_transition(I, C)
        params["LightCyanTrans"] = smooth(params["LightCyanTrans"], T, alpha)
        params["LightCyanScale"] = smooth(params["LightCyanScale"], estimate_light_scale(I, C, T), alpha)
        params["LightCyanValue"] = smooth(params["LightCyanValue"], estimate_light_value(I, C, T), alpha)
        params["CyanGamma"] = smooth(params["CyanGamma"], estimate_gamma(I, C, weights), alpha)
        params["CyanDensity"] = smooth(params["CyanDensity"], estimate_density(C), alpha)

        # Magenta
        M = curves[:, 2]
        T = estimate_transition(I, M)
        params["LightMagentaTrans"] = smooth(params["LightMagentaTrans"], T, alpha)
        params["LightMagentaScale"] = smooth(params["LightMagentaScale"], estimate_light_scale(I, M, T), alpha)
        params["LightMagentaValue"] = smooth(params["LightMagentaValue"], estimate_light_value(I, M, T), alpha)
        params["MagentaGamma"] = smooth(params["MagentaGamma"], estimate_gamma(I, M, weights), alpha)
        params["MagentaDensity"] = smooth(params["MagentaDensity"], estimate_density(M), alpha)

        # Yellow
        Y = curves[:, 3]
        params["YellowGamma"] = smooth(params["YellowGamma"], estimate_gamma(I, Y), alpha)
        params["YellowDensity"] = smooth(params["YellowDensity"], estimate_density(Y), alpha)

        # Black
        K = curves[:, 4]
        params["BlackGamma"] = smooth(params["BlackGamma"], estimate_gamma(I, K), alpha)
        params["BlackDensity"] = smooth(params["BlackDensity"], estimate_density(K), alpha)

        # Composite gamma (CcMmY)
        gray = np.mean(curves[:, 1:4], axis=1)
        params["CompositeGamma"] = smooth(
            params["CompositeGamma"],
            estimate_gamma(I, gray),
            alpha,
        )

        click.echo(f"Processed run {run}: {Path(cal).name}")

    click.echo("\nEstimated Gutenprint parameters:\n")
    for k, v in params.items():
        click.echo(f"{k} = {v:.4f}")


if __name__ == "__main__":
    main()
