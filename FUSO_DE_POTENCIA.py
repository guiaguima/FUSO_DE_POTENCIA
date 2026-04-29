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
atrito_porca_map = {"Bronze": 0.12, "Plástico/Nylon": 0.08, "Aço": 0.20}
atrito_guias_map = {"Guia Linear (Esferas)": 0.005, "Deslizamento (Bucha/Plástico)": 0.15, "Metal sobre Metal": 0.25}
fatores_apoio = {"Simples-Simples": 0.97, "Fixo-Simples": 1.51, "Fixo-Fixo": 2.19, "Fixo-Livre": 0.34}

st.title("⚙️ Analisador Especialista de Fusos")

# --- SIDEBAR ---
st.sidebar.header("1. Geometria e Montagem")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0)
tipo_apoio = st.sidebar.selectbox("Fixação das Extremidades", list(fatores_apoio.keys()))

st.sidebar.header("2. Guias e Orientação")
mat_guia = st.sidebar.selectbox("Tipo de Guia de Apoio", list(atrito_guias_map.keys()))
angulo_deg = st.sidebar.slider("Inclinação (0° Horiz - 90° Vert)", 0, 90, 0)
massa_kg = st.sidebar.number_input("Massa da Carga (kg)", value=50.0)
dist_excentrica = st.sidebar.number_input("Braço de Alavanca (mm)", value=100.0)
dist_patins = st.sidebar.number_input("Distância entre Patins (mm)", value=200.0)

st.sidebar.header("3. Operação")
v_alvo = st.sidebar.number_input("Velocidade (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo de Aceleração (s)", value=0.1)
t_ambiente = st.sidebar.slider("Temp. Ambiente (°C)", 10, 50, 25)

if tipo_fuso == "Esferas":
    ca_dinamico = st.sidebar.number_input("Capacidade Dinâmica C (N)", value=12000.0)
    altura_porca = 40.0
else:
    mat_p = st.sidebar.selectbox("Material da Porca", list(atrito_porca_map.keys()))
    altura_porca = st.sidebar.number_input("Altura da Porca (mm)", value=30.0)

# --- BLOCO DE CÁLCULOS ---
g = 9.81
ang_rad = math.radians(angulo_deg)
mu_guia = atrito_guias_map[mat_guia]

f_grav_ax = massa_kg * g * math.sin(ang_rad)
f_norm_peso = massa_kg * g * math.cos(ang_rad)
momento_tomb = (massa_kg * g) * (dist_excentrica / 1000)
f_normal_extra = momento_tomb / (dist_patins / 1000) if dist_patins > 0 else 0
f_atrito_guias = mu_guia * (f_norm_peso + (f_normal_extra * 2))
f_inercia = massa_kg * ((v_alvo/1000)/t_acc)
f_axial_total = f_grav_ax + f_atrito_guias + f_inercia

rpm = (v_alvo * 60) / passo
omega = (2 * math.pi * rpm) / 60
d_medio = (d_nom + d_nuc) / 2

if tipo_fuso == "Trapezoidal":
    mu_f = atrito_porca_map[mat_p]
    sec_alfa = 1.03
    tr_nm = (f_axial_total * d_medio / 2 * ((passo + math.pi*mu_f*d_medio*sec_alfa)/(math.pi*d_medio - mu_f*passo*sec_alfa))) / 1000
    eficiencia = 0.35
else:
    tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.9 * 1000)
    eficiencia = 0.90

m_fuso = (math.pi * (d_nom/2000)**2) * comprimento * 7850
j_fuso = 0.5 * m_fuso * (d_nom/2000)**2
torque_pico = tr_nm + (j_fuso * (omega / t_acc))
potencia_pico = torque_pico * omega

# Segurança e Térmico
E_aco = 2.1e11
I_fuso = (math.pi * (d_nuc/1000)**4) / 64
m_fuso_lin = (math.pi * (d_nuc/2000)**2) * 7850
n_critica = (fatores_apoio[tipo_apoio] * 9.55 * (math.pi / comprimento**2) * math.sqrt((E_aco * I_fuso) / m_fuso_lin))
carga_critica = (math.pi**2 * E_aco * I_fuso) / (2.0 * comprimento)**2
fs_flambagem = carga_critica / f_axial_total if f_axial_total > 0 else 100

p_calor = (potencia_pico / eficiencia) - potencia_pico if eficiencia > 0 else 0
area_dissip = (math.pi * d_nom/10) * (comprimento * 100)
t_final = t_ambiente + (p_calor / (area_dissip * 0.002))

# --- DASHBOARD ---
st.subheader("📊 Métricas de Performance")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Torque de Pico", f"{torque_pico:.2f} N.m")
m2.metric("Rotação", f"{int(rpm)} RPM")
m3.metric("Potência", f"{potencia_pico:.1f} W")
m4.metric("Temp. Est.", f"{int(t_final)} °C")

st.divider()

tab1, tab2, tab3 = st.tabs(["🚀 Dinâmica", "🛡️ Segurança", "💧 Manutenção"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Distribuição de Forças**")
        df_forcas = pd.DataFrame({"Origem": ["Gravidade", "Atrito Guias", "Inércia"], "Força (N)": [f_grav_ax, f_atrito_guias, f_inercia]})
        st.plotly_chart(px.bar(df_forcas, x="Origem", y="Força (N)", color="Origem", text_auto='.1f'), use_container_width=True)
    with col2:
        st.write("**Perfil de Velocidade**")
        fig_vel = px.line(x=[0, t_acc, t_acc+1, t_acc+1.1], y=[0, v_alvo, v_alvo, 0], labels={'x':'Tempo (s)', 'y':'Velocidade (mm/s)'})
        st.plotly_chart(fig_vel, use_container_width=True)

with tab2:
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Vibração e Flambagem")
        st.write(f"Velocidade Crítica: **{int(n_critica)} RPM**")
        st.write(f"Fator de Segurança (Flambagem): **{fs_flambagem:.2f}**")
        if rpm > n_critica * 0.8: st.error("⚠️ Rotação próxima ao limite crítico!")
    with col4:
        st.subheader("Precisão")
        def_mm = (f_axial_total * (comprimento * 1000)) / (((math.pi * d_nuc**2)/4) * 210000)
        st.metric("Deformação Elástica", f"{def_mm*1000:.1f} µm")

with tab3:
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Lubrificação")
        vol_graxa = (d_nom * passo) * 0.0015
        st.write(f"Volume de Graxa Sugerido: **{vol_graxa:.2f} cm³**")
        st.write(f"Calor Dissipado: **{p_calor:.1f} W**")
        st.info("**Intervalos Sugeridos:**\n* A cada **200 km** de percurso\n* Ou a cada **500 horas** de uso")
    with col6:
        st.subheader("Saúde do Fuso e Desgaste")
        if tipo_fuso == "Esferas":
            l10 = (ca_dinamico / (f_axial_total * 1.2))**3 * 10**6 / (rpm * 60) if rpm > 0 else 0
            st.write(f"Vida L10 estimada: **{int(l10)} horas**")
        else:
            # Cálculo do Fator PV
            area_contato = d_nom * altura_porca
            v_desl = (rpm * passo) / 60000 # m/s
            pv = (f_axial_total / area_contato) * v_desl
            
            st.write(f"Fator PV: **{pv:.4f} MPa.m/s**")
            
            # Indicação de Saúde PV
            if pv < 0.1:
                st.success("✅ Fator PV Ótimo: Baixo desgaste e temperatura controlada.")
            elif pv < 0.2:
                st.warning("⚠️ Fator PV Moderado: Requer lubrificação frequente. Monitorar aquecimento.")
            else:
                st.error("🚨 Fator PV Crítico: Risco de deformação da porca e falha prematura!")
        
        st.divider()
        for motor, dados in motores_nema.items():
            if dados['torque'] > torque_pico * 1.5:
                st.write(f"Motor sugerido: **{motor}**")
                breakimport streamlit as st
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
atrito_porca_map = {"Bronze": 0.12, "Plástico/Nylon": 0.08, "Aço": 0.20}
atrito_guias_map = {"Guia Linear (Esferas)": 0.005, "Deslizamento (Bucha/Plástico)": 0.15, "Metal sobre Metal": 0.25}
fatores_apoio = {"Simples-Simples": 0.97, "Fixo-Simples": 1.51, "Fixo-Fixo": 2.19, "Fixo-Livre": 0.34}

st.title("⚙️ Analisador Especialista de Fusos")

# --- SIDEBAR ---
st.sidebar.header("1. Geometria e Montagem")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", value=20.0)
d_nuc = st.sidebar.number_input("Diâmetro do Núcleo (mm)", value=17.0)
passo = st.sidebar.number_input("Passo (mm)", value=5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", value=1.0)
tipo_apoio = st.sidebar.selectbox("Fixação das Extremidades", list(fatores_apoio.keys()))

st.sidebar.header("2. Guias e Orientação")
mat_guia = st.sidebar.selectbox("Tipo de Guia de Apoio", list(atrito_guias_map.keys()))
angulo_deg = st.sidebar.slider("Inclinação (0° Horiz - 90° Vert)", 0, 90, 0)
massa_kg = st.sidebar.number_input("Massa da Carga (kg)", value=50.0)
dist_excentrica = st.sidebar.number_input("Braço de Alavanca (mm)", value=100.0)
dist_patins = st.sidebar.number_input("Distância entre Patins (mm)", value=200.0)

st.sidebar.header("3. Operação")
v_alvo = st.sidebar.number_input("Velocidade (mm/s)", value=50.0)
t_acc = st.sidebar.number_input("Tempo de Aceleração (s)", value=0.1)
t_ambiente = st.sidebar.slider("Temp. Ambiente (°C)", 10, 50, 25)

if tipo_fuso == "Esferas":
    ca_dinamico = st.sidebar.number_input("Capacidade Dinâmica C (N)", value=12000.0)
    altura_porca = 40.0
else:
    mat_p = st.sidebar.selectbox("Material da Porca", list(atrito_porca_map.keys()))
    altura_porca = st.sidebar.number_input("Altura da Porca (mm)", value=30.0)

# --- BLOCO DE CÁLCULOS ---
g = 9.81
ang_rad = math.radians(angulo_deg)
mu_guia = atrito_guias_map[mat_guia]

f_grav_ax = massa_kg * g * math.sin(ang_rad)
f_norm_peso = massa_kg * g * math.cos(ang_rad)
momento_tomb = (massa_kg * g) * (dist_excentrica / 1000)
f_normal_extra = momento_tomb / (dist_patins / 1000) if dist_patins > 0 else 0
f_atrito_guias = mu_guia * (f_norm_peso + (f_normal_extra * 2))
f_inercia = massa_kg * ((v_alvo/1000)/t_acc)
f_axial_total = f_grav_ax + f_atrito_guias + f_inercia

rpm = (v_alvo * 60) / passo
omega = (2 * math.pi * rpm) / 60
d_medio = (d_nom + d_nuc) / 2

if tipo_fuso == "Trapezoidal":
    mu_f = atrito_porca_map[mat_p]
    sec_alfa = 1.03
    tr_nm = (f_axial_total * d_medio / 2 * ((passo + math.pi*mu_f*d_medio*sec_alfa)/(math.pi*d_medio - mu_f*passo*sec_alfa))) / 1000
    eficiencia = 0.35
else:
    tr_nm = (f_axial_total * passo) / (2 * math.pi * 0.9 * 1000)
    eficiencia = 0.90

m_fuso = (math.pi * (d_nom/2000)**2) * comprimento * 7850
j_fuso = 0.5 * m_fuso * (d_nom/2000)**2
torque_pico = tr_nm + (j_fuso * (omega / t_acc))
potencia_pico = torque_pico * omega

# Segurança e Térmico
E_aco = 2.1e11
I_fuso = (math.pi * (d_nuc/1000)**4) / 64
m_fuso_lin = (math.pi * (d_nuc/2000)**2) * 7850
n_critica = (fatores_apoio[tipo_apoio] * 9.55 * (math.pi / comprimento**2) * math.sqrt((E_aco * I_fuso) / m_fuso_lin))
carga_critica = (math.pi**2 * E_aco * I_fuso) / (2.0 * comprimento)**2
fs_flambagem = carga_critica / f_axial_total if f_axial_total > 0 else 100

p_calor = (potencia_pico / eficiencia) - potencia_pico if eficiencia > 0 else 0
area_dissip = (math.pi * d_nom/10) * (comprimento * 100)
t_final = t_ambiente + (p_calor / (area_dissip * 0.002))

# --- DASHBOARD ---
st.subheader("📊 Métricas de Performance")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Torque de Pico", f"{torque_pico:.2f} N.m")
m2.metric("Rotação", f"{int(rpm)} RPM")
m3.metric("Potência", f"{potencia_pico:.1f} W")
m4.metric("Temp. Est.", f"{int(t_final)} °C")

st.divider()

tab1, tab2, tab3 = st.tabs(["🚀 Dinâmica", "🛡️ Segurança", "💧 Manutenção"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Distribuição de Forças**")
        df_forcas = pd.DataFrame({"Origem": ["Gravidade", "Atrito Guias", "Inércia"], "Força (N)": [f_grav_ax, f_atrito_guias, f_inercia]})
        st.plotly_chart(px.bar(df_forcas, x="Origem", y="Força (N)", color="Origem", text_auto='.1f'), use_container_width=True)
    with col2:
        st.write("**Perfil de Velocidade**")
        fig_vel = px.line(x=[0, t_acc, t_acc+1, t_acc+1.1], y=[0, v_alvo, v_alvo, 0], labels={'x':'Tempo (s)', 'y':'Velocidade (mm/s)'})
        st.plotly_chart(fig_vel, use_container_width=True)

with tab2:
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Vibração e Flambagem")
        st.write(f"Velocidade Crítica: **{int(n_critica)} RPM**")
        st.write(f"Fator de Segurança (Flambagem): **{fs_flambagem:.2f}**")
        if rpm > n_critica * 0.8: st.error("⚠️ Rotação próxima ao limite crítico!")
    with col4:
        st.subheader("Precisão")
        def_mm = (f_axial_total * (comprimento * 1000)) / (((math.pi * d_nuc**2)/4) * 210000)
        st.metric("Deformação Elástica", f"{def_mm*1000:.1f} µm")

with tab3:
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Lubrificação")
        vol_graxa = (d_nom * passo) * 0.0015
        st.write(f"Volume de Graxa Sugerido: **{vol_graxa:.2f} cm³**")
        st.write(f"Calor Dissipado: **{p_calor:.1f} W**")
        st.info("**Intervalos Sugeridos:**\n* A cada **200 km** de percurso\n* Ou a cada **500 horas** de uso")
    with col6:
        st.subheader("Vida Útil e Motores")
        if tipo_fuso == "Esferas":
            l10 = (ca_dinamico / (f_axial_total * 1.2))**3 * 10**6 / (rpm * 60) if rpm > 0 else 0
            st.write(f"Vida L10 estimada: **{int(l10)} horas**")
        else:
            pv = (f_axial_total / (d_nom * altura_porca)) * ((rpm * passo) / 60000)
            st.write(f"Fator PV: **{pv:.3f} MPa.m/s**")
        
        for motor, dados in motores_nema.items():
            if dados['torque'] > torque_pico * 1.5:
                st.success(f"Motor Recomendado: **{motor}**")
                break
