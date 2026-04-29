import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Engenharia de Fusos Pro", layout="wide")

# --- BANCOS DE DADOS ---
atrito_materiais = {"Bronze (Lubrificado)": 0.10, "Polímero": 0.08, "Aço": 0.15}
atrito_guias = {"Guia Linear": 0.005, "Deslizamento": 0.15, "Sem Guia": 0.0}

st.title("⚙️ Simulador de Dinâmica e Precisão de Fusos")

# --- SIDEBAR ---
st.sidebar.header("1. Geometria")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0)

st.sidebar.header("2. Dinâmica e Carga")
massa_total = st.sidebar.number_input("Massa Total (kg)", value=50.0)
v_desejada = st.sidebar.number_input("Velocidade (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo Acc (s)", value=0.2)
angulo_deg = st.sidebar.slider("Inclinação (°)", 0, 90, 0)

st.sidebar.header("3. Parâmetros de Precisão")
if tipo_fuso == "Trapezoidal":
    backlash_nominal = st.sidebar.slider("Folga (Backlash) da Porca (mm)", 0.05, 0.30, 0.10)
else:
    backlash_nominal = st.sidebar.slider("Folga (Backlash) da Porca (mm)", 0.00, 0.05, 0.01)

# --- CÁLCULOS DINÂMICOS ---
g = 9.81
ang_rad = math.radians(angulo_deg)
f_axial_estatica = (massa_total * g * math.sin(ang_rad)) + (0.005 * massa_total * g * math.cos(ang_rad))
f_inercia = massa_total * ((v_desejada / 1000) / t_acc)
f_axial_total = f_axial_estatica + f_inercia

# --- CÁLCULOS DE PRECISÃO ---
# 1. Deformação Elástica (Delta = F * L / A * E)
E_aco = 210000 # N/mm² (MPa)
area_nuc_mm2 = (math.pi * d_nuc**2) / 4
# Calculamos a deformação no comprimento total (pior caso)
deformacao_mm = (f_axial_total * (comprimento * 1000)) / (area_nuc_mm2 * E_aco)
erro_total_micras = (deformacao_mm + backlash_nominal) * 1000

# Torque e Potência
d_medio = (d_nom + d_nuc) / 2
tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.9 * 1000) if tipo_fuso == "Esferas" else (f_axial_total * 0.005) # Simplificado

# --- INTERFACE ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Erro de Precisão Total", f"{erro_total_micras:.1f} µm")
c2.metric("Deformação Elástica", f"{deformacao_mm*1000:.1f} µm")
c3.metric("Torque de Pico", f"{tr_nm:.2f} N.m")
c4.metric("Vel. de Avanço", f"{v_desejada} mm/s")

st.divider()

col_inf1, col_inf2 = st.columns(2)

with col_inf1:
    st.subheader("🎯 Análise de Incerteza de Posição")
    st.write(f"Ao aplicar uma carga de **{f_axial_total:.1f} N**, o fuso sofre uma deformação de **{deformacao_mm:.4f} mm**.")
    st.write(f"Somado ao backlash da porca (**{backlash_nominal} mm**), sua precisão teórica é de **±{erro_total_micras/1000:.3f} mm**.")
    
    if erro_total_micras > 100:
        st.warning("⚠️ Precisão Baixa: Recomendado usar fuso de esferas ou maior diâmetro.")
    else:
        st.success("✅ Precisão compatível com aplicações de média/alta fidelidade.")

with col_inf2:
    st.subheader("📈 Relação Deformação x Carga")
    # Gráfico simples de Hooke
    cargas_hooke = [c for c in range(0, int(f_axial_total * 1.5), 100)]
    defors_hooke = [(c * (comprimento * 1000)) / (area_nuc_mm2 * E_aco) * 1000 for c in cargas_hooke]
    df_precisao = pd.DataFrame({"Carga (N)": cargas_hooke, "Deformação (µm)": defors_hooke})
    st.plotly_chart(px.line(df_precisao, x="Carga (N)", y="Deformação (µm)", title="Elasticidade do Fuso"), use_container_width=True)
