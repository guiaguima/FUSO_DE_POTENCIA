import streamlit as st
import math
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Engenharia de Fusos Master", layout="wide")

# --- BANCOS DE DADOS ---
motores_nema = {
    "NEMA 17": {"torque": 0.45}, 
    "NEMA 23": {"torque": 2.2},
    "NEMA 34": {"torque": 8.5}, 
    "Servo 400W": {"torque": 1.27}
}
atrito_porca = {"Bronze": 0.12, "Plástico/Nylon": 0.08, "Aço": 0.20}

st.title("⚙️ Simulador Especialista: Fusos de Potência")

# --- SIDEBAR: ENTRADAS ---
st.sidebar.header("1. Geometria e Montagem")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0)

st.sidebar.header("2. Orientação e Carga")
angulo_deg = st.sidebar.slider("Inclinação (0° Horiz - 90° Vert)", 0, 90, 0)
massa_kg = st.sidebar.number_input("Massa da Carga (kg)", value=50.0)
dist_excentrica = st.sidebar.number_input("Braço de Alavanca (mm)", value=100.0)
dist_patins = st.sidebar.number_input("Distância entre Patins (mm)", value=200.0)

st.sidebar.header("3. Dinâmica e Ambiente")
v_alvo = st.sidebar.number_input("Velocidade Alvo (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo de Aceleração (s)", value=0.1)
t_ambiente = st.sidebar.slider("Temp. Ambiente (°C)", 10, 50, 25)

# --- CÁLCULOS TÉCNICOS ---

# Constantes e Decomposição
g = 9.81
ang_rad = math.radians(angulo_deg)
mu_guia = 0.005 # Coeficiente para guias lineares de esferas

# 1. Definição das Forças (Correção do NameError)
f_gravidade_axial = massa_kg * g * math.sin(ang_rad)
f_normal_peso = massa_kg * g * math.cos(ang_rad)  # Variável definida aqui

# 2. Efeito do Braço de Alavanca (Excentricidade)
momento = (massa_kg * g) * (dist_excentrica / 1000)
f_normal_extra = momento / (dist_patins / 1000) if dist_patins > 0 else 0

# 3. Atrito e Inércia
# f_normal_peso foi definida na linha 44, agora pode ser usada aqui:
f_atrito_guias = mu_guia * (f_normal_peso + (f_normal_extra * 2))
f_inercia = massa_kg * ((v_alvo / 1000) / t_acc)
f_axial_total = f_gravidade_axial + f_atrito_guias + f_inercia

# 4. Torque e Rotação
rpm = (v_alvo * 60) / passo
omega = (2 * math.pi * rpm) / 60
d_medio = (d_nom + d_nuc) / 2

if tipo_fuso == "Trapezoidal":
    # Seletor de material da porca apenas para trapezoidal
    mat_p = st.sidebar.selectbox("Material da Porca", list(atrito_porca.keys()))
    mu_f = atrito_porca[mat_p]
    sec_alfa = 1.03 # Fator para ângulo de flanco de 14.5°
    tr_nm = (f_axial_total * d_medio / 2 * ((passo + math.pi*mu_f*d_medio*sec_alfa)/(math.pi*d_medio - mu_f*passo*sec_alfa))) / 1000
    eficiencia = 0.35
else:
    tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.9 * 1000)
    eficiencia = 0.90

# 5. Inércia do Fuso
m_fuso = (math.pi * (d_nom/2000)**2) * comprimento * 7850
j_fuso = 0.5 * m_fuso * (d_nom/2000)**2
torque_pico = tr_nm + (j_fuso * (omega / t_acc))

# 6. Análise Térmica
p_util = f_axial_total * (v_alvo / 1000)
p_calor = (p_util / eficiencia) - p_util
area_dissip = (math.pi * d_nom / 10) * (comprimento * 100) # cm²
t_final = t_ambiente + (p_calor / (area_dissip * 0.002))

# --- INTERFACE DE RESULTADOS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Torque de Pico", f"{torque_pico:.2f} N.m")
c2.metric("Força Axial Total", f"{f_axial_total:.1f} N")
c3.metric("Potência (Calor)", f"{p_calor:.1f} W")
c4.metric("Temp. Est estimada", f"{int(t_final)} °C")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🌡️ Comportamento Térmico")
    if t_final > 70:
        st.error(f"Temperatura Crítica: {int(t_final)}°C. Risco de falha de lubrificação.")
    elif t_final > 45:
        st.warning(f"Temperatura Elevada: {int(t_final)}°C. Verifique a graxa periodicamente.")
    else:
        st.success(f"Operação Segura: {int(t_final)}°C.")

with col_b:
    st.subheader("🤖 Recomendação de Motor")
    for motor, dados in motores_nema.items():
        if dados['torque'] > torque_pico * 1.3:
            st.write(f"Sugestão: **{motor}**")
            st.progress(min(torque_pico / dados['torque'], 1.0))
            break
    else:
        st.error("Torque acima da capacidade NEMA padrão.")

st.subheader("📊 Fator PV e Desgaste")
pv = (f_axial_total / (d_nom * 30)) * ((rpm * passo) / 60000)
st.write(f"O fator PV atual é **{pv:.4f} MPa.m/s**. (Limite sugerido: 0.1 para polímeros, 0.2 para bronze)")
