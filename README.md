# I2C Sensors Visualizing Script

## About

The script allows to plot graphs using CSV output from I2C Sensor Test Script.

## Run

The tool can be run from the repository root using `run.ps1` or `run` scripts in Windows PowerShell or Bash. But first, setup virtual environment. For example, in PowerShell:
```
git clone https://github.com/condevtion/i2cs-graph.git
cd i2cs-graph
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r .\requirements\prod.txt
```

Let's assume that you have data from an i2cs-test utility run in `day.csv` (with `--csv` flag you can get CSV formatted data). To visualize them split into three dedicated charts - atmospheric, light, and color just run:
```
.\run.ps1 day.csv
```

<img width="640" height="523" alt="i2cs-graph-split" src="https://github.com/user-attachments/assets/3654a027-3c8e-48d7-a62e-eba340df56a5" />

or if you want to put all together in one chart add `--combined` option:
```
.\run.ps1 --combined day.csv
```

<img width="640" alt="i2cs-graph-combined" src="https://github.com/user-attachments/assets/61ce81fe-600b-4c1e-a5d7-29d5efc64dd2" />
