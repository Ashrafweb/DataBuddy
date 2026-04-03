from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
import json

try:
    import google.generativeai as genai
except Exception:
    genai = None
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class QueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    explanation: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


class TableInfo(BaseModel):
    table_name: str
    columns: List[str]


def get_db_connection():
    """Create PostgreSQL connection"""
    try:
        db_url = os.environ.get('POSTGRES_URL', 'postgresql://user:password@localhost:5432/sql_agent')
        conn = psycopg2.connect(db_url, connect_timeout=10)
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


def validate_sql(sql: str) -> tuple[bool, Optional[str]]:
    """Validate SQL query for safety"""
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in sql_upper:
            return False, f"Query contains forbidden operation: {keyword}"
    return True, None


def get_database_schema() -> str:
    """Get database schema information with exact case-sensitive names"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use pg_class to get exact case-sensitive table names
        cursor.execute("""
            SELECT c.relname as table_name
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' 
            AND c.relkind = 'r'
            ORDER BY c.relname
        """)
        tables = cursor.fetchall()
        
        schema_info = "Database Schema (use double quotes for mixed-case identifiers):\n"
        for table in tables:
            table_name = table[0]
            # Use attname from pg_attribute to get exact column names
            cursor.execute("""
                SELECT a.attname as column_name, 
                       pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = %s 
                AND n.nspname = 'public'
                AND a.attnum > 0 
                AND NOT a.attisdropped
                ORDER BY a.attnum
            """, (table_name,))
            columns = cursor.fetchall()
            
            # Show table name with quotes if it contains uppercase or special chars
            display_name = f'"{table_name}"' if table_name != table_name.lower() else table_name
            schema_info += f"\nTable: {display_name}\n"
            for col in columns:
                col_name = col[0]
                display_col = f'"{col_name}"' if col_name != col_name.lower() else col_name
                schema_info += f"  - {display_col} ({col[1]})\n"
        
        cursor.close()
        conn.close()
        return schema_info
    except Exception as e:
        logging.error(f"Failed to get schema: {e}")
        return "Schema information unavailable"


async def generate_sql_with_gemini(question: str, session_id: str) -> str:
    """Use Google Gemini (Generative AI) to generate SQL, with safe fallbacks."""
    try:
        schema = get_database_schema()

        system_message = f"""You are an intelligent SQL engineer. Generate PostgreSQL queries based on user questions.

{schema}

Rules:
1. Generate ONLY the SQL query, no explanations
2. Use SELECT statements only
3. Do not use DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, CREATE
4. Limit results to 100 rows maximum
5. Return only the SQL query text
6. Use PostgreSQL syntax

CRITICAL - PostgreSQL Identifier Quoting:
- Table and column names with uppercase letters MUST be wrapped in double quotes
- Example: "InvestorsWallet", "User", "Investor" (note the quotes)
- Lowercase-only names don't need quotes: users, products, orders
- ALWAYS check the schema above - if a name is shown with quotes, use quotes in your query
- Incorrect: FROM InvestorsWallet -> Correct: FROM "InvestorsWallet"
- Incorrect: JOIN User -> Correct: JOIN "User"

CRITICAL - String Matching Intelligence:
- For name searches, ALWAYS use ILIKE with % wildcards for flexible matching
- Names may have variations (e.g., "nayeem reza" could be "Md Nayeem Reza", "Nayeem Ahmed Reza", etc.)
- Use: WHERE column_name ILIKE '%search_term%' for partial case-insensitive matching
- For multiple words in a name, match each word: WHERE column_name ILIKE '%word1%' AND column_name ILIKE '%word2%'
- Prefer fuzzy matching over exact equality (=) when dealing with text fields like names, titles, descriptions
- For email/ID lookups, exact match is acceptable
- Consider common prefixes/suffixes (Mr., Ms., Dr., Jr., Sr., etc.)

Examples:
- User asks "investor named john doe" -> WHERE name ILIKE '%john%' AND name ILIKE '%doe%'
- User asks "user reza" -> WHERE name ILIKE '%reza%'
- User asks "product with 'laptop'" -> WHERE product_name ILIKE '%laptop%'"""

        api_key = os.environ.get("GEMINI_API_KEY")

        if genai and api_key:
            try:
                genai.configure(api_key=api_key)
                
                # Use the correct Gemini API with GenerativeModel
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Combine system message and user question
                full_prompt = f"{system_message}\n\nUser Question: {question}"
                
                # Generate content
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.0,
                    )
                )
                
                # Extract the SQL text
                sql = response.text.strip()
                
                # Remove markdown code blocks if present
                if sql.startswith("```"):
                    sql = sql.replace("```sql", "").replace("```", "").strip()
                
                logging.info(f"Generated SQL via Gemini: {sql}")
                return sql
            except Exception as e:
                logging.error(f"Gemini client error: {e}")
                # fall through to rule-based fallback below

        # Rule-based fallback (simple, safe SQL generator for common requests)
        import re

        # Example: "show first 5 rows of users"
        m = re.search(r"first\s+(\d+)\s+rows\s+of\s+([A-Za-z0-9_]+)", question, re.I)
        if m:
            n = m.group(1)
            table = m.group(2)
            return f"SELECT * FROM {table} LIMIT {n}"

        # Example: "list columns of users"
        m = re.search(r"(columns|schema|fields)\s+(?:of|for)\s+([A-Za-z0-9_]+)", question, re.I)
        if m:
            table = m.group(2)
            return f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = 'public'"

        # Very generic fallback
        return "SELECT 1"
    except Exception as e:
        logging.error(f"AI query generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI query generation failed: {str(e)}")


def execute_sql(sql: str) -> tuple[List[Dict[str, Any]], float]:
    """Execute SQL query and return results"""
    import time
    start_time = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        execution_time = (time.time() - start_time) * 1000
        return [dict(row) for row in results], execution_time
    except Exception as e:
        logging.error(f"SQL execution error: {e}")
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")


@api_router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Main endpoint: question -> SQL -> results"""
    try:
        sql = await generate_sql_with_gemini(request.question, request.session_id)
        
        is_valid, error_msg = validate_sql(sql)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        results, exec_time = execute_sql(sql)
        
        return QueryResponse(
            sql=sql,
            results=results,
            row_count=len(results),
            execution_time_ms=round(exec_time, 2),
            explanation=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/tables", response_model=List[TableInfo])
async def get_tables():
    """Get list of available tables and their columns"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = cursor.fetchall()
        
        table_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            table_info.append(TableInfo(
                table_name=table_name,
                columns=[col[0] for col in columns]
            ))
        
        cursor.close()
        conn.close()
        return table_info
    except Exception as e:
        logging.error(f"Failed to get tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/health")
async def health_check():
    """Check if database connection is working"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@api_router.get("/")
async def root():
    return {"message": "SQL Agent API"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()