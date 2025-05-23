# Analisador de Nuvens de Palavras de Canais do YouTube

Este projeto coleta transcrições dos vídeos mais recentes de canais específicos do YouTube, gera nuvens de palavras a partir dessas transcrições e as exibe em uma interface web interativa construída com Streamlit. A aplicação permite que o usuário dispare o processo de coleta e geração de dados diretamente pela interface.

## Funcionalidades

*   **Coleta de Dados do YouTube:**
    *   Busca os vídeos mais recentes de uma lista pré-definida de canais do YouTube.
    *   Utiliza `yt-dlp` para baixar as legendas/transcrições disponíveis (priorizando português).
    *   Extrai metadados dos vídeos, como título, data de publicação e visualizações.
*   **Processamento de Texto e Geração de Nuvens de Palavras:**
    *   Limpa o texto das transcrições (remove timestamps, tags HTML, etc.).
    *   Utiliza a biblioteca `wordcloud` para gerar imagens de nuvens de palavras a partir do texto das transcrições de cada canal.
    *   Emprega uma lista customizada de *stopwords* em português para melhorar a relevância das palavras na nuvem.
*   **Interface Web Interativa (Streamlit):**
    *   Exibe as nuvens de palavras geradas.
    *   Mostra informações do canal (banner, link) e do último vídeo analisado (thumbnail, título, link).
    *   Permite ao usuário ampliar as nuvens de palavras para melhor visualização.
    *   **Funcionalidade de Execução:** O usuário pode iniciar o script de coleta e processamento de dados diretamente pela interface web.
    *   Feedback em tempo real (opcionalmente expansível) durante a execução do script de coleta.
*   **Relatórios e Logging:**
    *   Salva os dados coletados e processados em arquivos JSON.
    *   Gera logs detalhados da execução do script de coleta.



## Tecnologias Utilizadas

*   **Python 3.x**
*   **Streamlit:** Para a interface web interativa.
*   **yt-dlp:** Para baixar informações e legendas de vídeos do YouTube.
*   **wordcloud:** Para gerar as nuvens de palavras.
*   **NLTK (Natural Language Toolkit):** Para *stopwords* em português e tokenização (se necessário).
*   **Matplotlib:** Usado internamente pela biblioteca `wordcloud` para renderizar as imagens.
*   **Requests (indireto):** Usado por `yt-dlp` e outras bibliotecas para comunicação HTTP.

## Estrutura do Projeto
├── logs/ # Arquivos de log da coleta de dados
├── relatorios/ # Relatórios JSON consolidados das coletas
├── trans/ # Diretório de transcrições e dados processados
│ ├── nuvens_palavras/ # Imagens das nuvens de palavras geradas
│ ├── temp_subs/ # Diretório temporário para legendas baixadas
│ └── [nome_canal].json # Dados detalhados por canal (transcrições, etc.)
├── noingles.py # Script principal para coleta e processamento de dados
├── wordcloud_processor.py # Módulo para geração de nuvens de palavras e stopwords
├── streamlit_app.py # Arquivo da aplicação Streamlit
├── requirements.txt # Dependências do Python
└── README.md # Este arquivo

## Instalação

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/adalbertobrant/youtubenuvens.git
    cd youtubenuvens
    ```

2.  **Crie e Ative um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # No Windows:
    # venv\Scripts\activate
    # No macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    Certifique-se de que você tem o `pip` atualizado.
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
    O arquivo `requirements.txt` deve conter:
    ```
    streamlit
    yt-dlp
    wordcloud
    nltk
    matplotlib
    # Pillow (geralmente uma dependência do matplotlib/wordcloud, mas bom listar)
    Pillow 
    ```
    *Nota: `nltk` pode precisar baixar recursos adicionais na primeira execução. O script `wordcloud_processor.py` tenta fazer isso automaticamente para `stopwords` e `punkt`.*

4.  **(Opcional, mas recomendado para `yt-dlp`): Instale o FFmpeg**
    `yt-dlp` pode necessitar do FFmpeg para algumas operações de download ou extração de áudio/vídeo. Consulte a [documentação do yt-dlp](https://github.com/yt-dlp/yt-dlp#installation) para instruções de instalação do FFmpeg em seu sistema operacional.

## Modo de Uso

1.  **Execute a Aplicação Streamlit:**
    Navegue até o diretório raiz do projeto no seu terminal e execute:
    ```bash
    streamlit run streamlit_app.py
    ```
    A aplicação será aberta automaticamente no seu navegador web padrão (geralmente em `http://localhost:8501`).

2.  **Execute a Coleta de Dados (dentro da Aplicação):**
    *   Na barra lateral da aplicação Streamlit, clique no botão "🚀 Executar Coleta de Dados e Gerar Nuvens".
    *   Aguarde o processo ser concluído. Você pode acompanhar o progresso (de forma resumida) e, opcionalmente, expandir uma seção para ver o log detalhado.
    *   Este processo pode levar vários minutos, dependendo do número de canais e da velocidade da sua conexão com a internet.

3.  **Visualize os Resultados:**
    *   Após a conclusão da coleta, os dados dos canais (com suas respectivas nuvens de palavras, banners e informações do último vídeo) serão exibidos na página principal da aplicação.
    *   Navegue pelos canais e clique nas nuvens de palavras para ampliá-las.

## Configuração

*   **Canais do YouTube:** A lista de canais a serem analisados está definida na variável `TARGET_CHANNEL_URLS` dentro do arquivo `noingles.py`. Você pode modificar esta lista para incluir os canais de seu interesse.
*   **Stopwords:** Palavras irrelevantes a serem excluídas das nuvens de palavras podem ser customizadas na função `get_portuguese_stopwords()` dentro do arquivo `wordcloud_processor.py`.

## Contribuição

Contribuições são bem-vindas! Se você tiver sugestões para melhorar o projeto, sinta-se à vontade para:

1.  Fazer um Fork do projeto.
2.  Criar uma nova Branch (`git checkout -b feature/sua-feature`).
3.  Fazer Commit de suas alterações (`git commit -am 'Adiciona nova feature'`).
4.  Fazer Push para a Branch (`git push origin feature/sua-feature`).
5.  Abrir um Pull Request.

