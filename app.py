import streamlit as st
import requests
from bs4 import BeautifulSoup
import tempfile
import fitz  # PyMuPDF para PDFs
import docx

# -------------------------
# Upload e extração do currículo
# -------------------------
def extrair_curriculo(arquivo, tipo):
    if tipo == "Pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        texto = ""
        with fitz.open(nome_temp) as doc:
            for page in doc:
                texto += page.get_text()
        return texto
    elif tipo == "Docx":
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        doc = docx.Document(nome_temp)
        return "\n".join([p.text for p in doc.paragraphs])
    elif tipo == "Txt":
        return arquivo.read().decode("utf-8")
    return ""

# -------------------------
# Scraping de vagas (exemplo: Vagas.com)
# -------------------------
def coletar_vagas(palavra_chave="python"):
    url = f"https://www.vagas.com.br/vagas-de-{palavra_chave}"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    vagas = []

    # Atenção: seletores CSS podem mudar conforme o site
    for vaga in soup.find_all("div", class_="vaga"):  # classe exemplo
        titulo = vaga.find("h2").text.strip() if vaga.find("h2") else ""
        empresa = vaga.find("span", class_="empresa").text.strip() if vaga.find("span", class_="empresa") else ""
        link = vaga.find("a")["href"] if vaga.find("a") else ""
        vagas.append({"titulo": titulo, "empresa": empresa, "link": link})
    return vagas

# -------------------------
# Análise de compatibilidade usando GPT/DeepSeek
# -------------------------
def calcula_compatibilidade(curriculo, vaga, provedor, modelo, api_key):
    prompt = f"""
    Analise a compatibilidade do seguinte currículo com a vaga:

    Currículo:
    {curriculo}

    Vaga:
    {vaga['titulo']} - {vaga['empresa']}

    Avalie a compatibilidade de 0 a 100 e explique brevemente.
    Retorne apenas o número e a explicação em formato: score: explicação
    """
    if provedor == "DeepSeek":
        url = f"https://openrouter.ai/api/v1/{modelo}/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json={"inputs": prompt})
        if resp.status_code == 200:
            return resp.json()['outputs'][0]['output_text']
    else:  # OpenAI
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        json_data = {
            "model": modelo,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        resp = requests.post(url, headers=headers, json=json_data)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
    return "Erro na análise"

# -------------------------
# Interface Streamlit
# -------------------------
st.title("💼 Recomendador de Vagas por Currículo")

tipo_arquivo = st.selectbox("Tipo de currículo", ["Pdf", "Docx", "Txt"])
arquivo = st.file_uploader("Upload do currículo", type=[tipo_arquivo.lower()])
provedor = st.selectbox("Provedor de IA", ["DeepSeek", "OpenAI"])
modelo = st.selectbox("Modelo", ["deepseek-r1", "deepseek-coder", "gpt-4o-mini"])
api_key = st.text_input("API Key", type="password")

if st.button("Analisar e Buscar Vagas") and arquivo is not None and api_key != "":
    curriculo_texto = extrair_curriculo(arquivo, tipo_arquivo)
    st.subheader("📋 Texto do Currículo")
    st.text(curriculo_texto[:500] + "...")  # mostra parte do currículo

    st.subheader("💼 Vagas Encontradas")
    vagas = coletar_vagas("python")  # ou outra palavra-chave
    resultados = []
    for vaga in vagas:
        compat = calcula_compatibilidade(curriculo_texto, vaga, provedor, modelo, api_key)
        resultados.append({"vaga": vaga, "compat": compat})

    # Mostra resultados
    for res in resultados:
        st.markdown(f"- **{res['vaga']['titulo']}** | {res['vaga']['empresa']} | [Link]({res['vaga']['link']})")
        st.text(f"Compatibilidade: {res['compat']}")
