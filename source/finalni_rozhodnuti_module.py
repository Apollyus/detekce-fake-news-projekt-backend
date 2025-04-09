from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

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
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """You are a fact-checking AI assistant. Analyze the given claim against the provided evidence.
                You must return your response in exactly this format (including the exact labels):
                VERDICT: [must be exactly TRUE, FALSE, or UNCERTAIN]
                CONFIDENCE: [number between 0 and 1]
                SUPPORTING EVIDENCE: [list clear factual points that support the claim]
                CONTRADICTING EVIDENCE: [list clear factual points that contradict the claim]
                EXPLANATION: [provide brief, clear analysis]"""
            },
            {
                "role": "user",
                "content": f"Claim to evaluate: {prompt}\n\nFound evidence:\n{claims_text}"
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