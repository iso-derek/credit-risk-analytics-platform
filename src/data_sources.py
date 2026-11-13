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
MAX_DOWNLOAD_BYTES = 15_000_000


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


def _download_bounded(url=UCI_URL,max_bytes=MAX_DOWNLOAD_BYTES):
    if not url.startswith('https://'): raise ValueError('Public dataset URL must use HTTPS.')
    response=requests.get(url,timeout=(5,30),stream=True)
    try:
        response.raise_for_status()
        length=response.headers.get('Content-Length')
        try: declared_size=int(length) if length is not None else None
        except (TypeError,ValueError): declared_size=None
        if declared_size is not None and declared_size>max_bytes: raise ValueError('Unexpectedly large credit dataset.')
        chunks=[];size=0
        for chunk in response.iter_content(chunk_size=64_000):
            if not chunk: continue
            size+=len(chunk)
            if size>max_bytes: raise ValueError('Unexpectedly large credit dataset.')
            chunks.append(chunk)
        return b''.join(chunks)
    finally:
        response.close()


def download_public_credit():
    content=_download_bounded()
    df,spec=public_credit_dataset(pd.read_csv(BytesIO(content)))
    spec['source_sha256']=hashlib.sha256(content).hexdigest()
    return df,spec

# ---------------------------------------------------------------- Statlog German Credit (UCI 144, CC BY 4.0)
GERMAN_URL = 'https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip'
GERMAN_CITATION = 'Hofmann, H. (1994). Statlog (German Credit Data). UCI Machine Learning Repository. DOI:10.24432/C5NC77 (CC BY 4.0).'
GERMAN_COLUMNS = ['checking_account', 'duration_months', 'credit_history', 'purpose', 'credit_amount', 'savings',
                  'employment_since', 'installment_rate', 'personal_status_sex', 'other_debtors', 'residence_years',
                  'property', 'age', 'other_installment_plans', 'housing', 'existing_credits', 'job', 'dependants',
                  'telephone', 'foreign_worker', 'class']
GERMAN_CODES = {
    'A11': 'Overdrawn (below 0 DM)', 'A12': '0–200 DM', 'A13': '200 DM or more', 'A14': 'No checking account',
    'A30': 'No credit taken or all repaid', 'A31': 'All credit at this bank repaid', 'A32': 'Existing credit repaid on time so far',
    'A33': 'Late payments in the past', 'A34': 'Critical account or credit elsewhere',
    'A40': 'New car', 'A41': 'Used car', 'A42': 'Furniture or equipment', 'A43': 'Radio or television', 'A44': 'Domestic appliances',
    'A45': 'Repairs', 'A46': 'Education', 'A47': 'Vacation', 'A48': 'Retraining', 'A49': 'Business', 'A410': 'Other',
    'A61': 'Under 100 DM', 'A62': '100–500 DM', 'A63': '500–1,000 DM', 'A64': '1,000 DM or more', 'A65': 'None or unknown',
    'A71': 'Unemployed', 'A72': 'Under 1 year', 'A73': '1–4 years', 'A74': '4–7 years', 'A75': '7 years or more',
    'A91': 'Male · divorced or separated', 'A92': 'Female · divorced, separated or married', 'A93': 'Male · single',
    'A94': 'Male · married or widowed', 'A95': 'Female · single',
    'A101': 'None', 'A102': 'Co-applicant', 'A103': 'Guarantor',
    'A121': 'Real estate', 'A122': 'Savings agreement or life insurance', 'A123': 'Car or other', 'A124': 'None or unknown',
    'A141': 'Bank', 'A142': 'Stores', 'A143': 'None', 'A151': 'Rents', 'A152': 'Owns', 'A153': 'Lives for free',
    'A171': 'Unemployed or unskilled (non-resident)', 'A172': 'Unskilled (resident)', 'A173': 'Skilled employee or official',
    'A174': 'Management, self-employed or highly qualified',
    'A191': 'No', 'A192': 'Yes', 'A201': 'Yes', 'A202': 'No',
}
GERMAN_NUMERIC = ['duration_months', 'credit_amount', 'installment_rate', 'residence_years', 'existing_credits', 'dependants']
# Sex, age and foreign-worker status are protected characteristics in lending: they are kept only for the
# subgroup (fairness) diagnostics and are never model inputs.
GERMAN_CATEGORICAL = ['checking_account', 'credit_history', 'purpose', 'savings', 'employment_since', 'other_debtors',
                      'property', 'other_installment_plans', 'housing', 'job', 'telephone']


def german_credit_dataset(raw_text: str):
    rows = [line.split() for line in raw_text.strip().splitlines()]
    df = pd.DataFrame(rows, columns=GERMAN_COLUMNS)
    for column in GERMAN_NUMERIC + ['age', 'class']:
        df[column] = pd.to_numeric(df[column], errors='raise')
    for column in set(GERMAN_COLUMNS) - set(GERMAN_NUMERIC) - {'age', 'class'}:
        unknown = set(df[column]) - set(GERMAN_CODES)
        if unknown: raise ValueError(f'Unknown German Credit codes in {column}: {sorted(unknown)}')
        df[column] = df[column].map(GERMAN_CODES)
    df['sex'] = df.personal_status_sex.str.split(' · ').str[0]
    df['default'] = (df['class'] == 2).astype(int)  # 1 = good, 2 = bad credit risk
    df['application_id'] = [f'DE-{i:04d}' for i in range(1, len(df) + 1)]
    spec = {'numeric': GERMAN_NUMERIC, 'categorical': GERMAN_CATEGORICAL, 'exposure': 'credit_amount', 'currency': 'DEM',
            'source': GERMAN_CITATION, 'source_url': GERMAN_URL, 'synthetic': False,
            'target_horizon': "Good or bad credit risk as classified by the lender (Southern Germany, 1970s; 1994 Statlog release)",
            'exposure_assumption': 'Requested credit amount used as an exposure proxy',
            'split_limit': 'Single historical cohort of 1,000 applicants: no out-of-time validation claim',
            'protected_fields': ['sex', 'age', 'foreign_worker']}
    validate_dataset(df, GERMAN_NUMERIC + GERMAN_CATEGORICAL, spec['exposure'])
    return df.drop(columns=['class', 'personal_status_sex']), spec


def download_german_credit():
    import zipfile
    content = _download_bounded(GERMAN_URL, max_bytes=2_000_000)
    with zipfile.ZipFile(BytesIO(content)) as archive:
        text = archive.read('german.data').decode('latin-1')
    df, spec = german_credit_dataset(text)
    spec['source_sha256'] = hashlib.sha256(content).hexdigest()
    return df, spec
