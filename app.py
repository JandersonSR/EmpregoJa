import streamlit as st
from dotenv import load_dotenv
import os
import requests
import time

load_dotenv()

# 🔗 URL do backend FastAPI (Render)
API_BASE = os.getenv("SERVER_URL", "http://localhost:3000")

st.set_page_config(page_title="Buscador de empregos", layout="wide")

# ==============================
# 🏠 Cabeçalho
# ==============================
st.title("🔎 Buscador de empregos")
st.write("Envie ou atualize seu currículo e veja vagas compatíveis!")

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

col1, col2, col3 = st.columns(3)

# ==============================
# 🚀 Enviar novo currículo
# ==============================
with col1:
    if uploaded_file and st.button("📤 Enviar Currículo"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        data = {"email": email}

        st.info("Enviando currículo para o servidor...")
        try:
            response = requests.post(f"{API_BASE}/curriculo/upload", files=files, data=data, timeout=60)
            if response.status_code == 200:
                job_id = response.json().get("id")
                st.success(f"Currículo enviado com sucesso! ID: {job_id}")

                # Polling do status
                with st.spinner("Processando currículo..."):
                    for _ in range(30):  # até 1 minuto (~30 * 2s)
                        status_resp = requests.get(f"{API_BASE}/status/{job_id}")
                        if status_resp.status_code == 200:
                            data = status_resp.json()
                            status = data.get("status")
                            result = data.get("resultado")
                            if status == "concluido":
                                st.success("✅ Processamento concluído!")
                                break
                        time.sleep(2)

                if result:
                    st.subheader("Vagas compatíveis:")
                    for vaga in result:
                        st.markdown(f"**{vaga['titulo']}** - {vaga['empresa']}")
                        st.progress(vaga["compatibilidade"])
                else:
                    st.warning("Nenhum resultado encontrado ou tempo limite atingido.")
            else:
                st.error("Erro ao enviar currículo. Verifique o backend.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao enviar currículo: {e}")

# ==============================
# 🔄 Atualizar currículo
# ==============================
with col2:
    if uploaded_file and st.button("♻️ Atualizar Currículo"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        data = {"email": email}
        st.info("Atualizando currículo existente...")
        try:
            response = requests.post(f"{API_BASE}/curriculo/atualizar", files=files, data=data, timeout=60)
            if response.status_code == 200:
                st.success("✅ Currículo atualizado com sucesso!")
            else:
                st.error("Erro ao atualizar currículo.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao atualizar currículo: {e}")

# ==============================
# 🔍 Buscar vagas do currículo já enviado
# ==============================
with col3:
    if st.button("🔎 Buscar Vagas para meu Currículo"):
        st.info("Buscando vagas associadas ao seu currículo...")
        try:
            response = requests.get(f"{API_BASE}/curriculo/vagas", params={"email": email}, timeout=60)
            if response.status_code == 200:
                data = response.json()
                vagas = data.get("resultado", [])
                if vagas:
                    st.success(f"{len(vagas)} vagas encontradas:")
                    for vaga in vagas:
                        st.markdown(f"**{vaga['titulo']}** - {vaga['empresa']}")
                        st.progress(vaga["compatibilidade"])
                else:
                    st.warning("Nenhuma vaga encontrada ainda. Aguarde o processamento.")
            else:
                st.error("Erro ao buscar vagas. Verifique o backend.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão: {e}")
