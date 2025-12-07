# Color-profile a CMYK printer using a scanner

**Semi-automated workflow to create CMYK printer ICC profiles using a calibrated flatbed scanner (poor man’s colorimeter).**  
*Built around ArgyllCMS, tailored for EpsonScan2.*

---

## 🎯 Overview

This repository contains a **semi-automated, reproducible workflow** for creating a **CMYK printer color profile** using:

- **ArgyllCMS** (targen, printtarg, scanin, colprof, xicclu)  
- A **flatbed scanner** (EpsonScan2 via command line)  
- A **scanner ICC file** (calibrating the scanner to act as a low-budget colorimeter)  

The resulting profile is good enough for hobby-level CMYK workflows when a spectrophotometer is unavailable.

The scripts here automate most steps of the profiling process, including:

- Generating CMYK patch sheets  
- Printing via CUPS  
- Scanning with EpsonScan2  
- Reading charts using scanin, including failure handling and manual fiducial correction  
- Iteratively tuning the black curve  
- Building the final ICC profile  

---

## ⚠️ Important notes

- A **scanner ICC profile must match your exact scanner & settings**.  
  - This repository includes **my scanner profile for the Epson XP-970** *(printer/scanner combo)*.  
  - **Other scanners or other Epson models require their own calibration.**  
- This workflow is **tailored to Epson scanners** via the `epsonscan2` command-line interface. If your scanner is different, replace 03_scan or drop the TIFF files for the various pages in `/scans`.
- The ICC you generate is as (in)accurate as your scanner calibration and your scanner. Also, your scanner isn't a colorimeter.

---

## 📁 Repository Contents

```
env.sh               # Environment configuration that **you** need to adjust
01_targen.sh         # Color patches and target generation (PS file)
02_print.sh          # Print PS file
03_scan.sh           # EpsonScan2 automated scanning + page counting
04_read_scan.sh      # Measure patches (scanin with fallback for manual fiducials)
05_blackprep.sh      # Preparation for creating a black generation curve
06_blacklimits.sh    # Aid plots for creating a black generation curve
07_blackcurve.sh     # Helper to iteratively tweak the black generation curve parameters
08_createprofile.sh  # Creates the profile
09_checkprofile.sh   # Checks the profile (currently: just plots the resulting black generation curve)

ScanSettings.SF2     # Example EpsonScan2 user setting file
K_CURVE.conf         # Persistently stores last black generation curve

/icc/                # Scanner calibration ICCs
/scans/              # Scanned TIFFs
README.md
```

---

## 🔧 Dependencies

### Required:

- Linux (tested on Ubuntu/Debian, should be portable)

- **ArgyllCMS**  
  - `targen`, `printtarg`, `scanin`, `colprof`, `xicclu`

- **EpsonScan2** (Linux version)

---

## 🧭 Quick Start

### 0. Edit `env.sh`
Adjust:

- `SESSION`
- `PRINTER_NAME`
- `SCAN_SETTING_FILE`
- the scanner ICC file path
- target ink/media settings

### 1. Generate test charts
```
./01_targen.sh
```

### 2. Print them
```
./02_print.sh
```

### 3. Scan
```
./03_scan.sh
```

Uses EpsonScan2; auto-detects number of pages from `.ps` file; prompts if needed.

### 4. Read scans with `scanin`
```
./04_read_scan.sh
```

If `scanin` fails:

- You are prompted to enter fiducial coordinates:  
  `X1,Y1,X2,Y2,X3,Y3,X4,Y4`  
- The script re-runs until successful (or `q` to quit).

### 5. Prepare preliminary profile for black generation curve
```
./05_blackprep.sh
```

### 6. Inspect black limits
```
./06_blacklimits.sh
```

Two `xicclu` windows appear (min/max black). Keep them open for reference.

### 7. Tune black generation curve interactively
```
./07_blackcurve.sh "-kp 0 0 0.86 0.75 0.55"
```

You can run this repeatedly until satisfied; for the meaning of these parameters, see the [ArgyllCMS guide](https://www.argyllcms.com/doc/Scenarios.html#PP6).
The chosen curve is saved to `K_CURVE.conf` and passed to the subsequent steps.

### 8. Create final ICC profile
```
./08_createprofile.sh
```

ICC output goes into the current directory.


### 9. Check the final ICC profile
```
./09_checkprofile.sh
```

For the moment, it just plots the final black generation curve.
