"""
Agente de busca de vagas — saída em JSON para GitHub Pages.
Roda via GitHub Actions (gratuito) ou localmente.

Instalação:
    pip install requests beautifulsoup4
"""

import requests, time, json, datetime, sys
from pathlib import Path
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup

# ── Configuração ───────────────────────────────────────────────────────────────

JSON_PATH = Path(__file__).parent / "vagas.json"

TERMOS_BUSCA = {
    "Ciência de Dados": [
        "Cientista de Dados", "Data Scientist",
        "Analista de Dados Sênior", "Senior Data Analyst",
    ],
    "Machine Learning": [
        "Machine Learning Engineer", "Engenheiro de Machine Learning",
        "Deep Learning Engineer", "ML Engineer", "Modelagem Estocástica",
    ],
    "Oceanografia": [
        "Analista Oceanográfico", "Oceanógrafo", "Engenheiro Oceânico",
        "Ocean Engineer", "Physical Oceanography", "Oceanographer",
    ],
    "Sensoriamento Remoto": [
        "Remote Sensing Specialist", "Especialista em Sensoriamento Remoto",
        "Processamento de Imagens SAR", "SAR Processing",
        "Analista de Radar", "Geoprocessamento", "GIS Specialist",
    ],
    "Docência": [
        "Professor Universitário", "Docente de Engenharia",
        "Professor Adjunto Matemática", "Professor Engenharia",
    ],
}

PERFIL_KEYWORDS = [
    "python","matlab","machine learning","deep learning","oceanografia",
    "sensoriamento remoto","remote sensing","sar","satellite","satélite",
    "geoprocessamento","gis","roms","hycom","copernicus","noaa","inpe",
    "tensorflow","pytorch","xarray","netcdf","pandas","sql","spark",
    "engenharia oceânica","matemática aplicada","professor","pesquisador",
    "processamento de imagens","radar","inglês avançado","pos-doc",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
}

DELAY            = 2.5
MAX_POR_TERMO    = 10

# ── Modelo ─────────────────────────────────────────────────────────────────────

class Vaga:
    def __init__(self):
        self.id          = ""
        self.titulo      = ""
        self.empresa     = ""
        self.area        = ""
        self.fonte       = ""
        self.local       = ""
        self.data_achada = datetime.date.today().isoformat()
        self.prazo       = ""
        self.nivel       = ""
        self.modalidade  = ""
        self.salario     = ""
        self.link        = ""
        self.keywords    = ""
        self.prioridade  = "media"
        self.score       = 0
        # campos que o usuário edita no browser
        self.status      = "pendente"   # pendente | verificado | enviado | rejeitado
        self.data_envio  = ""
        self.observacoes = ""

    def calcular_score(self):
        txt = f"{self.titulo} {self.empresa} {self.keywords}".lower()
        self.score = sum(1 for kw in PERFIL_KEYWORDS if kw in txt)
        self.prioridade = "alta" if self.score >= 5 else "media" if self.score >= 2 else "baixa"

    def inferir_nivel(self):
        t = self.titulo.lower()
        if any(x in t for x in ["sênior","senior","sr.","sr "]):     self.nivel = "Sênior"
        elif any(x in t for x in ["pleno","mid"]):                   self.nivel = "Pleno"
        elif any(x in t for x in ["júnior","junior","jr."]):         self.nivel = "Júnior"
        elif any(x in t for x in ["professor","docente","adjunto"]): self.nivel = "Professor"
        elif any(x in t for x in ["pesquisador","researcher","scientist"]): self.nivel = "Pesquisador"
        elif any(x in t for x in ["pós-doc","pos-doc","postdoc"]):   self.nivel = "Pós-doc"
        else:                                                          self.nivel = "Sênior"

    def inferir_modalidade(self):
        t = f"{self.titulo} {self.local}".lower()
        if any(x in t for x in ["remoto","remote","home office"]):   self.modalidade = "Remoto"
        elif any(x in t for x in ["híbrido","hybrid"]):              self.modalidade = "Híbrido"
        else:                                                          self.modalidade = "Presencial"

    def chave(self):
        return f"{self.titulo.lower().strip()}|{self.empresa.lower().strip()}"

    def to_dict(self):
        return self.__dict__

# ── Scrapers ───────────────────────────────────────────────────────────────────

def get_html(url):
    for t in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if t < 2: time.sleep(DELAY * 2)
            else: print(f"    ⚠  {url[:55]}... {e}")
    return None

def scrape_linkedin(termo, area):
    vagas, enc = [], quote_plus(termo)
    url = f"https://www.linkedin.com/jobs/search/?keywords={enc}&location=Brasil&f_TPR=r604800"
    html = get_html(url)
    if not html: return vagas
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("div.base-card")[:MAX_POR_TERMO]:
        try:
            v = Vaga()
            v.titulo   = (card.select_one("h3.base-search-card__title") or object()).get_text(strip=True) or termo
            v.empresa  = (card.select_one("h4.base-search-card__subtitle") or object()).get_text(strip=True) or "N/D"
            v.local    = (card.select_one("span.job-search-card__location") or object()).get_text(strip=True) or "Brasil"
            a          = card.select_one("a.base-card__full-link")
            v.link     = a["href"].split("?")[0] if a else url
            v.area, v.fonte, v.keywords = area, "LinkedIn", termo
            v.inferir_nivel(); v.inferir_modalidade(); v.calcular_score()
            vagas.append(v)
        except: continue
    time.sleep(DELAY)
    return vagas

def scrape_indeed(termo, area):
    vagas, enc = [], quote_plus(termo)
    url = f"https://br.indeed.com/jobs?q={enc}&l=Brasil&sort=date&fromage=14"
    html = get_html(url)
    if not html: return vagas
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("div.job_seen_beacon")[:MAX_POR_TERMO]:
        try:
            v = Vaga()
            t2  = card.select_one("h2.jobTitle span[title]")
            emp = card.select_one("span.companyName")
            loc = card.select_one("div.companyLocation")
            jk  = card.select_one("a[data-jk]")
            sal = card.select_one("div.salary-snippet-container")
            v.titulo   = t2["title"] if t2 else termo
            v.empresa  = emp.get_text(strip=True) if emp else "N/D"
            v.local    = loc.get_text(strip=True) if loc else "Brasil"
            v.link     = f"https://br.indeed.com/viewjob?jk={jk['data-jk']}" if jk else url
            v.salario  = sal.get_text(strip=True) if sal else ""
            v.area, v.fonte, v.keywords = area, "Indeed", termo
            v.inferir_nivel(); v.inferir_modalidade(); v.calcular_score()
            vagas.append(v)
        except: continue
    time.sleep(DELAY)
    return vagas

def scrape_noaa(termo, area):
    vagas, enc = [], quote_plus(termo)
    try:
        r = requests.get(
            f"https://data.usajobs.gov/api/search?Keyword={enc}&ResultsPerPage=10&SortField=OpenDate&SortDirection=Desc",
            headers={"Host":"data.usajobs.gov","User-Agent":"agente-vagas/1.0","Authorization-Key":""},
            timeout=15)
        items = r.json().get("SearchResult",{}).get("SearchResultItems",[])
    except Exception as e:
        print(f"    ⚠  USAJOBS: {e}"); return vagas
    for item in items[:MAX_POR_TERMO]:
        try:
            pos = item.get("MatchedObjectDescriptor",{})
            v = Vaga()
            v.titulo   = pos.get("PositionTitle", termo)
            v.empresa  = pos.get("OrganizationName","NOAA/Federal")
            v.local    = pos.get("PositionLocationDisplay","USA")
            v.link     = pos.get("PositionURI","https://www.usajobs.gov/")
            v.prazo    = pos.get("ApplicationCloseDate","")[:10]
            rem        = pos.get("PositionRemuneration",[{}])
            v.salario  = f"USD {rem[0].get('MinimumRange','')}-{rem[0].get('MaximumRange','')}" if rem else ""
            v.area, v.fonte, v.keywords = area, "NOAA/USAJOBS", termo
            v.nivel, v.modalidade = "Pesquisador", "Presencial"
            v.inferir_nivel(); v.calcular_score()
            vagas.append(v)
        except: continue
    time.sleep(DELAY)
    return vagas

def scrape_esa(termo, area):
    vagas = []
    html = get_html("https://www.esa.int/About_Us/Careers/Current_vacancies_and_Young_Graduate_Trainee_posts")
    if not html: return vagas
    soup = BeautifulSoup(html, "html.parser")
    kws  = termo.lower().split()
    for a in soup.select("a[href*='/Careers/']"):
        txt = a.get_text(strip=True)
        if len(txt) < 10: continue
        if any(kw in txt.lower() for kw in kws):
            v = Vaga()
            v.titulo, v.empresa = txt, "ESA — European Space Agency"
            v.local, v.modalidade = "Europa / Remoto", "Híbrido"
            v.link = urljoin("https://www.esa.int", a.get("href",""))
            v.area, v.fonte, v.keywords = area, "ESA/Copernicus", termo
            v.inferir_nivel(); v.calcular_score()
            vagas.append(v)
            if len(vagas) >= MAX_POR_TERMO: break
    time.sleep(DELAY)
    return vagas

def scrape_inpe(area):
    vagas = []
    html = get_html("https://www.gov.br/inpe/pt-br/assuntos/noticias")
    if not html: return vagas
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("a[href]"):
        txt = a.get_text(strip=True)
        if len(txt) > 15 and any(k in txt.lower() for k in ["seleção","concurso","bolsa","vaga","edital"]):
            v = Vaga()
            v.titulo   = txt[:120]
            v.empresa  = "INPE — Instituto Nac. de Pesquisas Espaciais"
            v.local    = "Brasil — São José dos Campos (SP)"
            v.link     = urljoin("https://www.gov.br", a["href"])
            v.area, v.fonte = area, "INPE"
            v.keywords = "Sensoriamento Remoto, Satélites, Geoprocessamento"
            v.nivel, v.modalidade, v.prioridade = "Pesquisador", "Presencial", "alta"
            v.calcular_score()
            vagas.append(v)
            if len(vagas) >= 5: break
    time.sleep(DELAY)
    return vagas

def scrape_vagas_com(termo, area):
    vagas = []
    slug = termo.lower().replace(" ","-").replace("/","-")
    url  = f"https://www.vagas.com.br/vagas-de-{slug}"
    html = get_html(url)
    if not html: return vagas
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("li.vaga")[:MAX_POR_TERMO]:
        try:
            v = Vaga()
            t2  = card.select_one("a.link-detalhes-vaga")
            emp = card.select_one("span.emNome")
            loc = card.select_one("span.local")
            v.titulo  = t2.get_text(strip=True) if t2 else termo
            v.empresa = emp.get_text(strip=True) if emp else "N/D"
            v.local   = loc.get_text(strip=True) if loc else "Brasil"
            v.link    = urljoin("https://www.vagas.com.br", t2["href"]) if t2 else url
            v.area, v.fonte, v.keywords = area, "Vagas.com.br", termo
            v.inferir_nivel(); v.inferir_modalidade(); v.calcular_score()
            vagas.append(v)
        except: continue
    time.sleep(DELAY)
    return vagas

# ── Orquestrador ───────────────────────────────────────────────────────────────

def buscar_todas():
    todas, total, atual = [], sum(len(v) for v in TERMOS_BUSCA.values()), 0
    print(f"\n{'═'*60}\n  AGENTE DE VAGAS  |  {datetime.date.today()}\n{'═'*60}")
    for area, termos in TERMOS_BUSCA.items():
        print(f"\n▶  {area}")
        for termo in termos:
            atual += 1
            print(f"   [{atual}/{total}] {termo}")
            for fn, label in [
                (lambda t,a: scrape_linkedin(t,a), "LinkedIn"),
                (lambda t,a: scrape_indeed(t,a),   "Indeed"),
                (lambda t,a: scrape_vagas_com(t,a), "Vagas.com"),
            ]:
                sys.stdout.write(f"        {label}... "); sys.stdout.flush()
                v = fn(termo, area); print(len(v)); todas.extend(v)
            if area in ["Oceanografia","Sensoriamento Remoto","Machine Learning"]:
                sys.stdout.write("        NOAA... "); sys.stdout.flush()
                v = scrape_noaa(termo, area); print(len(v)); todas.extend(v)
        if area in ["Sensoriamento Remoto","Oceanografia","Machine Learning"]:
            v = scrape_esa(area, area)
            print(f"   ESA: {len(v)}"); todas.extend(v)
    v = scrape_inpe("Sensoriamento Remoto")
    print(f"\n▶  INPE: {len(v)}"); todas.extend(v)
    print(f"\n✔  Total coletado: {len(todas)}")
    return todas

# ── JSON ───────────────────────────────────────────────────────────────────────

def carregar_json():
    if JSON_PATH.exists():
        with open(JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"vagas": [], "ultima_atualizacao": ""}

def salvar_json(vagas_novas):
    dados = carregar_json()
    existentes = {v["titulo"].lower().strip() + "|" + v["empresa"].lower().strip()
                  for v in dados["vagas"]}

    adicionadas = 0
    for v in sorted(vagas_novas, key=lambda x: x.score, reverse=True):
        if v.chave() not in existentes:
            existentes.add(v.chave())
            d = v.to_dict()
            # gera id único
            d["id"] = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{adicionadas}"
            dados["vagas"].append(d)
            adicionadas += 1

    dados["ultima_atualizacao"] = datetime.datetime.now().isoformat(timespec="seconds")
    dados["total"] = len(dados["vagas"])

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"  ✔  {adicionadas} vagas novas adicionadas ao JSON.")
    print(f"  ✔  Total no arquivo: {dados['total']}")
    return adicionadas

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time as _t; t0 = _t.time()
    vagas = buscar_todas()
    salvar_json(vagas)
    print(f"\n  Concluído em {round(_t.time()-t0)}s\n")
