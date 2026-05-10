import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, TIMESTAMP, ForeignKey, func, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from datetime import date, datetime, timedelta
import re
from unicodedata import normalize
from collections import defaultdict

# ============================================================================
# CONEXIÓN DIRECTA A SUPABASE
# ============================================================================
DB_URI_NUBE = "postgresql://postgres.tmeyajjnufkzzlgsuxxh:dNLKduxW3lKzQt7A@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(
    DB_URI_NUBE,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 10},
    poolclass=NullPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# MODELOS
# ============================================================================
class Supermercado(Base):
    __tablename__ = 'supermercados'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    url_base = Column(String)
    activo = Column(Boolean, default=True)

class ProductoReferencia(Base):
    __tablename__ = 'productos_referencia'
    id = Column(Integer, primary_key=True)
    nombre_producto = Column(String(255), nullable=False)
    marca = Column(String(100), nullable=False)
    categoria = Column(String(100))
    presentacion = Column(String(100))
    activo = Column(Boolean, default=True)
    es_propio = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

class PrecioHistorico(Base):
    __tablename__ = 'precios_historicos'
    id = Column(Integer, primary_key=True)
    supermercado_id = Column(Integer, ForeignKey('supermercados.id'))
    producto_referencia_id = Column(Integer, ForeignKey('productos_referencia.id'))
    nombre_original = Column(String(255), nullable=False)
    precio_bs = Column(Numeric(12,2))
    precio_usd = Column(Numeric(12,2))
    tasa_bcv = Column(Numeric(10,4))
    fecha_extraccion = Column(TIMESTAMP, default=datetime.now)
    url_pagina = Column(String)
    categoria_extraida = Column(String(100))
    match_score = Column(Integer)
    matched_automatically = Column(Boolean, default=False)


# ============================================================================
# CONFIGURACIÓN DE TEMA Y ESTADÍSTICA
# ============================================================================
st.set_page_config(page_title="Market Intelligence - Purolomo", page_icon="🐔", layout="wide")

if "tema" not in st.session_state:
    st.session_state.tema = "light"
if "estadistica" not in st.session_state:
    st.session_state.estadistica = "Mediana"

def toggle_tema():
    st.session_state.tema = "dark" if st.session_state.tema == "light" else "light"

def toggle_estadistica():
    st.session_state.estadistica = "Promedio" if st.session_state.estadistica == "Mediana" else "Mediana"


# ============================================================================
# CSS (mejorado, sin estilos de colores para tabla porque usamos pandas directo)
# ============================================================================
if st.session_state.tema == "light":
    tema_css = """
    <style>
        .stApp { background-color: #F8F9FA; }
        .stApp, .stMarkdown, .stDataFrame, .stSelectbox, .stMultiSelect, .stDateInput, .stCheckbox, .stToggle, .stButton { color: #1E1E1E; }
        h1, h2, h3 { color: #CC0000 !important; }
        .metric-red { background-color: #FFF5F5; border-left: 6px solid #CC0000; border-radius: 16px; padding: 16px; color: #1E1E1E; }
        .metric-green { background-color: #F0FFF4; border-left: 6px solid #00A859; border-radius: 16px; padding: 16px; color: #1E1E1E; }
        .metric-neutral { background-color: #F2F2F2; border-left: 6px solid #6C757D; border-radius: 16px; padding: 16px; color: #1E1E1E; }
        .super-metric {
            background-color: white;
            border-radius: 20px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-top: 4px solid #CC0000;
            transition: transform 0.2s;
        }
        .super-metric:hover { transform: translateY(-2px); }
        .stButton button { background-color: #CC0000; color: white; border-radius: 30px; font-weight: bold; border: none; }
        .stButton button:hover { background-color: #00A859; }
        .stCheckbox label { background-color: white; padding: 6px 14px; border-radius: 30px; border: 1px solid #E5E5E5; }
        .stCheckbox label:hover { border-color: #CC0000; background-color: #FFF5F5; }
        .dataframe {
            font-size: 14px;
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .dataframe th {
            background: linear-gradient(135deg, #CC0000, #990000);
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 12px 8px;
        }
        .dataframe td {
            text-align: center;
            padding: 10px 8px;
            vertical-align: middle;
            background-color: #FFFFFF;
            color: #1E1E1E;
        }
        .dataframe tr:nth-child(even) td { background-color: #F8F9FA; }
        .dataframe tr:hover td { background-color: #FFF0F0; }
        .dataframe td:first-child {
            font-weight: 600;
            background-color: #F2F2F2;
            text-align: left;
            padding-left: 16px;
        }
        .centered-title { text-align: center; font-size: 0.85rem; color: #6C757D; margin-top: 8px; }
        div[data-baseweb="select"] div { color: #CC0000 !important; }
    </style>
    """
else:
    tema_css = """
    <style>
        .stApp { background-color: #121212; }
        .stApp, .stMarkdown, .stDataFrame, .stSelectbox, .stMultiSelect, .stDateInput, .stCheckbox, .stToggle, .stButton, label, .st-df, .st-emotion-cache-1v0mbdj, .st-emotion-cache-10trblm, .st-emotion-cache-1r4qj8v, .st-emotion-cache-1v3ca8t, .st-emotion-cache-1wivap2, .st-emotion-cache-183lzff, .st-emotion-cache-1kyxreq, .st-emotion-cache-1aumxhk, .st-emotion-cache-16txtl3, .st-emotion-cache-1inwz65 {
            color: #FFFFFF !important;
        }
        h1, h2, h3, h4, h5, h6 { color: #CC0000 !important; }
        .streamlit-expanderHeader, .streamlit-expanderContent {
            color: #FFFFFF !important;
            background-color: #1E1E1E !important;
        }
        .metric-red { background-color: #2D2D2D; border-left: 6px solid #CC0000; border-radius: 16px; padding: 16px; color: #FFFFFF; }
        .metric-green { background-color: #2D2D2D; border-left: 6px solid #00A859; border-radius: 16px; padding: 16px; color: #FFFFFF; }
        .metric-neutral { background-color: #2D2D2D; border-left: 6px solid #6C757D; border-radius: 16px; padding: 16px; color: #FFFFFF; }
        .super-metric {
            background-color: #2D2D2D;
            border-radius: 20px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            border-top: 4px solid #CC0000;
            transition: transform 0.2s;
        }
        .super-metric:hover { transform: translateY(-2px); }
        .stButton button { background-color: #CC0000; color: white; border-radius: 30px; font-weight: bold; border: none; }
        .stButton button:hover { background-color: #00A859; }
        .stCheckbox label {
            background-color: #2D2D2D;
            padding: 6px 14px;
            border-radius: 30px;
            border: 1px solid #555;
            color: white !important;
        }
        .stCheckbox label span { color: white !important; }
        .st-b7, .st-b8, .st-b9, .st-ba, .st-cb, .st-cc, .st-cd, .stToggle label, .stToggle span { color: white !important; }
        .stDateInput input, .stDateInput label {
            color: white !important;
            background-color: #2D2D2D !important;
        }
        .stDateInput div { color: white !important; }
        div[data-baseweb="select"] div { color: #CC0000 !important; }
        .dataframe {
            font-size: 14px;
            border-collapse: separate;
            border-spacing: 0;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .dataframe th {
            background: linear-gradient(135deg, #CC0000, #800000);
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 12px 8px;
        }
        .dataframe td {
            text-align: center;
            padding: 10px 8px;
            vertical-align: middle;
            background-color: #2D2D2D;
            color: #F0F0F0;
        }
        .dataframe tr:nth-child(even) td { background-color: #3A3A3A; }
        .dataframe tr:hover td { background-color: #4A4A4A; }
        .dataframe td:first-child {
            font-weight: 600;
            background-color: #3D3D3D;
            text-align: left;
            padding-left: 16px;
            color: #FFAAAA;
        }
        .centered-title { text-align: center; font-size: 0.85rem; color: #CCCCCC; margin-top: 8px; }
    </style>
    """

st.markdown(tema_css, unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center;'>🥩 Purolomo Intelligence</h3>", unsafe_allow_html=True)
st.title("📊 Market Intelligence - Purolomo & Marcas Aliadas")
st.caption("Comparativa de precios - Tabla con precios hasta la última fecha común al gráfico")

# ============================================================================
# BARRA SUPERIOR
# ============================================================================
col_t1, col_t2, col_t3 = st.columns([1, 1, 3])
with col_t1:
    tema_icono = "☀️" if st.session_state.tema == "light" else "🌙"
    st.button(f"{tema_icono} Tema", on_click=toggle_tema, help="Cambiar tema")
with col_t2:
    estadistica_icono = "📊" if st.session_state.estadistica == "Mediana" else "📈"
    st.button(f"{estadistica_icono} {st.session_state.estadistica}", on_click=toggle_estadistica, help="Alternar mediana/promedio")
with col_t3:
    usar_usd = st.toggle("💰 USD", value=True)
    moneda = "USD" if usar_usd else "Bs"

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def extraer_peso(nombre):
    if not nombre:
        return ""
    patron = r'(\d+(?:[.,]\d+)?)\s*(kg|kilo|gr|g)'
    match = re.search(patron, nombre.lower())
    if match:
        cantidad = float(match.group(1).replace(',', '.'))
        unidad = match.group(2)
        if unidad in ['kg', 'kilo']:
            return f"{int(cantidad)}kg" if cantidad.is_integer() else f"{cantidad}kg"
        elif unidad in ['gr', 'g']:
            return f"{int(cantidad)}gr" if cantidad.is_integer() else f"{cantidad}gr"
    return ""

def normalizar_categoria(nombre):
    if not nombre:
        return ""
    texto = normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('ASCII').lower()
    marcas = [
        'la lucha', 'punta de monte', 'alibal', 'purolomo', 'san blas', 'purovo', 'milpa',
        'renata', 'mary', 'pantera', 'plumrose', 'gama', 'dulce mar', 'montserratina',
        'movilla', 'mallorca', 'oscar mayer', 'ricci', 'tovar', 'san jose', 'sky chefs',
        'chocozuela', 'quaker', 'kellogg', 'post', 'maizoritos', 'miduchy', 'naru',
        'jossie', 'primor', 'competencia', 'el drago', 'fiesta', 'la leonesa', 'tigo'
    ]
    for m in marcas:
        texto = re.sub(rf'\b{re.escape(m)}\b', '', texto)
    texto = re.sub(r'\b(de|la|el|los|las|para|con|sin|y|o|a|ante|bajo|cabe|contra|desde|durante|en|entre|hacia|hasta|mediante|por|según|so|sobre|tras|blanco|integral|premium|superior|extra|light|fresco|natural|original|tipo|clásico|deluxe|gourmet|familiar|económico|canilla|tipo)\b', '', texto)
    texto = re.sub(r'[^\w\s]', ' ', texto)
    palabras = [p for p in texto.split() if len(p) > 2 and not p.isdigit()]
    return palabras[0] if palabras else "sin_categoria"

def cumple_reglas(nombre_producto, palabras_incluir, palabras_excluir):
    nombre_norm = normalize('NFKD', nombre_producto.lower()).encode('ASCII', 'ignore').decode('ASCII')
    nombre_norm = re.sub(r'[^a-z0-9]', '', nombre_norm)
    for p in palabras_incluir:
        p_norm = normalize('NFKD', p.lower()).encode('ASCII', 'ignore').decode('ASCII')
        p_norm = re.sub(r'[^a-z0-9]', '', p_norm)
        if p_norm not in nombre_norm:
            return False
    for p in palabras_excluir:
        p_norm = normalize('NFKD', p.lower()).encode('ASCII', 'ignore').decode('ASCII')
        p_norm = re.sub(r'[^a-z0-9]', '', p_norm)
        if p_norm in nombre_norm:
            return False
    return True

def calcular_cobertura(precios_comp_ult, productos_unicos, super_ids_unicos):
    total_combinaciones_posibles = len(productos_unicos) * len(super_ids_unicos)
    total_datos_existentes = len(precios_comp_ult)
    cobertura = (total_datos_existentes / total_combinaciones_posibles) * 100 if total_combinaciones_posibles > 0 else 0
    return cobertura, total_datos_existentes, total_combinaciones_posibles

def formatear_nombre_producto(nombre):
    if not nombre:
        return nombre
    palabras = nombre.lower().split()
    return " ".join(palabras).capitalize()

# ============================================================================
# CONEXIÓN A BD Y FILTROS
# ============================================================================
session = SessionLocal()
marcas_propias = ['La Lucha', 'Punta de Monte', 'Alibal', 'Purolomo', 'San Blas', 'Purovo', 'Milpa']

st.markdown("### 🎚️ Filtros")
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    fechas = session.query(func.min(PrecioHistorico.fecha_extraccion), func.max(PrecioHistorico.fecha_extraccion)).first()
    min_fecha = fechas[0] if fechas[0] else date.today()
    max_fecha = fechas[1] if fechas[1] else date.today()
    fecha_inicio = st.date_input("Desde", min_fecha, min_value=min_fecha, max_value=max_fecha)
with col_f2:
    fecha_fin = st.date_input("Hasta", max_fecha, min_value=min_fecha, max_value=max_fecha)
with col_f3:
    st.write("")

# Fechas para variaciones
hoy = fecha_fin
ayer = hoy - timedelta(days=1)
hace_7_dias = hoy - timedelta(days=7)

super_con_datos = session.query(Supermercado).join(PrecioHistorico).filter(
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).distinct().all()
if not super_con_datos:
    st.error("No hay datos en el rango seleccionado.")
    st.stop()

super_options = {s.nombre: s.id for s in super_con_datos}
st.markdown("**🏬 Supermercados con datos:**")
selected_super_nombres = []
cols = st.columns(len(super_options))
for idx, (nombre, sid) in enumerate(super_options.items()):
    with cols[idx]:
        if st.checkbox(nombre, value=True, key=f"sup_{sid}"):
            selected_super_nombres.append(nombre)
selected_super_ids = [super_options[n] for n in selected_super_nombres]

st.markdown("---")
st.markdown("### 📦 Productos Purolomo & Aliados por supermercado")

# ============================================================================
# TOTAL DE PRODUCTOS PROPIOS (MANUAL)
# ============================================================================
TOTAL_PRODUCTOS_PROPIOS = 21   # ← CAMBIE AQUÍ SI EL NÚMERO ES DIFERENTE

info_super = {}

if selected_super_nombres:
    cols_metric = st.columns(len(selected_super_nombres))
    for idx, sup_nombre in enumerate(selected_super_nombres):
        sup_id = super_options[sup_nombre]

        # Productos propios que aparecen en este supermercado
        productos_actual = session.query(PrecioHistorico.nombre_original).join(
            ProductoReferencia, PrecioHistorico.producto_referencia_id == ProductoReferencia.id
        ).filter(
            PrecioHistorico.supermercado_id == sup_id,
            PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin),
            ProductoReferencia.marca.in_(marcas_propias),
            ProductoReferencia.activo == True
        ).distinct().all()
        count_actual = len(productos_actual)
        porcentaje = (count_actual / TOTAL_PRODUCTOS_PROPIOS) * 100

        # Verificar si hay datos del día anterior
        productos_ayer = session.query(PrecioHistorico.nombre_original).join(
            ProductoReferencia, PrecioHistorico.producto_referencia_id == ProductoReferencia.id
        ).filter(
            PrecioHistorico.supermercado_id == sup_id,
            PrecioHistorico.fecha_extraccion == ayer,
            ProductoReferencia.marca.in_(marcas_propias),
            ProductoReferencia.activo == True
        ).distinct().all()
        count_ayer = len(productos_ayer)
        # Verificar si hay datos de hace 7 días
        productos_7d = session.query(PrecioHistorico.nombre_original).join(
            ProductoReferencia, PrecioHistorico.producto_referencia_id == ProductoReferencia.id
        ).filter(
            PrecioHistorico.supermercado_id == sup_id,
            PrecioHistorico.fecha_extraccion == hace_7_dias,
            ProductoReferencia.marca.in_(marcas_propias),
            ProductoReferencia.activo == True
        ).distinct().all()
        count_7d = len(productos_7d)

        # Calcular variaciones solo si hay datos comparables (count_ayer > 0)
        if count_ayer > 0:
            var_diaria = ((count_actual - count_ayer) / count_ayer * 100)
            flecha_diaria = "↑" if var_diaria > 0 else ("↓" if var_diaria < 0 else "→")
            color_diaria = "#00A859" if var_diaria > 0 else ("#CC0000" if var_diaria < 0 else "#6C757D")
            texto_diaria = f"{abs(var_diaria):.1f}%"
        else:
            var_diaria = None

        if count_7d > 0:
            var_semanal = ((count_actual - count_7d) / count_7d * 100)
            flecha_semanal = "↑" if var_semanal > 0 else ("↓" if var_semanal < 0 else "→")
            color_semanal = "#00A859" if var_semanal > 0 else ("#CC0000" if var_semanal < 0 else "#6C757D")
            texto_semanal = f"{abs(var_semanal):.1f}%"
        else:
            var_semanal = None

        html = f"""
        <div class="super-metric">
            <strong>{sup_nombre}</strong><br>
            <span style="font-size: 1.8rem; color:#CC0000; font-weight:bold;">{count_actual}</span>
            <span style="font-size: 1rem;"> ({porcentaje:.1f}%)</span><br>
            <span style="font-size: 0.75rem;">productos aliados</span>
        """
        if var_diaria is not None:
            html += f"""
            <div style="font-size: 0.75rem; margin-top: 5px;">
                📈 vs ayer: <span style="color:{color_diaria};">{flecha_diaria} {texto_diaria}</span>
            </div>
            """
        if var_semanal is not None:
            html += f"""
            <div style="font-size: 0.75rem;">
                📅 vs hace 7d: <span style="color:{color_semanal};">{flecha_semanal} {texto_semanal}</span>
            </div>
            """
        html += "</div>"
        with cols_metric[idx]:
            st.markdown(html, unsafe_allow_html=True)
    st.markdown("---")

# Expander de diagnóstico
with st.expander("🔍 Productos propios encontrados en cada supermercado (según la BD)"):
    for sup_nombre in selected_super_nombres:
        sup_id = super_options[sup_nombre]
        productos_sup = session.query(PrecioHistorico.nombre_original).join(
            ProductoReferencia, PrecioHistorico.producto_referencia_id == ProductoReferencia.id
        ).filter(
            PrecioHistorico.supermercado_id == sup_id,
            PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin),
            ProductoReferencia.marca.in_(marcas_propias),
            ProductoReferencia.activo == True
        ).distinct().all()
        st.markdown(f"**{sup_nombre}** - {len(productos_sup)} productos")
        if productos_sup:
            df_detalle = pd.DataFrame([p[0] for p in productos_sup], columns=["Producto (nombre_original)"])
            st.dataframe(df_detalle, use_container_width=True, hide_index=True)
        else:
            st.caption("No hay productos propios en este supermercado")

with st.expander("📋 Lista de productos propios (total manual)"):
    st.caption(f"Total considerado para el porcentaje: {TOTAL_PRODUCTOS_PROPIOS} productos")
    st.info("Puedes ajustar el número cambiando la variable 'TOTAL_PRODUCTOS_PROPIOS' en el código.")

# ============================================================================
# SELECTOR DE PRODUCTO PROPIO
# ============================================================================
productos_propios_list = session.query(ProductoReferencia).filter(
    ProductoReferencia.marca.in_(marcas_propias),
    ProductoReferencia.activo == True
).all()
opciones = {f"{p.marca} - {p.nombre_producto} ({p.presentacion})" if p.presentacion else f"{p.marca} - {p.nombre_producto}": p.id for p in productos_propios_list}
producto_label = st.selectbox("🔍 Selecciona un producto propio:", list(opciones.keys()))
producto_id = opciones[producto_label]
producto_actual = session.get(ProductoReferencia, producto_id)

# ============================================================================
# PRECIOS DEL PRODUCTO PROPIO
# ============================================================================
precios_propio = session.query(PrecioHistorico).filter(
    PrecioHistorico.producto_referencia_id == producto_id,
    PrecioHistorico.supermercado_id.in_(selected_super_ids),
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).all()
if not precios_propio:
    st.warning(f"⚠️ El producto '{producto_label}' no tiene precios en los supermercados seleccionados. Se mostrará solo la competencia.")

# ============================================================================
# COMPETIDORES
# ============================================================================
todos_precios = session.query(PrecioHistorico).filter(
    PrecioHistorico.supermercado_id.in_(selected_super_ids),
    PrecioHistorico.fecha_extraccion.between(fecha_inicio, fecha_fin)
).all()

reglas = session.execute(text("SELECT palabras_incluir, palabras_excluir FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id}).fetchone()
competidores = []
if reglas and (reglas[0] or reglas[1]):
    palabras_incluir = list(reglas[0]) if reglas[0] else []
    palabras_excluir = list(reglas[1]) if reglas[1] else []
    for p in todos_precios:
        if p.producto_referencia_id == producto_id:
            continue
        if cumple_reglas(p.nombre_original, palabras_incluir, palabras_excluir):
            competidores.append(p)
    st.info(f"📏 Usando reglas personalizadas: +{', '.join(palabras_incluir)}  -{', '.join(palabras_excluir)}")
else:
    categoria_propia = normalizar_categoria(producto_actual.nombre_producto)
    for p in todos_precios:
        if p.producto_referencia_id == producto_id:
            continue
        if normalizar_categoria(p.nombre_original) == categoria_propia:
            competidores.append(p)
    st.info(f"📏 Sin reglas, usando categoría: '{categoria_propia}'")

# ============================================================================
# TABLA COMPARATIVA (con colores directos para extremos)
# ============================================================================
todas_fechas = sorted(set(p.fecha_extraccion.date() for p in (precios_propio + competidores)))
if not todas_fechas:
    st.warning("No hay fechas disponibles.")
    st.stop()
else:
    fecha_comun = todas_fechas[-1]
    ultimos_hasta_fecha = {}
    for p in (precios_propio + competidores):
        if p.fecha_extraccion.date() <= fecha_comun:
            key = (p.supermercado_id, p.nombre_original)
            precio_val = p.precio_usd if usar_usd else p.precio_bs
            if key not in ultimos_hasta_fecha or p.fecha_extraccion > ultimos_hasta_fecha[key]["fecha"]:
                ultimos_hasta_fecha[key] = {
                    "precio": float(precio_val),
                    "fecha": p.fecha_extraccion,
                    "nombre_original": p.nombre_original,
                }
    
    productos_unicos = sorted(set(k[1] for k in ultimos_hasta_fecha.keys()))
    super_ids_unicos = sorted(set(k[0] for k in ultimos_hasta_fecha.keys()))
    super_nombres = [session.get(Supermercado, sid).nombre for sid in super_ids_unicos]
    
    df_valores = pd.DataFrame(index=[formatear_nombre_producto(prod) for prod in productos_unicos], columns=super_nombres)
    for prod in productos_unicos:
        prod_formateado = formatear_nombre_producto(prod)
        for sid, sup_nombre in zip(super_ids_unicos, super_nombres):
            key = (sid, prod)
            if key in ultimos_hasta_fecha:
                precio = ultimos_hasta_fecha[key]["precio"]
                fecha = ultimos_hasta_fecha[key]["fecha"]
                celda = f"{precio:.2f} ({fecha.strftime('%d/%m')})" if precio else "Sin datos"
            else:
                celda = "Sin datos"
            df_valores.loc[prod_formateado, sup_nombre] = celda
    
    nombre_propio_tabla = None
    for prod in productos_unicos:
        if producto_actual.nombre_producto.lower() in prod.lower() or producto_actual.marca.lower() in prod.lower():
            nombre_propio_tabla = formatear_nombre_producto(prod)
            break
    if not nombre_propio_tabla and precios_propio:
        nombre_propio_tabla = formatear_nombre_producto(precios_propio[0].nombre_original)
    
    # Función para colorear extremos directamente con estilos CSS en línea
    def colorear_extremos(fila):
        estilos = []
        precios = []
        for col in fila.index:
            celda = fila[col]
            if celda != "Sin datos":
                try:
                    precio = float(celda.split()[0])
                    precios.append((col, precio))
                except:
                    precios.append((col, None))
            else:
                precios.append((col, None))
        validos = [(col, p) for (col, p) in precios if p is not None]
        if not validos:
            return [''] * len(fila)
        min_precio = min(p[1] for p in validos)
        max_precio = max(p[1] for p in validos)
        for col, p in precios:
            if p is None:
                estilos.append('')
            elif p == min_precio:
                estilos.append('color: #00A859; font-weight: bold;')
            elif p == max_precio:
                estilos.append('color: #CC0000; font-weight: bold;')
            else:
                estilos.append('')
        return estilos
    
    def resaltar_fila(row):
        if row.name == nombre_propio_tabla:
            return ['background-color: #2E7D32; color: white; font-weight: bold;'] * len(row)
        return [''] * len(row)
    
    styled = df_valores.style.apply(resaltar_fila, axis=1)
    styled = styled.apply(colorear_extremos, axis=1)
    styled = styled.set_properties(**{'text-align': 'center', 'font-size': '13px'})
    styled = styled.set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('background-color', '#CC0000'), ('color', 'white'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#FFF0F0')]},
    ])
    
    st.subheader(f"🛒 Comparativa: {producto_actual.marca} - {producto_actual.nombre_producto}")
    st.dataframe(styled, use_container_width=True, height=400)
    st.markdown(f"<p class='centered-title'>📅 Precios correspondientes a la fecha más reciente con datos: {fecha_comun.strftime('%d/%m/%Y')} (cada celda muestra su última actualización hasta esa fecha)</p>", unsafe_allow_html=True)

# ============================================================================
# KPIS
# ============================================================================
st.subheader("📈 Indicadores Clave")

if precios_propio:
    ultimo_precio_propio = max(precios_propio, key=lambda x: x.fecha_extraccion)
    precio_propio_ultimo = float(ultimo_precio_propio.precio_usd if usar_usd else ultimo_precio_propio.precio_bs)
    fecha_propio_ultimo = ultimo_precio_propio.fecha_extraccion
    ultimo_precio_texto = f"{precio_propio_ultimo:.2f} {moneda}"
else:
    precio_propio_ultimo = 0
    ultimo_precio_texto = "Sin datos"

precios_competidores_tabla = []
if 'df_valores' in locals() and nombre_propio_tabla:
    for idx in df_valores.index:
        if idx != nombre_propio_tabla:
            for col in df_valores.columns:
                celda = df_valores.loc[idx, col]
                if celda != "Sin datos":
                    try:
                        precio = float(celda.split()[0])
                        precios_competidores_tabla.append(precio)
                    except:
                        pass

if precios_competidores_tabla:
    if st.session_state.estadistica == "Mediana":
        valor_comp = np.median(precios_competidores_tabla)
    else:
        valor_comp = np.mean(precios_competidores_tabla)
    num_comp_tabla = len(precios_competidores_tabla)
else:
    valor_comp = 0
    num_comp_tabla = 0

diff = precio_propio_ultimo - valor_comp
diff_rel = (diff / valor_comp) * 100 if valor_comp else 0

if precio_propio_ultimo > valor_comp:
    clase_metric = "metric-red"
    mensaje = "Precio por encima de la competencia"
    icono = "🔴"
elif precio_propio_ultimo < valor_comp:
    clase_metric = "metric-green"
    mensaje = "Precio por debajo de la competencia"
    icono = "🟢"
else:
    clase_metric = "metric-neutral"
    mensaje = "Precio igual a la competencia"
    icono = "⚪"

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="{clase_metric}" title="Último precio registrado del producto propio">
        <strong>💰 {producto_actual.marca} (Último)</strong><br>
        <span style="font-size: 1.8rem;">{ultimo_precio_texto}</span>
        <div style="font-size: 0.7rem; margin-top: 4px;">📅 Fecha: {fecha_propio_ultimo.strftime('%d/%m/%Y') if precios_propio else 'N/A'}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="{clase_metric}" title="Promedio/Mediana de los últimos precios de los competidores mostrados en la tabla">
        <strong>🏷️ Competencia (en tabla)</strong><br>
        <span style="font-size: 1.8rem;">{valor_comp:.2f} {moneda}</span>
        <div style="font-size: 0.7rem; margin-top: 4px;">📊 Basado en {num_comp_tabla} precios de competidores</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="{clase_metric}">
        <strong>📊 Diferencia</strong><br>
        <span style="font-size: 1.6rem;">{diff:+.2f} {moneda}</span><br>
        <span style="font-size: 0.9rem;">({diff_rel:+.1f}%)</span><br>
        <span style="font-size: 0.85rem;">{icono} {mensaje}</span>
    </div>
    """, unsafe_allow_html=True)

st.caption(f"🔍 Análisis basado en los últimos precios disponibles: producto propio vs competidores mostrados en la tabla. Estadística: {st.session_state.estadistica} sobre los precios de competidores.")

# ============================================================================
# GRÁFICO EVOLUTIVO
# ============================================================================
titulo_est = "Mediana" if st.session_state.estadistica == "Mediana" else "Promedio"

st.subheader(f"📈 Evolución de precios - {titulo_est} de la competencia vs producto propio")
st.caption(f"📅 Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")

fechas_disponibles = sorted(set(p.fecha_extraccion.date() for p in (precios_propio + competidores)))
if not fechas_disponibles:
    st.info("No hay datos para el gráfico evolutivo.")
else:
    ultimos_por_fecha = {}
    for fecha in fechas_disponibles:
        if fecha > fechas_disponibles[0]:
            idx_prev = fechas_disponibles.index(fecha)-1
            ultimos_por_fecha[fecha] = ultimos_por_fecha[fechas_disponibles[idx_prev]].copy()
        else:
            ultimos_por_fecha[fecha] = {}
        for p in competidores:
            if p.fecha_extraccion.date() == fecha:
                key = p.nombre_original
                precio = p.precio_usd if usar_usd else p.precio_bs
                ultimos_por_fecha[fecha][key] = precio
        for p in precios_propio:
            if p.fecha_extraccion.date() == fecha:
                key = f"__propio__{p.nombre_original}"
                precio = p.precio_usd if usar_usd else p.precio_bs
                ultimos_por_fecha[fecha][key] = precio
    
    datos_evol = []
    for fecha in fechas_disponibles:
        precios_comp = [v for k, v in ultimos_por_fecha[fecha].items() if not k.startswith('__propio__')]
        if precios_comp:
            if st.session_state.estadistica == "Mediana":
                stat_comp = np.median(precios_comp)
            else:
                stat_comp = np.mean(precios_comp)
            datos_evol.append({"Fecha": fecha, "Tipo": "Competencia", "Precio": stat_comp})
        precios_prop_hasta_fecha = [v for k, v in ultimos_por_fecha[fecha].items() if k.startswith('__propio__')]
        if precios_prop_hasta_fecha:
            ultimo_precio_prop = precios_prop_hasta_fecha[-1]
            datos_evol.append({"Fecha": fecha, "Tipo": producto_actual.marca, "Precio": ultimo_precio_prop})
    
    df_evol = pd.DataFrame(datos_evol).sort_values("Fecha").drop_duplicates(subset=["Fecha", "Tipo"])
    
    if not df_evol.empty:
        colores_map = {producto_actual.marca: "#CC0000", "Competencia": "#00A859"}
        fig_evol = px.line(df_evol, x="Fecha", y="Precio", color="Tipo", markers=True,
                           labels={"Precio": f"Precio ({moneda})", "Fecha": "Fecha"},
                           color_discrete_map=colores_map,
                           title=f"Evolución - {titulo_est} diaria (último precio por competidor)")
        fig_evol.update_traces(textposition="top center", texttemplate='%{y:.2f}', marker=dict(size=8))
        if st.session_state.tema == "dark":
            fig_evol.update_layout(
                plot_bgcolor="#2D2D2D",
                paper_bgcolor="#2D2D2D",
                legend_title=None,
                height=450,
                hovermode="x unified",
                font=dict(color="white", size=12),
                legend=dict(font=dict(color="white"), bgcolor="#2D2D2D", bordercolor="white", borderwidth=1)
            )
            fig_evol.update_xaxes(title_font_color="white", tickfont_color="white", gridcolor="#555555")
            fig_evol.update_yaxes(title_font_color="white", tickfont_color="white", gridcolor="#555555")
        else:
            fig_evol.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend_title=None,
                height=450,
                hovermode="x unified",
                font=dict(color="black", size=12)
            )
        fig_evol.update_xaxes(tickformat="%Y-%m-%d", tickangle=45, dtick="D1")
        st.plotly_chart(fig_evol, use_container_width=True)
    else:
        st.info("No hay datos suficientes para el gráfico evolutivo.")

# ============================================================================
# BOXPLOT POR DÍA
# ============================================================================
st.subheader("📊 Distribución de precios de la competencia por día (Boxplot)")
st.caption(f"📅 Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
if competidores:
    box_data = []
    for p in competidores:
        fecha = p.fecha_extraccion.date()
        precio = p.precio_usd if usar_usd else p.precio_bs
        sup_nombre = session.get(Supermercado, p.supermercado_id).nombre
        box_data.append({"Fecha": fecha, "Precio": precio, "Supermercado": sup_nombre, "Producto": p.nombre_original})
    df_box = pd.DataFrame(box_data)
    fig_box = px.box(df_box, x="Fecha", y="Precio", points="all",
                     labels={"Precio": f"Precio ({moneda})", "Fecha": "Fecha"},
                     title="Distribución diaria de precios de competidores",
                     color_discrete_sequence=["#00A859"])
    fig_box.update_traces(marker=dict(size=6, color="#00A859", opacity=0.7), jitter=0, pointpos=0,
                          hovertemplate='<b>Producto:</b> %{text}<br><b>Precio:</b> %{y:.2f}<extra></extra>',
                          text=df_box['Producto'] + ' (' + df_box['Supermercado'] + ')')
    if st.session_state.tema == "dark":
        fig_box.update_layout(
            plot_bgcolor="#2D2D2D",
            paper_bgcolor="#2D2D2D",
            height=450,
            font=dict(color="white"),
            legend=dict(font=dict(color="white"), bgcolor="#2D2D2D", bordercolor="white", borderwidth=1)
        )
        fig_box.update_xaxes(title_font_color="white", tickfont_color="white", gridcolor="#555555")
        fig_box.update_yaxes(title_font_color="white", tickfont_color="white", gridcolor="#555555")
    else:
        fig_box.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=450,
            font=dict(color="black")
        )
    fig_box.update_xaxes(tickformat="%Y-%m-%d", tickangle=45, dtick="D1")
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("No hay competidores para mostrar boxplot.")

# ============================================================================
# NUEVO GRÁFICO: TOP 3 COMPETIDORES MÁS BARATOS vs PRODUCTO PROPIO
# ============================================================================
with st.expander("🏆 Comparativa de precios: Competidores más baratos vs producto propio"):
    if precios_propio and competidores:
        precio_propio = precio_propio_ultimo
        ultimos_competidores = {}
        for p in competidores:
            key = p.nombre_original
            if key not in ultimos_competidores or p.fecha_extraccion > ultimos_competidores[key]['fecha']:
                ultimos_competidores[key] = {'precio': float(p.precio_usd if usar_usd else p.precio_bs), 'fecha': p.fecha_extraccion}
        top_3 = sorted(ultimos_competidores.items(), key=lambda x: x[1]['precio'])[:3]
        
        if top_3:
            data_bar = []
            data_bar.append({"Competidor": producto_actual.marca, "Precio": precio_propio, "Tipo": "Propio"})
            for nombre, info in top_3:
                data_bar.append({"Competidor": nombre[:45], "Precio": info['precio'], "Tipo": "Competencia"})
            df_bar = pd.DataFrame(data_bar)
            fig_bar = px.bar(df_bar, x="Competidor", y="Precio", color="Tipo",
                             color_discrete_map={"Propio": "#CC0000", "Competencia": "#00A859"},
                             title="Último precio: Producto propio vs 3 competidores más baratos",
                             labels={"Precio": f"Precio ({moneda})", "Competidor": ""},
                             text="Precio")
            fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_bar.update_layout(height=450, xaxis_tickangle=-45, font=dict(size=11))
            if st.session_state.tema == "dark":
                fig_bar.update_layout(plot_bgcolor="#2D2D2D", paper_bgcolor="#2D2D2D", font=dict(color="white"))
            else:
                fig_bar.update_layout(plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"))
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.markdown("**📋 Detalle de los competidores más económicos:**")
            detalle = []
            for nombre, info in top_3:
                detalle.append({"Competidor": nombre, "Precio": f"{info['precio']:.2f} {moneda}", "Fecha": info['fecha'].strftime('%d/%m/%Y')})
            st.dataframe(pd.DataFrame(detalle), use_container_width=True, hide_index=True)
        else:
            st.info("No hay competidores con precios para comparar.")
    else:
        st.warning("No hay datos del producto propio o no hay competidores en el período seleccionado.")

# ============================================================================
# GRÁFICO POR SUPERMERCADO (MEJORADO)
# ============================================================================
with st.expander("📊 Evolución de precios del producto propio por supermercado"):
    if precios_propio:
        # Convertir a DataFrame
        df_sup = []
        for p in precios_propio:
            sup_nombre = session.get(Supermercado, p.supermercado_id).nombre
            precio = p.precio_usd if usar_usd else p.precio_bs
            df_sup.append({"Fecha": p.fecha_extraccion.date(), "Supermercado": sup_nombre, "Precio": float(precio)})
        df_sup = pd.DataFrame(df_sup)
        if not df_sup.empty:
            # Obtener lista de supermercados únicos
            supermercados_unicos = df_sup['Supermercado'].unique()
            # Selección múltiple de supermercados a mostrar
            seleccion_sup = st.multiselect("Selecciona supermercados a visualizar:", options=supermercados_unicos, default=supermercados_unicos, key="sup_selector")
            if seleccion_sup:
                df_filtrado = df_sup[df_sup['Supermercado'].isin(seleccion_sup)]
                if not df_filtrado.empty:
                    fig_sup = px.line(df_filtrado, x="Fecha", y="Precio", color="Supermercado", markers=True,
                                      labels={"Precio": f"Precio ({moneda})", "Fecha": "Fecha"},
                                      title=f"Evolución de {producto_actual.marca} - {producto_actual.nombre_producto} por supermercado")
                    fig_sup.update_traces(marker=dict(size=8))
                    # Ajustes de diseño
                    fig_sup.update_layout(
                        xaxis_title="Fecha",
                        yaxis_title=f"Precio ({moneda})",
                        legend_title="Supermercado",
                        height=450,
                        hovermode="x unified"
                    )
                    if st.session_state.tema == "dark":
                        fig_sup.update_layout(plot_bgcolor="#2D2D2D", paper_bgcolor="#2D2D2D", font=dict(color="white"))
                        fig_sup.update_xaxes(gridcolor="#555555", title_font_color="white", tickfont_color="white")
                        fig_sup.update_yaxes(gridcolor="#555555", title_font_color="white", tickfont_color="white")
                        fig_sup.update_layout(legend=dict(font=dict(color="white"), bgcolor="#2D2D2D", bordercolor="white", borderwidth=1))
                    else:
                        fig_sup.update_layout(plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"))
                    fig_sup.update_xaxes(tickformat="%Y-%m-%d", tickangle=45)
                    st.plotly_chart(fig_sup, use_container_width=True)
                else:
                    st.info("No hay datos para los supermercados seleccionados.")
            else:
                st.warning("Selecciona al menos un supermercado.")
        else:
            st.info("No hay datos suficientes para el gráfico por supermercado.")
    else:
        st.warning("No hay precios del producto propio en el período seleccionado.")

# ============================================================================
# EDITOR DE REGLAS Y DIAGNÓSTICO
# ============================================================================
with st.expander("✏️ Editar reglas de inclusión/exclusión para este producto"):
    st.markdown("""
    **Instrucciones:**  
    - **Incluir** (separado por comas): palabras que **deben** aparecer en el nombre del competidor.  
    - **Excluir** (separado por comas): palabras que **no** deben aparecer.  
    """)
    reglas_actuales = session.execute(text("SELECT palabras_incluir, palabras_excluir FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id}).fetchone()
    incluir_actual = ", ".join(reglas_actuales[0]) if reglas_actuales and reglas_actuales[0] else ""
    excluir_actual = ", ".join(reglas_actuales[1]) if reglas_actuales and reglas_actuales[1] else ""
    incluir_edit = st.text_input("Palabras que DEBEN aparecer", value=incluir_actual)
    excluir_edit = st.text_input("Palabras que NO deben aparecer", value=excluir_actual)
    if st.button("Guardar reglas"):
        nueva_incluir = [p.strip().lower() for p in incluir_edit.split(",") if p.strip()]
        nueva_excluir = [p.strip().lower() for p in excluir_edit.split(",") if p.strip()]
        session.execute(text("DELETE FROM reglas_match WHERE producto_propio_id = :pid"), {"pid": producto_id})
        session.execute(text("INSERT INTO reglas_match (producto_propio_id, palabras_incluir, palabras_excluir) VALUES (:pid, :incluir, :excluir)"), {"pid": producto_id, "incluir": nueva_incluir, "excluir": nueva_excluir})
        session.commit()
        st.success("Reglas guardadas. Recargando página...")
        st.rerun()

with st.expander("🔍 Diagnóstico (reglas y competidores rechazados)"):
    if reglas and (reglas[0] or reglas[1]):
        st.write(f"**Reglas activas:** Incluir: {', '.join(palabras_incluir)} | Excluir: {', '.join(palabras_excluir)}")
        st.write("**Competidores ACEPTADOS (mostrados en tabla):**")
        for p in competidores[:20]:
            st.write(f"✅ {p.nombre_original}")
        st.write("**Competidores RECHAZADOS (primeros 20):**")
        rechazados = [p for p in todos_precios if p.producto_referencia_id != producto_id and not cumple_reglas(p.nombre_original, palabras_incluir, palabras_excluir)]
        for p in rechazados[:20]:
            st.write(f"❌ {p.nombre_original}")
    else:
        st.write("No hay reglas definidas, se usa categoría automática.")

session.close()
st.caption("🚀 Los KPIs muestran el último precio del producto propio y el promedio/mediana de los competidores que aparecen en la tabla. El gráfico evolutivo usa el último precio por competidor hasta cada fecha. Los porcentajes de productos por supermercado se calculan sobre un total manual de 21 productos propios. Las variaciones solo se muestran cuando hay datos comparables.")
