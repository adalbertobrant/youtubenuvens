import os
import re
import json
# import time # Não é mais estritamente necessário sem Selenium, mas pode ser útil para delays futuros
import textwrap
import logging
from datetime import datetime
# from bs4 import BeautifulSoup # Não é mais usado
# from deep_translator import GoogleTranslator # Removido, pois não há mais tradução
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree import ElementTree # For parsing .srv3 subtitles if needed

# Importar o novo módulo e suas constantes/funções
from wordcloud_processor import generate_wordcloud_from_text, WORDCLOUDS_SUBDIR_NAME, get_portuguese_stopwords

# === Configuração de diretórios ===
LOG_DIR = "logs"
TRANS_DIR = "trans"
REPORT_DIR = "relatorios"
# Adicionar um diretório temporário para legendas baixadas por yt-dlp
SUBTITLES_TEMP_DIR = os.path.join(TRANS_DIR, "temp_subs")
# Adicionar diretório para nuvens de palavras (dentro de TRANS_DIR)
WORDCLOUDS_DIR = os.path.join(TRANS_DIR, WORDCLOUDS_SUBDIR_NAME)


# Adicionar WORDCLOUDS_DIR à criação de diretórios
for dir_path in [LOG_DIR, TRANS_DIR, REPORT_DIR, SUBTITLES_TEMP_DIR, WORDCLOUDS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# === Logging com arquivo por data ===
log_filename = os.path.join(LOG_DIR, f"coleta_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar stopwords uma vez para reutilização
PORTUGUESE_STOPWORDS = get_portuguese_stopwords()


# === URLs dos canais ===
TARGET_CHANNEL_URLS = [
    "https://www.youtube.com/@MePoupe/videos", # MePoupe
    "https://www.youtube.com/@primorico/videos", # O Primo Rico
    "https://www.youtube.com/@economistasincero/videos", # Economista Sincero
    "https://www.youtube.com/@GustavocerbasiBr/videos", # Gustavo Cerbasi
    "https://www.youtube.com/@nathfinancas/videos", # Nath Finanças
    "https://www.youtube.com/@TiagoReisYT/videos" , # Tiago Reis
    "https://www.youtube.com/@btgpactual/videos" ,  # BTG Pactual
    "https://www.youtube.com/@StormerOficial/videos" , # Stormer
    "https://www.youtube.com/@RoneyAlbertFrajola/videos" , # Roney Albert
    "https://www.youtube.com/c/Jos%C3%A9KoboriOficial/videos" , # José Kobori
    "https://www.youtube.com/@ChartsFB/videos", # Fausto Botelho
    "https://www.youtube.com/@iontrader/videos" , # Íon Trader
    "https://www.youtube.com/@ogrowallst/videos", # Ogro Wall Street
]

# === Utilitários ===

# def split_text(text, max_length=4999): # Removido - não é mais necessário sem tradução
#     return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def format_for_a4(text, width=70):
    if not text or not text.strip():
        return ""
    return '\n'.join(textwrap.wrap(text, width))

# def translate_text(text, source='pt', target='en'): # Removido - não há mais tradução
#     # ...
#     pass

def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name) # Remove caracteres inválidos em nomes de arquivo Windows/Linux
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)[:100] # Limita e substitui outros não alfanuméricos

# === Coleta de vídeos ===

def get_latest_channel_videos(channel_url, num_videos=1):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'playlistend': num_videos,
        'dump_single_json': True,
        'nocheckcertificate': True,
        'geo_bypass_country': 'BR', # Adicionado
    }
    videos = []
    channel_title_from_playlist = None
    try:
        with YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(channel_url, download=False)
            channel_title_from_playlist = playlist_info.get('uploader') or playlist_info.get('channel') or playlist_info.get('title')

            if 'entries' in playlist_info:
                for entry in playlist_info.get('entries', []):
                    if entry:
                        video_id = entry.get('id')
                        video_title = entry.get('title')
                        videos.append({
                            'id': video_id,
                            'title': video_title,
                            'publish_date': None,
                            'views': None,
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'channel_title_from_playlist': channel_title_from_playlist
                        })
                return videos
    except Exception as e:
        logger.error(f"Erro ao buscar vídeos do canal {channel_url}: {e}")
    return []


# === Utilitários de Parse de Legendas ===
def parse_vtt_content(vtt_content):
    lines = vtt_content.splitlines()
    transcript_parts = []
    for line in lines:
        line = line.strip()
        if not line or "WEBVTT" in line or "-->" in line or re.match(r'^\d+$', line):
            continue
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r' ', ' ', line) # Trata non-breaking space (U+00A0)
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            transcript_parts.append(line)
    return '\n'.join(transcript_parts)

def parse_srv3_content(srv3_content):
    try:
        root = ElementTree.fromstring(srv3_content)
        texts = []
        for p_element in root.findall('.//p'):
            if p_element.text:
                texts.append(p_element.text.strip())
        if not texts: # Fallback se não encontrar em <p>
            for text_element in root.findall('.//text'):
                if text_element.text:
                    texts.append(text_element.text.strip())
        return '\n'.join(texts)
    except ElementTree.ParseError as e:
        logger.error(f"Erro ao parsear conteúdo SRV3 (XML): {e}")
        # Tenta extração bruta como fallback
        plain_text = re.sub(r'<[^>]+>', ' ', srv3_content)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        return plain_text
    except Exception as e:
        logger.error(f"Erro inesperado ao parsear SRV3: {e}")
        return ""


# === Coleta de transcrição com yt-dlp ===
def get_transcript_with_yt_dlp(video_id, preferred_lang='pt'):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    subtitle_output_template = os.path.join(SUBTITLES_TEMP_DIR, f"{video_id}_subtitle")

    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [preferred_lang, 'pt-BR'],
        'subtitlesformat': 'vtt/srv3/best',
        'skip_download': True,
        'quiet': True,
        'nocheckcertificate': True,
        'logtostderr': False,
        'outtmpl': subtitle_output_template,
        'geo_bypass_country': 'BR', # Adicionado
    }

    original_text = ""
    source_lang_of_transcript = None
    actual_subtitle_file_path = None

    try:
        with YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Tentando baixar legenda para {video_id} com template: {subtitle_output_template}")
            info_dict = ydl.extract_info(video_url, download=True) # download=True para que as legendas sejam escritas

            if 'requested_subtitles' in info_dict and info_dict['requested_subtitles']:
                sub_info = None
                # Prioriza o idioma preferido
                if preferred_lang in info_dict['requested_subtitles']:
                    sub_info = info_dict['requested_subtitles'][preferred_lang]
                    source_lang_of_transcript = preferred_lang
                elif 'en' in info_dict['requested_subtitles']: # Fallback para inglês
                    sub_info = info_dict['requested_subtitles']['en']
                    source_lang_of_transcript = 'en'
                    logger.info(f"Legenda em '{preferred_lang}' não encontrada para {video_id}. Usando 'en'.")
                # Adicionar mais fallbacks se necessário (ex: 'es', etc.)
                
                if sub_info and 'filepath' in sub_info and sub_info['filepath']:
                    actual_subtitle_file_path = sub_info['filepath']
                elif sub_info and 'data' in sub_info: # Se yt-dlp retornou os dados diretamente
                    raw_content = sub_info['data']
                    sub_ext = sub_info.get('ext', 'vtt') # Assume vtt se não especificado
                    if sub_ext == 'vtt':
                        original_text = parse_vtt_content(raw_content)
                    elif sub_ext == 'srv3':
                        original_text = parse_srv3_content(raw_content)
                    else:
                        logger.warning(f"Formato de legenda em 'data' não suportado '{sub_ext}' para {video_id}")
                        return None
                else: # Tenta encontrar o arquivo manualmente (fallback, 'filepath' deveria funcionar)
                    logger.warning(f"'filepath' não encontrado em sub_info para {video_id}. Tentando busca manual.")
                    
                    langs_to_try = []
                    if source_lang_of_transcript: # Se já sabemos o idioma de alguma forma
                        langs_to_try.append(source_lang_of_transcript)
                    if preferred_lang not in langs_to_try:
                        langs_to_try.append(preferred_lang)
                    if 'en' not in langs_to_try: # Garante que 'en' seja tentado se não for um dos anteriores
                        langs_to_try.append('en')
                    
                    unique_langs_to_try = []
                    seen_langs = set()
                    for lang in langs_to_try:
                        if lang not in seen_langs:
                            unique_langs_to_try.append(lang)
                            seen_langs.add(lang)

                    for lang_check in unique_langs_to_try:
                        for ext_check in ['vtt', 'srv3']:
                            # O nome do arquivo será algo como: video_id_subtitle.pt.vtt
                            path_to_check = f"{subtitle_output_template}.{lang_check}.{ext_check}"
                            if os.path.exists(path_to_check):
                                actual_subtitle_file_path = path_to_check
                                if not source_lang_of_transcript: # Atualiza se não foi definido
                                    source_lang_of_transcript = lang_check
                                break # Sai do loop de extensões
                            else: # yt-dlp às vezes não usa o template completo para subs
                                path_to_check_alt = os.path.join(SUBTITLES_TEMP_DIR, f"{video_id}.{lang_check}.{ext_check}")
                                if os.path.exists(path_to_check_alt):
                                    actual_subtitle_file_path = path_to_check_alt
                                    if not source_lang_of_transcript:
                                        source_lang_of_transcript = lang_check
                                    break # Sai do loop de extensões
                        if actual_subtitle_file_path: # Se encontrou, sai do loop de idiomas
                            break
                    
                    if actual_subtitle_file_path:
                        logger.info(f"Arquivo de legenda encontrado manualmente: {actual_subtitle_file_path}")

            if actual_subtitle_file_path and os.path.exists(actual_subtitle_file_path):
                logger.info(f"Lendo arquivo de legenda: {actual_subtitle_file_path}")
                with open(actual_subtitle_file_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                
                if actual_subtitle_file_path.endswith('.vtt'):
                    original_text = parse_vtt_content(raw_content)
                elif actual_subtitle_file_path.endswith('.srv3'):
                    original_text = parse_srv3_content(raw_content)
                else:
                    logger.warning(f"Formato de arquivo de legenda não suportado: {actual_subtitle_file_path}")
                    original_text = "" # Ou talvez tentar tratar como texto puro?
                
                # Limpa o arquivo de legenda baixado
                try:
                    os.remove(actual_subtitle_file_path)
                    logger.debug(f"Arquivo de legenda temporário removido: {actual_subtitle_file_path}")
                except OSError as e_rem:
                    logger.warning(f"Não foi possível remover o arquivo de legenda {actual_subtitle_file_path}: {e_rem}")
            
            if not original_text:
                logger.warning(f"Nenhuma transcrição encontrada ou extraída para {video_id} (idioma tentado: {source_lang_of_transcript or preferred_lang}).")
                return None

            return {
                'original': original_text,
                'formatted_original': format_for_a4(original_text),
                'source_language': source_lang_of_transcript # Pode ser None se não foi determinado
            }

    except Exception as e:
        logger.error(f"Erro ao obter transcrição com yt-dlp para {video_id}: {e}")
        # import traceback # Para depuração mais detalhada
        # logger.error(traceback.format_exc())
        return None


# === Processa canal ===
def process_channel(channel_url):
    logger.info(f"Processando canal: {channel_url}")
    
    initial_videos_data = get_latest_channel_videos(channel_url, num_videos=1) # num_videos=1 para pegar o vídeo mais recente
    
    if not initial_videos_data:
        logger.warning(f"Nenhum vídeo encontrado para o canal {channel_url}")
        return None

    first_video_data = initial_videos_data[0]
    channel_name_initial = first_video_data.get('channel_title_from_playlist') or channel_url.split('/')[-2] or channel_url.split('/')[-1]


    data = {
        'url': channel_url,
        'nome_canal': channel_name_initial, # Será atualizado se uma melhor info for encontrada
        'videos_processados': [],
        'caminho_nuvem_palavras': None # Novo campo para a nuvem de palavras do canal
    }
    
    # Coletar todas as transcrições dos vídeos processados para este canal
    # Se num_videos=1, será apenas a transcrição do vídeo mais recente.
    # Se num_videos > 1, concatenará as transcrições.
    all_transcripts_for_channel = []

    try:
        for video_meta in initial_videos_data: 
            video_id = video_meta['id']
            video_title = video_meta['title']
            video_url_yt = video_meta['url']

            logger.info(f"Processando vídeo: {video_title} ({video_id})")

            # Configuração para obter metadados do vídeo, com geo_bypass_country
            video_info_opts = {
                'quiet': True,
                'nocheckcertificate': True,
                'geo_bypass_country': 'BR', # Adicionado e corrigido
            }
            publish_date_final = None
            views_final = None
            
            try:
                with YoutubeDL(video_info_opts) as ydl_vid: # Corrigido aqui
                    info = ydl_vid.extract_info(video_url_yt, download=False)
                    publish_date_str = info.get('upload_date') # YYYYMMDD
                    if publish_date_str:
                        publish_date_final = datetime.strptime(publish_date_str, '%Y%m%d').strftime('%Y-%m-%d')
                    views_final = info.get('view_count')
                    uploader_name = info.get('uploader') or info.get('channel')
                    if uploader_name and data['nome_canal'] == channel_name_initial: # Atualiza se for a inicial
                        data['nome_canal'] = uploader_name 
            except Exception as e_vid_info:
                logger.warning(f"Não foi possível obter metadados detalhados (data, views) para {video_id}: {e_vid_info}")

            transcript_data = get_transcript_with_yt_dlp(video_id, preferred_lang='pt')
            
            processed_video_entry = {
                'id': video_id,
                'titulo': video_title,
                'data_publicacao': publish_date_final,
                'visualizacoes': views_final,
                'url': video_url_yt,
                'transcricao': transcript_data if transcript_data else {'status': 'não disponível'}
            }
            if transcript_data and 'source_language' in transcript_data:
                 processed_video_entry['idioma_transcricao_original'] = transcript_data['source_language']
            
            data['videos_processados'].append(processed_video_entry)

            # Adiciona a transcrição original à lista para a nuvem de palavras do canal
            if transcript_data and transcript_data.get('original'):
                all_transcripts_for_channel.append(transcript_data['original'])
        
        # Gerar nuvem de palavras para o canal se houver transcrições
        if all_transcripts_for_channel:
            full_transcript_text_for_channel = "\n".join(all_transcripts_for_channel)
            
            # Usa o nome do canal (que pode ter sido atualizado) para o arquivo da nuvem
            wc_filename_base = sanitize_filename(data['nome_canal'])
            wordcloud_filename = f"wc_{wc_filename_base}.png"
            wordcloud_output_path = os.path.join(WORDCLOUDS_DIR, wordcloud_filename)
            
            logger.info(f"Gerando nuvem de palavras para o canal '{data['nome_canal']}'...")
            generated_wc_path = generate_wordcloud_from_text(
                full_transcript_text_for_channel,
                wordcloud_output_path,
                stopwords_list=PORTUGUESE_STOPWORDS # Passa as stopwords carregadas
            )
            if generated_wc_path:
                # Armazena o caminho relativo ao diretório TRANS_DIR
                data['caminho_nuvem_palavras'] = os.path.join(WORDCLOUDS_SUBDIR_NAME, wordcloud_filename)
            else:
                logger.warning(f"Não foi possível gerar a nuvem de palavras para o canal '{data['nome_canal']}'.")
        else:
            logger.info(f"Nenhuma transcrição disponível para gerar nuvem de palavras para o canal '{data['nome_canal']}'.")

        save_individual_transcript(data)
        return data

    except Exception as e:
        logger.error(f"Erro ao processar canal {channel_url}: {e}")
        # import traceback
        # logger.error(traceback.format_exc()) # Descomente para debug detalhado
        return None

# === Salva transcrição individual ===
def save_individual_transcript(data_channel):
    try:
        # Usa o nome do canal do dicionário, que pode ter sido refinado
        nome_base_arquivo = sanitize_filename(data_channel['nome_canal'])
        path = os.path.join(TRANS_DIR, f"{nome_base_arquivo}.json")
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data_channel, f, ensure_ascii=False, indent=2)
        logger.info(f"Dados salvos para o canal '{data_channel['nome_canal']}': {path}")
    except Exception as e:
        logger.error(f"Erro ao salvar dados individuais para '{data_channel.get('nome_canal', 'Desconhecido')}': {e}")


# === Salva relatório geral ===
def generate_report(all_channel_data):
    try:
        filename = os.path.join(REPORT_DIR, f"transcricoes_coletadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_channel_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Relatório consolidado gerado: {filename}")
    except Exception as e:
        logger.error(f"Erro ao salvar relatório final: {e}")

# === Execução principal ===
if __name__ == "__main__":
    logger.info("Início da coleta de dados...")
    
    # Garante que os recursos do NLTK estão disponíveis antes de iniciar as threads
    from wordcloud_processor import ensure_nltk_resources
    ensure_nltk_resources() # Chamada explícita aqui, embora já seja chamada na importação de wordcloud_processor

    all_collected_data = []
    # Reduzir workers se estiver tendo problemas de rate limiting ou recursos
    # max_workers=2 ou 3 pode ser mais estável.
    with ThreadPoolExecutor(max_workers=3) as executor: 
        future_to_url = {executor.submit(process_channel, url): url for url in TARGET_CHANNEL_URLS}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    all_collected_data.append(result)
                else:
                    logger.warning(f"Nenhum resultado retornado para o canal: {url}")
            except Exception as e:
                logger.error(f"Erro ao obter resultado da thread para {url}: {e}")
                # import traceback
                # logger.error(traceback.format_exc()) # Descomente para debug detalhado

    if all_collected_data:
        generate_report(all_collected_data)
    else:
        logger.warning("Nenhum dado foi coletado com sucesso de nenhum canal.")
    
    logger.info("Fim da coleta de dados.")
