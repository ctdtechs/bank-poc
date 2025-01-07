import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_models import ChatOllama
import mysql.connector
import json

# AI Model Initialization
ollama = ChatOllama(model="llama3.1:latest", base_url="http://37.27.125.244:11434")

# Database connection
dbcon = "mysql+mysqlconnector://iHrms:%21ctd%21%40%21%32o24%40%21@37.27.125.244/poc_test_db"
engine = create_engine(dbcon)
db = SQLDatabase(engine)

# SQL Query Prompt Template
template = """
Based on the table schema below, write a MySQL query that would answer the user's question:
{schema}

Question: {question}

MySQL Query:
"""
prompt = ChatPromptTemplate.from_template(template)

def get_schema(_):
    """Fetch the schema of the database."""
    return db.get_table_info()

# SQL Query Generation Chain
sql_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | ollama.bind(stop=["\nMySQL Query:"])
    | StrOutputParser()
)

def execute_query(query):
    """Execute a generated SQL query and return results."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchall()
    except Exception as e:
        return str(e)

def summarize_results(results):
    """Use AI to summarize the query results."""
    summary_prompt = f"Summarize the following database query results: {results}"
    response = ollama.invoke(summary_prompt)
    
    # If the response is a dictionary, extract the desired field
    if response:
        st.write(response.content)
    else:
        return "No Response from AI model."

def categorize_transaction(description):
    """Use AI to categorize the bank transaction based on the description."""
    categories = ["Groceries", "Entertainment", "Bills", "Transportation", "Dining", "Salary", "Others"]
    category_prompt = f"Categorize the following bank transaction description into one of the categories: {', '.join(categories)}. Description: {description}"
    response = ollama.invoke(category_prompt)
    return response.strip()

def fetch_transactions():
    """Fetch transactions from the database."""
    db_conn = mysql.connector.connect(
        host="37.27.125.244",
        user="iHrms",
        password="!ctd!@!2o24@!",
        database="poc_test_db"
    )
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM BankStatements")
    transactions = cursor.fetchall()
    db_conn.close()
    return transactions

# Streamlit UI
st.title("Bank Transaction Analysis")

# Section: User Question Input
st.subheader("Ask a Question About Bank Transactions")
user_question = st.text_input("Enter your question:")

if user_question:
    # Generate and display SQL query
    response = sql_chain.invoke({"question": user_question})
    query = response.split("```sql")[1].strip().split("```")[0] if "```sql" in response else response.strip()
    st.subheader("Step 1: Generated SQL Query from AI")
    st.code(query, language="sql")
    
    # Execute query and display results
    query_result = execute_query(query)
    st.subheader("Step 2: Obtains Query Result from DB")
    with st.expander("View Query Result"):
        st.write(query_result)
    
    # Summarize query results
    if query_result:
        st.subheader("Step 3: Analysis Transaction")
        summary = summarize_results(query_result)
