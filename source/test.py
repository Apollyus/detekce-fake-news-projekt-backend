from filtrace_clanku_module import filter_relevant_articles, simple_similarity

# Test data
test_response = {
    "items": [{'title': 'Zemřela zpěvačka a herečka Anna Julie Slováčková | ČeskéNoviny.cz', 'link': 'https://www.ceskenoviny.cz/zpravy/2657604', 'snippet': '3 days ago ... Praha - Zemřela zpěvačka a herečka Anna Julie Slováčková. Serveru Blesk.cz to potvrdil její otec, hudebník Felix Slováček.'}, {'title': 'Zemřela zpěvačka Anna Julie Slováčková — ČT24 — Česká televize', 'link': 'https://ct24.ceskatelevize.cz/clanek/kultura/zemrela-zpevacka-anna-julie-slovackova-359808', 'snippet': '3 days ago ... Po několikaletém boji s rakovinou zemřela zpěvačka Anna Julie Slováčková. Webu Blesk.cz to potvrdil její otec Felix Slováček.'}, {'title': 'Zpěvačka Anna K. slaví 60. narozeniny - iDNES.cz', 'link': 'https://www.idnes.cz/zpravy/revue/spolecnost/zpevacka-anna-k-sedesatiny-luciana-krecarova.A250103_093514_lidicky_zar', 'snippet': 'Jan 4, 2025 ... ... Anna K, Tomáš Vartecký, Rakovina, Vrchlabí, Divadlo Semafor. Nejčtenější. Zemřela Anna Julie Slováčková, vedla dlouhý boj s rakovinou · Tohle že\xa0...'}, {'title': 'Zemřela Anna Slováčková. Zákeřná nemoc byla nad její síly | Život v ...', 'link': 'https://zivotvcesku.cz/zemrela-anna-slovackova-zakerna-nemoc-byla-nad-jeji-sily/', 'snippet': '3 days ago ... 2025. V neděli 6. dubna přišla hudební scéna o výrazný hlas – ve věku 29 let zemřela zpěvačka a herečka Anna Julie Slováčková. Smutnou zprávu\xa0...'}, {'title': 'Po boji s rakovinou zemřela zpěvačka Anna Slováčková | Reflex.cz', 'link': 'https://www.reflex.cz/clanek/zpravy/129687/po-boji-s-rakovinou-zemrela-zpevacka-anna-slovackova.html', 'snippet': 'Po těžké a dlouhé léčbě rakoviny zemřela zpěvačka Anna Julie Slováčková. Informaci Blesku potvrdil její otec, hudebník Felix Slováček.'}, {'title': 'Ceny Anděl 2025: Zpěvačka Anna K. se opět usmívá, minulost ...', 'link': 'https://www.extra.cz/anna-k-je-jako-vymenena-opet-rozdava-usmevy-tomas-vartecky-je-minulosti-356e4', 'snippet': '4 days ago ... Na udílení Cen Anděl 2025 nejvíce zářila Anna K. Od té doby, co se zpěvačka objevila ve dveřích, tak se usmívala od ucha k uchu.'}, {'title': 'Zemřela zpěvačka a herečka Anna Slováčková, bylo jí 29 let', 'link': 'https://denikn.cz/minuta/1700134/', 'snippet': '3 days ago ... Dceři zpěvačky a herečky Dády Patrasové a saxofonisty Slováčka diagnostikovali lékaři rakovinu prsu ve 24 letech. Poté co se zotavila, jí lékaři\xa0...'}, {'title': 'Zemřela zpěvačka a herečka Anna Slováčková. Bylo jí 29 let ...', 'link': 'https://www.irozhlas.cz/kultura/hudba/zemrela-zpevacka-a-herecka-anna-slovackova-bylo-ji-29-let_2504062229_jar', 'snippet': 'V roce 2023 se jí ale vrátila v podobě nádoru na plicích. Aktualizováno Praha 22:29 6. 4. 2025 (Aktualizováno: 22:36 6. 4. 2025) Sdílet na Facebooku Sdílet\xa0...'}, {'title': 'Zemřela zpěvačka Anna Julie Slováčková. Žila naplno a tvořila do ...', 'link': 'https://radioblanik.cz/aktualne/zajimavosti/zemrela-zpevacka-anna-julie-slovackova-zila-naplno-a-tvorila-do-posledni-chvile', 'snippet': 'Žila naplno a tvořila do poslední chvíle. Zajímavosti. 7. 4. 2025. Zemřela zpěvačka Anna Julie Slováčková. Žila naplno a tvořila do poslední chvíle.'}, {'title': 'Anna Slováčková - Wikipedia', 'link': 'https://en.wikipedia.org/wiki/Anna_Slov%C3%A1%C4%8Dkov%C3%A1', 'snippet': '6 April 2025(2025-04-06) (aged 29). Prague, Czech Republic. Occupation(s) ... "Zemřela zpěvačka Anna Slováčková. Ve 29 letech podlehla rakovině". Seznam\xa0...'}]
}

# Test keywords
keywords = ["Anna K zpěvačka zemřela"]

# Debug: Print similarity scores
for article in test_response["items"]:
    text = f"{article['title']} {article['snippet']}"
    for kw in keywords:
        similarity = simple_similarity(text, kw)
        print(f"\nSimilarity check:")
        print(f"Text: {text}")
        print(f"Keyword: {kw}")
        print(f"Similarity score: {similarity}")

# Call the function with lower threshold
results = filter_relevant_articles(
    response_json=test_response,
    keywords=keywords,
    threshold=0.7  # Lowered threshold for testing
)

'''print("\nResults found:", len(results))

# Print results
for article in results:
    print("\nNalezený relevantní článek:")
    print(f"Titulek: {article['title']}")
    print(f"Odkaz: {article['link']}")
    print(f"Úryvek: {article['snippet']}")
    print("-" * 50)'''

print(results)