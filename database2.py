import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from datetime import datetime

# ============================================================================
# CONEXIÓN A SUPABASE (Transaction pooler, puerto 6543)
# Usa la contraseña que generaste: zv938jjYf3wWjONO
# ============================================================================
DB_URI_NUBE = "postgresql://postgres.tmeyajjnufkzzlgsuxxh:dNLKduxW3lKzQt7A@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(
    DB_URI_NUBE,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 10},
    poolclass=NullPool   # Evita problemas en Streamlit Cloud
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================================
# MODELOS (exactamente como los tienes en tu base de datos local)
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