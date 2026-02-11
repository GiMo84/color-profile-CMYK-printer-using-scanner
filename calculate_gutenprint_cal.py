import click
import numpy as np
import math
from scipy.optimize import curve_fit
import re

# --- Constants & Defaults ---
# Standard starting points for Gutenprint
DEFAULT_PARAMS = {
    'CyanGamma': 1.0, 'CyanDensity': 1.0,
    'LightCyanValue': 0.35, 'LightCyanScale': 1.0, 'LightCyanTrans': 0.6,
    
    'MagentaGamma': 1.0, 'MagentaDensity': 1.0,
    'LightMagentaValue': 0.35, 'LightMagentaScale': 1.0, 'LightMagentaTrans': 0.6,
    
    'YellowGamma': 1.0, 'YellowDensity': 1.0,
    
    'BlackGamma': 1.0, 'BlackDensity': 1.0,
    
    'CompositeGamma': 1.0
}

# Channel Mapping in .cal file
# Index 0=Input, 1=C, 2=M, 3=Y, 4=K
CHAN_IDX = {'Cyan': 1, 'Magenta': 2, 'Yellow': 3, 'Black': 4}

# --- Parsing Logic ---

def parse_cal_file(filepath):
    """
    Parses an Argyll .cal file.
    Returns two dictionaries:
      - curves: {channel_idx: (input_array, output_array)}
      - de_resp: {channel_idx: (input_array, de_array)}
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    curves = {}
    de_resp = {}
    
    # Locate Data Blocks
    in_curves = False
    in_de = False
    
    data_curves = []
    data_de = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check descriptors to switch modes
        if 'DESCRIPTOR "Argyll Device Calibration Curves"' in line:
            in_curves = False; in_de = False # Wait for BEGIN_DATA
        if 'DESCRIPTOR "Argyll Output Calibration Expected DE Response"' in line:
            in_curves = False; in_de = False
            
        if line.startswith("BEGIN_DATA"):
            # Check which block we are entering based on previous headers
            # A bit heuristics: look at the last descriptor or assumes order
            # Safer: check previous lines or just check context. 
            # We'll use a state flag triggered by the DESCRIPTOR.
            pass 
        
        # Actually, simpler: The blocks are separated by DESCRIPTOR.
        # Let's re-parse simply.
    
    # Robust Block Parser
    current_block = None
    
    for line in lines:
        line = line.strip()
        if 'DESCRIPTOR "Argyll Device Calibration Curves"' in line:
            current_block = 'CURVES'
            continue
        elif 'DESCRIPTOR "Argyll Output Calibration Expected DE Response"' in line:
            current_block = 'DE'
            continue
        elif line.startswith("BEGIN_DATA"):
            continue
        elif line.startswith("END_DATA_FORMAT"):
            continue
        elif line.startswith("END_DATA"):
            current_block = None
            continue
        elif line.startswith("CAL") or line.startswith("Originator") or line.startswith("Created"):
            continue
            
        # Parse Data
        if current_block and line and line[0].isdigit():
            parts = [float(x) for x in line.split()]
            if current_block == 'CURVES':
                data_curves.append(parts)
            elif current_block == 'DE':
                data_de.append(parts)

    # Convert to Numpy
    dc = np.array(data_curves)
    dde = np.array(data_de)

    # Structure Data
    # Columns: 0=Input, 1=C, 2=M, 3=Y, 4=K
    if dc.size > 0:
        inp = dc[:,0]
        for name, i in CHAN_IDX.items():
            curves[name] = (inp, dc[:,i])
            
    if dde.size > 0:
        inp = dde[:,0]
        for name, i in CHAN_IDX.items():
            de_resp[name] = (inp, dde[:,i])
            
    return curves, de_resp

# --- Analysis Models ---

def fit_gamma(x, y):
    """
    Fits y = x^g.
    Returns g.
    """
    def func(x, g):
        return x**g
    
    # Avoid zero errors
    x_clean = x + 1e-6
    y_clean = y + 1e-6
    
    try:
        popt, _ = curve_fit(func, x_clean, y_clean, p0=[1.0])
        return popt[0]
    except:
        return 1.0

def analyze_light_ink(inp, curve, de_curve, current_val, current_trans):
    """
    Estimates corrections for LightCyanValue/LightCyanTrans based on the curve shape.
    
    Logic:
    - The .cal curve corrects the printer.
    - If Curve < Input (Bowing Down) in highlights: Printer is too dark. Light Ink Value should be HIGHER (lighter definition).
    - If Curve > Input (Bowing Up) in highlights: Printer is too light. Light Ink Value should be LOWER (darker definition).
    """
    
    # 1. Analyze 0% to 50% range (Highlights/Light Ink zone)
    mask = inp <= 0.6
    x_part = inp[mask]
    y_part = curve[mask]
    
    # Calculate Area Under Curve Difference
    # Positive = Boosting (Need more ink -> Decrease Value)
    # Negative = Cutting (Need less ink -> Increase Value)
    diff = y_part - x_part
    avg_diff = np.mean(diff)
    
    # Tuning Sensitivity
    # A diff of 0.1 is huge. 
    val_correction = avg_diff * -0.8 # Invert sign
    
    new_val = current_val + val_correction
    new_val = max(0.1, min(0.9, new_val)) # Clamp
    
    # 2. Analyze Transition (Smoothness)
    # Look for inflection points in the DE curve derivative
    # If derivative spikes, the transition is rough.
    # This is complex to automate blindly, we'll use a simple heuristic on the curve bump.
    
    # If there is a sharp correction "S-curve" around 0.4-0.6, adjust Trans.
    # For now, we will keep Trans static unless Value hits limits.
    
    return new_val

def analyze_density(inp, de_curve):
    """
    Check for saturation.
    If DE curve plateaus before 1.0, Density is too high.
    """
    # Look at slope of last 10%
    mask = inp > 0.9
    if len(de_curve[mask]) < 2: return 1.0
    
    slope = (de_curve[-1] - de_curve[mask][0]) / (inp[-1] - inp[mask][0])
    
    # A healthy slope should be significant.
    # If slope is near zero, we are saturated.
    if slope < 10.0: # Arbitrary threshold for DE slope
        return 0.95 # Suggest reduction
    return 1.0 # Keep steady (or could suggest increase if very steep)

# --- Main Processor ---

@click.command()
@click.argument('cal_files', nargs=-1, type=click.Path(exists=True))
def process(cal_files):
    """
    Calculates Gutenprint XML parameters from Argyll .cal files.
    Supports history: pass files in order (run1.cal run2.cal ...)
    to refine the estimation cumulatively.
    """
    
    if not cal_files:
        click.echo("Please provide at least one .cal file.")
        return

    # Start with defaults
    params = DEFAULT_PARAMS.copy()
    
    click.echo(f"Processing {len(cal_files)} file(s)...")
    
    for i, fpath in enumerate(cal_files):
        click.echo(f"  > Analyzing Run {i+1}: {fpath}")
        curves, de_resp = parse_cal_file(fpath)
        
        # --- Update Params based on this file ---
        
        # 1. Update Gammas
        for color in ['Cyan', 'Magenta', 'Yellow', 'Black']:
            if color in curves:
                inp, out = curves[color]
                
                # Fit the correction gamma
                g_corr = fit_gamma(inp, out)
                
                # Update Cumulative Gamma
                # If .cal says "Apply x^0.5", and we currently have Gamma 1.0
                # New Gamma = 1.0 * 0.5 = 0.5.
                params[f'{color}Gamma'] *= g_corr
                
        # 2. Update Composite Gamma
        # Average of CMY gammas from the file
        g_c = fit_gamma(curves['Cyan'][0], curves['Cyan'][1])
        g_m = fit_gamma(curves['Magenta'][0], curves['Magenta'][1])
        g_y = fit_gamma(curves['Yellow'][0], curves['Yellow'][1])
        avg_g = (g_c + g_m + g_y) / 3.0
        params['CompositeGamma'] *= avg_g
        
        # 3. Update Light Ink Values (Cyan/Magenta only)
        for color in ['Cyan', 'Magenta']:
            if color in curves and color in de_resp:
                new_val = analyze_light_ink(
                    curves[color][0], 
                    curves[color][1], 
                    de_resp[color][1],
                    params[f'Light{color}Value'],
                    params[f'Light{color}Trans']
                )
                params[f'Light{color}Value'] = new_val
                
        # 4. Update Density (Saturation check via DE)
        for color in ['Cyan', 'Magenta', 'Yellow', 'Black']:
             if color in de_resp:
                 dens_mod = analyze_density(de_resp[color][0], de_resp[color][1])
                 params[f'{color}Density'] *= dens_mod

    # --- Output Result ---
    
    click.echo("\n" + "="*60)
    click.echo("CALCULATED GUTENPRINT PARAMETERS")
    click.echo("="*60)
    click.echo("Copy these values into your printer XML definition.\n")
    
    # Helper to print nicely
    def p_row(key, val, comment=""):
        click.echo(f"{key:<25} {val:<8.4f}  {comment}")

    click.echo("--- Cyan Channel ---")
    p_row("CyanDensity", params['CyanDensity'])
    p_row("CyanGamma", params['CyanGamma'])
    p_row("LightCyanValue", params['LightCyanValue'], "Lower=Uses More Light Ink")
    p_row("LightCyanScale", params['LightCyanScale'])
    p_row("LightCyanTrans", params['LightCyanTrans'])
    click.echo("")

    click.echo("--- Magenta Channel ---")
    p_row("MagentaDensity", params['MagentaDensity'])
    p_row("MagentaGamma", params['MagentaGamma'])
    p_row("LightMagentaValue", params['LightMagentaValue'], "Lower=Uses More Light Ink")
    p_row("LightMagentaScale", params['LightMagentaScale'])
    p_row("LightMagentaTrans", params['LightMagentaTrans'])
    click.echo("")

    click.echo("--- Yellow Channel ---")
    p_row("YellowDensity", params['YellowDensity'])
    p_row("YellowGamma", params['YellowGamma'])
    click.echo("")

    click.echo("--- Black Channel ---")
    p_row("BlackDensity", params['BlackDensity'])
    p_row("BlackGamma", params['BlackGamma'])
    click.echo("")
    
    click.echo("--- Global ---")
    p_row("CompositeGamma", params['CompositeGamma'])
    click.echo("="*60)

if __name__ == '__main__':
    process()