
import json
from pathlib import Path
import os

# Support both Docker (/app/) and local environments
ROOT_DIR = Path(os.environ.get('APP_ROOT', Path(__file__).parent))

def check_tanger():
    with open(ROOT_DIR / 'ports_africains.json', 'r') as f:
        ports = json.load(f)
    
    tanger = next((p for p in ports if "Tanger" in p['port_name']), None)
    if tanger:
        print(json.dumps(tanger, indent=2))

if __name__ == "__main__":
    check_tanger()
