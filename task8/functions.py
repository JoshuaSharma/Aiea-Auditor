from openai import OpenAI
from dotenv import load_dotenv
import os
from pyswip import Prolog
load_dotenv()
from pyswip import Prolog
import re


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
prolog = Prolog()
#Made with chatgpt below
def extract_code(text):

    if "```" in text:
        fences = [m.start() for m in re.finditer("```", text)]
        
        if len(fences) >= 2:
            code_block = text[fences[0]+3:fences[-1]]
            first_line_end = code_block.find('\n')
            if first_line_end > 0:
                language_line = code_block[:first_line_end].strip()
                if not language_line.startswith(':-'):  
                    code_block = code_block[first_line_end+1:]
            return code_block.strip()
    

    lines = text.strip().split('\n')
    prolog_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith(':-') or line.endswith('.') or line.startswith('?-'):
            prolog_lines.append(line)
    
    if prolog_lines:
        return '\n'.join(prolog_lines)
    
    return text.replace('```prolog', '').replace('```', '').strip()