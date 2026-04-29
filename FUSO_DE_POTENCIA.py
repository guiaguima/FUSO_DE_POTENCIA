import streamlit as st
import math
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Engenharia de Fusos Pro", layout="wide", page_icon="⚙️")

# --- BANCO DE DADOS E CONSTANTES ---
materiais_atrito = {
    "Aço em Bronze (Lubrificado)": 0.10,
    "Aço em Aço (Lubrificado)": 0.15,
    "Aço em Ferro Fundido": 0.18,
    "Fuso de Esferas (Baixo Atrito)": 0.02
}

fatores_carga = {
    "Operação Suave (Sem Choques)": 1.1,
    "Operação Normal": 1.3,
    "Operação com Impactos/Vibração": 1.7
}

apoios_velocidade = {
    "Simples-Simples (Apoiado-Apoiado)": 0.97,
    "Engastado-Simples (Fixo-Apoiado)": 1.51,
    "Engastado-Engastado (Fixo-Fixo)": 2.19,
    "Engastado-Livre (Balanço)": 0.34
}

# --- SIDEBAR: ENTRADAS DE DADOS ---
st.sidebar.header("📋 1. Geometria e Montagem")
tipo_fuso = st.sidebar.selectbox("Tipo de Fuso", ["Trapezoidal", "Esferas"])
d_nom = st.sidebar.number_input("Diâmetro Nominal (mm)", 10.0, 100.0, 20.0)
d_nucleo = st.sidebar.number_input("Diâmetro do Núcleo (mm)", 5.0, 90.0, 17.0)
passo = st.sidebar.number_input("Avanço/Passo (mm)", 1.0, 50.0, 5.0)
comprimento = st.sidebar.number_input("Comprimento Livre (m)", 0.1, 5.0, 1.0)
tipo_apoio = st.sidebar.selectbox("Tipo de Fixação (Extremidades)", list(apoios_velocidade.keys()))

st.sidebar.header("⚖️ 2. Condições de Operação")
carga = st.sidebar.number_input("Carga Axial Operacional (N)", value=2500.0)
rpm = st.sidebar.number_input("Rotação Desejada (RPM)", value=750.0)
horas_dia = st.sidebar.slider("Horas de Uso por Dia", 1, 24, 8)

if tipo_fuso == "Esferas":
    st.sidebar.header("⏳ 3. Vida Útil e Carga")
    ca_dinamico = st.sidebar.number_input("Capacidade Dinâmica C (N)", value=15000.0)
    fw_nome = st.sidebar.selectbox("Condição de Trabalho (f_w)", list(fatores_carga.keys()))
    fw = fatores_carga[fw_nome]
else:
    fw = 1.0
    ca_dinamico = 0

# --- LÓGICA DE CÁLCULO ---

# A. Torque e Potência
d_medio = (d_nom + d_nucleo) / 2
mu = materiais_atrito["Fuso de Esferas (Baixo Atrito)"] if tipo_fuso == "Esferas" else materiais_atrito["Aço em Bronze (Lubrificado)"]

if tipo_fuso == "Trapezoidal":
    alfa = math.radians(14.5)
    sec_alfa = 1 / math.cos(alfa)
    tr_nm = ((carga * d_medio / 2) * ((passo + math.pi * mu * d_medio * sec_alfa) / (math.pi * d_medio - mu * passo * sec_alfa))) / 1000
else:
    eficiencia = 0.90
    tr_nm = (carga * passo) / (2 * math.pi * eficiencia * 1000)

potencia_w = tr_nm * ((2 * math.pi * rpm) / 60)

# B. Segurança (Flambagem de Euler)
E = 2.1e11 # Pa
I = (math.pi * (d_nucleo/1000)**4) / 64
K = 2.0 # Fator de comprimento efetivo (ajustável)
carga_critica = (math.pi**2 * E * I) / (K * comprimento)**2
fs_flambagem = carga_critica / carga if carga > 0 else 0

# C. Velocidade Crítica (Vibração)
rho = 7850 # kg/m3
area_nucleo = math.pi * (d_nucleo/2000)**2
m_linear = area_nucleo * rho
f_s_critico = apoios_velocidade[tipo_apoio]
n_critica = (f_s_critico * 9.55 * (math.pi / comprimento**2) * math.sqrt((E * I) / m_linear))
n_limite = n_critica * 0.8

# D. Vida Útil L10 (Apenas Esferas)
l10_horas = (ca_dinamico / (carga * fw))**3 * 10**6 / (rpm * 60) if tipo_fuso == "Esferas" else 0

# E. Lubrificação
vol_relub = (d_nom * passo) * 0.0015
dist_dia_km = (rpm * passo * 60 * horas_dia) / 1_000_000
dias_lub = 200 / dist_dia_km if dist_dia_km > 0 else 365

# --- INTERFACE PRINCIPAL ---
st.title("⚙️ Analisador Especialista de Fusos")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Torque Requerido", f"{tr_nm:.2f} N.m")
col2.metric("Potência Motor", f"{potencia_w:.2f} W")
col3.metric("F.S. Flambagem", f"{fs_flambagem:.2f}")
col4.metric("Vel. Crítica", f"{int(n_critica)} RPM")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Performance e Gráficos", "🛡️ Segurança e Vibração", "💧 Manutenção"])

with tab1:
    st.subheader("Análise de Potência Dinâmica")
    rpms_sim = list(range(100, int(rpm * 1.5) + 100, 100))
    pots_sim = [tr_nm * ((2 * math.pi * r) / 60) for r in rpms_sim]
    df_pot = pd.DataFrame({"RPM": rpms_sim, "Potência (W)": pots_sim})
    fig_pot = px.line(df_pot, x="RPM", y="Potência (W)", title="Necessidade de Potência vs Velocidade")
    st.plotly_chart(fig_pot, use_container_width=True)
    
    if tipo_fuso == "Esferas":
        st.info(f"**Vida Útil L10 Estimada:** {int(l10_horas)} horas de operação.")

with tab2:
    st.subheader("Verificação de Estabilidade")
    c_v1, c_v2 = st.columns(2)
    with c_v1:
        st.write("**Análise de Flambagem (Euler)**")
        if fs_flambagem > 3: st.success("Fuso Seguro contra Flambagem")
        else: st.error("Risco de Flambagem Detectado!")
        
    with c_v2:
        st.write("**Análise de Velocidade Crítica**")
        if rpm < n_limite: st.success("Rotação dentro do limite seguro")
        else: st.warning("Rotação próxima ou acima do limite crítico!")

with tab3:
    st.subheader("Plano de Lubrificação")
    st.write(f"Para manter a eficiência, recomenda-se a relubrificação com **{vol_relub:.2f} cm³** de graxa.")
    st.write(f"Baseado no uso de {horas_dia}h/dia, o ciclo estimado é a cada **{int(dias_lub)} dias**.")

# --- GERADOR DE PDF ---
def gerar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "Relatorio Tecnico de Dimensionamento", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(10)
    pdf.cell(0, 7, f"Data: {datetime.date.today()}", ln=True)
    pdf.cell(0, 7, f"Fuso: {tipo_fuso} {d_nom}x{passo}mm", ln=True)
    pdf.cell(0, 7, f"Carga Axial: {carga} N", ln=True)
    pdf.cell(0, 7, f"Torque Calculado: {tr_nm:.2f} N.m", ln=True)
    pdf.cell(0, 7, f"Potencia Calculada: {potencia_w:.2f} W", ln=True)
    pdf.cell(0, 7, f"Velocidade Critica: {int(n_critica)} RPM", ln=True)
    pdf.cell(0, 7, f"Fator de Seguranca Flambagem: {fs_flambagem:.2f}", ln=True)
    
    if tipo_fuso == "Esferas":
        pdf.cell(0, 7, f"Vida Util Estimada (L10): {int(l10_horas)} horas", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Notas de Manutencao:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"- Relubrificar com {vol_relub:.2f} cm3 a cada {int(dias_lub)} dias.", ln=True)
    
    return pdf.output()

# Download na Sidebar
st.sidebar.divider()
if st.sidebar.button("📄 Gerar Relatório Técnico"):
    pdf_bytes = gerar_pdf()
    st.sidebar.download_button(
        label="📥 Baixar PDF",
        data=bytes(pdf_bytes),
        file_name="Memoria_Calculo_Fuso.pdf",
        mime="application/pdf"
    )
