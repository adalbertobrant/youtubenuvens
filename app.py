# streamlit_app.py
import streamlit as st
import os
import json
import glob
from yt_dlp import YoutubeDL
import subprocess
import sys

# === Configuration ===
REPORT_DIR = "relatorios"
TRANS_DIR = "trans"
WORDCLOUDS_SUBDIR_NAME = "nuvens_palavras"
WORDCLOUDS_BASE_DIR = os.path.join(TRANS_DIR, WORDCLOUDS_SUBDIR_NAME)
SCRIPT_TO_RUN = "noingles.py"

# === Helper Functions ===

def run_collection_script():
    script_path = os.path.abspath(SCRIPT_TO_RUN)
    if not os.path.exists(script_path):
        st.error(f"Script '{SCRIPT_TO_RUN}' não encontrado em '{script_path}'. Verifique o caminho.")
        return False, "Script não encontrado."

    # Mensagem de início visível fora do expander
    st.info(f"Iniciando a execução de '{SCRIPT_TO_RUN}'... Este processo pode ser demorado.")
    
    log_output_for_return = [] # Para retornar o log completo no final
    
    try:
        python_executable = sys.executable
        process = subprocess.Popen(
            [python_executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,
            cwd=os.path.dirname(script_path)
        )

        # Coloca o log detalhado em tempo real dentro de um expander
        with st.expander("Clique para acompanhar o log detalhado da execução", expanded=False):
            log_display_area = st.empty()
            live_log_lines = []

            for line in iter(process.stdout.readline, ''):
                line_cleaned = line.strip()
                log_output_for_return.append(line_cleaned)
                
                live_log_lines.append(line_cleaned)
                # Mantém apenas as últimas N linhas para exibição em tempo real para não sobrecarregar o expander
                if len(live_log_lines) > 50: 
                    live_log_lines.pop(0)
                log_display_area.code("\n".join(live_log_lines), language="log")
            
            # Ao final do loop, mostra o log completo dentro do expander se o usuário o abrir depois
            # ou se ele já estava aberto.
            log_display_area.code("\n".join(log_output_for_return), language="log")

        process.stdout.close()
        return_code = process.wait()

        if return_code == 0:
            st.success(f"Script '{SCRIPT_TO_RUN}' executado com sucesso!") # Mensagem de sucesso visível
            return True, "\n".join(log_output_for_return)
        else:
            st.error(f"Script '{SCRIPT_TO_RUN}' finalizado com erro (código: {return_code}). Verifique o log detalhado acima se necessário.") # Mensagem de erro visível
            return False, "\n".join(log_output_for_return)

    except FileNotFoundError:
        err_msg = f"Erro: O Python executable '{sys.executable}' ou o script '{script_path}' não foi encontrado."
        st.error(err_msg)
        log_output_for_return.append(err_msg)
        return False, "\n".join(log_output_for_return)
    except Exception as e:
        err_msg = f"Erro ao executar o script '{SCRIPT_TO_RUN}': {e}"
        st.error(err_msg)
        log_output_for_return.append(err_msg)
        return False, "\n".join(log_output_for_return)

@st.cache_data
def get_latest_report_data():
    try:
        list_of_files = glob.glob(os.path.join(REPORT_DIR, 'transcricoes_coletadas_*.json'))
        if not list_of_files:
            return None, None
        latest_file = max(list_of_files, key=os.path.getctime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, os.path.basename(latest_file)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de relatório: {e}")
        return None, None

@st.cache_data
def get_channel_banner_url(channel_youtube_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'dump_single_json': True,
        'playlist_items': '0',
        'nocheckcertificate': True,
        'geo_bypass_country': 'BR', # Adicione esta linha
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            if channel_youtube_url.endswith("/videos"):
                 channel_youtube_url = channel_youtube_url.replace("/videos", "")
            elif "/c/" in channel_youtube_url and channel_youtube_url.endswith("/videos"):
                 channel_youtube_url = channel_youtube_url.rsplit("/videos", 1)[0]

            info = ydl.extract_info(channel_youtube_url, download=False)
            thumbnails = info.get('thumbnails')
            if thumbnails:
                banner_thumbnail = thumbnails[-1]
                for thumb in reversed(thumbnails):
                    if thumb.get('width', 0) > 1000 and thumb.get('url'):
                        banner_thumbnail = thumb
                        break
                return banner_thumbnail.get('url')
    except Exception as e:
        print(f"Banner fetch error for {channel_youtube_url}: {e}")
    return None

# === Streamlit App ===
st.set_page_config(layout="wide", page_title="Análise de Canais do YouTube")

st.title("🔎 Análise de Nuvens de Palavras de Canais do YouTube")
st.markdown("""
Esta aplicação permite visualizar nuvens de palavras geradas a partir das transcrições
dos vídeos mais recentes de canais de finanças do YouTube.
Você pode atualizar os dados executando o script de coleta diretamente pela interface.
""")

st.sidebar.header("Controles")
if st.sidebar.button("🚀 Executar Coleta de Dados e Gerar Nuvens"):
    st.cache_data.clear()
    st.cache_resource.clear()

    # O spinner agora é mais genérico, já que o log detalhado está no expander
    with st.spinner(f"Executando '{SCRIPT_TO_RUN}'... Aguarde a finalização."):
        success, script_log_output = run_collection_script() # A função run_collection_script agora lida com o display do log
        
    # As mensagens de sucesso/erro da execução do script são mostradas dentro de run_collection_script
    # A mensagem da sidebar pode ser mais concisa ou removida se as mensagens na área principal forem suficientes.
    if success:
        st.sidebar.success("Processo de coleta finalizado.")
    else:
        st.sidebar.error("Processo de coleta finalizado com erros.")

st.sidebar.markdown("---")

report_result = get_latest_report_data()
all_channel_data = None
latest_report_name = None

if report_result:
    all_channel_data, latest_report_name = report_result

if latest_report_name:
    st.sidebar.success(f"Relatório carregado: {latest_report_name}")
else:
    st.sidebar.info("Nenhum relatório encontrado. Execute a coleta de dados.")

if all_channel_data:
    processed_channels_count = 0
    for channel_data in all_channel_data:
        relative_wordcloud_path = channel_data.get('caminho_nuvem_palavras')

        if relative_wordcloud_path:
            full_wordcloud_path = os.path.join(TRANS_DIR, relative_wordcloud_path)

            if os.path.exists(full_wordcloud_path):
                processed_channels_count +=1
                st.markdown("---")
                
                channel_name = channel_data.get('nome_canal', 'Nome do Canal Indisponível')
                channel_url_from_report = channel_data.get('url', '#')

                st.subheader(f"📺 {channel_name}")

                col1, col2 = st.columns([1, 2])

                with col1:
                    main_channel_page_url = channel_url_from_report.replace('/videos', '') if channel_url_from_report != '#' else '#'
                    st.markdown(f"**Canal:** [{channel_name}]({main_channel_page_url})")
                    
                    banner_url = get_channel_banner_url(channel_url_from_report)
                    if banner_url:
                        st.image(banner_url, caption="Banner do Canal", use_container_width=True)
                    else:
                        st.caption("Banner do canal não disponível.")

                    if channel_data.get('videos_processados'):
                        latest_video = channel_data['videos_processados'][0]
                        video_title = latest_video.get('titulo', 'Título Indisponível')
                        video_url_yt = latest_video.get('url', '#')
                        video_id = latest_video.get('id')

                        st.markdown(f"**Último Vídeo Analisado:** [{video_title}]({video_url_yt})")
                        if video_id:
                            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                            st.image(thumbnail_url, caption="Thumbnail do Vídeo", use_container_width=True)
                    else:
                        st.write("Nenhuma informação de vídeo encontrada neste relatório.")

                with col2:
                    st.markdown("**Nuvem de Palavras Gerada:**")
                    st.image(full_wordcloud_path, caption=f"Nuvem de palavras para {channel_name}", use_container_width=True)
                    with st.popover("🔎 Ampliar Nuvem"):
                        st.image(full_wordcloud_path, use_container_width=True)
        
    if processed_channels_count == 0:
         st.info("Nenhuma nuvem de palavras foi encontrada para exibição nos dados do relatório atual. "
                 "Tente executar a coleta de dados se ainda não o fez, ou verifique os logs do script de coleta.")

elif latest_report_name is None and not any(st.session_state.get(widget_id, {}).get('value', False) for widget_id in st.session_state if isinstance(st.session_state[widget_id], dict) and 'value' in st.session_state[widget_id]):
    st.info("Nenhum dado de relatório encontrado. Clique em 'Executar Coleta de Dados' na barra lateral para gerar os dados.")
else:
    button_clicked_heuristic = False
    for key in st.session_state:
        # Tentativa de verificar se o botão foi pressionado olhando o widget state.
        # Streamlit não tem uma forma direta de saber se um botão específico causou o rerun sem usar callbacks
        # ou setando uma flag no session_state explicitamente no on_click.
        # Esta heurística pode não ser perfeita.
        if isinstance(st.session_state[key], dict) and st.session_state[key].get('value', False) and "button" in key.lower(): # Verifica se é um botão e foi clicado
             button_clicked_heuristic = True
             break
    if not button_clicked_heuristic and latest_report_name is None:
        st.info("Clique em '🚀 Executar Coleta de Dados e Gerar Nuvens' na barra lateral para iniciar o processo.")


st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido para visualização de dados de canais.")
