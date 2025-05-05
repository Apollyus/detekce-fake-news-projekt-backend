from openai import OpenAI
from source.modules.config import config  # Import instance konfigurace, ne modul

api_key = config.OPENAI_API_KEY  # Použití API klíče z konfigurace

# Inicializace klienta s API klíčem jako pojmenovaným parametrem
client = OpenAI(api_key=api_key)

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
        model="gpt-4o-mini",
        messages=[
    {
        "role": "system",
        "content": """You are a fact-checking AI assistant. You MUST respond in Czech language only.
        Analyze the given claim against the provided evidence.
        If there is insufficient or no concrete evidence provided, you should lean towards marking the claim as FALSE rather than UNCERTAIN.
        
        You must return your response in exactly this format (including the exact labels):
        VERDICT: [must be exactly TRUE, FALSE, or UNCERTAIN]
        CONFIDENCE: [number between 0 and 1]
        SUPPORTING EVIDENCE: [v češtině vypiš faktické body podporující tvrzení]
        CONTRADICTING EVIDENCE: [v češtině vypiš faktické body vyvracející tvrzení]
        EXPLANATION: [v češtině poskytni stručnou a jasnou analýzu]
        
        Guidelines for verdicts:
        - TRUE: Použij pouze když existují silné, přímé důkazy podporující tvrzení
        - FALSE: Použij když důkazy odporují tvrzení NEBO když není dostatek konkrétních důkazů
        - UNCERTAIN: Použij pouze když existují protichůdné důkazy stejné váhy
        
        When evaluating evidence:
        - Nedostatek důkazů by měl vést k označení tvrzení jako FALSE
        - Mimořádná tvrzení vyžadují mimořádné důkazy
        - Zvažuj důvěryhodnost a konkrétnost poskytnutých důkazů"""
    },
    {
        "role": "user",
        "content": f"Claim to verify: {prompt}\n\nAvailable evidence:\n{claims_text}"
    }
],
        temperature=0.3,  # Nižší teplota pro konzistentnější formátování
        max_tokens=1000
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