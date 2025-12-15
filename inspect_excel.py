import pandas as pd
import os

file_path = "documents/valencia.xls"

try:
    df = pd.read_excel(file_path)
    print("Columns:", df.columns.tolist())
    print("First 3 rows:")
    print(df.head(3).to_string())
except Exception as e:
    print(f"Error reading excel: {e}")
