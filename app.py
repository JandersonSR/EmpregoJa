import streamlit as st
import os
import requests
import time

# Configuração do backend (Node.js API)
API_BASE = os.getenv("SERVER_URL", "http://localhost:3000")  # ajuste se rodar em outro host

st.set_page_config(page_title="EmpregoJá", layout="wide")

st.title("🔎 EmpregoJá")
st.write("Upload do seu currículo para encontrar vagas compatíveis!")

# Upload de currículo
uploaded_file = st.file_uploader("Envie seu currículo (PDF, DOCX ou TXT)", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    if st.button("Enviar Currículo"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}

        try:
            response = requests.post(f"{API_BASE}/upload", files=files)
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao enviar currículo: {e}")

        if response.status_code == 200:
            job_id = response.json().get("id")
            st.success(f"Currículo enviado com sucesso! ID: {job_id}")

            # Polling do status
            with st.spinner("Processando currículo..."):
                status = "pendente"
                result = None
                for _ in range(30):  # tenta por 30x (~30 segundos)
                    status_resp = requests.get(f"{API_BASE}/status/{job_id}")
                    if status_resp.status_code == 200:
                        data = status_resp.json()
                        status = data.get("status")
                        result = data.get("resultado")
                        if status == "concluido":
                            break
                    time.sleep(2)

                if status == "concluido" and result:
                    st.success("✅ Processamento concluído!")
                    st.subheader("Vagas compatíveis:")
                    for vaga in result:
                        st.write(f"**{vaga['titulo']}** - {vaga['empresa']}")
                        st.progress(vaga["compatibilidade"])
                else:
                    st.warning("Tempo limite atingido. Tente novamente mais tarde.")
        else:
            st.error("Erro ao enviar currículo. Verifique o backend.")
