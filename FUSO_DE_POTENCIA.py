import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Engenharia de Fusos Master", layout="wide")

# --- BANCOS DE DADOS ---
motores_nema = {
    "NEMA 17": {"torque": 0.45}, "NEMA 23": {"torque": 2.2},
    "NEMA 34": {"torque": 8.5}, "Servo 400W": {"torque": 1.27}
}
atrito_porca = {"Bronze": 0.12, "Plástico/Nylon": 0.08, "Aço": 0.20}

st.title("⚙️ Simulador de Engenharia de Fusos (Completo)")

# --- SIDEBAR ---
st.sidebar.header("1. Especificações do Fuso")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento (m)", value=1.0)

st.sidebar.header("2. Aplicação e Carga")
angulo_deg = st.sidebar.slider("Inclinação (0° Horiz - 90° Vert)", 0, 90, 0)
massa_kg = st.sidebar.number_input("Massa (kg)", value=50.0)
dist_excentrica = st.sidebar.number_input("Braço de Alavanca (mm)", value=100.0)
dist_patins = st.sidebar.number_input("Distância entre Patins (mm)", value=200.0)

st.sidebar.header("3. Ciclo de Trabalho")
v_alvo = st.sidebar.number_input("Velocidade (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo Acc (s)", value=0.1)
t_ambiente = st.sidebar.slider("Temp. Ambiente (°C)", 10, 50, 25)

# --- CÁLCULOS INTEGRADOS ---
g = 9.81
ang_rad = math.radians(angulo_deg)
mu_guia = 0.005

# Forças
f_grav_ax = massa_kg * g * math.sin(ang_rad)
f_norm_peso = massa_kg * g * math.cos(ang_rad)
momento = (massa_kg * g) * (dist_excentrica / 1000)
f_norm_extra = momento / (dist_patins / 1000) if dist_patins > 0 else 0
f_atrito_guias = mu_guia * (f_normal_peso + (f_normal_extra * 2))
f_inercia = massa_kg * ((v_alvo/1000)/t_acc)
f_axial_total = f_grav_ax + f_atrito_guias + f_inercia

# Torque e Rotação
rpm = (v_alvo * 60) / passo
omega = (2 * math.pi * rpm) / 60
d_medio = (d_nom + d_nuc) / 2

if tipo_fuso == "Trapezoidal":
    mu_f = atrito_porca[st.sidebar.selectbox("Material Porca", list(atrito_porca.keys()))]
    sec_a = 1.03
    tr_nm = (f_axial_total * d_medio / 2 * ((passo + math.pi*mu_f*d_medio*sec_a)/(math.pi*d_medio - mu_f*passo*sec_a))) / 1000
    eficiencia = 0.35
else:
    tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.9 * 1000)
    eficiencia = 0.90

# --- ANÁLISE TÉRMICA ---
p_util = f_axial_total * (v_alvo / 1000) # Watts úteis
p_total = p_util / eficiencia
p_calor = p_total - p_util # Calor gerado (W)

# Coeficiente de dissipação simplificado (h * Area)
# Estimativa: um fuso dissipa aprox. 0.05W por grau acima do ambiente por cm2
area_dissip_cm2 = (math.pi * d_nom/10) * (comprimento * 100)
t_estimada = t_ambiente + (p_calor / (area_dissip_cm2 * 0.002)) 

# --- INTERFACE ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Torque de Pico", f"{tr_nm:.2f} N.m")
m2.metric("Potência Dissipada", f"{p_calor:.1f} W", delta="Calor", delta_color="inverse")
m3.metric("Temp. Porca (Est.)", f"{int(t_estimada)}°C")
m4.metric("Fator PV", f"{(f_axial_total/(d_nom*30))*((rpm*passo)/60000):.3f}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🌡️ Análise de Aquecimento")
    st.write(f"O fuso gera **{p_calor:.1f} Watts** de calor por atrito.")
    if t_estimada > 70:
        st.error(f"CUIDADO: Temperatura alta ({int(t_estimada)}°C). Risco de degradação do lubrificante.")
    elif t_estimada > 45:
        st.warning(f"Temperatura estável em {int(t_estimada)}°C. Monitore a lubrificação.")
    else:
        st.success(f"Operação fria: {int(t_estimada)}°C.")

with col_b:
    st.subheader("🚀 Seleção NEMA (Sugerida)")
    for motor, dados in motores_nema.items():
        if dados['torque'] > tr_nm * 1.5:
            st.success(f"Use um **{motor}**")
            st.caption(f"Torque disponível: {dados['torque']} N.m")
            break
