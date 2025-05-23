import os
import re
import nltk
from wordcloud import WordCloud
#import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

# Nome do diretório para salvar as nuvens de palavras (será criado dentro de TRANS_DIR)
WORDCLOUDS_SUBDIR_NAME = "nuvens_palavras"

# Tenta baixar 'stopwords' e 'punkt' do NLTK se não estiverem presentes
# 'punkt' é necessário para tokenização em algumas versões do WordCloud ou para pré-processamento futuro
def ensure_nltk_resources():
    resources = {"corpora/stopwords": "stopwords", "tokenizers/punkt": "punkt"}
    for resource_path, resource_id in resources.items():
        try:
            nltk.data.find(resource_path)
            logger.debug(f"Recurso NLTK '{resource_id}' já está presente.")
        except nltk.downloader.DownloadError:
            logger.info(f"Recurso NLTK '{resource_id}' não encontrado. Baixando...")
            nltk.download(resource_id, quiet=True)
            logger.info(f"Recurso NLTK '{resource_id}' baixado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao verificar/baixar recurso NLTK '{resource_id}': {e}")

ensure_nltk_resources()

def get_portuguese_stopwords():
    """Retorna uma lista de stopwords em português do NLTK, mais algumas personalizadas."""
    try:
        base_stopwords = set(nltk.corpus.stopwords.words('portuguese'))
        # Adicione aqui outras stopwords comuns em transcrições ou específicas do seu domínio

        custom_stopwords = {

    # outras
    'interior', 'entrar', 'ideal', 'começam', 'estudando', 'ganhar', 'ganho', 'ganhei', 'perda', 'perdi', 'perdeu', 'perdendo', 'perca', 'cedo', 'necessariamente', 'elevado', 'recebe', 'mês', 'distante', 'jovem', 'juventude', 'velho', 'adulto', 'criança', 'nesse', 'nessa', 'neste', 'nesta', 'hoje', 'amanhã', 'depois', 'ontem', 'pagar', 'entrar', 'concluir', 'dessa', 'desse', 'filhos', 'casamento', 'ideal', 'começam', 'ocupado', 'filho', 'familiar', 'mês', 'pagando', 'cresci', 'cresce', 'crescimento', 'deparar', 'chato', 'falando', 'deixa', 'deixar', 'deixou', 'toda', 'todo', 'cozinha', 'repente', 'ama', 'função', 'funções', 'funcionalidade', 'piada', 'relação', 'muitas', 'muito', 'muita', 'muitos', 'Pô', 'pô', 'ó', 'Ó', 'atrás', 'dentro', 'todas', 'mundo', 'vams', 'meio', 'chama', 'diferente', 'diferença', 'diferentes', 'atender', 'atendimento', 'whatsapp', 'novos', 'acredita', 'operador', 'evolução', 'ajuda', 'pai', 'filho', 'surpreendendo', 'passado', 'conseguir','esquece', 'esquecer', 'esquecida', 'filhos', 'filha', 'filhas', 'fila', 'filas', 'puxada', 'alguns', 'alguma', 'algumas', 'coisa', 'coisas', 'leves', 'leve', 'grandes', 'grandeza', 'grandão', 'paraa', 'lugar', 'chegar', 'chegou', 'chegada', 'largada', 'trazer', 'vezes','gosto', 'gosta', 'Uhum', 
    # --- Artigos ---
    'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',

    # --- Preposições ---
    'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
    'por', 'pelo', 'pela', 'pelos', 'pelas',
    'para', 'pra', 'pro', # 'pra' e 'pro' são contrações informais importantes
    'com', 'sem', 'sob', 'sobre', 'ante', 'após', 'até', 'contra',
    'desde', 'entre', 'perante', 'trás', 'através', 'segundo', 'conforme', 'durante',

    # --- Conjunções ---
    'e', 'ou', 'mas', 'porém', 'contudo', 'entretanto', 'todavia',
    'que', 'se', 'porque', 'pois', 'quando', 'enquanto', 'embora',
    'como', 'assim', 'logo', 'portanto', 'então', 'assim', 'afinal',

    # --- Pronomes Pessoais e Tratamento ---
    'eu', 'tu', 'ele', 'ela', 'nós', 'vós', 'eles', 'elas',
    'me', 'te', 'se', 'lhe', 'nos', 'vos', 'lhes',
    'mim', 'ti', 'si', 'conosco', 'convosco',
    'você', 'vocês', 'sr', 'sra', 'senhor', 'senhora',

    # --- Pronomes Possessivos ---
    'meu', 'minha', 'meus', 'minhas',
    'teu', 'tua', 'teus', 'tuas',
    'seu', 'sua', 'seus', 'suas', # Já cobre 'dele', 'dela', 'deles', 'delas' implicitamente
    'nosso', 'nossa', 'nossos', 'nossas',
    'vosso', 'vossa', 'vossos', 'vossas',

    # --- Pronomes Demonstrativos ---
    'este', 'esta', 'estes', 'estas', 'isto',
    'esse', 'essa', 'esses', 'essas', 'isso',
    'aquele', 'aquela', 'aqueles', 'aquelas', 'aquilo',
    'tal', 'tais', 'mesmo', 'mesma', 'mesmos', 'mesmas',
    'outro', 'outra', 'outros', 'outras',

    # --- Pronomes Indefinidos e Relativos ---
    'alguém', 'ninguém', 'tudo', 'nada', 'algo', 'cada', 'qualquer', 'quaisquer',
    'quem', 'qual', 'quais', 'cujo', 'cuja', 'cujos', 'cujas', 'onde', 'quanto', 'quantos', 'quanta', 'quantas',

    # --- Advérbios Comuns (tempo, lugar, modo, intensidade, etc.) ---
    'aqui', 'ali', 'lá', 'aí', 'acolá', 'cá',
    'agora', 'hoje', 'ontem', 'amanhã', 'depois', 'antes', 'breve',
    'sempre', 'nunca', 'jamais', 'ainda', 'já',
    'muito', 'pouco', 'mais', 'menos', 'bem', 'mal', 'assim', 'quase',
    'também', 'só', 'somente', 'apenas', 'inclusive', 'exclusive',
    'talvez', 'certamente', 'realmente', 'provavelmente', 'acaso',
    'onde', 'aonde', 'donde', 'como', 'quando',

    # --- Verbos Auxiliares e Comuns (em algumas formas) ---
    # Ser
    'ser', 'sou', 'és', 'é', 'somos', 'sois', 'são',
    'era', 'eras', 'era', 'éramos', 'éreis', 'eram',
    'fui', 'foste', 'foi', 'fomos', 'fostes', 'foram',
    'serei', 'serás', 'será', 'seremos', 'sereis', 'serão',
    'seria', 'serias', 'seria', 'seríamos', 'seríeis', 'seriam',
    'sendo', 'sido',
    # Estar
    'estar', 'estou', 'estás', 'está', 'estamos', 'estais', 'estão',
    'estava', 'estavas', 'estava', 'estávamos', 'estáveis', 'estavam',
    'esteve', 'estiveste', 'esteve', 'estivemos', 'estivestes', 'estiveram',
    'estarei', 'estarás', 'estará', 'estaremos', 'estareis', 'estarão',
    'estaria', 'estarias', 'estaria', 'estaríamos', 'estaríeis', 'estariam',
    'estando', 'estado',
    # Ter
    'ter', 'tenho', 'tens', 'tem', 'temos', 'tendes', 'têm',
    'tinha', 'tinhas', 'tinha', 'tínhamos', 'tínheis', 'tinham',
    'tive', 'tiveste', 'teve', 'tivemos', 'tivestes', 'tiveram',
    'terei', 'terás', 'terá', 'teremos', 'tereis', 'terão',
    'teria', 'terias', 'teria', 'teríamos', 'teríeis', 'teriam',
    'tendo', 'tido',
    # Haver
    'haver', 'hei', 'hás', 'há', 'havemos', 'haveis', 'hão',
    'havia', 'houve', 'haverá', 'haveria',
    # Ir
    'ir', 'vou', 'vais', 'vai', 'vamos', 'ides', 'vão', # 'vamo' é coloquial
    'ia', 'ias', 'ia', 'íamos', 'íeis', 'iam',
    'fui', 'foste', 'foi', 'fomos', 'fostes', 'foram', # Repetido de 'ser', mas comum para 'ir'
    'irei', 'irás', 'irá', 'iremos', 'ireis', 'irão',
    'iria', 'irias', 'iria', 'iríamos', 'iríeis', 'iriam',
    'indo', 'ido',
    # Fazer
    'fazer', 'faço', 'fazes', 'faz', 'fazemos', 'fazeis', 'fazem',
    'fazia', 'fiz', 'fez', 'fará', 'faria', 'feito', 'fazendo',
    # Poder
    'poder', 'posso', 'podes', 'pode', 'podemos', 'podeis', 'podem',
    'podia', 'pude', 'pôde', 'poderá', 'poderia', 'podendo', 'podido',
    # Dizer
    'dizer', 'digo', 'dizes', 'diz', 'dizemos', 'dizeis', 'dizem',
    'dizia', 'disse', 'dirá', 'diria', 'dizendo', 'dito',
    # Querer
    'querer', 'quero', 'queres', 'quer', 'queremos', 'quereis', 'querem',
    'queria', 'quis', 'quisera', 'querendo', 'querido',
    # Saber
    'saber', 'sei', 'sabes', 'sabe', 'sabemos', 'sabeis', 'sabem',
    'sabia', 'soube', 'saberá', 'saberia', 'sabendo', 'sabido',
    # Ver
    'ver', 'vejo', 'vês', 'vê', 'vemos', 'vedes', 'veem',
    'via', 'vi', 'viu', 'verá', 'veria', 'vendo', 'visto', 'enxerga', 'olha', 'olhar', 'olhando',
    # Dar
    'dar', 'dou', 'dás', 'dá', 'damos', 'dais', 'dão',
    'dava', 'dei', 'deu', 'dará', 'daria', 'dando', 'dado',
    # Vir
    'vir', 'venho', 'vens', 'vem', 'vimos', 'vindes', 'vêm',
    'vinha', 'vim', 'veio', 'virá', 'viria', 'vindo',
    # Ficar
    'ficar', 'fico', 'fica', 'ficamos', 'ficam', 'ficava', 'fiquei', 'ficou', 'ficará', 'ficaria', 'ficando',
    # Achar
    'achar', 'acho', 'acha', 'achamos', 'acham', 'achava', 'achei', 'achou', 'achará', 'acharia', 'achando',

    # --- Interjeições e Expressões Comuns (coloquiais BR) ---
    'né', 'tá', 'tô', 'aí', 'daí', 'então', 'poxa', 'puts', 'eita', 'vixe', 'xi', 'ué', 'uai',
    'tipo', 'mano', 'cara', 'meu', # 'cara' e 'meu' como vocativos/interjeições
    'ah', 'oh', 'ih', 'eh', 'hem', 'hein', 'hum', 'hmm', 'olá', 'oi', 'alô',
    'oba', 'opa', 'epa', 'ora', 'pois', 'psiu', 'oba', 'eba',
    'caramba', 'nossa', 'céus', 'credo', 'ufa', 'valeu', 'beleza', 'show', 'joia', 'legal', 'bacana', 'massa', 'top',
    'ok', 'okay', 'certo', 'combinado',

    # --- Saudações e Despedidas ---
    'bom', 'boa', 'dia', 'tarde', 'noite', # "bom dia", "boa tarde", "boa noite"
    'obrigado', 'obrigada', 'de nada', 'por nada', 'disponha',
    'tchau', 'adeus', 'até logo', 'até mais',

    # --- Palavras Genéricas / Vagas / Enchimento ---
    'coisa', 'coisas', 'negócio', 'parada', 'lance', 'bagulho', 'troço',
    'gente', 'pessoal', 'galera', 'turma', 'pessoa', 'pessoas',
    'parte', 'ponto', 'lado', 'jeito', 'forma', 'maneira', 'modo',
    'questão', 'assunto', 'caso', 'situação', 'problema', 'solução',
    'nível', 'grau', 'espécie', 'exemplo', 'fato',
    'momento', 'hora', 'tempo', 'vez', 'instante', 'época',
    'tudo', # Já incluso em pronomes indefinidos, mas reforçando
    'alguma', 'nenhuma', 'vários', 'várias', 'diversos', 'diversas',
    'grande', 'pequeno', 'enorme', 'mínimo', 'máximo',
    'alto', 'baixo', 'novo', 'velho',
    'primeiro', 'segundo', 'terceiro', 'último', # Numerais ordinais básicos
    'próprio', 'própria',

    # --- Numerais Cardinais (por extenso, os mais comuns) ---
    'zero', 'um', 'dois', 'duas', 'três', 'quatro', 'cinco',
    'seis', 'sete', 'oito', 'nove', 'dez',

    # --- Termos de Mídia Social / YouTube (se relevante para seu contexto) ---
    'vídeo', 'canal', 'link', 'post', 'clique', 'clicar', 'curtir', 'curte', 'like',
    'compartilhar', 'compartilhe', 'comentar', 'comentário', 'comenta', 'comentem',
    'inscrição', 'inscrever', 'inscreva-se', 'inscreva', 'segue', 'seguir', 'seguindo',
    'live', 'stories', 'feed', 'perfil', 'conta', 'online', 'site', 'blog',
    'descrição', 'abaixo', 'acima', 'confira', 'veja', 'assista',

    # --- Conectores Orais / Vícios de Linguagem (muitos já cobertos, mas reforçando) ---
    'basicamente', 'literalmente', 'justamente', 'exatamente', 'principalmente',
    'enfim', 'finalmente', 'aliás', 'inclusive', 'além', 'ademais',
    'quer dizer', 'ou seja', 'isto é', 'por exemplo',

    # --- Termos de Processo/Ação Genéricos ---
    'começar', 'começa', 'começando', 'iniciar', 'inicia', 'iniciando',
    'terminar', 'termina', 'terminando', 'finalizar', 'finaliza', 'finalizando',
    'continuar', 'continua', 'continuando', 'seguir', 'segue', 'seguindo', # 'seguir' também pode ser de 'follow'
    'usar', 'usa', 'usando', 'utilizar', 'utiliza', 'utilizando',
    'mostrar', 'mostra', 'mostrando', 'apresentar', 'apresenta', 'apresentando',
    'colocar', 'coloca', 'colocando', 'botar', 'bota', 'botando', # 'botar' é mais informal
    'pegar', 'pega', 'pegando',
    'falar', 'fala', 'falando', 'conversar', 'conversa', 'conversando',
    'perguntar', 'pergunta', 'perguntando', 'responder', 'responde', 'respondendo',

    # --- Palavras de comparação e grau ---
    'tão', 'tanto', 'tanta', 'tantos', 'tantas', 'quanto',
    'maior', 'menor', 'melhor', 'pior',
    'super', 'hiper', 'mega', 'ultra', # prefixos comuns que viram palavras
}


        return list(base_stopwords.union(custom_stopwords))
    except LookupError:
        logger.error("Pacote 'stopwords' do NLTK não encontrado. Tente nltk.download('stopwords').")
        return list({'que', 'de', 'do', 'da', 'o', 'a', 'e', 'é', 'um', 'uma'}) # Fallback básico
    except Exception as e:
        logger.error(f"Erro ao carregar stopwords: {e}")
        return []

def generate_wordcloud_from_text(text, output_filepath, stopwords_list=None):
    """
    Gera uma nuvem de palavras a partir de um texto e a salva em um arquivo.

    Args:
        text (str): O texto para gerar a nuvem de palavras.
        output_filepath (str): O caminho completo para salvar a imagem da nuvem de palavras.
        stopwords_list (list, optional): Lista de stopwords. Se None, usa as de português.

    Returns:
        str: O caminho para o arquivo da nuvem de palavras gerada, ou None se erro.
    """
    if not text or not text.strip():
        logger.warning("Texto vazio fornecido para geração da nuvem de palavras.")
        return None

    if stopwords_list is None:
        stopwords_list = get_portuguese_stopwords()

    try:
        # Remove URLs e menções @ que podem poluir a nuvem
        text_cleaned = re.sub(r'http\S+', '', text)
        text_cleaned = re.sub(r'@\w+', '', text_cleaned)
        text_cleaned = re.sub(r'#\w+', '', text_cleaned) # Remove hashtags

        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            stopwords=set(stopwords_list), # WordCloud espera um set para eficiência
            min_font_size=10,
            collocations=False, # Evita bigramas comuns como "bom dia" se não desejar
            normalize_plurals=False # Tenta normalizar plurais, pode ser útil
        ).generate(text_cleaned)

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        plt.savefig(output_filepath, bbox_inches='tight')
        plt.close() # Libera memória
        logger.info(f"Nuvem de palavras gerada e salva em: {output_filepath}")
        return output_filepath
    except Exception as e:
        logger.error(f"Erro ao gerar nuvem de palavras para '{os.path.basename(output_filepath)}': {e}")
        # import traceback
        # logger.error(traceback.format_exc())
        return None

if __name__ == '__main__':
    # Exemplo de uso (para teste rápido)
    ensure_nltk_resources()
    test_text = """
    Olá pessoal, bem-vindos ao meu canal! No vídeo de hoje vamos falar sobre finanças,
    investimentos e como economizar dinheiro. Não se esqueça de curtir o vídeo, se inscrever
    no canal e ativar o sininho para não perder nenhuma novidade. Fazer um bom planejamento
    financeiro é muito importante para o seu futuro. Obrigado por assistir e até a próxima!
    dinheiro dinheiro dinheiro investimento investimento economia.
    """
    pt_stopwords = get_portuguese_stopwords()
    print(f"Stopwords: {pt_stopwords[:20]}...") # Mostra algumas

    # Cria um diretório de teste para a nuvem
    test_output_dir = "test_wordclouds"
    os.makedirs(test_output_dir, exist_ok=True)
    test_output_path = os.path.join(test_output_dir, "exemplo_nuvem.png")

    generate_wordcloud_from_text(test_text, test_output_path, stopwords_list=pt_stopwords)
    if os.path.exists(test_output_path):
        print(f"Nuvem de exemplo gerada em: {test_output_path}")
