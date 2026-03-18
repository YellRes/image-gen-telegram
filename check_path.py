import os
from pathlib import Path
print(f"CWD: {os.getcwd()}")
p = Path("images/test.png")
print(f"Path('{p}') exists: {p.exists()}")
print(f"Absolute path: {p.resolve()}")
