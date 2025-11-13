import streamlit as st
from dotenv import load_dotenv
import os
import requests
import time

load_dotenv()

# 🔗 URL do backend Express
API_BASE = os.getenv("SERVER_URL", "http://localhost:3000")

st.set_page_config(page_title="Buscador de Empregos", layout="wide")

# ==============================
# 🏠 Cabeçalho
# ==============================
st.title("🔎 Buscador de Empregos")
st.write("Envie seu currículo e veja vagas compatíveis!")

# ==============================
# 📧 Campo de email
# ==============================
email = st.text_input("Digite seu e-mail:", placeholder="exemplo@email.com")

if not email:
    st.warning("⚠️ Por favor, insira um e-mail para continuar.")
    st.stop()

# ==============================
# 📂 Upload de currículo
# ==============================
uploaded_file = st.file_uploader("Envie seu currículo (PDF, DOCX ou TXT)", type=["pdf", "docx", "txt"])

col1, col2 = st.columns(2)

# Função auxiliar para exibir vagas
def exibir_vagas(vagas):
    st.subheader("Vagas compatíveis:")
    for vaga in vagas:
        titulo = vaga.get("titulo", "Sem título")
        empresa = vaga.get("empresa", "Empresa não informada")
        compat = vaga.get("compatibilidade", 0)
        st.markdown(f"**{titulo}** - {empresa}")
        st.progress(min(max(compat, 0), 1))  # evita erro se compat for fora de 0–1

# ==============================
# 🚀 Enviar / atualizar currículo
# ==============================
with col1:
    if uploaded_file and st.button("📤 Enviar Currículo"):
        st.session_state["mensagem"] = None
        st.session_state["vagas"] = None

        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        data = {"email": email}

        with st.spinner("Enviando currículo para o servidor..."):
            try:
                response = requests.post(f"{API_BASE}/curriculo/upload", files=files, data=data, timeout=90)

                if response.status_code == 200:
                    job_id = response.json().get("id")
                    st.success(f"✅ Currículo enviado com sucesso! ID: {job_id}")

                    # Polling do status
                    with st.spinner("⏳ Processando currículo..."):
                        result = None
                        for _ in range(30):  # 30 tentativas (~60s)
                            status_resp = requests.get(f"{API_BASE}/curriculo/status/{job_id}", timeout=20)
                            if status_resp.status_code == 200:
                                status_data = status_resp.json()
                                status = status_data.get("status")
                                result = status_data.get("resultado")
                                if status == "concluido":
                                    break
                            time.sleep(2)

                        if result:
                            st.success("✅ Processamento concluído!")
                            exibir_vagas(result)
                        else:
                            st.warning("⚠️ Nenhum resultado encontrado ou tempo limite atingido.")
                else:
                    st.error(f"Erro ao enviar currículo. ({response.status_code})")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erro ao enviar currículo: {e}")

# ==============================
# 🔍 Buscar vagas associadas ao e-mail
# ==============================
with col2:
    if st.button("🔎 Buscar Vagas do Meu Currículo"):
        st.session_state["mensagem"] = None
        st.session_state["vagas"] = None

        with st.spinner("Buscando vagas associadas..."):
            try:
                response = requests.get(f"{API_BASE}/curriculo/vagas", params={"email": email}, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    vagas = data.get("resultado", [])
                    if vagas:
                        st.success(f"{len(vagas)} vagas encontradas:")
                        exibir_vagas(vagas)
                    else:
                        st.warning("Nenhuma vaga encontrada ainda. Aguarde o processamento.")
                else:
                    st.error(f"Erro ao buscar vagas. ({response.status_code})")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erro de conexão: {e}")
