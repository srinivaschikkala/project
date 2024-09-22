"""Main server"""
from fastapi import FastAPI
from app.routers import curd ,auth
from dotenv import load_dotenv 
app = FastAPI() 

load_dotenv()

from os import environ
# Include the CRUD router
app.include_router(router=curd.router)
app.include_router(router=auth.router)


# from sqlalchemy import create_engine, inspect

# # Replace with your MySQL connection details
# database_url = 'mysql+pymysql://root:Agile&123@localhost:3306/test'
# engine = create_engine(database_url)

# # Create an inspector object
# inspector = inspect(engine)

# # Get the table names
# tables = inspector.get_table_names()

# # Print the table names
# for table in tables:
#     print(table)
