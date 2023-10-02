# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 17:02:01 2023

@author: Shane Tomasello

@note: This script takes a PDF and scraps it textual for data then feeds the data as an entry in an excel document.
"""

from openai.embeddings_utils import get_embedding
import tiktoken
import time
import openai
import pandas as pd
import os
import PyPDF2
import re


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

t = time.localtime()
start_time = time.time()

openai.api_key = '<OpenAI_Key>' #this is for Catherine's key

COMPLETIONS_MODEL = "text-davinci-003"

pdf_dir = '<Directory_of_pdf>'

embeddings = []

#need to iterate through doc types, use the label below to differentiate which one is which
document_type = '<Doc Type Here>'

for filename in os.listdir(pdf_dir):
    if filename.endswith('.pdf'):
        pdf_path = os.path.join(pdf_dir, filename)
        with open(pdf_path, 'rb') as pdf_file:
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            #so we can get 3 layers to each embedding for best performance
            prev_paragraph = ''
            prev_prev_paragraph = ''
            
            for page_num in range(len(pdf_reader.pages)):
                
                text = pdf_reader.pages[page_num].extract_text()
                text = re.sub(r'^\s+|\s+?$', '', text) #remove leading/trailing spaces
                text = re.sub("\n\n", "Z2liY2hhcmxpZXByb21vdGlv", text) #replace the \n\n
                text = re.sub("\n \n", "Z2liY2hhcmxpZXByb21vdGlv", text) #replace the \n \n
                text = re.sub("\n", " ", text) #replace the \n that are left over
                text = re.sub(' +', ' ', text) #remove the extra spaces
                text = text.replace(".", "").replace(".", ".") #remove the extra periods
                text = text.replace(" s ", "") #remove the extra s that are scattered about
                text = text.replace(" d ", "") #remove the extra d that are scattered about
                
                paragraphs = text.split("Z2liY2hhcmxpZXByb21vdGlv")
                
                paragraph_number = 1
                
                for paragraph in paragraphs:
                    
                    if paragraph != "":
                        
                        published_paragraph = paragraph
                        
                        #add chunks of previous context if the paragraph is too small
                        if len(published_paragraph) < 100:
                            published_paragraph = prev_paragraph + " " + published_paragraph
                            
                            if len(published_paragraph) < 200:
                                published_paragraph = prev_prev_paragraph + " " + published_paragraph
                                
                        tokens = num_tokens_from_string(published_paragraph, "cl100k_base")
                       
                        if tokens < 4000:
                           
                            time.sleep(3)
                            
                            embedding = {
                                 'doctype': document_type,
                                 'name': filename,
                                 'page': page_num + 1, # no start on page 0
                                 'paragraph': paragraph_number,
                                 'tokens': num_tokens_from_string(published_paragraph, "cl100k_base"),
                                 'text': published_paragraph,
                                 'embedding': get_embedding(published_paragraph, engine='text-embedding-ada-002')                             
                            }
                            
                            embeddings.append(embedding)                     
                        
                        #so we can get 3 layers to each embedding for best performance if we have a small paragraph
                        prev_prev_paragraph = prev_paragraph
                        prev_paragraph = published_paragraph
                        
                        paragraph_number += 1

df = pd.DataFrame(embeddings)

for index, row in df.iterrows():
    df.at[index, "embedding_id"] = index
    
df = df.rename(columns={'name': 'title'})

df.to_excel("<Location_to_excel>")

