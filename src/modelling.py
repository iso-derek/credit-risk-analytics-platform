"""Fit, calibrate, select, then evaluate on an untouched applicant holdout."""
import hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score, average_precision_score, precision_score, recall_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from data_sources import synthetic_dataset, validate_dataset


def split_applicants(df,seed=42):
    indices=np.arange(len(df))
    development,test=train_test_split(indices,test_size=.15,stratify=df.default,random_state=seed)
    fit_cal,validation=train_test_split(development,test_size=.15/.85,stratify=df.default.iloc[development],random_state=seed+1)
    train,calibration=train_test_split(fit_cal,test_size=.15/.70,stratify=df.default.iloc[fit_cal],random_state=seed+2)
    return {'train':train,'calibration':calibration,'validation':validation,'test':test}


def build_models():
    return {'Logistic regression':LogisticRegression(max_iter=2000,random_state=42),
            'Random forest':RandomForestClassifier(n_estimators=120,max_depth=8,min_samples_leaf=15,random_state=42,n_jobs=1)}


def preprocessor(spec):
    return ColumnTransformer([
        ('numeric',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),spec['numeric']),
        ('categorical',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore'))]),spec['categorical'])])


class ProbabilityModel:
    def __init__(self,pipeline,calibrator=None): self.pipeline,self.calibrator=pipeline,calibrator
    def predict_proba(self,X):
        p=np.clip(self.pipeline.predict_proba(X)[:,1],1e-7,1-1e-7)
        if self.calibrator is not None: p=self.calibrator.predict_proba(np.log(p/(1-p)).reshape(-1,1))[:,1]
        return np.column_stack([1-p,p])


def probability_metrics(y,p,ead,lgd=.45):
    y,p,ead=np.asarray(y),np.asarray(p),np.asarray(ead)
    predicted=float(np.sum(p*ead*lgd)); proxy=float(np.sum(y*ead*lgd))
    return {'roc_auc':float(roc_auc_score(y,p)),'pr_auc':float(average_precision_score(y,p)),
            'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1])),
            'precision':float(precision_score(y,p>=.5,zero_division=0)),'recall':float(recall_score(y,p>=.5,zero_division=0)),
            'confusion_matrix':confusion_matrix(y,p>=.5,labels=[0,1]),'expected_loss':predicted,
            'default_weighted_loss_proxy':proxy,'loss_proxy_error':predicted-proxy}


def reliability_table(y,p,bins=10):
    frame=pd.DataFrame({'outcome':np.asarray(y),'probability':np.asarray(p)})
    frame['bin']=pd.cut(frame.probability,np.linspace(0,1,bins+1),include_lowest=True)
    result=frame.groupby('bin',observed=True).agg(predicted_pd=('probability','mean'),observed_default_rate=('outcome','mean'),applicants=('outcome','size')).reset_index()
    result['bin']=result['bin'].astype(str)
    return result


def score_band(p):
    return 'A (<5%)' if p<.05 else 'B (5–10%)' if p<.10 else 'C (10–18%)' if p<.18 else 'D (18–30%)' if p<.30 else 'E (30%+)'


def train_credit_models(df=None,spec=None,seed=42,models=None,partitions=None,lgd=.45):
    if df is None: df,spec=synthetic_dataset()
    elif spec is None:
        from preprocessing import engineer_features
        df=engineer_features(df)
        _,spec=synthetic_dataset(200)
    df=df.reset_index(drop=True).copy()
    features=spec['numeric']+spec['categorical']
    validate_dataset(df,features,spec['exposure'])
    if not 0<=lgd<=1: raise ValueError('LGD must lie between 0 and 1.')
    parts=split_applicants(df,seed) if partitions is None else partitions
    if set(parts)!={'train','calibration','validation','test'}: raise ValueError('Four named partitions required.')
    joined=np.concatenate(list(parts.values()))
    if len(joined)!=len(df) or set(joined)!=set(range(len(df))) or len(np.unique(joined))!=len(joined):
        raise ValueError('Partitions must cover every row exactly once without overlap.')
    if any(set(df.default.iloc[idx].unique())!={0,1} for idx in parts.values()): raise ValueError('Each partition needs both outcomes.')
    X,y=df[features],df.default.astype(int)
    tr,ca,va,te=(parts[k] for k in ['train','calibration','validation','test'])
    candidates,validation={},{}
    for name,model in (build_models() if models is None else models).items():
        pipe=Pipeline([('preprocessor',preprocessor(spec)),('model',model)])
        pipe.fit(X.iloc[tr],y.iloc[tr])
        raw=ProbabilityModel(pipe)
        p_cal=raw.predict_proba(X.iloc[ca])[:,1]
        sigmoid=LogisticRegression(C=1e3,max_iter=1000).fit(np.log(p_cal/(1-p_cal)).reshape(-1,1),y.iloc[ca])
        for variant,fitted in [('raw',raw),('calibrated',ProbabilityModel(pipe,sigmoid))]:
            label=f'{name} / {variant}'; candidates[label]=fitted
            validation[label]=probability_metrics(y.iloc[va],fitted.predict_proba(X.iloc[va])[:,1],df[spec['exposure']].iloc[va],lgd)
    if not candidates: raise ValueError('At least one model is required.')
    # Freeze selections before accessing final test outcomes.
    best=min(validation,key=lambda k:(validation[k]['log_loss'],k))
    rank_best=max(validation,key=lambda k:(validation[k]['roc_auc'],k))
    test_models,probabilities={},{}
    for label,fitted in candidates.items():
        p=fitted.predict_proba(X.iloc[te])[:,1]; probabilities[label]=p
        test_models[label]={**probability_metrics(y.iloc[te],p,df[spec['exposure']].iloc[te],lgd),'pipeline':fitted}
    scored=df.iloc[te].copy()
    scored['probability_default']=probabilities[best]; scored['ead']=scored[spec['exposure']]; scored['lgd']=lgd
    scored['expected_loss']=scored.probability_default*scored.ead*lgd
    scored['credit_score_band']=scored.probability_default.map(score_band)
    if 'loan_purpose' not in scored: scored['loan_purpose']='Credit card'
    manifest=pd.DataFrame({'application_id':df.application_id,'split':''})
    for name,idx in parts.items(): manifest.loc[idx,'split']=name
    reference={c:(X.iloc[tr][c].median() if c in spec['numeric'] else X.iloc[tr][c].mode().iloc[0]) for c in features}
    return {'models':test_models,'validation':validation,'best_model_name':best,'ranking_model_name':rank_best,
            'best_pipeline':candidates[best],'scored_data':scored,'test_probabilities':probabilities,
            'reliability':reliability_table(y.iloc[te],probabilities[best]),'split_manifest':manifest,'spec':spec,
            'seed':seed,'reference':reference,'validation_X':X.iloc[va],'validation_y':y.iloc[va],
            'data_sha256':hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()}


def model_feature_importance(result):
    imp=permutation_importance(result['best_pipeline'].pipeline,result['validation_X'],result['validation_y'],
                               scoring='roc_auc',n_repeats=3,random_state=result['seed'])
    return pd.DataFrame({'feature':result['validation_X'].columns,'importance':imp.importances_mean,
                         'standard_deviation':imp.importances_std}).sort_values('importance',ascending=False)


def applicant_sensitivity(result,applicant):
    spec=result['spec']; features=spec['numeric']+spec['categorical']
    base=pd.DataFrame([applicant])[features]; predict=result['best_pipeline'].predict_proba
    p=float(predict(base)[0,1]); rows=[]
    for name in features:
        modified=base.copy(); modified[name]=result['reference'][name]
        if spec['synthetic']:
            from preprocessing import engineer_features
            if name in {'loan_to_income','risk_rule_score'}: continue
            modified=engineer_features(modified)
        other=float(predict(modified[features])[0,1])
        rows.append({'feature':name,'applicant_value':str(base.iloc[0][name]),'training_reference':str(result['reference'][name]),'pd_change':p-other})
    return pd.DataFrame(rows).sort_values('pd_change',key=abs,ascending=False)
