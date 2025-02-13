import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder
import io
from streamlit.components.v1 import html
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import tempfile
from datetime import datetime
import tomli  # Add this import for reading TOML files

def load_project_config():
    """Load project configuration from pyproject.toml"""
    try:
        with open("pyproject.toml", "rb") as f:
            return tomli.load(f)
    except Exception as e:
        st.error(f"Error loading project configuration: {str(e)}")
        return None

# Load project configuration
project_config = load_project_config()
if project_config:
    st.sidebar.text(f"Version: {project_config['project']['version']}")
    st.sidebar.text(f"App: {project_config['project']['name']}")

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações iniciais da página
st.set_page_config(
    page_title="Milie Mind Bot 🧠",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Detecta o tema atual
def get_theme():
    # Injeta JavaScript para detectar o tema
    js_code = """
        <script>
            const theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', theme);
        </script>
    """
    html(js_code, height=0)
    return 'dark' if st.get_option("theme.base") == "dark" else 'light'

# Título e descrição
st.title("Milie Mind Bot 🧠")
st.markdown("### Acompanhamento de Consultas para Crianças no Espectro Autista")
st.markdown("---")

# CSS personalizado com suporte a temas
st.markdown("""
    <style>
    :root[data-theme="light"] {
        --bg-color: #ffffff;
        --text-color: #333333;
        --primary-color: #9d4edd;
        --secondary-color: #bb86fc;
        --card-bg: #f8f9fa;
        --card-border: #e9ecef;
    }
    
    :root[data-theme="dark"] {
        --bg-color: #121212;
        --text-color: #e0e0e0;
        --primary-color: #bb86fc;
        --secondary-color: #9d4edd;
        --card-bg: #2c2c2c;
        --card-border: #bb86fc;
    }
    
    body {
        background-color: var(--bg-color);
        color: var(--text-color);
    }
    
    .main {
        background-color: var(--bg-color);
        padding: 20px;
        border-radius: 10px;
    }
    
    h1, h2, h3 {
        color: var(--text-color);
        font-weight: 600;
        margin-top: 1.5em;
    }
    
    .stButton>button {
        background-color: var(--primary-color);
        color: var(--bg-color);
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: var(--secondary-color);
        transform: translateY(-2px);
    }
    
    .analysis-box {
        border: 2px solid var(--primary-color);
        padding: 20px;
        border-radius: 15px;
        background-color: var(--card-bg);
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(145deg, var(--card-bg), var(--bg-color));
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid var(--primary-color);
    }
    
    .encouragement {
        color: var(--primary-color);
        font-size: 1.3em;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        background: linear-gradient(145deg, var(--card-bg), var(--bg-color));
        border-radius: 10px;
        margin: 20px 0;
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0% { box-shadow: 0 0 5px var(--primary-color); }
        50% { box-shadow: 0 0 20px var(--primary-color); }
        100% { box-shadow: 0 0 5px var(--primary-color); }
    }
    
    .emotion-tag {
        display: inline-block;
        padding: 5px 10px;
        margin: 5px;
        border-radius: 15px;
        background-color: var(--primary-color);
        color: var(--bg-color);
    }
    
    .medical-report {
        font-family: 'Courier New', monospace;
        background-color: var(--card-bg);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid var(--card-border);
    }
    
    .stDownloadButton>button {
        background-color: var(--primary-color);
        color: var(--bg-color);
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }
    
    .stDownloadButton>button:hover {
        background-color: var(--secondary-color);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# Inicializa o cliente Groq
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY"))

# Função para transcrever o áudio
def transcrever_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcription = client_groq.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3-turbo",
            prompt="Por favor, transcreva o áudio com clareza e precisão.",
            response_format="json",
            language="pt",
            temperature=0.0
        )
    return transcription.text

# Função para analisar o texto utilizando prompt engineering avançado
def analisar_texto(texto):
    # Prompt para análise familiar
    family_prompt = (
        "Você é uma especialista em psicologia infantil e neurociência, com foco em TEA. "
        "Analise o relato de forma acolhedora e empática, focando em:\n\n"
        "1. 💭 **Análise Emocional:**\n"
        "   - Emoções identificadas (com emojis)\n"
        "   - Intensidade das emoções (1-10)\n"
        "   - Tom geral da comunicação\n\n"
        "2. 🌟 **Pontos Positivos:**\n"
        "   - Progressos observados\n"
        "   - Habilidades demonstradas\n\n"
        "3. 🎯 **Sugestões Práticas:**\n"
        "   - Atividades para casa\n"
        "   - Dicas de interação\n"
        "Use linguagem acessível e mantenha tom positivo e encorajador."
    )
    
    # Prompt para relatório médico
    medical_prompt = (
        "Você é um especialista em neuropsiquiatria infantil com foco em TEA. "
        "Elabore um relatório técnico detalhado considerando:\n\n"
        "1. **Avaliação Clínica:**\n"
        "   - Padrões de comunicação verbal/não-verbal\n"
        "   - Indicadores comportamentais do TEA\n"
        "   - Funções executivas e cognitivas\n\n"
        "2. **Análise Sensorial:**\n"
        "   - Processamento sensorial\n"
        "   - Respostas a estímulos\n"
        "   - Padrões de autorregulação\n\n"
        "3. **Métricas Quantitativas:**\n"
        "   - Escalas padronizadas quando aplicável\n"
        "   - Comparativo com linha base\n"
        "Use terminologia técnica apropriada e formate em estilo de relatório médico."
    )
    
    # Realiza as duas análises
    family_response = client_groq.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": family_prompt},
            {"role": "user", "content": texto}
        ],
        temperature=0.4,
        max_tokens=1024
    )
    
    medical_response = client_groq.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": medical_prompt},
            {"role": "user", "content": texto}
        ],
        temperature=0.2,
        max_tokens=2048
    )
    
    return {
        "family": family_response.choices[0].message.content,
        "medical": medical_response.choices[0].message.content
    }

# Função para criar visualizações de dados
def criar_visualizacoes(analise):
    import plotly.graph_objects as go
    import re
    
    # Extrai valores numéricos da análise (exemplo)
    # Isso dependerá do formato da resposta do modelo
    emocoes = {
        'Alegria': 0,
        'Ansiedade': 0,
        'Frustração': 0,
        'Interesse': 0,
        'Calma': 0
    }
    
    # Atualiza o dicionário baseado na análise
    for emocao in emocoes.keys():
        if emocao.lower() in analise.lower():
            # Procura por números próximos à emoção
            match = re.search(f"{emocao.lower()}.*?(\d+)", analise.lower())
            if match:
                emocoes[emocao] = int(match.group(1))
    
    # Cria gráfico de radar
    fig = go.Figure(data=go.Scatterpolar(
        r=list(emocoes.values()),
        theta=list(emocoes.keys()),
        fill='toself',
        line_color='#bb86fc'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0')
    )
    
    return fig

# Função para processar o áudio (salva em um arquivo temporário)
def process_audio(audio_data, file_extension=".wav"):
    if audio_data is not None:
        # Caso o formato seja dict (formato do mic_recorder)
        if isinstance(audio_data, dict):
            if 'bytes' not in audio_data:
                return None
            audio_bytes = audio_data['bytes']
        else:
            audio_bytes = audio_data

        audio_path = f"temp_audio{file_extension}"
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        try:
            # Exibe o player de áudio
            st.audio(audio_bytes, format=f"audio/{file_extension[1:]}")
            return audio_path
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o áudio: {str(e)}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return None

# Interface de entrada de áudio
st.markdown("### 🎙️ Escolha como fornecer o áudio")

# Cria abas para gravação e upload
tab1, tab2 = st.tabs(["Gravar Áudio", "Fazer Upload"])

# Inicializa o estado da sessão para armazenar o caminho do áudio
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None

with tab1:
    st.markdown("Clique no botão abaixo para começar a gravar")
    # Utiliza o mic_recorder para gravar áudio
    audio_bytes = mic_recorder(
        key="recorder",
        start_prompt="Clique para Gravar",
        stop_prompt="Parar Gravação",
        just_once=True
    )
    if audio_bytes:
        st.success("Áudio gravado com sucesso!")
        st.session_state.audio_path = process_audio(audio_bytes)

with tab2:
    st.markdown("Você pode fazer upload de um arquivo de áudio gravado anteriormente.")
    uploaded_file = st.file_uploader("Escolha um arquivo de áudio", type=['wav', 'mp3', 'm4a'])
    if uploaded_file is not None:
        st.session_state.audio_path = process_audio(
            uploaded_file.getvalue(),
            file_extension="." + uploaded_file.name.split('.')[-1]
        )

# Botão para processar a análise
if st.session_state.audio_path:
    if st.button("Processar Análise", key="analyze_button"):
        with st.spinner("Processando transcrição e análise..."):
            try:
                transcricao = transcrever_audio(st.session_state.audio_path)
                analises = analisar_texto(transcricao)
                
                st.markdown("---")
                st.markdown("## 📊 Resultados da Análise")
                
                # Mensagem de encorajamento animada
                st.markdown('<div class="encouragement">✨ Análise Concluída com Sucesso! ✨</div>', unsafe_allow_html=True)
                
                # Exibe a transcrição
                with st.expander("📝 Transcrição do Áudio", expanded=True):
                    st.markdown('<div class="analysis-box">{}</div>'.format(transcricao), unsafe_allow_html=True)
                
                # Cria tabs para diferentes visões
                tab_familia, tab_medico = st.tabs(["👨‍👩‍👧‍👦 Visão para Família", "👨‍⚕️ Relatório Médico"])
                
                with tab_familia:
                    st.markdown('<div class="analysis-box">{}</div>'.format(analises["family"]), unsafe_allow_html=True)
                    fig = criar_visualizacoes(analises["family"])
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab_medico:
                    st.markdown('<div class="medical-report">{}</div>'.format(analises["medical"]), unsafe_allow_html=True)
                    
                    # Botão para download do relatório
                    if st.button("📥 Baixar Relatório Médico (PDF)"):
                        try:
                            with st.spinner("Gerando PDF..."):
                                # Cria o PDF
                                pdf_path = criar_relatorio_pdf(transcricao, analises["medical"])
                                
                                # Lê o arquivo PDF
                                with open(pdf_path, "rb") as pdf_file:
                                    pdf_bytes = pdf_file.read()
                                
                                # Oferece o download
                                st.download_button(
                                    label="📄 Clique para baixar o relatório",
                                    data=pdf_bytes,
                                    file_name=f"relatorio_medico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf"
                                )
                                
                                # Remove o arquivo temporário
                                os.remove(pdf_path)
                                
                        except Exception as e:
                            st.error(f"Erro ao gerar o PDF: {str(e)}")
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar o áudio: {str(e)}")
            finally:
                if os.path.exists(st.session_state.audio_path):
                    os.remove(st.session_state.audio_path)
                st.session_state.audio_path = None

# Instruções de uso
st.markdown("---")
st.markdown("""
### Como usar:
1. Grave um áudio utilizando o gravador acima ou faça o upload de um arquivo existente.
2. Clique no botão 'Processar Análise' para obter a transcrição e a análise do relato.
3. Visualize os resultados organizados em seções para facilitar a interpretação.
""")

# Adicione esta nova função para criar o PDF
def criar_relatorio_pdf(transcricao, analise_medica):
    # Cria um arquivo temporário para o PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_path = tmp_file.name
        
        # Configuração do documento
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Justify',
            alignment=TA_JUSTIFY,
            fontSize=11,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='Header',
            alignment=TA_CENTER,
            fontSize=16,
            leading=20,
            spaceAfter=30
        ))
        
        # Conteúdo do documento
        content = []
        
        # Cabeçalho
        header = Paragraph(
            "Relatório de Avaliação Neuropsiquiátrica",
            styles['Header']
        )
        content.append(header)
        
        # Data
        data_atual = datetime.now().strftime("%d/%m/%Y")
        data = Paragraph(
            f"Data: {data_atual}",
            styles['Normal']
        )
        content.append(data)
        content.append(Spacer(1, 12))
        
        # Transcrição
        content.append(Paragraph("Transcrição do Áudio:", styles['Heading2']))
        content.append(Spacer(1, 6))
        content.append(Paragraph(transcricao, styles['Justify']))
        content.append(Spacer(1, 12))
        
        # Análise Médica
        content.append(Paragraph("Análise Técnica:", styles['Heading2']))
        content.append(Spacer(1, 6))
        content.append(Paragraph(analise_medica, styles['Justify']))
        
        # Rodapé
        content.append(Spacer(1, 30))
        footer = Paragraph(
            "Documento gerado automaticamente pelo Milie Mind Bot",
            styles['Normal']
        )
        content.append(footer)
        
        # Gera o PDF
        doc.build(content)
        
        return pdf_path
