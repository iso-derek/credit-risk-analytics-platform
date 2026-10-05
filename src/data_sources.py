"""Dataset contracts; retain the original meaning and currency of public data."""
import hashlib
from io import BytesIO
import numpy as np
import pandas as pd
import requests
from data_generation import generate_credit_data
from preprocessing import NUMERIC_FEATURES, CATEGORICAL_FEATURES, engineer_features

UCI_URL = 'https://archive.ics.uci.edu/static/public/350/data.csv'
UCI_CITATION = 'Yeh, I. (2009). Default of Credit Card Clients. UCI. DOI:10.24432/C55S3H (CC BY 4.0).'
UCI_NAMES = ['LIMIT_BAL','SEX','EDUCATION','MARRIAGE','AGE','PAY_0','PAY_2','PAY_3','PAY_4','PAY_5','PAY_6'] + [f'BILL_AMT{i}' for i in range(1,7)] + [f'PAY_AMT{i}' for i in range(1,7)]


def validate_dataset(df, features, exposure):
    missing = set(list(features)+['default','application_id',exposure])-set(df)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    if len(df)<200 or df['default'].value_counts().min()<20:
        raise ValueError('Use at least 200 applicants and 20 examples of each outcome.')
    if df.default.isna().any() or set(df.default.unique())!={0,1}:
        raise ValueError('Default outcomes must contain both 0 and 1 without missing labels.')
    if df.application_id.isna().any() or df.application_id.duplicated().any():
        raise ValueError('Applicant IDs must be unique and non-missing.')
    ead=pd.to_numeric(df[exposure],errors='coerce')
    if not np.isfinite(ead).all() or (ead<0).any(): raise ValueError('Exposure must be finite and non-negative.')
    for c in features:
        if df[c].isna().all(): raise ValueError(f'Entirely missing feature: {c}')
        if pd.api.types.is_numeric_dtype(df[c]) and np.isinf(df[c].dropna()).any():
            raise ValueError(f'Infinite value in {c}')


def synthetic_dataset(n_rows=5000, seed=42):
    df=engineer_features(generate_credit_data(n_rows,seed))
    spec={'numeric':NUMERIC_FEATURES,'categorical':CATEGORICAL_FEATURES,'exposure':'loan_amount',
          'currency':'USD','source':'Synthetic simulation','synthetic':True,'seed':seed,
          'target_horizon':'Unspecified simulated default outcome; not an annual PD',
          'exposure_assumption':'Original loan amount used as an exposure proxy'}
    return df,spec


def public_credit_dataset(raw):
    df=raw.rename(columns={f'X{i}':name for i,name in enumerate(UCI_NAMES,1)}).copy()
    target=next((c for c in ['Y','default payment next month','default.payment.next.month','default'] if c in df),None)
    if target is None or 'ID' not in df: raise ValueError('Expected UCI columns ID, X1…X23, Y or their original names.')
    df=df.rename(columns={target:'default','ID':'application_id'})
    numeric=['LIMIT_BAL']+[f'BILL_AMT{i}' for i in range(1,7)]+[f'PAY_AMT{i}' for i in range(1,7)]
    categorical=['PAY_0','PAY_2','PAY_3','PAY_4','PAY_5','PAY_6']
    if set(numeric+categorical+['default'])-set(df): raise ValueError('Missing public financial/outcome fields.')
    for c in numeric+categorical+['default']: df[c]=pd.to_numeric(df[c],errors='raise')
    for c in categorical: df[c]=df[c].map(lambda x:str(int(x)) if pd.notna(x) else np.nan)
    df['exposure_proxy']=df.BILL_AMT1.clip(lower=0)
    spec={'numeric':numeric,'categorical':categorical,'exposure':'exposure_proxy','currency':'TWD',
          'source':UCI_CITATION,'source_url':UCI_URL,'synthetic':False,
          'target_horizon':'Default payment next month (Taiwan, 2005 cohort)',
          'exposure_assumption':'max(September statement balance, 0); not observed default-time EAD',
          'split_limit':'Single cohort: no out-of-time validation claim'}
    validate_dataset(df,numeric+categorical,spec['exposure'])
    return df,spec


def download_public_credit():
    response=requests.get(UCI_URL,timeout=30)
    response.raise_for_status()
    if len(response.content)>15_000_000: raise ValueError('Unexpectedly large credit dataset.')
    df,spec=public_credit_dataset(pd.read_csv(BytesIO(response.content)))
    spec['source_sha256']=hashlib.sha256(response.content).hexdigest()
    return df,spec
