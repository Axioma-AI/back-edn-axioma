import re
import pandas as pd

def convert_nan_to_none(value):
    if isinstance(value, pd.Series):
        return value.apply(lambda x: None if pd.isna(x) else x)
    elif isinstance(value, list):
        return [None if pd.isna(x) else x for x in value]
    else:
        return None if pd.isna(value) else value
    
def convert_nan_to_empty_string(value):
    if isinstance(value, pd.Series):
        return value.apply(lambda x: "" if pd.isna(x) else x)
    elif isinstance(value, list):
        return ["" if pd.isna(x) else x for x in value]
    else:
        return "" if pd.isna(value) else value

def remove_surrogates(text):
    if isinstance(text, str):
        return re.sub(r'[\ud800-\udfff]', '', text)
    return text

def clean_dataframe(df):
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].apply(remove_surrogates)
    return df