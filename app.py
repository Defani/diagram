import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st

st.set_page_config(page_title="Diagram Teks", page_icon="📊", layout="wide")

# ---------------------------------------------------------------
# 15 sample color palettes
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

CHART_TYPES = ["Bar", "Garis (Line)", "Pie", "Scatter", "Area", "Histogram", "Box"]

if "annotations" not in st.session_state:
    st.session_state.annotations = []

# ---------------------------------------------------------------
# Sidebar - DATA
# ---------------------------------------------------------------
st.sidebar.title("📊 Diagram Teks")
st.sidebar.caption("Tempel data teks → diagram matplotlib, siap export.")

with st.sidebar.expander("1. Data", expanded=True):
    sumber = st.radio("Sumber data", ["Tempel teks (CSV)", "Upload file CSV"])
    default_csv = "Kategori,Nilai\nA,23\nB,45\nC,12\nD,38\nE,29"
    if sumber == "Tempel teks (CSV)":
        teks = st.text_area("Tempel data (format CSV)", value=default_csv, height=140)
        try:
            df = pd.read_csv(io.StringIO(teks))
        except Exception as e:
            st.error(f"Gagal baca data: {e}")
            df = pd.read_csv(io.StringIO(default_csv))
    else:
        up = st.file_uploader("Upload CSV", type=["csv"])
        df = pd.read_csv(up) if up is not None else pd.read_csv(io.StringIO(default_csv))

    kolom = list(df.columns)

with st.sidebar.expander("2. Jenis & Warna", expanded=True):
    jenis = st.selectbox("Jenis diagram", CHART_TYPES)
    palet_nama = st.selectbox("Palet warna (15 sample)", list(PALETTES.keys()))
    warna = PALETTES[palet_nama]

    if jenis == "Histogram":
        kol_y = st.selectbox("Kolom nilai", kolom)
        kol_x = None
    else:
        kol_x = st.selectbox("Kolom X / label", kolom, index=0)
        kol_y = st.selectbox("Kolom Y / nilai", kolom, index=min(1, len(kolom) - 1))

with st.sidebar.expander("3. Judul & Label", expanded=False):
    judul = st.text_input("Judul diagram", "Judul Diagram")
    judul_size = st.slider("Ukuran font judul", 8, 28, 14)
    label_x = st.text_input("Label X", kol_x if kol_x else "")
    label_y = st.text_input("Label Y", kol_y if kol_y else "")
    label_size = st.slider("Ukuran font label sumbu", 6, 20, 11)

with st.sidebar.expander("4. Sumbu X", expanded=False):
    x_show_label = st.checkbox("Tampilkan label X", True)
    x_rotasi = st.slider("Rotasi tick label X", 0, 90, 30)
    x_log = st.checkbox("Skala log X (numerik saja)", False)
    x_range_auto = st.checkbox("Range X otomatis", True)
    if not x_range_auto:
        x_min = st.number_input("X min", value=0.0)
        x_max = st.number_input("X max", value=10.0)
    x_grid = st.checkbox("Gridline X", False)
    x_tick_dir = st.selectbox("Arah tick X", ["out", "in", "inout"], index=0)

with st.sidebar.expander("5. Sumbu Y", expanded=False):
    y_show_label = st.checkbox("Tampilkan label Y", True)
    y_log = st.checkbox("Skala log Y", False)
    y_range_auto = st.checkbox("Range Y otomatis", True)
    if not y_range_auto:
        y_min = st.number_input("Y min", value=0.0)
        y_max = st.number_input("Y max", value=100.0)
    y_grid = st.checkbox("Gridline Y", True)
    y_nticks = st.slider("Jumlah tick Y (perkiraan)", 2, 20, 6)
    y_tick_dir = st.selectbox("Arah tick Y", ["out", "in", "inout"], index=0)

with st.sidebar.expander("6. Gaya Bingkai (Spine)", expanded=False):
    spine_top = st.checkbox("Tampilkan garis atas", False)
    spine_right = st.checkbox("Tampilkan garis kanan", False)
    spine_left = st.checkbox("Tampilkan garis kiri", True)
    spine_bottom = st.checkbox("Tampilkan garis bawah", True)
    axis_lw = st.slider("Ketebalan garis sumbu", 0.5, 4.0, 1.0, 0.5)
    grid_style = st.selectbox("Gaya garis grid", ["--", "-", ":", "-."], index=0)
    grid_alpha = st.slider("Transparansi grid", 0.0, 1.0, 0.4, 0.1)

with st.sidebar.expander("7. Canvas — Anotasi teks", expanded=False):
    st.caption("Tambah teks/panah manual di atas diagram (posisi pakai koordinat data).")
    with st.form("form_anotasi", clear_on_submit=True):
        a_text = st.text_input("Teks anotasi")
        c1, c2 = st.columns(2)
        a_x = c1.number_input("Posisi X", value=0.0)
        a_y = c2.number_input("Posisi Y", value=0.0)
        a_size = st.slider("Ukuran font anotasi", 6, 24, 11)
        a_color = st.color_picker("Warna teks", "#000000")
        a_arrow = st.checkbox("Pakai panah (arah ke titik 0,0)")
        submitted = st.form_submit_button("➕ Tambah anotasi")
        if submitted and a_text.strip():
            st.session_state.annotations.append(
                dict(text=a_text, x=a_x, y=a_y, size=a_size, color=a_color, arrow=a_arrow)
            )
    if st.session_state.annotations:
        for i, a in enumerate(st.session_state.annotations):
            cols = st.columns([4, 1])
            cols[0].write(f"“{a['text']}” @ ({a['x']}, {a['y']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.annotations.pop(i)
                st.rerun()

with st.sidebar.expander("8. Ukuran & Export", expanded=True):
    lebar = st.slider("Lebar (in)", 4, 16, 8)
    tinggi = st.slider("Tinggi (in)", 3, 12, 5)
    dpi = st.slider("DPI (resolusi export)", 72, 600, 200, step=1)
    fmt = st.selectbox("Format export", ["PNG", "SVG", "PDF"])

# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
st.title("📊 Diagram Teks")
st.caption("Tempel/upload data teks, atur sumbu & canvas, langsung jadi gambar publikasi.")

with st.expander("Lihat data", expanded=False):
    st.dataframe(df, use_container_width=True)

fig, ax = plt.subplots(figsize=(lebar, tinggi), dpi=100)

try:
    n = len(df)
    warna_cycle = (warna * (n // len(warna) + 1))[:n]

    if jenis == "Bar":
        ax.bar(df[kol_x].astype(str), df[kol_y], color=warna_cycle)
    elif jenis == "Garis (Line)":
        ax.plot(df[kol_x].astype(str), df[kol_y], marker="o", color=warna[0])
    elif jenis == "Pie":
        ax.pie(df[kol_y], labels=df[kol_x].astype(str), autopct="%1.1f%%", colors=warna_cycle)
        ax.axis("equal")
    elif jenis == "Scatter":
        ax.scatter(df[kol_x], df[kol_y], color=warna[0], s=80)
    elif jenis == "Area":
        ax.fill_between(df[kol_x].astype(str), df[kol_y], color=warna[0], alpha=0.6)
        ax.plot(df[kol_x].astype(str), df[kol_y], color=warna[0])
    elif jenis == "Histogram":
        ax.hist(df[kol_y], bins=10, color=warna[0], edgecolor="white")
    elif jenis == "Box":
        ax.boxplot(df[kol_y].dropna(), patch_artist=True, boxprops=dict(facecolor=warna[0]))

    ax.set_title(judul, fontsize=judul_size, fontweight="bold")

    if jenis != "Pie":
        if x_show_label:
            ax.set_xlabel(label_x, fontsize=label_size)
        if y_show_label:
            ax.set_ylabel(label_y, fontsize=label_size)

        if jenis in ("Bar", "Garis (Line)", "Area"):
            plt.setp(ax.get_xticklabels(), rotation=x_rotasi, ha="right" if x_rotasi else "center")

        if y_log:
            try:
                ax.set_yscale("log")
            except Exception:
                pass
        if x_log and jenis in ("Scatter",):
            try:
                ax.set_xscale("log")
            except Exception:
                pass

        if not y_range_auto:
            ax.set_ylim(y_min, y_max)
        if not x_range_auto and jenis in ("Scatter",):
            ax.set_xlim(x_min, x_max)

        if jenis != "Box":
            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=y_nticks))

        ax.tick_params(axis="x", direction=x_tick_dir)
        ax.tick_params(axis="y", direction=y_tick_dir)

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

    for a in st.session_state.annotations:
        if a["arrow"]:
            ax.annotate(a["text"], xy=(0, 0), xytext=(a["x"], a["y"]),
                        fontsize=a["size"], color=a["color"],
                        arrowprops=dict(arrowstyle="->", color=a["color"]))
        else:
            ax.text(a["x"], a["y"], a["text"], fontsize=a["size"], color=a["color"])

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    buf = io.BytesIO()
    ext = fmt.lower()
    mime = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}[ext]
    fig.savefig(buf, format=ext, dpi=dpi, bbox_inches="tight")
    st.download_button(f"⬇️ Download {fmt} (DPI {dpi})", data=buf.getvalue(),
                        file_name=f"diagram_teks.{ext}", mime=mime)

except Exception as e:
    st.error(f"Tidak bisa membuat diagram: {e}")

st.divider()
st.caption("Diagram Teks · dibangun dengan Streamlit + Matplotlib")
