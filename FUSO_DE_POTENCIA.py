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
fatores_apoio = {"Simples-Simples": 0.97, "Fixo-Simples": 1.51, "Fixo-Fixo": 2.19, "Fixo-Livre": 0.34}

st.title("⚙️ Analisador Especialista de Fusos")

# --- SIDEBAR: ENTRADAS ---
st.sidebar.header("1. Geometria e Montagem")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0)
tipo_apoio = st.sidebar.selectbox("Fixação das Extremidades", list(fatores_apoio.keys()))

st.sidebar.header("2. Orientação e Excentricidade")
angulo_deg = st.sidebar.slider("Inclinação (0° Horiz - 90° Vert)", 0, 90, 0)
massa_kg = st.sidebar.number_input("Massa da Carga (kg)", value=50.0)
dist_excentrica = st.sidebar.number_input("Braço de Alavanca (mm)", value=100.0)
dist_patins = st.sidebar.number_input("Distância entre Patins (mm)", value=200.0)

st.sidebar.header("3. Operação e Ambiente")
v_alvo = st.sidebar.number_input("Velocidade (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo de Aceleração (s)", value=0.1)
t_ambiente = st.sidebar.slider("Temp. Ambiente (°C)", 10, 50, 25)

if tipo_fuso == "Esferas":
    ca_dinamico = st.sidebar.number_input("Capacidade Dinâmica C (N)", value=12000.0)
else:
    mat_p = st.sidebar.selectbox("Material da Porca", list(atrito_porca.keys()))
    altura_porca = st.sidebar.number_input("Altura da Porca (mm)", value=30.0)

# --- CÁLCULOS TÉCNICOS ---
g = 9.81
ang_rad = math.radians(angulo_deg)
mu_guia = 0.005 

# 1. Forças e Excentricidade
f_grav_ax = massa_kg * g * math.sin(ang_rad)
f_norm_peso = massa_kg * g * math.cos(ang_rad)
momento = (massa_kg * g) * (dist_excentrica / 1000)
f_norm_extra = momento / (dist_patins / 1000) if dist_patins > 0 else 0
f_atrito_guias = mu_guia * (f_norm_peso + (f_norm_extra * 2))
f_inercia = massa_kg * ((v_alvo/1000)/t_acc)
f_axial_total = f_grav_ax + f_atrito_guias + f_inercia

# 2. Torque e Rotação
rpm = (v_alvo * 60) / passo
omega = (2 * math.pi * rpm) / 60
d_medio = (d_nom + d_nuc) / 2

if tipo_fuso == "Trapezoidal":
    mu_f = atrito_porca[mat_p]
    sec_alfa = 1.03
    tr_nm = (f_axial_total * d_medio / 2 * ((passo + math.pi*mu_f*d_medio*sec_alfa)/(math.pi*d_medio - mu_f*passo*sec_alfa))) / 1000
    eficiencia = 0.35
else:
    tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.9 * 1000)
    eficiencia = 0.90

# 3. Inércia do Fuso e Torque de Pico
m_fuso = (math.pi * (d_nom/2000)**2) * comprimento * 7850
j_fuso = 0.5 * m_fuso * (d_nom/2000)**2
torque_pico = tr_nm + (j_fuso * (omega / t_acc))

# 4. Velocidade Crítica e Flambagem
E_aco = 2.1e11
I_fuso = (math.pi * (d_nuc/1000)**4) / 64
m_fuso_lin = (math.pi * (d_nuc/2000)**2) * 7850
n_critica = (fatores_apoio[tipo_apoio] * 9.55 * (math.pi / comprimento**2) * math.sqrt((E_aco * I_fuso) / m_fuso_lin))
carga_critica = (math.pi**2 * E_aco * I_fuso) / (2.0 * comprimento)**2
fs_flambagem = carga_critica / f_axial_total if f_axial_total > 0 else 100

# 5. Térmico e Vida Útil
p_calor = ((f_axial_total * (v_alvo/1000)) / eficiencia) - (f_axial_total * (v_alvo/1000))
area_dissip = (math.pi * d_nom/10) * (comprimento * 100)
t_final = t_ambiente + (p_calor / (area_dissip * 0.002))

# --- INTERFACE ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Torque de Pico", f"{torque_pico:.2f} N.m")
m2.metric("Temp. Est. Porca", f"{int(t_final)} °C")
m3.metric("Vel. Crítica", f"{int(n_critica)} RPM")
m4.metric("F.S. Flambagem", f"{fs_flambagem:.2f}")

st.divider()

tab1, tab2, tab3 = st.tabs(["🚀 Dinâmica e Precisão", "🛡️ Segurança Estrutural", "💧 Manutenção e Vida"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Análise de Cargas")
        st.write(f"- Força Gravitacional: {f_grav_ax:.1f} N")
        st.write(f"- Atrito (Guias + Momento): {f_atrito_guias:.1f} N")
        st.write(f"- Força de Inércia: {f_inercia:.1f} N")
        st.info(f"O braço de {dist_excentrica}mm aumentou o atrito das guias em {(mu_guia * f_normal_extra * 2):.1f} N.")
    with col2:
        st.subheader("Motorização Sugerida")
        for motor, dados in motores_nema.items():
            if dados['torque'] > torque_pico * 1.5:
                st.success(f"Motor: **{motor}**")
                st.write(f"Margem de segurança: {((dados['torque']/torque_pico)-1)*100:.0f}%")
                break

with tab2:
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Vibração e Ressonância")
        if rpm > n_critica * 0.8:
            st.error(f"⚠️ Alerta: Rotação ({int(rpm)} RPM) muito próxima da crítica!")
        else:
            st.success(f"✅ Rotação segura. Limite de segurança: {int(n_critica*0.8)} RPM.")
    with col4:
        st.subheader("Deformação Elástica")
        def_mm = (f_axial_total * (comprimento * 1000)) / (((math.pi * d_nuc**2)/4) * 210000)
        st.metric("Deformação Axial", f"{def_mm*1000:.1f} µm")

with tab3:
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Lubrificação e Calor")
        vol_graxa = (d_nom * passo) * 0.0015
        st.write(f"Volume sugerido: **{vol_graxa:.2f} cm³**")
        st.write(f"Potência dissipada em calor: **{p_calor:.1f} W**")
    with col6:
        st.subheader("Durabilidade")
        if tipo_fuso == "Esferas":
            l10 = (ca_dinamico / (f_axial_total * 1.2))**3 * 10**6 / (rpm * 60) if rpm > 0 else 0
            st.write(f"Vida Útil L10: **{int(l10)} horas**")
        else:
            pv = (f_axial_total / (d_nom * altura_porca)) * ((rpm * passo) / 60000)
            st.write(f"Fator PV: **{pv:.3f} MPa.m/s**")
            if pv > 0.15: st.warning("Atenção: PV elevado para porcas trapezoidais.")
