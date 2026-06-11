#!/usr/bin/env python3
"""
EPORTH Blog Generator
Gera e publica posts no blog da Shopify a partir de referências diversas.

Uso:
  python blog_generator.py --url https://site.com/artigo
  python blog_generator.py --topic "energia solar para camping"
  python blog_generator.py --produto delta-pro
  python blog_generator.py --evento "Green November 2026"
  python blog_generator.py --topic "backup residencial" --publish
"""

import argparse
import base64
import json
import os
import random
import sys
from html.parser import HTMLParser
from pathlib import Path

from google import genai
from google.genai import types as genai_types
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
WIKI_DIR = SCRIPT_DIR / "wiki"
WIKI_CONTEUDO_DIR = WIKI_DIR / "conteudo"

PRODUCT_WIKI_MAP = {
    "delta-pro": "ecoflow-delta-pro.md",
    "delta-pro-ultra": "ecoflow-delta-pro-ultra-esquemas-ligacao.md",
    "delta-3": "ecoflow-delta-3.md",
    "delta-compacto": "ecoflow-delta-compacto.md",
    "river": "ecoflow-river.md",
    "wave-3": "ecoflow-geradores-wave3.md",
    "paineis": "ecoflow-paineis-solares.md",
    "portfolio": "portfolio-ecoflow.md",
    "bluetti": "portfolio-bluetti.md",
}

# ---------------------------------------------------------------------------
# Context loaders
# ---------------------------------------------------------------------------

def load_brand_context() -> str:
    parts = []
    for fname in ("brand-guidelines.md", "identidade-eporth.md"):
        f = WIKI_CONTEUDO_DIR / fname
        if f.exists():
            parts.append(f.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def load_product_wiki(product_key: str) -> str:
    if product_key not in PRODUCT_WIKI_MAP:
        available = ", ".join(PRODUCT_WIKI_MAP.keys())
        print(f"Produto '{product_key}' não encontrado. Disponíveis: {available}")
        sys.exit(1)
    product_file = WIKI_DIR / PRODUCT_WIKI_MAP[product_key]
    if not product_file.exists():
        print(f"Arquivo {product_file} não encontrado.")
        return ""
    return product_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# URL content extraction
# ---------------------------------------------------------------------------

class _SimpleTextExtractor(HTMLParser):
    SKIP = {"script", "style", "meta", "link", "head", "noscript"}

    def __init__(self):
        super().__init__()
        self._current = None
        self.chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        self._current = tag.lower()

    def handle_data(self, data):
        if self._current not in self.SKIP:
            s = data.strip()
            if s:
                self.chunks.append(s)


def fetch_url_content(url: str) -> str:
    # Try trafilatura first (best extraction quality)
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
            if text:
                return text
    except ImportError:
        pass

    # Fallback: requests + basic HTML parser
    headers = {"User-Agent": "Mozilla/5.0 (compatible; EporthBlogBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    extractor = _SimpleTextExtractor()
    extractor.feed(resp.text)
    # Return up to first 8000 chars to stay within context
    return " ".join(extractor.chunks)[:8000]


# ---------------------------------------------------------------------------
# Pexels image search
# ---------------------------------------------------------------------------

def fetch_pexels_images(keywords: list[str], count: int = 3) -> list[dict]:
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        return []

    images = []
    headers = {"Authorization": api_key}

    for keyword in keywords:
        if len(images) >= count:
            break
        is_cover = len(images) == 0
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={
                    "query": keyword,
                    "per_page": 5 if is_cover else 1,
                    "orientation": "landscape",
                    "size": "large",
                },
                timeout=10,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
            if photos:
                # For cover: pick highest-resolution photo
                p = max(photos, key=lambda x: x.get("width", 0)) if is_cover else photos[0]
                img_url = p["src"]["large"]

                img_bytes = None
                try:
                    img_resp = requests.get(img_url, timeout=15)
                    img_resp.raise_for_status()
                    img_bytes = img_resp.content
                except Exception:
                    pass

                images.append({
                    "src": img_url,
                    "_bytes": img_bytes,
                    "alt": p.get("alt", keyword),
                    "photographer": p.get("photographer", "Pexels"),
                    "_keyword": keyword,
                })
        except Exception:
            continue

    return images




def fetch_new_pexels_image(keyword: str, exclude_url: str = "") -> dict | None:
    """Fetch a different Pexels image for the same keyword, excluding the current one."""
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        return None
    headers = {"Authorization": api_key}
    for page in random.sample(range(1, 6), 3):  # try up to 3 random pages
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": keyword, "per_page": 10, "orientation": "landscape", "page": page},
                timeout=10,
            )
            resp.raise_for_status()
            photos = [p for p in resp.json().get("photos", []) if p["src"]["large"] != exclude_url]
            if not photos:
                continue
            p = random.choice(photos)
            img_url = p["src"]["large"]
            img_bytes = None
            try:
                img_bytes = requests.get(img_url, timeout=15).content
            except Exception:
                pass
            return {
                "src": img_url,
                "_bytes": img_bytes,
                "alt": p.get("alt", keyword),
                "photographer": p.get("photographer", "Pexels"),
                "_keyword": keyword,
            }
        except Exception:
            continue
    return None


def _make_img_tag(img: dict) -> str:
    photographer = img.get("photographer", "")
    alt = img.get("alt", "")
    if photographer and photographer != "Upload manual":
        caption = f'Foto: {photographer} / Pexels'
    elif alt:
        caption = alt
    else:
        caption = ""
    return (
        f'<figure style="margin:28px 0;">'
        f'<img src="{img["src"]}" alt="{alt}" '
        f'style="width:100%;border-radius:8px;display:block;" />'
        f'<figcaption style="font-size:0.78rem;color:#888;text-align:center;margin-top:6px;">'
        f'{caption}</figcaption>'
        f'</figure>'
    )


def insert_images_into_html(body_html: str, images: list[dict]) -> str:
    """Insert body images into HTML. images[0] is the Shopify cover — not inserted into body."""
    if not images:
        return body_html

    body_imgs = images[1:]  # images[0] is cover only (uploaded separately to Shopify)
    if not body_imgs:
        return body_html

    result = body_html

    if len(body_imgs) >= 1:
        # First body image: after 2nd </p> following first <h2>
        h2_pos = result.find("<h2>")
        if h2_pos != -1:
            p1 = result.find("</p>", h2_pos)
            p2 = result.find("</p>", p1 + 4) if p1 != -1 else -1
            insert_pos = (p2 + 4) if p2 != -1 else (p1 + 4 if p1 != -1 else len(result))
        else:
            p1 = result.find("</p>")
            p2 = result.find("</p>", p1 + 4) if p1 != -1 else -1
            insert_pos = (p2 + 4) if p2 != -1 else (p1 + 4 if p1 != -1 else len(result))
        result = result[:insert_pos] + "\n" + _make_img_tag(body_imgs[0]) + "\n" + result[insert_pos:]

    if len(body_imgs) >= 2:
        # Second body image: after first </p> following second <h2>/<h3>
        first_h2 = result.find("<h2>")
        second_h2 = result.find("<h2>", first_h2 + 4) if first_h2 != -1 else -1
        # Fallback to h3 if no second h2
        if second_h2 == -1:
            first_h3 = result.find("<h3>")
            second_h3 = result.find("<h3>", first_h3 + 4) if first_h3 != -1 else result.find("<h3>")
            second_h2 = second_h3
        insert_pos = -1
        if second_h2 != -1:
            p1 = result.find("</p>", second_h2)
            if p1 != -1:
                insert_pos = p1 + 4
        if insert_pos == -1:
            # Fallback: insert at ~2/3 of the document by paragraph count
            all_p_ends = [i + 4 for i in range(len(result) - 3) if result[i:i+4] == "</p>"]
            if len(all_p_ends) >= 3:
                insert_pos = all_p_ends[len(all_p_ends) * 2 // 3]
            else:
                insert_pos = len(result)
        result = result[:insert_pos] + "\n" + _make_img_tag(body_imgs[1]) + "\n" + result[insert_pos:]

    return result


# ---------------------------------------------------------------------------
# Claude generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """Você é o redator sênior de conteúdo da EPORTH (Energia Portátil LTDA), especialista em SEO e no tom de voz da marca.

CONTEXTO DA MARCA:
{brand_context}

REGRAS DE CONTEÚDO:
- Tom: técnico mas humano, RS com ambição nacional, inspirador sem ser vago
- Posicionar a EPORTH como especialista — não apenas revendedora
- Mencionar parceria EcoFlow quando o produto for EcoFlow
- CTA explícito no final: link para energiaportatil.com.br
- SEO: título com palavra-chave principal, subtítulos H2/H3 naturais, parágrafos curtos
- Tamanho: 800–1200 palavras
- Nunca inventar especificações técnicas — usar apenas o que foi fornecido
- Verde Frequência (#BBFF3C) é a cor de destaque da marca — mencionar no contexto certo

FORMATO DE RESPOSTA — retorne SOMENTE JSON válido, sem markdown:
{{
  "title": "Título SEO otimizado (60-70 chars)",
  "meta_description": "Meta description de 150-160 caracteres",
  "tags": "4 a 5 tags curtas separadas por vírgula (máx 2 palavras cada)",
  "image_keywords": ["termo em inglês para busca no Pexels", "termo 2", "termo 3"],
  "body_html": "<h2>...</h2><p>...</p> (HTML completo do artigo, sem <html>/<body>)",
  "summary_html": "<p>Resumo de 2-3 linhas para preview do blog</p>"
}}

Em image_keywords: coloque 3 termos em inglês fotográficos e específicos do contexto visual do artigo.
- Seja descritivo do cenário exato: "portable power station camping night", "solar panel rooftop installation", "family home blackout emergency"
- Inclua o produto ou contexto visual esperado na foto — não termos abstratos como "energy" ou "technology"
- Ao menos 1 keyword deve incluir o produto principal do artigo (ex: "ecoflow portable battery", "power station outdoor")
- Pense em como um fotógrafo descreveria a cena — quem aparece, onde, o que está acontecendo
- EPORTH é uma empresa BRASILEIRA: sempre que o tema envolver pessoas, torcidas, eventos, festas, clima ou cotidiano, adicione "brazil" ou "brazilian" na keyword — ex: "brazilian soccer fans stadium", "brazil family home power outage", "brazilian camping outdoor adventure", "brazil summer heat portable fan"
- Para temas neutros (produto técnico sem contexto cultural) o qualificador geográfico não é necessário"""


def generate_blog_with_claude(
    reference_type: str,
    reference_content: str,
    brand_context: str,
    extra_context: str = "",
) -> dict:
    type_prompts = {
        "url": f"Reescreva e adapte o seguinte conteúdo de referência para a EPORTH, com identidade própria:\n\n{reference_content}",
        "topic": f"Crie um artigo de blog completo sobre o seguinte tema:\n\n{reference_content}",
        "produto": f"Crie um artigo educativo e comercial sobre o produto, usando as especificações abaixo:\n\n{reference_content}",
        "evento": f"Crie um artigo de blog alinhado ao seguinte evento/data sazonal da EPORTH:\n\n{reference_content}",
    }

    user_prompt = type_prompts[reference_type]
    if extra_context:
        user_prompt += f"\n\nContexto adicional: {extra_context}"
    user_prompt += "\n\nRetorne APENAS o JSON válido."

    print("Gerando conteúdo com Gemini 2.5 Flash...")
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_TEMPLATE.format(brand_context=brand_context),
            response_mime_type="application/json",
        ),
        contents=user_prompt,
    )
    # Strip control characters that break JSON parsing (e.g. raw tabs in wiki content)
    import re as _re
    clean_text = _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
    article = json.loads(clean_text)

    # Fetch and insert Pexels images
    keywords = article.get("image_keywords", [])
    if keywords and os.environ.get("PEXELS_API_KEY"):
        print(f"Buscando imagens no Pexels: {keywords}")
        images = fetch_pexels_images(keywords, count=3)
        if images:
            article["body_html"] = insert_images_into_html(article["body_html"], images)
            article["_images"] = images  # kept for preview base64 swap
            print(f"{len(images)} imagem(ns) inserida(s).")

    return article


# ---------------------------------------------------------------------------
# Shopify publishing
# ---------------------------------------------------------------------------

def post_to_shopify(article_data: dict, published: bool = False) -> dict:
    store_url = os.environ["SHOPIFY_STORE_URL"]   # ex: eporth.myshopify.com
    access_token = os.environ["SHOPIFY_ACCESS_TOKEN"]
    blog_id = os.environ["SHOPIFY_BLOG_ID"]

    url = f"https://{store_url}/admin/api/2025-01/blogs/{blog_id}/articles.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
    }
    payload = {
        "article": {
            "title": article_data["title"],
            "author": "EPORTH",
            "tags": article_data.get("tags", ""),
            "body_html": article_data["body_html"],
            "excerpt": article_data.get("summary_html", ""),
            "published": published,
            "metafields": [
                {
                    "key": "description_tag",
                    "value": article_data.get("meta_description", ""),
                    "type": "single_line_text_field",
                    "namespace": "global",
                }
            ],
        }
    }

    # Featured/cover image — upload first Pexels image as base64 attachment
    images = article_data.get("_images", [])
    if images and images[0].get("_bytes"):
        first = images[0]
        payload["article"]["image"] = {
            "attachment": base64.b64encode(first["_bytes"]).decode("utf-8"),
            "filename": "cover.jpg",
            "alt": first.get("alt", ""),
        }

    resp = requests.post(url, headers=headers, json=payload)
    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text[:500]
        raise Exception(f"Shopify {resp.status_code}: {detail}")
    return resp.json()["article"]


def get_shopify_blogs() -> list:
    """Lista os blogs disponíveis na loja — útil para descobrir o SHOPIFY_BLOG_ID."""
    store_url = os.environ["SHOPIFY_STORE_URL"]
    access_token = os.environ["SHOPIFY_ACCESS_TOKEN"]
    url = f"https://{store_url}/admin/api/2024-01/blogs.json"
    headers = {"X-Shopify-Access-Token": access_token}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["blogs"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def check_env(skip_shopify: bool = False) -> None:
    required = ["GOOGLE_API_KEY"]
    if not skip_shopify:
        required += ["SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN", "SHOPIFY_BLOG_ID"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"Erro: variáveis faltando no .env: {', '.join(missing)}")
        print("Copie .env.example para .env e preencha os valores.")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EPORTH Blog Generator — gera e publica posts no blog da Shopify",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python blog_generator.py --url https://site.com/artigo
  python blog_generator.py --topic "energia solar para camping"
  python blog_generator.py --produto delta-pro
  python blog_generator.py --evento "Green November 2026"
  python blog_generator.py --topic "backup residencial" --publish
  python blog_generator.py --list-blogs
        """,
    )

    ref_group = parser.add_mutually_exclusive_group()
    ref_group.add_argument("--url", help="URL de referência para reescrever")
    ref_group.add_argument("--topic", help="Tema para gerar o blog do zero")
    ref_group.add_argument(
        "--produto",
        choices=list(PRODUCT_WIKI_MAP.keys()),
        help="Produto da WIKI para gerar blog educativo",
    )
    ref_group.add_argument("--evento", help="Evento ou data sazonal (ex: 'Green November')")
    ref_group.add_argument(
        "--list-blogs",
        action="store_true",
        help="Lista os blogs disponíveis na Shopify (para obter SHOPIFY_BLOG_ID)",
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publicar imediatamente (padrão: salvar como rascunho)",
    )
    parser.add_argument(
        "--no-shopify",
        action="store_true",
        help="Apenas gerar o conteúdo, sem publicar no Shopify",
    )
    parser.add_argument("--output", help="Caminho para salvar o JSON gerado (ex: post.json)")

    args = parser.parse_args()

    # List blogs mode
    if args.list_blogs:
        missing = [v for v in ["SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN"] if not os.environ.get(v)]
        if missing:
            print(f"Erro: variáveis faltando no .env: {', '.join(missing)}")
            sys.exit(1)
        blogs = get_shopify_blogs()
        print("\nBlogs disponíveis na Shopify:")
        for b in blogs:
            print(f"  ID: {b['id']}  |  Título: {b['title']}  |  Handle: {b['handle']}")
        return

    if not any([args.url, args.topic, args.produto, args.evento]):
        parser.print_help()
        sys.exit(1)

    check_env(skip_shopify=args.no_shopify)

    # Load brand context
    print("Carregando contexto da marca...")
    brand_context = load_brand_context()

    # Determine reference type and content
    if args.url:
        print(f"Buscando conteúdo da URL: {args.url}")
        reference_content = fetch_url_content(args.url)
        reference_type = "url"
    elif args.topic:
        reference_content = args.topic
        reference_type = "topic"
    elif args.produto:
        print(f"Carregando ficha técnica: {args.produto}")
        reference_content = load_product_wiki(args.produto)
        reference_type = "produto"
    else:
        reference_content = args.evento
        reference_type = "evento"

    # Generate content via Claude
    article_data = generate_blog_with_claude(reference_type, reference_content, brand_context)

    print(f"\nTítulo:  {article_data['title']}")
    print(f"Meta:    {article_data.get('meta_description', '')[:80]}...")
    print(f"Tags:    {article_data.get('tags', '')}")

    # Save JSON output if requested
    if args.output:
        Path(args.output).write_text(
            json.dumps(article_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Salvo em: {args.output}")

    # Publish to Shopify
    if not args.no_shopify:
        print("\nPublicando no Shopify...")
        result = post_to_shopify(article_data, published=args.publish)
        status = "publicado" if args.publish else "rascunho"
        store_url = os.environ["SHOPIFY_STORE_URL"]
        print(f"Post criado como {status}!")
        print(f"ID: {result['id']}")
        print(f"URL: https://{store_url}/blogs/news/{result['handle']}")
    elif not args.output:
        # Print generated content to stdout if nowhere else to go
        print("\n--- CONTEÚDO GERADO ---")
        print(json.dumps(article_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
