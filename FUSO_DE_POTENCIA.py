import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Engenharia de Fusos Pro", layout="wide")

# --- BANCOS DE DADOS ---
atrito_materiais = {"Bronze (Lubrificado)": 0.10, "Latão": 0.12, "Polímero": 0.08, "Aço": 0.15}
atrito_guias = {"Guia Linear": 0.005, "Deslizamento": 0.15, "Sem Guia": 0.0}
fatores_apoio = {"Simples-Simples": 0.97, "Fixo-Simples": 1.51, "Fixo-Fixo": 2.19, "Fixo-Livre": 0.34}

st.title("⚙️ Analisador Especialista de Fusos")

# --- SIDEBAR: TODOS OS INPUTS ---
st.sidebar.header("1. Geometria e Montagem")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0)
tipo_apoio = st.sidebar.selectbox("Fixação das Extremidades", list(fatores_apoio.keys()))

st.sidebar.header("2. Dinâmica e Carga")
massa_total = st.sidebar.number_input("Massa Total (kg)", value=50.0)
v_desejada = st.sidebar.number_input("Velocidade Alvo (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo de Aceleração (s)", value=0.2)
angulo_deg = st.sidebar.slider("Inclinação (0°=H, 90°=V)", 0, 90, 0)
mat_guia = st.sidebar.selectbox("Tipo de Guia", list(atrito_guias.keys()))

if tipo_fuso == "Esferas":
    st.sidebar.header("3. Parâmetros de Esferas")
    ca_dinamico = st.sidebar.number_input("Capacidade Dinâmica C (N)", value=12000.0)
else:
    st.sidebar.header("3. Parâmetros de Deslizamento")
    mat_porca = st.sidebar.selectbox("Material da Porca", list(atrito_materiais.keys()))
    altura_porca = st.sidebar.number_input("Altura da Porca (mm)", value=30.0)

# --- CÁLCULOS ---

# A. Dinâmica de Forças
g = 9.81
ang_rad = math.radians(angulo_deg)
mu_guia = atrito_guias[mat_guia]
f_axial_estatica = (massa_total * g * math.sin(ang_rad)) + (mu_guia * massa_total * g * math.cos(ang_rad))
aceleracao = (v_desejada / 1000) / t_acc
f_inercia = massa_total * aceleracao
f_axial_total = f_axial_estatica + f_inercia

# B. Torque e Potência
d_medio = (d_nom + d_nuc) / 2
rpm = (v_desejada * 60) / passo
omega = (2 * math.pi * rpm) / 60

if tipo_fuso == "Trapezoidal":
    mu_fuso = atrito_materiais[mat_porca]
    sec_alfa = 1 / math.cos(math.radians(14.5))
    num = passo + math.pi * mu_fuso * d_medio * sec_alfa
    den = math.pi * d_medio - mu_fuso * passo * sec_alfa
    tr_nm = (f_axial_total * d_medio / 2 * (num / den)) / 1000
else:
    tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.90 * 1000)

potencia_w = tr_nm * omega

# C. Segurança e Vibração
E = 2.1e11
I = (math.pi * (d_nuc/1000)**4) / 64
m_fuso_lin = (math.pi * (d_nuc/2000)**2) * 7850
n_critica = (fatores_apoio[tipo_apoio] * 9.55 * (math.pi / comprimento**2) * math.sqrt((E * I) / m_fuso_lin))
carga_critica = (math.pi**2 * E * I) / (2.0 * comprimento)**2
fs_flambagem = carga_critica / f_axial_total if f_axial_total > 0 else 100

# D. Vida Útil e Desgaste
if tipo_fuso == "Esferas":
    l10_horas = (ca_dinamico / (f_axial_total * 1.2))**3 * 10**6 / (rpm * 60) if rpm > 0 else 0
else:
    vel_desl = (rpm * passo) / 60000
    area_cont = math.pi * d_medio * (altura_porca / 2)
    pv_valor = (f_axial_total / area_cont) * vel_desl

# E. Precisão
deformacao_mm = (f_axial_total * (comprimento * 1000)) / (((math.pi * d_nuc**2)/4) * 210000)

# --- INTERFACE PRINCIPAL ---

# 1. Cards de Resumo
st.subheader("📊 Indicadores Principais (Pico de Aceleração)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Torque", f"{tr_nm:.2f} N.m")
m2.metric("Potência", f"{potencia_w:.1f} W")
m3.metric("Vel. Crítica", f"{int(n_critica)} RPM")
m4.metric("F.S. Flambagem", f"{fs_flambagem:.2f}")

st.divider()

# 2. Tabs Organizadoras
tab_din, tab_seg, tab_manut = st.tabs(["🚀 Dinâmica e Precisão", "🛡️ Segurança Estrutural", "💧 Manutenção e Vida"])

with tab_din:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write("**Perfil de Movimento**")
        st.write(f"Aceleração Linear: {aceleracao:.2f} m/s²")
        st.write(f"Rotação Necessária: {int(rpm)} RPM")
        fig_v = px.line(x=[0, t_acc, t_acc+1], y=[0, v_desejada, v_desejada], labels={'x':'Tempo (s)', 'y':'Velocidade (mm/s)'})
        st.plotly_chart(fig_v, use_container_width=True)
    with col_d2:
        st.write("**Incerteza de Posição**")
        st.metric("Deformação Elástica", f"{deformacao_mm*1000:.1f} µm")
        st.info("Esta deformação ocorre devido à compressão/tração axial do aço sob carga.")

with tab_seg:
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("**Verificação de Vibração**")
        if rpm > n_critica * 0.8:
            st.error(f"⚠️ Risco de Ressonância! O limite de segurança é {int(n_critica*0.8)} RPM.")
        else:
            st.success(f"✅ Rotação segura (Limite: {int(n_critica*0.8)} RPM).")
    with col_s2:
        st.write("**Estabilidade Axial**")
        if fs_flambagem < 3:
            st.warning("⚠️ Fator de segurança contra flambagem baixo.")
        else:
            st.success("✅ Estrutura estável contra flambagem.")

with tab_manut:
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.write("**Lubrificação**")
        vol_relub = (d_nom * passo) * 0.0015
        st.write(f"Volume sugerido: **{vol_relub:.2f} cm³**")
        st.caption("Frequência: a cada 200km ou 500h de uso.")
    with col_m2:
        st.write("**Durabilidade**")
        if tipo_fuso == "Esferas":
            st.write(f"Vida Útil L10 estimada: **{int(l10_horas)} horas**")
        else:
            st.write(f"Fator PV: **{pv_valor:.3f} MPa.m/s**")
            if pv_valor > 0.1: st.warning("Desgaste acelerado provável.")
