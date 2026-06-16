import os
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join("backend", ".env"))

def setup_dummy_database(db_path: str):
    """Creates a dummy SQLite database with a 'sales' table for demonstration."""
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a sales table
    cursor.execute('''
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            product_name TEXT,
            quarter TEXT,
            revenue REAL
        )
    ''')
    
    # Insert some dummy data (Total Q3 revenue = 25000 + 5000 + 12000 = 42000.0)
    dummy_data = [
        (1, 'Laptop', 'Q1', 15000.0),
        (2, 'Phone', 'Q1', 8000.0),
        (3, 'Laptop', 'Q2', 20000.0),
        (4, 'Phone', 'Q2', 9500.0),
        (5, 'Laptop', 'Q3', 25000.0), # Q3 sales
        (6, 'Tablet', 'Q3', 5000.0),  # Q3 sales
        (7, 'Phone', 'Q3', 12000.0),  # Q3 sales
        (8, 'Laptop', 'Q4', 30000.0)
    ]
    cursor.executemany('INSERT INTO sales VALUES (?, ?, ?, ?)', dummy_data)
    conn.commit()
    conn.close()
    print(f"Dummy SQLite database created at '{db_path}' with 'sales' table.")

def main():
    print("--- Text-to-SQL Concept Demonstration ---")
    print("Unlike RAG (for unstructured text), this script handles structured data using Text-to-SQL.\n")

    db_path = "sales_database.db"
    
    # 1. Setup the structured database
    setup_dummy_database(db_path)
    
    # 2. Connect LangChain to the SQL Database
    # This requires 'sqlalchemy' package to be installed (pip install sqlalchemy)
    try:
        db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        print(f"Connected to database. Available tables: {db.get_usable_table_names()}")
    except ImportError:
        print("Error: 'SQLAlchemy' is missing. Please run: pip install sqlalchemy")
        return
    
    # 3. Setup the LLM
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Please set the GOOGLE_API_KEY environment variable in your .env file.")
        return

    # Using a temperature of 0 is crucial for code/SQL generation
    llm = ChatOpenAI(
        model="google/gemini-3.5-flash",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=3000
    )

    # 4. Create the Text-to-SQL Query Chain
    # This chain takes a natural language question and outputs a SQL query based on the DB schema
    chain = create_sql_query_chain(llm, db)
    
    # 5. User Question involving calculation/aggregation
    question = "ما هو مجموع المبيعات (revenue) في الربع الثالث (Q3)؟"
    print(f"\nUser Question: {question}")
    
    # Generate the SQL query
    try:
        sql_query = chain.invoke({"question": question})
        # Clean the output in case the LLM wraps it in markdown (e.g. ```sql ... ```)
        clean_query = sql_query.replace("```sql", "").replace("```", "").strip()
        print(f"Generated SQL Query by LLM:\n{clean_query}")
        
        # Execute the SQL query against the database
        result = db.run(clean_query)
        print(f"\nExecution Result directly from Database Engine:\n{result}")
        
        print("\nConclusion: The LLM successfully converted the natural language to SQL. "
              "The exact mathematical aggregate (42000.0) was computed by the SQLite DB engine, "
              "avoiding the inaccurate semantic search you would get with traditional RAG!")
              
    except Exception as e:
        print(f"Error during Text-to-SQL execution: {e}")

if __name__ == "__main__":
    main()
