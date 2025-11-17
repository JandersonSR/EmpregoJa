import streamlit as st

from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
import time

load_dotenv()

API_BASE = os.getenv("SERVER_URL", "http://localhost:3000")

st.set_page_config(page_title="Buscador de Empregos", layout="wide")

st.title("🔎 Buscador de Empregos")
st.write("Envie seu currículo e compare com vagas usando diferentes métodos de IA.")

st_duration = 4

# ============================
# EMAIL
# ============================
email = st.text_input("Digite seu e-mail:", placeholder="exemplo@email.com")

if not email:
    st.warning("⚠️ Por favor, insira um e-mail para continuar.")
    st.stop()

# ============================
# SESSION STATE PARA VAGAS
# ============================
if "vagas" not in st.session_state:
    st.session_state.vagas = []

# container para evitar múltiplas renderizações
vagas_container = st.container()


# ============================
# CURRÍCULO
# ============================
uploaded_file = st.file_uploader("Envie seu currículo (PDF, DOCX ou TXT)", type=["pdf", "docx", "txt"])


# ============================
# FUNÇÕES DE EXIBIÇÃO
# ============================
def grafico_vaga(vaga):
    atendidos = len(vaga["requisitos_atendidos"])
    nao_atendidos = len(vaga["requisitos_nao_atendidos"])

    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.bar(["Atendidos", "Não atendidos"], [atendidos, nao_atendidos])
    ax.set_title("Resumo dos Requisitos")
    ax.set_ylabel("Quantidade")

    st.pyplot(fig)


def exibir_vagas(vagas):
    if not vagas:
        st.info("Nenhuma vaga encontrada.")
        return

    st.subheader("🔎 Vagas encontradas")

    for i in range(0, len(vagas), 2):
        col1, col2 = st.columns(2)

        if i < len(vagas):
            _exibir_card_vaga(vagas[i], col1)

        if i + 1 < len(vagas):
            _exibir_card_vaga(vagas[i+1], col2)


def _exibir_card_vaga(vaga, coluna):
    titulo = vaga.get("titulo", "Sem título")
    empresa = vaga.get("empresa", "Não informada")
    compat = float(vaga.get("compatibilidade", 0))
    requisitos_atendidos = vaga.get("requisitos_atendidos", [])
    requisitos_nao_atendidos = vaga.get("requisitos_nao_atendidos", [])
    sugestoes = vaga.get("melhorias_sugeridas", [])
    link = vaga.get("url", "#")

    with coluna:
        st.markdown(f"### {titulo}")
        st.markdown(f"**{empresa}**")

        st.markdown(
            f"""
            <div style='background:#eee;border-radius:8px;height:16px;width:100%;'>
                <div style='width:{compat*100}%;background:#0078ff;height:16px;border-radius:8px;'></div>
            </div>
            <p style='margin-top:5px;font-size:14px;'><b>{round(compat*100, 1)}%</b></p>
            """,
            unsafe_allow_html=True
        )

        colA, colB = st.columns(2)
        with colA:
            with st.expander("✔ Atendidos"):
                if requisitos_atendidos:
                    for r in requisitos_atendidos:
                        st.markdown(f"🟢 {r}")
                else:
                    st.markdown("—")

        with colB:
            with st.expander("❌ Não atendidos"):
                if requisitos_nao_atendidos:
                    for r in requisitos_nao_atendidos:
                        st.markdown(f"🔴 {r}")
                else:
                    st.markdown("—")

        if sugestoes:
            with st.expander("✨ Sugestões"):
                for s in sugestoes:
                    st.markdown(f"- {s}")

        if link != "#":
            st.markdown(f"🔗 [Acessar vaga]({link})")


# ============================
# UPLOAD DO CURRÍCULO
# ============================
if uploaded_file and st.button("📤 Enviar Currículo"):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    data = {"email": email}

    try:
        with st.spinner("Enviando currículo..."):
            resp = requests.post(f"{API_BASE}/curriculo/upload", files=files, data=data, timeout=90)

        if resp.status_code != 200:
            st.toast("❌ Falha no envio do currículo", icon="🚨", duration=st_duration)
            st.stop()

        st.toast("📤 Currículo enviado!", duration=st_duration)

        with st.spinner("🔄 Processando currículo..."):
            result = None
            for _ in range(25):
                status_resp = requests.get(f"{API_BASE}/curriculo/status/{email}", timeout=20)
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    if status_data.get("status") == "concluido":
                        result = status_data.get("resultado")
                        break
                time.sleep(2)

        if result:
            st.toast("🎉 Processamento concluído!", duration=st_duration)
            st.session_state.vagas = result  # <-- salva as vagas
        else:
            st.toast("⏳ Tempo limite atingido", icon="⚠️", duration=st_duration)

    except Exception as e:
        st.toast(f"❌ Erro: {str(e)}", icon="🚨", duration=st_duration)


# ============================
# BOTÕES DE COMPARAÇÃO
# ============================
st.header("Comparação de vagas")

colE, colL, colM = st.columns(3)

# Embeddings
with colE:
    if st.button("🧠 Comparar por Embeddings"):
        try:
            with st.spinner("Comparando via embeddings..."):
                resp = requests.get(
                    f"{API_BASE}/curriculo/comparar/embeddings",
                    params={"email": email},
                    timeout=60
                )

            if resp.status_code != 200:
                st.toast("❌ Falha ao comparar via embeddings", icon="🚨", duration=st_duration)
            else:
                vagas = resp.json().get("resultado", [])
                if vagas:
                    st.toast("🎯 Feito!")
                    st.session_state.vagas = vagas
                else:
                    st.toast("Nenhuma vaga encontrada", icon="ℹ️", duration=st_duration)

        except Exception as e:
            st.toast(f"❌ Erro: {str(e)}", icon="🚨", duration=st_duration)


# LLM
with colL:
    if st.button("🤖 Comparar por LLM"):
        try:
            with st.spinner("Chamando LLM para análise..."):
                resp = requests.get(
                    f"{API_BASE}/curriculo/comparar/llm",
                    params={"email": email},
                    timeout=90
                )

            if resp.status_code != 200:
                st.toast("❌ Erro na API LLM", icon="🚨", duration=st_duration)
            else:
                vagas = resp.json().get("resultado", [])
                if vagas:
                    st.toast("✨ Análise concluída!", duration=st_duration)
                    st.session_state.vagas = vagas
                else:
                    st.toast("ℹ️ Nenhuma vaga encontrada", duration=st_duration)

        except Exception as e:
            st.toast(f"❌ Erro: {str(e)}", icon="🚨", duration=st_duration)


# Misto
with colM:
    if st.button("⚡ Comparar Embeddings + LLM (Misto)"):
        try:
            with st.spinner("Executando pipeline híbrido..."):
                resp = requests.get(
                    f"{API_BASE}/curriculo/comparar/misto",
                    params={"email": email},
                    timeout=90
                )

            if resp.status_code != 200:
                st.toast("❌ Erro ao comparar no modo misto", icon="🚨", duration=st_duration)
            else:
                vagas = resp.json().get("resultado", [])
                if vagas:
                    st.toast("🚀 Pipeline finalizado!", duration=st_duration)
                    st.session_state.vagas = vagas
                else:
                    st.toast("ℹ️ Nenhuma vaga encontrada", icon="ℹ️", duration=st_duration)

        except Exception as e:
            st.toast(f"❌ Erro: {str(e)}", icon="🚨", duration=st_duration)


# ============================
# BUSCAR RESULTADOS EXISTENTES
# ============================
if st.button("🔎 Buscar Vagas Já Processadas"):
    try:
        with st.spinner("Buscando vagas..."):
            resp = requests.get(
                f"{API_BASE}/curriculo/vagas",
                params={"email": email},
                timeout=60
            )

        if resp.status_code != 200:
            st.toast("❌ Erro ao buscar vagas", icon="🚨", duration=st_duration)
        else:
            body = resp.json()
            vagas = body.get("data", {}).get("resultado", [])

            if vagas:
                st.toast("📌 Vagas carregadas!", duration=st_duration)
                st.session_state.vagas = vagas
            else:
                st.toast("ℹ️ Nenhuma vaga encontrada", icon="ℹ️", duration=st_duration)

    except Exception as e:
        st.toast(f"❌ Erro: {str(e)}", icon="🚨", duration=st_duration)


# ============================
# RENDERIZAÇÃO FINAL ÚNICA
# ============================
with vagas_container:
    exibir_vagas(st.session_state.vagas)
