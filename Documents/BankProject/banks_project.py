# Importing the required libraries

from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime 

# Setup file paths and variables
url = 'https://web.archive.org/web/20230908091635 /https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ["Name","MC_USD_Billion"]
db_name = 'Banks.db'
table_name = 'Largest_banks'
csv_path = os.path.join(os.getcwd(),'Largest_banks_data.csv')
rate_path = os.path.join(os.getcwd(), "exchange_rate.csv")
log_file = os.path.join(os.getcwd(),'code_log.txt')

def extract(url, table_attribs):
    page = requests.get(url).text
    data = BeautifulSoup(page,'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    table = data.find_all('table')[0]
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all("td")

        if len(cols) != 0:
            # Extract bank name safely
            name = cols[1].text.strip()

            # Extract Market Cap and clean it
            mc = cols[2].text.strip()          # removes \n automatically
            mc = mc.replace(",", "")           # remove commas
            mc = float(mc)                     # convert to float

            # Build dictionary
            data_dict = {
                "Name": name,
                "MC_USD_Billion": mc
            }

            # Convert dict → DataFrame row
            df1 = pd.DataFrame(data_dict, index=[0])

            # Append row
            df = pd.concat([df, df1], ignore_index=True)
    return df



def transform(df,rate_path):
    # Load exchange rate file
    rates = pd.read_csv(rate_path)

    # Convert to dictionary for easy access
    rate_dict = dict(zip(rates["Currency"], rates["Rate"]))

    # Add new currency columns
    df["MC_GBP_Billion"] = (df["MC_USD_Billion"] * rate_dict["GBP"]).round(2)
    df["MC_EUR_Billion"] = (df["MC_USD_Billion"] * rate_dict["EUR"]).round(2)
    df["MC_INR_Billion"] = (df["MC_USD_Billion"] * rate_dict["INR"]).round(2)
    print(df["MC_EUR_Billion"].iloc[4])
    return df
def load_to_csv(df, csv_path):
    df.to_csv(csv_path)
    
def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_queries(query_statement, sql_connection):
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)
    
def log_progress(message):
    timestamp_format = '%Y-%h-%d-%H:%M:%S' # Year-Monthname-Day-Hour-Minute-Second 
    now = datetime.now() # get current timestamp 
    timestamp = now.strftime(timestamp_format) 
    with open(log_file,"a") as f: 
        f.write(timestamp + ' : ' + message + '\n')   
        
# --- PHASE 1: START EXTRACT ---
log_progress("Preliminaries complete. Initiating ETL Process")
log_progress("Data extraction initiated")

df = extract(url, table_attribs)
log_progress("Data extraction complete. Initiating Transformation process")
print(df)
# --- PHASE 2: TRANSFORM ---
df = transform(df,rate_path)
log_progress('Data transformation complete. Initiating loading process')

# --- PHASE 3: LOAD ---
load_to_csv(df, csv_path)
log_progress('Data saved to CSV file')

sql_connection = sqlite3.connect(db_name)

log_progress('SQL Connection initiated.')

load_to_db(df, sql_connection, table_name)

log_progress('Data loaded to Database as table. Running the query')

query_statement = f""" 
SELECT * 
FROM {table_name}
"""
run_queries(query_statement, sql_connection)
query_statement = f""" 
SELECT AVG(MC_GBP_Billion) 
FROM {table_name}
"""
run_queries(query_statement, sql_connection)
query_statement = f""" 
SELECT Name 
FROM {table_name} LIMIT 5
"""
run_queries(query_statement, sql_connection)
query_statement = f"""
SELECT Name, MC_GBP_Billion AS Market_Cap, 'London' AS Office
FROM {table_name}

UNION ALL

SELECT Name, MC_EUR_Billion AS Market_Cap, 'Berlin' AS Office
FROM {table_name}

UNION ALL

SELECT Name, MC_INR_Billion AS Market_Cap, 'New Delhi' AS Office
FROM {table_name}
"""
run_queries(query_statement, sql_connection)

log_progress('Process Complete.')

sql_connection.close()
