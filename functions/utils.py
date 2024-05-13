import os
import json
from dotenv import find_dotenv, load_dotenv
import openai
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from operator import itemgetter
import streamlit as st

openai.api_key = st.secrets["OPENAI_API_KEY"]

#load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']

# Instantiate GPT Model 
model = ChatOpenAI(model="gpt-4-turbo")

# Load Prompts 
PROMPT_FOLDER = os.path.join(os.getcwd(), "prompts")
assert os.path.exists(PROMPT_FOLDER)

# Customer Profiling
with open(os.path.join(PROMPT_FOLDER, "Customer Profiling", "system_prompt.txt"), "r") as f:
    customer_profiling_system_prompt = f.read()
with open(os.path.join(PROMPT_FOLDER, "Customer Profiling", "human_prompt.txt"), "r") as f:
    customer_profiling_human_prompt = f.read()
    
# Copywriting 
with open(os.path.join(PROMPT_FOLDER, "Copywriting", "system_prompt.txt"), "r") as f:
    copywriting_system_prompt = f.read()
with open(os.path.join(PROMPT_FOLDER, "Copywriting", "human_prompt.txt"), "r") as f:
    copywriting_human_prompt = f.read()

class CustomerProfiling(BaseModel):
    customer_status: str = Field(description="The status of the customer (eg: VIC)")
    customer_geographical_needs: str = Field(description="The needs of the customer based on his location")
    customer_preferences: str = Field(description="The customer's identified preferences based on his purchase history")
    
def get_product_description(product_name_category):
    product_name, product_category = product_name_category
    product_file_mapping = {
        "fragrance": {
            "Chance Eau de Parfum Spray": "chance_eau_de_parfum_spray.txt",
            "Chance Eau de Toilette Spray": "chance_eau_de_toilette_spray.txt",
            "Chance Hair Mist": "chance_hair_mist.txt",
            "Coco Mademoiselle Eau de Parfum Spray": "coco_mademoiselle_eau_de_parfum_spray.txt",
            "Coco Mademoiselle Eau de Toilette Spray": "coco_mademoiselle_eau_de_toilette_spray.txt",
            "Cristale Eau de Parfum Spray": "cristale_eau_de_parfum_spray.txt",
            "Gabrielle Chanel Essence Eau de Parfum Spray": "gabrielle_chanel_essence_eau_de_parfum_spray.txt",
            "N°5 Eau de Parfum Spray": "N°5_eau_de_parfum_spray.txt",
            "N°5 Extrait Bottle": "N°5_extrait_bottle.txt",
            "N°5 Eau Premiere Spray": "N°5_eau_premiere_spray.txt",
            "N°19 Eau de Parfum Spray": "N°19_eau_de_parfum_spray.txt"
        },
        "skincare": {
            "N°1 de Chanel Lip and Cheek Balm": "N°1_de_chanel_lip_and_cheek_balm.txt",
            "N°1 de Chanel Powder-to-Foam Cleanser": "N°1_de_chanel_powder-to-foam_cleanser.txt",
            "N°1 de Chanel Revitalizing Cream": "N°1_de_chanel_revitalizing_cream.txt",
            "N°1 de Chanel Revitalizing Foundation": "N°1_de_chanel_revitalizing_foundation.txt",
            "N°1 de Chanel Revitalizing Serum": "N°1_de_chanel_revitalizing_serum.txt",
            "N°1 de Chanel Skin Enhancer": "N°1_de_chanel_skin_enhancer.txt"
        }
    }
    product_path = os.path.join(os.getcwd(), "data", "product_data", product_category, product_file_mapping[product_category][product_name])
    assert os.path.exists(product_path)
    
    with open(product_path, 'r') as f:
        product_description = f.read()
    
    return product_description

def get_chanel_persona():
    persona_path = os.path.join(os.getcwd(), "data", "persona", "chanel_persona.txt")
    assert os.path.exists(persona_path)
    
    with open(persona_path, "r") as f:
        persona = f.read()
    
    return persona

def get_brand_knowledge():
    brand_knowledge_path = os.path.join(os.getcwd(), "data", "brand_data", "brand_knowledge.txt")
    assert os.path.exists(brand_knowledge_path)
    
    with open(brand_knowledge_path, "r") as f:
        brand_knowledge = f.read()
        
    return brand_knowledge

def get_copywriting_guidelines():
    copywriting_guidelines_path = os.path.join(os.getcwd(), "data", "brand_data", "copywriting_guidelines.txt")
    assert os.path.exists(copywriting_guidelines_path)
    
    with open(copywriting_guidelines_path, "r") as f:
        copywriting_guidelines = f.read()
    
    return copywriting_guidelines

def get_platform_specs(platform_name):
    platform_specs_file_mapping = {
        "Chanel": "chanel.txt",
        "Sephora": "sephora.txt"
    }
    platform_specs_path = os.path.join(os.getcwd(), "data", "platform_specs", platform_specs_file_mapping[platform_name])
    assert os.path.exists(platform_specs_path)
    
    with open(platform_specs_path, "r") as f:
        platform_specs = f.read()
    
    return platform_specs

def format_customer_profile(customer_profile):
    formated_customer_profile = f"""
    Customer Description:
    {customer_profile["description"]}
    
    Customer Location:
    {customer_profile["location"]}
    
    Customer Status:
    {customer_profile["status"]}
    
    Customer Preferences:
    {customer_profile["purchase_history"]} 
    """
    return formated_customer_profile

class PersonalizedProductDescription(BaseModel):
    personalized_product_description: str = Field(description="The personalized product description copy.")
    

def personalize_content(product_category, product_name, customer_profile, platform_name):
    # Customer Profiling
    output_parser = JsonOutputParser(pydantic_object=CustomerProfiling)
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(customer_profiling_system_prompt),
            HumanMessagePromptTemplate.from_template(customer_profiling_human_prompt)
        ],
        input_variables=["customer_profile"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()}
    )
    customer_profiling_chain = prompt | model | output_parser
    
    # Copywriting
    copywriting_parser = JsonOutputParser(pydantic_object=PersonalizedProductDescription)
    copywriting_prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(copywriting_system_prompt),
            HumanMessagePromptTemplate.from_template(copywriting_human_prompt)
        ],
        input_variables=["chanel_persona", "customer_profile", "brand_knowledge", "copywriting_guidelines", "platform_specs"],
        partial_variables={'format_instructions': copywriting_parser.get_format_instructions()}
    )
    copywriting_chain = (
        RunnablePassthrough.assign(
            brand_knowledge=RunnableLambda(lambda x: get_brand_knowledge()),
            copywriting_guidelines=RunnableLambda(lambda x: get_copywriting_guidelines()),
            chanel_persona=RunnableLambda(lambda x: get_chanel_persona()),
            platform_specs=itemgetter('platform_name') | RunnableLambda(lambda x: get_platform_specs(x)),
            # customer_profile= customer_profiling_chain | RunnableLambda(lambda x: format_customer_profile(x)),
            customer_profile = customer_profiling_chain,
            product_description=itemgetter('product_name', 'product_category') | RunnableLambda(lambda x: get_product_description(x))
        )| copywriting_prompt
        | model
        | copywriting_parser
        | itemgetter('personalized_product_description')
    )
    
    return copywriting_chain.invoke({
        "platform_name": platform_name,
        "customer_profile": customer_profile,
        "product_name": product_name,
        "product_category": product_category
    })
    
def read_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return ""  # Return an empty string if the file does not exist

def write_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)