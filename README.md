# EPORTH Blog Generator

Ferramenta interna para gerar e publicar posts no blog da [EPORTH](https://energiaportatil.com.br) usando IA (Gemini 2.5 Flash) + imagens do Pexels + publicação direta na Shopify.

---

## Funcionalidades

- **Geração de conteúdo com IA** — artigos SEO-otimizados a partir de tema livre, URL, produto ou evento sazonal
- **Busca automática de imagens** — 3 imagens relevantes do Pexels com contexto brasileiro quando aplicável
- **Capa com identidade visual** — overlay de gradiente + logo EPORTH aplicado automaticamente
- **Upload de imagens personalizadas** — substitua qualquer slot por uma imagem própria
- **Publicação direta na Shopify** — como rascunho ou publicado, com metafields de SEO
- **Interface visual** — preview do artigo completo antes de publicar

---

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Interface | Streamlit |
| IA de conteúdo | Google Gemini 2.5 Flash (`google-genai`) |
| Imagens | Pexels API |
| Publicação | Shopify Admin REST API 2025-01 |
| Processamento de imagem | Pillow |

---

## Configuração local

### 1. Clone o repositório

```bash
git clone https://github.com/carlosssanttos/blogs-eporth.git
cd blogs-eporth
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz (nunca commite este arquivo):

```env
GOOGLE_API_KEY=sua_chave_google_ai
PEXELS_API_KEY=sua_chave_pexels
SHOPIFY_STORE_URL=suoja.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_...
SHOPIFY_BLOG_ID=123456789
```

### 4. Inicie a aplicação

```bash
streamlit run app.py
```

---

## Deploy no Streamlit Community Cloud

A aplicação está hospedada no Streamlit Cloud com deploy automático a cada push na branch `master`.

As variáveis de ambiente são configuradas em **Settings → Secrets** no painel do Streamlit Cloud, no formato TOML:

```toml
GOOGLE_API_KEY = "..."
PEXELS_API_KEY = "..."
SHOPIFY_STORE_URL = "..."
SHOPIFY_ACCESS_TOKEN = "..."
SHOPIFY_BLOG_ID = "..."
```

---

## Estrutura do projeto

```
├── app.py                  # Interface Streamlit
├── blog_generator.py       # Geração de conteúdo, busca de imagens, publicação Shopify
├── requirements.txt
├── assets/
│   ├── logo_small.png      # Logo EPORTH (usada no overlay da capa)
│   └── favicon.png         # Favicon do app
└── wiki/
    ├── conteudo/           # Brand guidelines e identidade EPORTH
    └── *.md                # Fichas técnicas dos produtos EcoFlow
```

---

## Uso

1. Escolha o tipo de referência na barra lateral: **Tema livre**, **URL**, **Produto** ou **Evento**
2. Preencha o campo correspondente e clique em **Gerar Blog**
3. Revise o artigo nas abas **Texto**, **Imagens** e **Editar**
4. Ajuste imagens se necessário (botão **Trocar** para nova busca no Pexels ou upload manual)
5. Clique em **Rascunho** ou **Publicar** para enviar à Shopify

---

## Segurança

- Todas as chaves de API ficam exclusivamente no `.env` (local) ou Secrets (Streamlit Cloud)
- O `.env` está no `.gitignore` e nunca é versionado
- Nenhuma chave deve aparecer no código ou no histórico do repositório
