import io
import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="SIPRES Smart School API", version="1.0.0")

REQUIRED_COLS = ["NIS", "Nama", "Kelas", "Alpa", "Menit_Terlambat", "Jumlah_Sanksi"]
ACCESS_CODE = os.getenv("SIPRES_ACCESS_CODE", "").strip()


BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / "public" / "index.html"

@app.get("/")
def home():
    # Use an absolute path because serverless working directories can differ.
    if not DASHBOARD_FILE.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard HTML tidak ditemukan pada lokasi: {DASHBOARD_FILE}"
        )
    return FileResponse(str(DASHBOARD_FILE), media_type="text/html")


def check_access(x_access_code: str | None):
    """Shared access-code gate. Configure SIPRES_ACCESS_CODE in Vercel."""
    if ACCESS_CODE and x_access_code != ACCESS_CODE:
        raise HTTPException(status_code=401, detail="Kode akses tidak sesuai.")


def evaluasi_status_sp(alpa: int, menit: int, sanksi: int) -> str:
    # Ambang batas dipertahankan sesuai notebook SIPRES.
    if alpa >= 5 or sanksi >= 3 or menit >= 120:
        return "🔴 Perlu SP 2"
    if alpa >= 3 or sanksi >= 2 or menit >= 40:
        return "🟡 Perlu SP 1"
    return "🟢 Aman"


@app.get("/health")
@app.get("/api/health")
def health():
    return {"ok": True, "app": "SIPRES Smart School", "access_protected": bool(ACCESS_CODE)}


@app.post("/analyze")
@app.post("/api/analyze")
async def analyze_excel(
    file: UploadFile = File(...),
    x_access_code: str | None = Header(default=None),
):
    check_access(x_access_code)

    filename = (file.filename or "").lower()
    if not filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Format file harus .xlsx.")

    content = await file.read()
    # Batas lunak untuk menghindari upload besar pada fungsi serverless.
    if len(content) > 4 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Ukuran file melebihi 4 MB. Pecah atau kecilkan file Excel, lalu unggah kembali."
        )

    try:
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"File Excel tidak dapat dibaca: {exc}")

    df.columns = df.columns.astype(str).str.strip()
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail="Kolom wajib belum ditemukan: " + ", ".join(missing)
        )
    if df.empty:
        raise HTTPException(status_code=400, detail="File Excel tidak berisi data siswa.")

    df["NIS"] = df["NIS"].fillna("").astype(str).str.strip()
    for col in ["Nama", "Kelas"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    for col in ["Alpa", "Menit_Terlambat", "Jumlah_Sanksi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            raise HTTPException(
                status_code=400,
                detail=f"Kolom {col} memiliki data kosong atau bukan angka yang valid."
            )
        if (df[col] < 0).any():
            raise HTTPException(status_code=400, detail=f"Nilai pada kolom {col} tidak boleh negatif.")
        df[col] = df[col].astype(int)

    df["Status_SP"] = [
        evaluasi_status_sp(int(a), int(m), int(s))
        for a, m, s in zip(df["Alpa"], df["Menit_Terlambat"], df["Jumlah_Sanksi"])
    ]

    total_siswa = int(len(df))
    aman = int((df["Status_SP"] == "🟢 Aman").sum())
    sp1 = int((df["Status_SP"] == "🟡 Perlu SP 1").sum())
    sp2 = int((df["Status_SP"] == "🔴 Perlu SP 2").sum())

    warning = df[df["Status_SP"].isin(["🟡 Perlu SP 1", "🔴 Perlu SP 2"])].copy()
    if warning.empty:
        warning_rows: list[dict[str, Any]] = [{
            "NIS": "-", "Nama": "Luar biasa! Tidak ada siswa melewati ambang batas SP",
            "Kelas": "-", "Alpa": 0, "Menit_Terlambat": 0,
            "Jumlah_Sanksi": 0, "Status_SP": "🟢 Aman"
        }]
    else:
        warning_rows = warning[REQUIRED_COLS + ["Status_SP"]].to_dict(orient="records")

    students = df[REQUIRED_COLS + ["Status_SP"]].to_dict(orient="records")

    # Convert numpy/int-like values to JSON-safe Python values.
    for row in students + warning_rows:
        for key, value in list(row.items()):
            if pd.isna(value):
                row[key] = ""
            elif hasattr(value, "item"):
                row[key] = value.item()

    return JSONResponse({
        "summary": {
            "total_siswa": total_siswa,
            "total_alpa": int(df["Alpa"].sum()),
            "total_menit": int(df["Menit_Terlambat"].sum()),
            "total_sanksi": int(df["Jumlah_Sanksi"].sum()),
            "aman": aman,
            "sp1": sp1,
            "sp2": sp2,
        },
        "warning": warning_rows,
        "students": students,
        "charts": {
            "status_labels": ["Aman", "Perlu SP 1", "Perlu SP 2"],
            "status_values": [aman, sp1, sp2],
            "violation_labels": ["Alpa", "Terlambat", "Pelanggaran"],
            "violation_values": [
                int((df["Alpa"] > 0).sum()),
                int((df["Menit_Terlambat"] > 0).sum()),
                int((df["Jumlah_Sanksi"] > 0).sum()),
            ],
        },
    })
