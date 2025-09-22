from openai import OpenAI
from source.modules.config import config  # Import instance konfigurace, ne modul

api_key = config.OPENROUTER_API_KEY  # Použití API klíče z konfigurace

# Inicializace klienta s OpenRouter API klíčem
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def evaluate_claim(prompt, found_claims):
    """
    Vyhodnocení pravdivosti tvrzení na základě seznamu nalezených tvrzení.
    
    Parametry:
        prompt (str): Tvrzení, které má být vyhodnoceno
        found_claims (list): Seznam relevantních tvrzení nalezených na internetu
    
    Vrací:
        dict: Obsahuje strukturovaný výsledek vyhodnocení
    """
    claims_text = "\n".join([f"- {claim}" for claim in found_claims])
    
    response = client.chat.completions.create(
        model="google/gemini-2.5-flash-lite",
        messages=[
    {
        "role": "system",
        "content": """Jsi AI asistent specializovaný na fact-checking. Odpovídej pouze v češtině.

        INSTRUKCE PRO ANALÝZU:
        1. Analyzuj tvrzení proti poskytnutým důkazům systematicky
        2. Hodnoť důvěryhodnost zdrojů a kvalitu informací
        3. Zvažuj časové souvislosti a kontext tvrzení
        4. Rozlišuj mezi faktickými chybami a neúplnými informacemi

        KRITÉRIA PRO ROZHODOVÁNÍ:
        • TRUE: Tvrzení je potvrzeno alespoň jedním spolehlivým zdrojem NEBO je logicky konzistentní s poskytnutými důkazy
        • FALSE: Tvrzení je jasně vyvráceno důkazy NEBO obsahuje prokazatelné faktické chyby
        • UNCERTAIN: Protichůdné informace, nedostatek kvalitních zdrojů NEBO nemožnost jednoznačného ověření

        PRAVIDLA HODNOCENÍ:
        - Označuj jako TRUE i částečně potvrzená tvrzení, pokud nejsou fakticky chybná
        - Označuj jako FALSE pouze při jasných faktických chybách nebo vyvracení
        - Buď tolerantní k drobným nepřesnostem v detailech
        - Zvažuj kontext a úhel pohledu článku
        - U nejasných případů preferuj UNCERTAIN místo FALSE

        FORMÁT ODPOVĚDI:
        VERDICT: [TRUE, FALSE, UNCERTAIN]
        CONFIDENCE: [0.0 to 1.0]
        EXPLANATION: [Stručné zdůvodnění - VELMI DŮLEŽITÉ, NEZAPOMEŇ!]"""
    },
    {
        "role": "user",
        "content": f"Claim: {prompt}\nEvidence:\n{claims_text}"
    }
],
        temperature=0.2,
        max_tokens=800
    )

    # Parsování odpovědi do strukturovaného formátu
    raw_analysis = response.choices[0].message.content
    lines = raw_analysis.strip().split('\n')
    structured_result = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Převod hodnoty confidence na float
            if key == 'CONFIDENCE':
                try:
                    value = float(value)
                except ValueError:
                    value = 0.0
                    
            structured_result[key] = value

    return {
        'verdict': structured_result.get('VERDICT', 'UNCERTAIN'),
        'confidence': structured_result.get('CONFIDENCE', 0.0),
        'supporting_evidence': structured_result.get('SUPPORTING EVIDENCE', ''),
        'contradicting_evidence': structured_result.get('CONTRADICTING EVIDENCE', ''),
        'explanation': structured_result.get('EXPLANATION', ''),
        'evaluated_claim': prompt,
        'evidence_used': found_claims
    }