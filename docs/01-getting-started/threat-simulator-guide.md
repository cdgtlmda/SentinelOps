# Threat Simulator User Guide

## Quick Start

1. **Run the system:**
   ```bash
   ./build_and_run.sh
   ```

2. **Test threat simulation via API:**
   ```bash
   curl http://localhost:8000/api/threat/stats
   curl -X POST "http://localhost:8000/api/threat/generate?count=2"
   curl -X POST "http://localhost:8000/api/threat/campaign?duration=3&intensity=high"
   ```

## API Endpoints

- `GET /api/threat/stats` - View scenario statistics
- `POST /api/threat/generate` - Generate threat scenarios
- `POST /api/threat/campaign` - Simulate attack campaigns

## CLI Usage

```bash
python src/tools/threat_simulator.py --stats
python src/tools/threat_simulator.py --batch 5
python src/tools/threat_simulator.py --campaign 10 --intensity high
```