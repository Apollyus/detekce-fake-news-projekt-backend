from openai import OpenAI
from source.modules.config import config  # Import the config instance, not the module

api_key = config.OPENAI_API_KEY  # Use the API key from the config

# Initialize with api_key as a named parameter
client = OpenAI(api_key=api_key)

def evaluate_claim(prompt, found_claims):
    """
    Evaluate the truthfulness of a prompt against a list of found claims.
    
    Args:
        prompt (str): The claim to be evaluated
        found_claims (list): List of relevant claims found on the internet
    
    Returns:
        dict: Contains structured evaluation result
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
        temperature=0.3,  # Lower temperature for more consistent formatting
        max_tokens=1000
    )

    # Parse the response into structured format
    raw_analysis = response.choices[0].message.content
    lines = raw_analysis.strip().split('\n')
    structured_result = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Convert confidence to float
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