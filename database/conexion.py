import streamlit as st
from sqlalchemy import create_engine

# Lee la URL directamente desde los Secrets seguros de Streamlit Cloud
DATABASE_URL = st.secrets["DATABASE_URL"]

# Crea el motor de SQLAlchemy
engine = create_engine(DATABASE_URL)
