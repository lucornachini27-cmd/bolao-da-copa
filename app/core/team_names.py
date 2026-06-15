"""De-para de nomes de seleções: inglês (ESPN) -> português do Brasil.

Se um nome não estiver no mapa, devolvemos o original (não quebra nada).
"""

TEAM_PT = {
    "Algeria": "Argélia",
    "Argentina": "Argentina",
    "Australia": "Austrália",
    "Austria": "Áustria",
    "Belgium": "Bélgica",
    "Bosnia-Herz": "Bósnia e Herzegovina",
    "Brazil": "Brasil",
    "Canada": "Canadá",
    "Cape Verde": "Cabo Verde",
    "Colombia": "Colômbia",
    "Congo DR": "RD Congo",
    "Croatia": "Croácia",
    "Curaçao": "Curaçao",
    "Czechia": "Tchéquia",
    "Ecuador": "Equador",
    "Egypt": "Egito",
    "England": "Inglaterra",
    "France": "França",
    "Germany": "Alemanha",
    "Ghana": "Gana",
    "Haiti": "Haiti",
    "Iran": "Irã",
    "Iraq": "Iraque",
    "Ivory Coast": "Costa do Marfim",
    "Japan": "Japão",
    "Jordan": "Jordânia",
    "Mexico": "México",
    "Morocco": "Marrocos",
    "Netherlands": "Holanda",
    "New Zealand": "Nova Zelândia",
    "Norway": "Noruega",
    "Panama": "Panamá",
    "Paraguay": "Paraguai",
    "Portugal": "Portugal",
    "Qatar": "Catar",
    "Saudi Arabia": "Arábia Saudita",
    "Scotland": "Escócia",
    "Senegal": "Senegal",
    "South Africa": "África do Sul",
    "South Korea": "Coreia do Sul",
    "Korea Republic": "Coreia do Sul",  # alias (ESPN às vezes usa)
    "Spain": "Espanha",
    "Sweden": "Suécia",
    "Switzerland": "Suíça",
    "Türkiye": "Turquia",
    "Turkey": "Turquia",  # alias
    "Tunisia": "Tunísia",
    "Uruguay": "Uruguai",
    "USA": "EUA",
    "Uzbekistan": "Uzbequistão",
}


def to_pt(name: str) -> str:
    """Traduz para PT-BR; fora do mapa, devolve o nome original."""
    return TEAM_PT.get(name, name)
