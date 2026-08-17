import io
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st

st.set_page_config(page_title="Ploots", page_icon=":material/bar_chart:", layout="wide")


# ---------------------------------------------------------------
# Helper: parsing berbagai format data (CSV/TSV/TXT/Excel/JSON)
# ---------------------------------------------------------------
def _parse_delimited_text(text):
    """Baca teks tabular dengan delimiter otomatis (koma/tab/titik-koma)."""
    return pd.read_csv(io.StringIO(text), sep=None, engine="python")


def _json_bytes_to_df(raw_bytes):
    """Terima JSON array-of-objects ATAU array 2D, kembalikan DataFrame."""
    data = json.loads(raw_bytes.decode("utf-8"))
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return pd.DataFrame(data)
    if isinstance(data, list) and data and isinstance(data[0], list):
        n_cols = max(len(row) for row in data)
        cols = [f"Kolom{i + 1}" for i in range(n_cols)]
        return pd.DataFrame(data, columns=cols)
    return pd.DataFrame(data)


def _load_uploaded_file(up):
    """Deteksi ekstensi file upload lalu parse sesuai tipenya.
    Untuk Excel multi-sheet, tampilkan pemilih sheet."""
    name = up.name.lower()
    if name.endswith((".xlsx", ".xlsm", ".xls")):
        try:
            xls = pd.ExcelFile(up)
        except Exception as e:
            raise RuntimeError(
                f"Gagal buka file Excel: {e}. "
                "Untuk file .xls lama, pastikan library 'xlrd' terpasang."
            )
        sheet = xls.sheet_names[0]
        if len(xls.sheet_names) > 1:
            sheet = st.selectbox("Pilih sheet", xls.sheet_names, key="excel_sheet_sel")
        return pd.read_excel(xls, sheet_name=sheet)
    elif name.endswith(".json"):
        return _json_bytes_to_df(up.getvalue())
    else:  # .csv, .tsv, .txt, atau lainnya -> delimiter otomatis
        raw = up.getvalue().decode("utf-8", errors="replace")
        return _parse_delimited_text(raw)


def transpose_df(df):
    """Tukar baris <-> kolom. Kolom pertama data asli jadi header baru,
    dan header asli jadi kolom pertama baru bernama 'Kolom'."""
    t = df.T
    t.columns = t.iloc[0].astype(str)
    t = t.iloc[1:].reset_index()
    t = t.rename(columns={"index": "Kolom"})
    t.columns.name = None
    for c in t.columns[1:]:
        converted = pd.to_numeric(t[c], errors="coerce")
        if converted.notna().all():
            t[c] = converted
    return t


def long_to_wide(df, x_col, series_col, value_col):
    """Pivot data long/tidy (X, Series, Value) menjadi bentuk lebar,
    tiap nilai unik di kolom Series jadi kolom tersendiri."""
    pivoted = df.pivot_table(index=x_col, columns=series_col, values=value_col, aggfunc="first")
    pivoted = pivoted.reset_index()
    pivoted.columns.name = None
    return pivoted

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,300..600,0..1,-50..200">
<style>
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
}
.sidebar-brand {
    display:flex; align-items:center; gap:8px; margin-bottom:2px;
}
.sidebar-brand .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-size: 26px;
    color: #18a0fb;
}
.sidebar-brand span.brand-text {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.3rem;
}
section[data-testid="stSidebar"] .stButton button {justify-content:flex-start; font-family:'Inter',sans-serif;}
.nav-active button {background-color: rgba(24,160,251,.14) !important; border-color:#18a0fb !important; color:#0d8ce6 !important;}
div[data-testid="stMetricValue"] {font-size: 1.1rem;}

/* -----------------------------------------------------------
   Canvas diam di tempat — hanya sidebar (menu) yang scroll.
   Sidebar & area utama masing-masing jadi panel tinggi-penuh
   dengan scroll internal sendiri, meniru layout app Ploots (JS):
   sidebar overflow-y:auto, main tetap diam/fixed di viewport.
   ----------------------------------------------------------- */
html, body {
    overflow: hidden !important;
    height: 100vh;
}
div[data-testid="stAppViewContainer"] {
    height: 100vh;
    overflow: hidden;
}
section[data-testid="stSidebar"] {
    height: 100vh;
}
section[data-testid="stSidebar"] > div:first-child {
    height: 100vh;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
}
div[data-testid="stMain"] {
    height: 100vh;
    overflow-y: auto;
    overflow-x: hidden;
}
div[data-testid="stMain"] > div.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Palet warna (15 sample)
# ---------------------------------------------------------------
PALETTES = {
    "Tab10": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
              "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
    "Set1": ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
             "#ffff33", "#a65628", "#f781bf", "#999999"],
    "Set2": ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854",
             "#ffd92f", "#e5c494", "#b3b3b3"],
    "Set3": ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
             "#fdb462", "#b3de69", "#fccde5", "#d9d9d9"],
    "Pastel1": ["#fbb4ae", "#b3cde3", "#ccebc5", "#decbe4", "#fed9a6",
                "#ffffcc", "#e5d8bd", "#fddaec", "#f2f2f2"],
    "Pastel2": ["#b3e2cd", "#fdcdac", "#cbd5e8", "#f4cae4", "#e6f5c9",
                "#fff2ae", "#f1e2cc", "#cccccc"],
    "Dark2": ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e",
              "#e6ab02", "#a6761d", "#666666"],
    "Accent": ["#7fc97f", "#beaed4", "#fdc086", "#ffff99", "#386cb0",
               "#f0027f", "#bf5b17", "#666666"],
    "Paired": ["#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99",
               "#e31a1c", "#fdbf6f", "#ff7f00", "#cab2d6", "#6a3d9a"],
    "Ocean": ["#03045e", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8"],
    "Sunset": ["#7400b8", "#9d4edd", "#c77dff", "#ff9e00", "#ff6d00"],
    "Forest": ["#1b4332", "#2d6a4f", "#40916c", "#74c69d", "#b7e4c7"],
    "Earth": ["#3a5a40", "#588157", "#a3b18a", "#dad7cd", "#bc6c25"],
    "Viridis": [plt.cm.viridis(i / 6) for i in range(7)],
    "Plasma": [plt.cm.plasma(i / 6) for i in range(7)],
}

FONTS = {
    "Sans Serif (default)": "sans-serif",
    "Serif": "serif",
    "Monospace": "monospace",
    "Cursive": "cursive",
    "Fantasy": "fantasy",
}

DPI_OPTIONS = [72, 96, 150, 200, 300, 400, 600]

# ---------------------------------------------------------------
# Fill pattern (hatch), format label nilai, posisi legend
# ---------------------------------------------------------------
HATCH_PATTERNS = ["/", "\\", "x", "-", "|", "+", "."]

VALUE_FORMAT_OPTIONS = [
    "Auto", "Integer", "1 desimal", "2 desimal", "Ribuan", "Persen", "Mata uang (Rp)",
]


def format_value(v, fmt):
    """Format satu nilai numerik sesuai pilihan format label."""
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return ""
    except TypeError:
        pass
    if fmt == "Integer":
        return f"{v:,.0f}".replace(",", ".")
    if fmt == "1 desimal":
        return f"{v:,.1f}".replace(",", ".")
    if fmt == "2 desimal":
        return f"{v:,.2f}".replace(",", ".")
    if fmt == "Ribuan":
        return f"{v:,.0f}".replace(",", ".")
    if fmt == "Persen":
        return f"{v:.1f}%"
    if fmt == "Mata uang (Rp)":
        return f"Rp {v:,.0f}".replace(",", ".")
    # Auto: 2 desimal, buang nol di belakang
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


LEGEND_POSITIONS = {
    "Terbaik (otomatis)": dict(loc="best"),
    "Atas Tengah": dict(loc="lower center", bbox_to_anchor=(0.5, 1.02)),
    "Bawah Tengah": dict(loc="upper center", bbox_to_anchor=(0.5, -0.18)),
    "Kiri Tengah (luar)": dict(loc="center right", bbox_to_anchor=(-0.08, 0.5)),
    "Kanan Tengah (luar)": dict(loc="center left", bbox_to_anchor=(1.02, 0.5)),
    "Kanan Atas (dalam)": dict(loc="upper right"),
    "Kiri Atas (dalam)": dict(loc="upper left"),
}

# ---------------------------------------------------------------
# 13 jenis diagram, dikelompokkan per kategori (gaya Ploots)
# ---------------------------------------------------------------
CHART_TYPE_DEFS = [
    {"category": "Bar", "value": "bar_single", "label": "Bar Tunggal", "icon": ":material/bar_chart:"},
    {"category": "Bar", "value": "bar_group", "label": "Bar Kelompok", "icon": ":material/equalizer:"},
    {"category": "Bar", "value": "bar_stack", "label": "Bar Tumpuk", "icon": ":material/stacked_bar_chart:"},
    {"category": "Garis & Area", "value": "line", "label": "Garis", "icon": ":material/show_chart:"},
    {"category": "Garis & Area", "value": "area", "label": "Area", "icon": ":material/area_chart:"},
    {"category": "Garis & Area", "value": "scatter", "label": "Sebar", "icon": ":material/scatter_plot:"},
    {"category": "Sirkular", "value": "pie", "label": "Pai", "icon": ":material/pie_chart:"},
    {"category": "Sirkular", "value": "donut", "label": "Donat", "icon": ":material/donut_large:"},
    {"category": "Distribusi", "value": "histogram", "label": "Histogram", "icon": ":material/insights:"},
    {"category": "Distribusi", "value": "box", "label": "Box Plot", "icon": ":material/candlestick_chart:"},
    {"category": "Distribusi", "value": "violin", "label": "Violin Plot", "icon": ":material/graphic_eq:"},
    {"category": "Lainnya", "value": "heatmap", "label": "Heatmap", "icon": ":material/grid_on:"},
    {"category": "Lainnya", "value": "waterfall", "label": "Waterfall", "icon": ":material/waterfall_chart:"},
]
CHART_LABELS = {d["value"]: d["label"] for d in CHART_TYPE_DEFS}
MULTI_Y_TYPES = {"bar_group", "bar_stack", "line", "area", "box", "violin", "heatmap"}

NAV_PANELS = [
    {"key": "data", "label": "Data", "icon": ":material/database:"},
    {"key": "chart_type", "label": "Jenis Diagram", "icon": ":material/bar_chart:"},
    {"key": "color", "label": "Warna & Gaya", "icon": ":material/palette:"},
    {"key": "titles", "label": "Judul & Label", "icon": ":material/description:"},
    {"key": "xaxis", "label": "Sumbu X", "icon": ":material/swap_horiz:"},
    {"key": "yaxis", "label": "Sumbu Y", "icon": ":material/swap_vert:"},
    {"key": "series", "label": "Series & Nilai", "icon": ":material/show_chart:"},
    {"key": "legend", "label": "Legend", "icon": ":material/legend_toggle:"},
    {"key": "frame", "label": "Bingkai", "icon": ":material/shapes:"},
    {"key": "annotate", "label": "Anotasi", "icon": ":material/match_case:"},
    {"key": "export", "label": "Ukuran & Export", "icon": ":material/file_save:"},
]

if "annotations" not in st.session_state:
    st.session_state.annotations = []
if "chart_type" not in st.session_state:
    st.session_state.chart_type = "bar_group"
if "active_panel" not in st.session_state:
    st.session_state.active_panel = "data"

default_csv = "Kategori,Nilai\nA,23\nB,45\nC,12\nD,38\nE,29"

# ---------------------------------------------------------------
# SIDEBAR — rail navigasi + panel aktif (mirip Ploots)
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<span class="material-symbols-outlined">bar_chart</span>'
        '<span class="brand-text">Ploots</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("Tempel data teks, susun diagram, ekspor siap pakai.")
    st.divider()

    for panel in NAV_PANELS:
        active = st.session_state.active_panel == panel["key"]
        if st.button(
            panel["label"], key=f"nav_{panel['key']}", icon=panel["icon"],
            width="stretch", type="primary" if active else "secondary",
        ):
            st.session_state.active_panel = panel["key"]
            st.rerun()

    st.divider()
    active_panel = st.session_state.active_panel

    # ---------------- Panel: Data ----------------
    if active_panel == "data":
        sumber = st.radio(
            "Sumber data",
            ["Tempel teks (CSV/TSV)", "Upload file (CSV/TSV/TXT/Excel/JSON)"],
        )
        if sumber == "Tempel teks (CSV/TSV)":
            teks = st.text_area(
                "Tempel data (delimiter koma/tab/titik-koma terdeteksi otomatis)",
                value=st.session_state.get("teks_data", default_csv), height=160,
            )
            st.session_state["teks_data"] = teks
            try:
                df_raw = _parse_delimited_text(teks)
            except Exception as e:
                st.error(f"Gagal baca data: {e}")
                df_raw = pd.read_csv(io.StringIO(default_csv))
        else:
            up = st.file_uploader(
                "Upload file", type=["csv", "tsv", "txt", "xlsx", "xls", "xlsm", "json"],
            )
            if up is not None:
                try:
                    df_raw = _load_uploaded_file(up)
                except Exception as e:
                    st.error(f"Gagal baca file: {e}")
                    df_raw = pd.read_csv(io.StringIO(default_csv))
            else:
                df_raw = pd.read_csv(io.StringIO(default_csv))

        # ---- Pengaturan lanjutan: transpose & bentuk data (wide/long) ----
        with st.expander(":material/tune: Pengaturan lanjutan data", icon=":material/tune:"):
            transpose_on = st.checkbox(
                "Transpose (tukar baris ↔ kolom)",
                value=st.session_state.get("transpose_on", False), key="transpose_on",
            )
            df_step = transpose_df(df_raw) if transpose_on else df_raw

            bentuk = st.radio(
                "Bentuk data",
                ["Lebar (wide) — pakai apa adanya", "Panjang/tidy — pivot ke lebar"],
                key="bentuk_data",
            )
            if bentuk == "Panjang/tidy — pivot ke lebar" and len(df_step.columns) >= 3:
                kolom_step = list(df_step.columns)
                c1, c2, c3 = st.columns(3)
                x_pivot = c1.selectbox("Kolom X", kolom_step, index=0, key="pivot_x")
                series_pivot = c2.selectbox(
                    "Kolom Series", kolom_step,
                    index=min(1, len(kolom_step) - 1), key="pivot_series",
                )
                value_pivot = c3.selectbox(
                    "Kolom Value", kolom_step,
                    index=min(2, len(kolom_step) - 1), key="pivot_value",
                )
                try:
                    df = long_to_wide(df_step, x_pivot, series_pivot, value_pivot)
                except Exception as e:
                    st.error(f"Gagal pivot data: {e}")
                    df = df_step
            else:
                df = df_step
        st.session_state["df"] = df
    else:
        df = st.session_state.get("df")
        if df is None:
            df = pd.read_csv(io.StringIO(st.session_state.get("teks_data", default_csv)))
            st.session_state["df"] = df

    kolom = list(df.columns)
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not numeric_cols:
        numeric_cols = kolom

    # ---------------- Panel: Jenis Diagram ----------------
    if active_panel == "chart_type":
        categories = []
        for d in CHART_TYPE_DEFS:
            if d["category"] not in categories:
                categories.append(d["category"])
        for cat in categories:
            st.markdown(f"**{cat}**")
            items = [d for d in CHART_TYPE_DEFS if d["category"] == cat]
            cols = st.columns(3)
            for i, d in enumerate(items):
                is_active = st.session_state.chart_type == d["value"]
                with cols[i % 3]:
                    if st.button(
                        d["label"], key=f"ct_{d['value']}", icon=d["icon"],
                        width="stretch", type="primary" if is_active else "secondary",
                    ):
                        st.session_state.chart_type = d["value"]
                        st.rerun()

    jenis = st.session_state.chart_type

    orientasi = "Vertikal"
    kol_x, kol_y, y_cols = None, None, []

    # Pemilihan kolom data selalu tersedia (dipakai lintas panel), tampil ringkas di panel Jenis Diagram
    if active_panel == "chart_type":
        st.divider()
        st.markdown("**Kolom data**")
        if jenis == "bar_single" and orientasi == "Horizontal":
            pass
        if jenis in ("bar_single", "bar_group", "bar_stack"):
            orientasi = st.selectbox("Orientasi bar", ["Vertikal", "Horizontal"], key="orientasi_sel")
        if jenis in MULTI_Y_TYPES:
            if jenis != "heatmap":
                kol_x = st.selectbox("Kolom X / label", kolom, index=0, key="kx_multi")
            else:
                kol_x = st.selectbox("Kolom baris (label)", kolom, index=0, key="kx_heat")
            default_y = [c for c in numeric_cols if c != kol_x][:3] or numeric_cols[:1]
            y_cols = st.multiselect("Kolom nilai (bisa lebih dari satu)", numeric_cols, default=default_y, key="ymulti")
        elif jenis == "histogram":
            kol_y = st.selectbox("Kolom nilai", numeric_cols, key="ky_hist")
        elif jenis == "waterfall":
            kol_x = st.selectbox("Kolom tahap/label", kolom, index=0, key="kx_wf")
            kol_y = st.selectbox("Kolom nilai (boleh negatif)", numeric_cols, key="ky_wf")
        else:
            kol_x = st.selectbox("Kolom X / label", kolom, index=0, key="kx_single")
            kol_y = st.selectbox("Kolom Y / nilai", numeric_cols, index=min(1, len(numeric_cols) - 1) if len(numeric_cols) > 1 else 0, key="ky_single")
    else:
        # simpan pilihan sebelumnya lewat session_state supaya tetap konsisten antar panel
        orientasi = st.session_state.get("orientasi_sel", "Vertikal")
        if jenis in MULTI_Y_TYPES:
            kol_x = st.session_state.get("kx_multi" if jenis != "heatmap" else "kx_heat", kolom[0])
            y_cols = st.session_state.get("ymulti", numeric_cols[:1])
        elif jenis == "histogram":
            kol_y = st.session_state.get("ky_hist", numeric_cols[0])
        elif jenis == "waterfall":
            kol_x = st.session_state.get("kx_wf", kolom[0])
            kol_y = st.session_state.get("ky_wf", numeric_cols[0])
        else:
            kol_x = st.session_state.get("kx_single", kolom[0])
            kol_y = st.session_state.get("ky_single", numeric_cols[0])

    # ---------------- Panel: Warna & Gaya ----------------
    if active_panel == "color":
        palet_nama = st.selectbox("Palet warna (15 sample)", list(PALETTES.keys()), key="palet_sel")
        style_mode = st.selectbox(
            "Mode gaya visual", ["Warna", "Warna + Pola (hatch)", "Pola (Grayscale, siap cetak)"],
            key="style_mode",
            help="'Pola' menambahkan hatch (garis/silang/titik) per series agar tetap jelas dibedakan saat dicetak hitam-putih.",
        )
    else:
        palet_nama = st.session_state.get("palet_sel", "Tab10")
        style_mode = st.session_state.get("style_mode", "Warna")
    warna = PALETTES[palet_nama]
    use_hatch = style_mode != "Warna"
    if style_mode == "Pola (Grayscale, siap cetak)":
        n_shades = max(len(kolom), 8)
        warna = [plt.cm.gray(v) for v in np.linspace(0.82, 0.32, n_shades)]

    def get_hatch(i):
        return HATCH_PATTERNS[i % len(HATCH_PATTERNS)] if use_hatch else None

    # ---------------- Panel: Judul & Label ----------------
    if active_panel == "titles":
        judul = st.text_input("Judul diagram", st.session_state.get("judul_val", "Judul Diagram"), key="judul_val")
        judul_size = st.number_input("Ukuran font judul", min_value=8, max_value=40, value=14, step=1, key="judul_size")
        font_nama = st.selectbox("Jenis font", list(FONTS.keys()), key="font_nama")
        label_x = st.text_input("Label X", st.session_state.get("label_x_val", kol_x or ""), key="label_x_val")
        label_y = st.text_input("Label Y", st.session_state.get("label_y_val", kol_y or ""), key="label_y_val")
        label_size = st.number_input("Ukuran font label sumbu", min_value=6, max_value=30, value=11, step=1, key="label_size")
        tick_size = st.number_input("Ukuran font tick (angka/label sumbu)", min_value=6, max_value=24, value=10, step=1, key="tick_size")
    judul = st.session_state.get("judul_val", "Judul Diagram")
    judul_size = st.session_state.get("judul_size", 14)
    font_nama = st.session_state.get("font_nama", "Sans Serif (default)")
    label_x = st.session_state.get("label_x_val", kol_x or "")
    label_y = st.session_state.get("label_y_val", kol_y or "")
    label_size = st.session_state.get("label_size", 11)
    tick_size = st.session_state.get("tick_size", 10)

    # ---------------- Panel: Sumbu X ----------------
    if active_panel == "xaxis":
        x_show_label = st.checkbox("Tampilkan label X", True, key="x_show_label")
        x_rotasi = st.number_input("Rotasi tick label X (derajat)", min_value=0, max_value=90, value=30, step=5, key="x_rotasi")
        x_log = st.checkbox("Skala log X (numerik saja)", False, key="x_log")
        x_range_auto = st.checkbox("Range X otomatis", True, key="x_range_auto")
        if not x_range_auto:
            st.number_input("X min", value=0.0, key="x_min")
            st.number_input("X max", value=10.0, key="x_max")
        x_grid = st.checkbox("Gridline X", False, key="x_grid")
        x_tick_dir = st.selectbox("Arah tick X", ["out", "in", "inout"], index=0, key="x_tick_dir")
    x_show_label = st.session_state.get("x_show_label", True)
    x_rotasi = st.session_state.get("x_rotasi", 30)
    x_log = st.session_state.get("x_log", False)
    x_range_auto = st.session_state.get("x_range_auto", True)
    x_min = st.session_state.get("x_min", 0.0)
    x_max = st.session_state.get("x_max", 10.0)
    x_grid = st.session_state.get("x_grid", False)
    x_tick_dir = st.session_state.get("x_tick_dir", "out")

    # ---------------- Panel: Sumbu Y ----------------
    if active_panel == "yaxis":
        y_show_label = st.checkbox("Tampilkan label Y", True, key="y_show_label")
        y_log = st.checkbox("Skala log Y", False, key="y_log")
        y_range_auto = st.checkbox("Range Y otomatis", True, key="y_range_auto")
        if not y_range_auto:
            st.number_input("Y min", value=0.0, key="y_min")
            st.number_input("Y max", value=100.0, key="y_max")
        y_grid = st.checkbox("Gridline Y", True, key="y_grid")
        y_nticks = st.number_input("Jumlah tick Y (perkiraan)", min_value=2, max_value=20, value=6, step=1, key="y_nticks")
        y_tick_dir = st.selectbox("Arah tick Y", ["out", "in", "inout"], index=0, key="y_tick_dir")
    y_show_label = st.session_state.get("y_show_label", True)
    y_log = st.session_state.get("y_log", False)
    y_range_auto = st.session_state.get("y_range_auto", True)
    y_min = st.session_state.get("y_min", 0.0)
    y_max = st.session_state.get("y_max", 100.0)
    y_grid = st.session_state.get("y_grid", True)
    y_nticks = st.session_state.get("y_nticks", 6)
    y_tick_dir = st.session_state.get("y_tick_dir", "out")

    # ---------------- Panel: Series & Nilai (sumbu Y sekunder, value label, error bar) ----------------
    SECONDARY_Y_TYPES = {"bar_group", "line", "area"}
    ERROR_BAR_TYPES = {"bar_single", "bar_group", "bar_stack", "line", "area", "scatter"}
    if active_panel == "series":
        st.markdown("**Sumbu Y sekunder**")
        if jenis in SECONDARY_Y_TYPES and y_cols:
            secondary_y_cols = st.multiselect(
                "Series yang ditampilkan di sumbu Y kanan (sekunder)",
                y_cols, default=[c for c in st.session_state.get("secondary_y_cols", []) if c in y_cols],
                key="secondary_y_cols",
            )
            secondary_label = st.text_input(
                "Label sumbu Y sekunder", st.session_state.get("secondary_label_val", ""), key="secondary_label_val",
            )
        else:
            st.caption("Hanya tersedia untuk Bar Kelompok, Garis, dan Area dengan minimal 1 kolom nilai dipilih.")
            secondary_y_cols, secondary_label = [], ""

        st.divider()
        st.markdown("**Label nilai**")
        value_labels_on = st.checkbox("Tampilkan label nilai di titik/bar", False, key="value_labels_on")
        value_format = st.selectbox("Format label nilai", VALUE_FORMAT_OPTIONS, key="value_format")

        st.divider()
        st.markdown("**Error bar**")
        if jenis in ERROR_BAR_TYPES:
            error_bars_on = st.checkbox("Tampilkan error bar", False, key="error_bars_on")
            error_mode = st.radio("Mode error bar", ["Persen dari nilai", "Nilai tetap"], key="error_mode")
            if error_mode == "Persen dari nilai":
                st.number_input("Persentase error (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0, key="error_pct")
            else:
                st.number_input("Nilai error tetap", value=1.0, step=0.5, key="error_fixed")
            c1, c2 = st.columns(2)
            c1.number_input("Cap width", min_value=0.0, max_value=20.0, value=4.0, step=1.0, key="error_capsize")
            c2.number_input("Ketebalan garis", min_value=0.5, max_value=5.0, value=1.2, step=0.2, key="error_lw")
            st.checkbox("Ikuti warna series (bukan hitam)", False, key="error_follow_color")
        else:
            st.caption("Hanya tersedia untuk Bar, Garis, Area, dan Sebar.")
            error_bars_on = False
    secondary_y_cols = [c for c in st.session_state.get("secondary_y_cols", []) if c in y_cols]
    secondary_label = st.session_state.get("secondary_label_val", "")
    value_labels_on = st.session_state.get("value_labels_on", False)
    value_format = st.session_state.get("value_format", "Auto")
    error_bars_on = st.session_state.get("error_bars_on", False) and jenis in ERROR_BAR_TYPES
    error_mode = st.session_state.get("error_mode", "Persen dari nilai")
    error_pct = st.session_state.get("error_pct", 10.0)
    error_fixed = st.session_state.get("error_fixed", 1.0)
    error_capsize = st.session_state.get("error_capsize", 4.0)
    error_lw = st.session_state.get("error_lw", 1.2)
    error_follow_color = st.session_state.get("error_follow_color", False)

    # ---------------- Panel: Legend ----------------
    if active_panel == "legend":
        legend_show = st.checkbox("Tampilkan legend", True, key="legend_show")
        legend_position = st.selectbox("Posisi legend", list(LEGEND_POSITIONS.keys()), key="legend_position")
        legend_cols = st.number_input("Jumlah kolom legend", min_value=1, max_value=4, value=1, step=1, key="legend_cols")
        legend_title = st.text_input("Judul legend (opsional)", st.session_state.get("legend_title_val", ""), key="legend_title_val")
        legend_border = st.checkbox("Tampilkan border legend", True, key="legend_border")
    legend_show = st.session_state.get("legend_show", True)
    legend_position = st.session_state.get("legend_position", "Terbaik (otomatis)")
    legend_cols = st.session_state.get("legend_cols", 1)
    legend_title = st.session_state.get("legend_title_val", "")
    legend_border = st.session_state.get("legend_border", True)

    # ---------------- Panel: Bingkai (Spine) ----------------
    if active_panel == "frame":
        spine_top = st.checkbox("Tampilkan garis atas", False, key="spine_top")
        spine_right = st.checkbox("Tampilkan garis kanan", False, key="spine_right")
        spine_left = st.checkbox("Tampilkan garis kiri", True, key="spine_left")
        spine_bottom = st.checkbox("Tampilkan garis bawah", True, key="spine_bottom")
        axis_lw = st.number_input("Ketebalan garis sumbu", min_value=0.5, max_value=5.0, value=1.0, step=0.5, key="axis_lw")
        grid_style = st.selectbox("Gaya garis grid", ["--", "-", ":", "-."], index=0, key="grid_style")
        grid_alpha = st.number_input("Transparansi grid (0-1)", min_value=0.0, max_value=1.0, value=0.4, step=0.1, key="grid_alpha")
    spine_top = st.session_state.get("spine_top", False)
    spine_right = st.session_state.get("spine_right", False)
    spine_left = st.session_state.get("spine_left", True)
    spine_bottom = st.session_state.get("spine_bottom", True)
    axis_lw = st.session_state.get("axis_lw", 1.0)
    grid_style = st.session_state.get("grid_style", "--")
    grid_alpha = st.session_state.get("grid_alpha", 0.4)

    # ---------------- Panel: Anotasi ----------------
    if active_panel == "annotate":
        st.caption("Tambah teks/panah manual di atas diagram (posisi pakai koordinat data).")
        with st.form("form_anotasi", clear_on_submit=True):
            a_text = st.text_input("Teks anotasi")
            c1, c2 = st.columns(2)
            a_x = c1.number_input("Posisi X", value=0.0)
            a_y = c2.number_input("Posisi Y", value=0.0)
            a_size = st.number_input("Ukuran font anotasi", min_value=6, max_value=30, value=11, step=1)
            a_color = st.color_picker("Warna teks", "#000000")
            a_arrow = st.checkbox("Pakai panah (arah ke titik 0,0)")
            submitted = st.form_submit_button("Tambah anotasi", icon=":material/add:")
            if submitted and a_text.strip():
                st.session_state.annotations.append(
                    dict(text=a_text, x=a_x, y=a_y, size=a_size, color=a_color, arrow=a_arrow)
                )
        if st.session_state.annotations:
            for i, a in enumerate(st.session_state.annotations):
                c = st.columns([4, 1])
                c[0].write(f"\u201c{a['text']}\u201d @ ({a['x']}, {a['y']})")
                if c[1].button("", key=f"del_{i}", icon=":material/delete:"):
                    st.session_state.annotations.pop(i)
                    st.rerun()

    # ---------------- Panel: Ukuran & Export ----------------
    if active_panel == "export":
        lebar = st.number_input("Lebar (in)", min_value=4, max_value=20, value=8, step=1, key="lebar")
        tinggi = st.number_input("Tinggi (in)", min_value=3, max_value=16, value=5, step=1, key="tinggi")
        dpi = st.selectbox("DPI (resolusi export)", DPI_OPTIONS, index=DPI_OPTIONS.index(200), key="dpi")
        fmt = st.selectbox("Format export", ["PNG", "SVG", "PDF"], key="fmt")
    lebar = st.session_state.get("lebar", 8)
    tinggi = st.session_state.get("tinggi", 5)
    dpi = st.session_state.get("dpi", 200)
    fmt = st.session_state.get("fmt", "PNG")

# ---------------------------------------------------------------
# AREA UTAMA — menu atas (tab) + canvas, tidak ikut scroll sidebar
# ---------------------------------------------------------------
st.title("Ploots")
st.caption("Diagram Teks — tempel data teks, susun diagram, ekspor siap pakai.")

tab_plot, tab_data = st.tabs([":material/show_chart: Plot View", ":material/database: Data View"])

with tab_data:
    st.subheader("Data")
    st.dataframe(df, width="stretch")
    if numeric_cols:
        st.subheader("Ringkasan statistik")
        desc = df[numeric_cols].describe().T
        desc = desc.rename(columns={
            "count": "Jumlah", "mean": "Rata-rata", "std": "Std Dev",
            "min": "Min", "25%": "Q1 (25%)", "50%": "Median", "75%": "Q3 (75%)", "max": "Max",
        })
        desc["Missing"] = df[numeric_cols].isna().sum()
        desc["Unik"] = df[numeric_cols].nunique()
        desc["Skewness"] = df[numeric_cols].skew()
        desc["Kurtosis"] = df[numeric_cols].kurt()
        kolom_urut = ["Jumlah", "Missing", "Unik", "Rata-rata", "Median", "Std Dev",
                      "Min", "Q1 (25%)", "Q3 (75%)", "Max", "Skewness", "Kurtosis"]
        st.dataframe(desc[kolom_urut].round(3), width="stretch")
        st.caption(
            "Skewness > 0: ekor distribusi condong ke kanan · < 0: condong ke kiri · "
            "≈ 0: mendekati simetris. Kurtosis mengukur 'keruncingan' distribusi "
            "relatif terhadap distribusi normal (0)."
        )

with tab_plot:
    plt.rcParams["font.family"] = FONTS[font_nama]
    fig, ax = plt.subplots(figsize=(lebar, tinggi), dpi=100)

    try:
        n = len(df)
        warna_cycle = (warna * (n // len(warna) + 1))[:n]
        horizontal = jenis in ("bar_single", "bar_group", "bar_stack") and orientasi == "Horizontal"
        has_axes_styling = True

        ax2 = None

        def compute_error(values):
            values = np.asarray(values, dtype=float)
            if error_mode == "Persen dari nilai":
                return np.abs(values * (error_pct / 100.0))
            return np.full_like(values, error_fixed, dtype=float)

        if jenis == "bar_single":
            values = df[kol_y].to_numpy(dtype=float)
            positions = np.arange(len(values))
            if horizontal:
                bars = ax.barh(df[kol_x].astype(str), values, color=warna_cycle)
            else:
                bars = ax.bar(df[kol_x].astype(str), values, color=warna_cycle)
            if use_hatch:
                for i, patch in enumerate(bars):
                    patch.set_hatch(get_hatch(i))
                    patch.set_edgecolor("black")
            if value_labels_on:
                ax.bar_label(bars, labels=[format_value(v, value_format) for v in values],
                             padding=3, fontsize=max(label_size - 2, 6))
            if error_bars_on:
                err = compute_error(values)
                ecolor = warna_cycle[0] if (error_follow_color and warna_cycle) else "black"
                if horizontal:
                    ax.errorbar(values, positions, xerr=err, fmt="none", ecolor=ecolor,
                                capsize=error_capsize, elinewidth=error_lw, zorder=5)
                else:
                    ax.errorbar(positions, values, yerr=err, fmt="none", ecolor=ecolor,
                                capsize=error_capsize, elinewidth=error_lw, zorder=5)

        elif jenis in ("bar_group", "bar_stack"):
            labels = df[kol_x].astype(str).tolist()
            positions = np.arange(len(labels))
            if secondary_y_cols:
                ax2 = ax.twinx()
            if jenis == "bar_group":
                width = 0.8 / max(len(y_cols), 1)
                for i, col in enumerate(y_cols):
                    offset = (i - (len(y_cols) - 1) / 2) * width
                    target_ax = ax2 if (ax2 is not None and col in secondary_y_cols) else ax
                    values = df[col].to_numpy(dtype=float)
                    pos_i = positions + offset
                    kwargs = dict(color=warna[i % len(warna)], label=col)
                    if use_hatch:
                        kwargs["hatch"] = get_hatch(i); kwargs["edgecolor"] = "black"
                    if horizontal:
                        cont = target_ax.barh(pos_i, values, height=width, **kwargs)
                    else:
                        cont = target_ax.bar(pos_i, values, width=width, **kwargs)
                    if value_labels_on:
                        target_ax.bar_label(cont, labels=[format_value(v, value_format) for v in values],
                                             padding=2, fontsize=max(label_size - 3, 6))
                    if error_bars_on:
                        err = compute_error(values)
                        ecolor = warna[i % len(warna)] if error_follow_color else "black"
                        if horizontal:
                            target_ax.errorbar(values, pos_i, xerr=err, fmt="none", ecolor=ecolor,
                                                capsize=error_capsize, elinewidth=error_lw, zorder=5)
                        else:
                            target_ax.errorbar(pos_i, values, yerr=err, fmt="none", ecolor=ecolor,
                                                capsize=error_capsize, elinewidth=error_lw, zorder=5)
            else:  # bar_stack (tidak mendukung sumbu Y sekunder)
                bottoms = np.zeros(len(labels))
                for i, col in enumerate(y_cols):
                    values = df[col].to_numpy(dtype=float)
                    kwargs = dict(color=warna[i % len(warna)], label=col)
                    if use_hatch:
                        kwargs["hatch"] = get_hatch(i); kwargs["edgecolor"] = "black"
                    if horizontal:
                        cont = ax.barh(positions, values, left=bottoms, **kwargs)
                    else:
                        cont = ax.bar(positions, values, bottom=bottoms, **kwargs)
                    if value_labels_on:
                        ax.bar_label(cont, labels=[format_value(v, value_format) for v in values],
                                     label_type="center", fontsize=max(label_size - 3, 6), color="white")
                    if error_bars_on:
                        err = compute_error(values)
                        ecolor = warna[i % len(warna)] if error_follow_color else "black"
                        top = bottoms + values
                        if horizontal:
                            ax.errorbar(top, positions, xerr=err, fmt="none", ecolor=ecolor,
                                        capsize=error_capsize, elinewidth=error_lw, zorder=5)
                        else:
                            ax.errorbar(positions, top, yerr=err, fmt="none", ecolor=ecolor,
                                        capsize=error_capsize, elinewidth=error_lw, zorder=5)
                    bottoms = bottoms + values
            if horizontal:
                ax.set_yticks(positions); ax.set_yticklabels(labels)
            else:
                ax.set_xticks(positions); ax.set_xticklabels(labels)

        elif jenis == "line":
            if secondary_y_cols:
                ax2 = ax.twinx()
            x_vals = df[kol_x].astype(str)
            for i, col in enumerate(y_cols):
                target_ax = ax2 if (ax2 is not None and col in secondary_y_cols) else ax
                values = df[col].to_numpy(dtype=float)
                target_ax.plot(x_vals, values, marker="o", label=col, color=warna[i % len(warna)])
                if value_labels_on:
                    for xi, yi in zip(x_vals, values):
                        target_ax.annotate(format_value(yi, value_format), (xi, yi),
                                            textcoords="offset points", xytext=(0, 7),
                                            ha="center", fontsize=max(label_size - 3, 6))
                if error_bars_on:
                    err = compute_error(values)
                    ecolor = warna[i % len(warna)] if error_follow_color else "black"
                    target_ax.errorbar(x_vals, values, yerr=err, fmt="none", ecolor=ecolor,
                                        capsize=error_capsize, elinewidth=error_lw, zorder=5)

        elif jenis == "area":
            if secondary_y_cols:
                ax2 = ax.twinx()
            x_vals = df[kol_x].astype(str)
            bottoms = np.zeros(len(df))
            bottoms2 = np.zeros(len(df))
            for i, col in enumerate(y_cols):
                target_ax = ax2 if (ax2 is not None and col in secondary_y_cols) else ax
                values = df[col].to_numpy(dtype=float)
                base = bottoms2 if target_ax is ax2 else bottoms
                top = base + values
                fill_kwargs = dict(color=warna[i % len(warna)], alpha=0.6, label=col)
                if use_hatch:
                    fill_kwargs["hatch"] = get_hatch(i); fill_kwargs["edgecolor"] = "black"
                target_ax.fill_between(x_vals, base, top, **fill_kwargs)
                target_ax.plot(x_vals, top, color=warna[i % len(warna)], linewidth=1)
                if value_labels_on:
                    for xi, yi in zip(x_vals, top):
                        target_ax.annotate(format_value(yi, value_format), (xi, yi),
                                            textcoords="offset points", xytext=(0, 7),
                                            ha="center", fontsize=max(label_size - 3, 6))
                if error_bars_on:
                    err = compute_error(values)
                    ecolor = warna[i % len(warna)] if error_follow_color else "black"
                    target_ax.errorbar(x_vals, top, yerr=err, fmt="none", ecolor=ecolor,
                                        capsize=error_capsize, elinewidth=error_lw, zorder=5)
                if target_ax is ax2:
                    bottoms2 = top
                else:
                    bottoms = top

        elif jenis == "scatter":
            values_y = df[kol_y].to_numpy(dtype=float)
            ax.scatter(df[kol_x], values_y, color=warna[0], s=80)
            if value_labels_on:
                for xi, yi in zip(df[kol_x], values_y):
                    ax.annotate(format_value(yi, value_format), (xi, yi),
                                textcoords="offset points", xytext=(0, 8),
                                ha="center", fontsize=max(label_size - 3, 6))
            if error_bars_on:
                err = compute_error(values_y)
                ecolor = warna[0] if error_follow_color else "black"
                ax.errorbar(df[kol_x], values_y, yerr=err, fmt="none", ecolor=ecolor,
                            capsize=error_capsize, elinewidth=error_lw, zorder=5)

        elif jenis == "pie":
            wedges, _texts, _autotexts = ax.pie(df[kol_y], labels=df[kol_x].astype(str), autopct="%1.1f%%", colors=warna_cycle)
            if use_hatch:
                for i, w in enumerate(wedges):
                    w.set_hatch(get_hatch(i)); w.set_edgecolor("black")
            ax.axis("equal")
            has_axes_styling = False

        elif jenis == "donut":
            wedges, _texts, _autotexts = ax.pie(df[kol_y], labels=df[kol_x].astype(str), autopct="%1.1f%%", colors=warna_cycle,
                   wedgeprops=dict(width=0.4))
            if use_hatch:
                for i, w in enumerate(wedges):
                    w.set_hatch(get_hatch(i)); w.set_edgecolor("black")
            ax.axis("equal")
            has_axes_styling = False

        elif jenis == "histogram":
            counts, bins, patches = ax.hist(df[kol_y], bins=10, color=warna[0], edgecolor="white")
            if use_hatch:
                for patch in patches:
                    patch.set_hatch(get_hatch(0))
                    patch.set_edgecolor("black")
            if value_labels_on:
                for count, left, right in zip(counts, bins[:-1], bins[1:]):
                    if count > 0:
                        ax.annotate(format_value(count, value_format), ((left + right) / 2, count),
                                    textcoords="offset points", xytext=(0, 4),
                                    ha="center", fontsize=max(label_size - 3, 6))

        elif jenis == "box":
            data_box = [df[c].dropna() for c in y_cols]
            bp = ax.boxplot(data_box, patch_artist=True, tick_labels=y_cols)
            for i, patch in enumerate(bp["boxes"]):
                patch.set_facecolor(warna[i % len(warna)])
                if use_hatch:
                    patch.set_hatch(get_hatch(i))
                    patch.set_edgecolor("black")

        elif jenis == "violin":
            data_v = [df[c].dropna() for c in y_cols]
            vp = ax.violinplot(data_v, showmeans=True)
            for i, body in enumerate(vp["bodies"]):
                body.set_facecolor(warna[i % len(warna)])
                body.set_alpha(0.7)
                if use_hatch:
                    body.set_hatch(get_hatch(i))
                    body.set_edgecolor("black")
            ax.set_xticks(range(1, len(y_cols) + 1))
            ax.set_xticklabels(y_cols)

        elif jenis == "heatmap":
            matrix = df[y_cols].to_numpy(dtype=float)
            im = ax.imshow(matrix, aspect="auto", cmap="viridis")
            ax.set_yticks(range(len(df)))
            ax.set_yticklabels(df[kol_x].astype(str))
            ax.set_xticks(range(len(y_cols)))
            ax.set_xticklabels(y_cols, rotation=x_rotasi, ha="right" if x_rotasi else "center")
            fig.colorbar(im, ax=ax, shrink=0.8)
            has_axes_styling = False

        elif jenis == "waterfall":
            labels = df[kol_x].astype(str).tolist()
            values = df[kol_y].to_numpy(dtype=float)
            cum = np.concatenate([[0], np.cumsum(values)])[:-1]
            colors_wf = ["#2ca02c" if v >= 0 else "#d62728" for v in values]
            bottoms = np.where(values >= 0, cum, cum + values)
            heights = np.abs(values)
            bars = ax.bar(labels, heights, bottom=bottoms, color=colors_wf)
            if use_hatch:
                for i, patch in enumerate(bars):
                    patch.set_hatch(get_hatch(i))
                    patch.set_edgecolor("black")
            if value_labels_on:
                for i, (b, h, v) in enumerate(zip(bottoms, heights, values)):
                    ax.annotate(format_value(v, value_format), (i, b + h),
                                textcoords="offset points", xytext=(0, 4),
                                ha="center", fontsize=max(label_size - 3, 6))

        ax.set_title(judul, fontsize=judul_size, fontweight="bold")

        if has_axes_styling:
            lbl_x, lbl_y = (label_y, label_x) if horizontal else (label_x, label_y)
            show_lbl_x, show_lbl_y = (y_show_label, x_show_label) if horizontal else (x_show_label, y_show_label)
            if show_lbl_x:
                ax.set_xlabel(lbl_x, fontsize=label_size)
            if show_lbl_y:
                ax.set_ylabel(lbl_y, fontsize=label_size)

            if jenis in ("bar_single", "bar_group", "bar_stack", "line", "area", "waterfall") and not horizontal:
                plt.setp(ax.get_xticklabels(), rotation=x_rotasi, ha="right" if x_rotasi else "center")

            value_axis = ax.xaxis if horizontal else ax.yaxis
            if y_log:
                try:
                    (ax.set_xscale if horizontal else ax.set_yscale)("log")
                except Exception:
                    pass
            if x_log and jenis == "scatter":
                try:
                    ax.set_xscale("log")
                except Exception:
                    pass

            if not y_range_auto:
                (ax.set_xlim if horizontal else ax.set_ylim)(y_min, y_max)
            if not x_range_auto and jenis == "scatter":
                ax.set_xlim(x_min, x_max)

            if jenis not in ("box", "violin"):
                value_axis.set_major_locator(mticker.MaxNLocator(nbins=y_nticks))

            ax.tick_params(axis="x", direction=x_tick_dir, labelsize=tick_size)
            ax.tick_params(axis="y", direction=y_tick_dir, labelsize=tick_size)
            if ax2 is not None:
                ax2.tick_params(axis="y", labelsize=tick_size)

            if x_grid:
                ax.xaxis.grid(True, linestyle=grid_style, alpha=grid_alpha)
            if y_grid:
                ax.yaxis.grid(True, linestyle=grid_style, alpha=grid_alpha)

            ax.spines["top"].set_visible(spine_top)
            ax.spines["right"].set_visible(spine_right)
            ax.spines["left"].set_visible(spine_left)
            ax.spines["bottom"].set_visible(spine_bottom)
            for s in ("top", "right", "left", "bottom"):
                ax.spines[s].set_linewidth(axis_lw)

        if ax2 is not None and secondary_label:
            ax2.set_ylabel(secondary_label, fontsize=label_size)

        if legend_show:
            handles, labels_leg = ax.get_legend_handles_labels()
            if ax2 is not None:
                h2, l2 = ax2.get_legend_handles_labels()
                handles += h2
                labels_leg += l2
            if handles:
                pos_kwargs = LEGEND_POSITIONS[legend_position]
                ax.legend(
                    handles, labels_leg, fontsize=label_size, ncol=legend_cols,
                    title=legend_title or None, frameon=legend_border, **pos_kwargs,
                )

        for a in st.session_state.annotations:
            if a["arrow"]:
                ax.annotate(a["text"], xy=(0, 0), xytext=(a["x"], a["y"]),
                            fontsize=a["size"], color=a["color"],
                            arrowprops=dict(arrowstyle="->", color=a["color"]))
            else:
                ax.text(a["x"], a["y"], a["text"], fontsize=a["size"], color=a["color"])

        fig.tight_layout()
        st.pyplot(fig, width="stretch")

        buf = io.BytesIO()
        ext = fmt.lower()
        mime = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}[ext]
        fig.savefig(buf, format=ext, dpi=dpi, bbox_inches="tight")
        st.download_button(
            f"Download {fmt} (DPI {dpi})", data=buf.getvalue(),
            file_name=f"diagram_teks.{ext}", mime=mime, icon=":material/download:",
        )

    except Exception as e:
        st.error(f"Tidak bisa membuat diagram ({CHART_LABELS.get(jenis, jenis)}): {e}")

    st.caption("Ploots · Diagram Teks · dibangun dengan Streamlit + Matplotlib")
