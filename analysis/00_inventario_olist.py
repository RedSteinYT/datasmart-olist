"""Inventario reproducible de las tablas originales de Olist."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "olist"
OUT = ROOT / "analysis" / "outputs_olist"
OUT.mkdir(exist_ok=True)

rows = []
for path in sorted(RAW.glob("*.csv")):
    data = pd.read_csv(path)
    rows.append({
        "archivo": path.name,
        "filas": len(data),
        "columnas": len(data.columns),
        "duplicados_exactos": int(data.duplicated().sum()),
        "columnas_con_nulos": "; ".join(
            f"{column}={int(count)}" for column, count in data.isna().sum().items() if count
        ) or "ninguna",
        "campos": ", ".join(data.columns),
    })

inventory = pd.DataFrame(rows)
inventory.to_csv(OUT / "inventario_tablas_olist.csv", index=False)
print(inventory.to_string(index=False))
