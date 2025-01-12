# Hit the chat gpt api to ask for harness design

from openai import OpenAI
import os

import subprocess
# set api key to environment variable OPENAI_KEY

import json
import sys

PROMPT_CONTEXT = '''
    You are a helpful assistant. 
    only output a yml file with pinout, notes, pin numbers. Please do not output any information other than the yml. It should follow this format:

connectors:
  J1: 
    pinlabels: ["TX+", "TX-", "RX+", "RX-","BI_DD+", "BI_DD-", "BI_DC+", "BI_DC-"]
    type: "D38999"
    subtype: receptacle
  J2:
    pinlabels: ["TX+", "TX-", "RX+", "RX-","BI_DD+", "BI_DD-", "BI_DC+", "BI_DC-"]
    type: "D38999"
    subtype: receptacle


cables:
  W1:
    wirecount: 8
    length: 2
    gauge: 24 AWG
    show_equiv: true
    color_code: T568A
    shield: true # cable shielding included
    notes: Connect the cable shield to the backshell for EMI grounding

connections:
  - # Connect twisted pairs for Ethernet
    - J1: [1-8]
    - W1: [1-8]
    - J2: [1-8]
    
    '''

# Query the OpenAI API
def queryGPT(query, model="gpt-4"):
    """
    Takes a query and returns the response from the OpenAI API.
    
    Parameters:
        query (str): The input query or prompt.
        model (str): The model to use for the query (default is "gpt-4").
    
    Returns:
        str: The response from the OpenAI API.
    """
    API_KEY= os.getenv("OPENAI_KEY")
    client = OpenAI(api_key=API_KEY)
 
    query = f"{PROMPT_CONTEXT}\n\n\n{query}"
    try:
        # Make an API call
        response = client.chat.completions.create(model=model,
        messages=[
            {"role": "system", "content": PROMPT_CONTEXT},
            {"role": "user", "content": query}
        ])
        # Extract the response content
        resp =  response.choices[0].message.content.strip()
        return clean_gpt_response(resp)
    except Exception as e:
        return f"An error occurred: {e}"
    

def clean_gpt_response(response):
    """
    Cleans the GPT response by removing any leading or trailing whitespace.
    
    Parameters:
        response (str): The GPT response to clean.
    
    Returns:
        str: The cleaned GPT response.
    """
    # remove everything before the word connectors. and remove any trailing ``
    response = response[response.find("connectors"):]
    cleaned_output = response.replace("`", "")

    return cleaned_output