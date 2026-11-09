"""Conexão com o MySQL (SQLAlchemy + PyMySQL). O endereço vem de DB_URL no backend/.env."""
from sqlalchemy import create_engine

import config

engine = create_engine(config.DB_URL, pool_pre_ping=True, pool_recycle=3600)
