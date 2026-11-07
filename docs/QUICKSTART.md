# Run and understand this project

## Windows
Double-click `Start.cmd` from the repository folder with Python 3.13 installed. Or open PowerShell in this folder:
```powershell
py -3.13 launch.py
```
The launcher creates a local environment, installs tested direct dependencies and starts the dashboard. It does not require administrator access or PowerShell activation. Python 3.12 is also supported: `py -3.12 launch.py`. No system Python packages are modified.

## macOS / Linux
`python3.12 launch.py` (or python3.13).

## Checks and reproducible runs
- `python launch.py tests`: run offline tests, returning nonzero on failure.
- `python launch.py research`: run the default research CLI and save its log, changed output snapshots, commit ID and dependency versions under a unique `runs/` directory.
- Research flags are forwarded, e.g. `python launch.py research --help`. Failed runs are recorded too. Unchanged artifacts are not copied; original output paths remain available. A successful run alone does not validate a research claim.
- Optional FinBERT and TensorFlow dependencies are not automatically installed.
- GitHub Actions tests Python 3.12/3.13 on Linux and Windows. A workflow file is not proof all matrix jobs passed; inspect Actions results.

## A useful walkthrough
1. Identify the dataset source before interpreting a chart. Demo/synthetic outputs show mechanics only.
2. Read the training, validation and test boundaries in the Research tab or exported metadata.
3. Compare against the baseline at the same budget, dates or coverage.
4. Change one assumption, record the run and explain why the result changed.
5. Read `RESEARCH_PROTOCOL.md` and `RESEARCH_RESULTS.md` before describing this as empirical research.

## Hosting
These are Python Streamlit applications. They need a Python-compatible host; the built-in Workers-based Sites host is not a drop-in runtime. Do not expose uploaded private data or the local investigation database in a public demo. No live hosted deployment has been created by these files.

