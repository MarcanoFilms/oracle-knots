# Control Center tests

Python tests for the Oracle Knots Control Center (`gui.py`, `oracle_net.py`).
They need no node build and no network: run them from the repository root with

```bash
python3 -m unittest discover -s test/gui -v
```

`bottle` must be importable (it is in `requirements.txt`; `./setup-gui.sh`
installs it into `gui-venv/`).
