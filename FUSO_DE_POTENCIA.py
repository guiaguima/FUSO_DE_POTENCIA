import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dimensionamento de Fusos", layout="wide", page_icon="⚙️")

# --- BANCO DE DADOS TÉCNICO ---
# Coeficientes de atrito médios (Lubrificados)
atrito_materiais = {
    "Bronze (Fosforoso/Grafitado)": 0.10,
    "Latão": 0.12,
    "Ferro Fundido": 0.15,
    "Aço (Fuso Aço + Porca Aço)": 0.20,
    "Polímero / Nylon (Autolubrificante)": 0.08
}

fatores_apoio = {
    "Apoiado - Apoiado (Simples)": 0.97,
    "Fixo - Apoiado (Engastado/Simples)": 1.51,
    "Fixo - Fixo (Engastado/Engastado)": 2.19,
    "Fixo - Livre (Balanço)": 0.34
}

st.title("⚙️ Dimensionamento de Fusos de Potência")
st.markdown("Cálculo de torque, potência, estabilidade e lubrificação.")

# --- SIDEBAR: ENTRADAS ---
st.sidebar.header("1. Geometria do Fuso")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal (Deslizamento)", "Esferas"])

d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0, step=1.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0, step=0.1)
passo = st.sidebar.number_input("Avanço / Passo (mm)", value=5.0, step=0.5)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0, step=0.1)

st.sidebar.header("2. Material e Atrito")
if tipo_fuso == "Trapezoidal (Deslizamento)":
    material_porca = st.sidebar.selectbox("Material da Porca (Fuso em Aço)", list(atrito_materiais.keys()))
    mu = atrito_materiais[material_porca]
    st.sidebar.caption(f"Coeficiente de atrito (μ) assumido: {mu}")
else:
    mu = 0.02 # Atrito de rolamento desprezível
    eficiencia_esferas = st.sidebar.slider("Eficiência do Fuso de Esferas (η)", 0.85, 0.98, 0.90)

st.sidebar.header("3. Operação")
carga = st.sidebar.number_input("Carga Axial (N)", value=2000.0, step=100.0)
rpm = st.sidebar.number_input("Rotação de Trabalho (RPM)", value=500.0, step=50.0)
tipo_apoio = st.sidebar.selectbox("Tipo de Fixação das Extremidades", list(fatores_apoio.keys()))

# --- CÁLCULOS DE ENGENHARIA ---

d_medio = (d_nom + d_nuc) / 2
omega = (2 * math.pi * rpm) / 60  # rad/s

# 1. Torque e Potência
if tipo_fuso == "Trapezoidal (Deslizamento)":
    alfa = math.radians(14.5) # Ângulo de flanco padrão ACME
    sec_alfa = 1 / math.cos(alfa)
    
    # Torque para subir carga (Tr)
    num = passo + math.pi * mu * d_medio * sec_alfa
    den = math.pi * d_medio - mu * passo * sec_alfa
    tr_nm = (carga * d_medio / 2 * (num / den)) / 1000
    
    # Torque para descer carga (Tl)
    num_l = math.pi * mu * d_medio * sec_alfa - passo
    den_l = math.pi * d_medio + mu * passo * sec_alfa
    tl_nm = (carga * d_medio / 2 * (num_l / den_l)) / 1000
else:
    tr_nm = (carga * passo) / (2 * math.pi * eficiencia_esferas * 1000)
    tl_nm = (carga * passo * eficiencia_esferas) / (2 * math.pi * 1000)

potencia_w = tr_nm * omega

# 2. Velocidade Crítica e Flambagem
E = 210000000000 # Módulo de Elasticidade Aço (Pa)
I = (math.pi * (d_nuc/1000)**4) / 64 # Momento de Inércia (m4)
rho = 7850 # kg/m3
m_linear = (math.pi * (d_nuc/2000)**2) * rho # kg/m

fs_v = fatores_apoio[tipo_apoio]
n_critica = (fs_v * 9.55 * (math.pi / comprimento**2) * math.sqrt((E * I) / m_linear))

# --- EXIBIÇÃO DE RESULTADOS ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Torque de Subida", f"{tr_nm:.2f} N.m")
with c2:
    st.metric("Potência Requerida", f"{potencia_w:.2f} W")
with c3:
    st.metric("Vel. Crítica", f"{int(n_critica)} RPM")

st.divider()

# --- ANÁLISE TÉCNICA ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🛡️ Estabilidade")
    if rpm > n_critica * 0.8:
        st.error(f"ALERTA: Rotação muito próxima da crítica ({int(n_critica)} RPM). Risco de vibração excessiva.")
    else:
        st.success("Rotação segura em relação à velocidade crítica.")
    
    # Verificação de Auto-bloqueio (Trapezoidal)
    if tipo_fuso == "Trapezoidal (Deslizamento)":
        if tl_nm > 0:
            st.info("Fuso Autobloqueante: A carga não desce sozinha.")
        else:
            st.warning("Fuso Não-Autobloqueante: A carga pode descer sem torque aplicado.")

with col_b:
    st.subheader("💧 Lubrificação Sugerida")
    vol_relub = (d_nom * passo) * 0.0015
    st.write(f"Volume de relubrificação: **{vol_relub:.2f} cm³**")
    st.caption("Frequência recomendada: a cada 200km de percurso linear ou 500h de uso.")

# --- GRÁFICO ---
st.subheader("📊 Sensibilidade: Torque x Carga Axial")
cargas_sim = [c for c in range(0, int(carga * 2), 100)]
if tipo_fuso == "Trapezoidal (Deslizamento)":
    torques_sim = [((c * d_medio / 2 * ((passo + math.pi * mu * d_medio * 1.03) / (math.pi * d_medio - mu * passo * 1.03))) / 1000) for c in cargas_sim]
else:
    torques_sim = [(c * passo) / (2 * math.pi * 0.9 * 1000) for c in cargas_sim]

df_fig = pd.DataFrame({"Carga (N)": cargas_sim, "Torque (N.m)": torques_sim})
st.plotly_chart(px.line(df_fig, x="Carga (N)", y="Torque (N.m)"), use_container_width=True)
