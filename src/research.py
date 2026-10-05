"""Loss sensitivity and paired, applicant-level probability comparisons."""
import io
import json
import zipfile
import numpy as np
import pandas as pd


def loss_scenarios(scored, odds_multiplier=1., lgd=.45, exposure_multiplier=1.):
    if not np.isfinite([odds_multiplier,lgd,exposure_multiplier]).all() or odds_multiplier<=0 or not 0<=lgd<=1 or exposure_multiplier<0:
        raise ValueError('Use positive odds, non-negative exposure and LGD in [0,1].')
    p=scored.probability_default.to_numpy(float); exposure=scored.ead.to_numpy(float)
    if not np.isfinite(p).all() or ((p<0)|(p>1)).any() or not np.isfinite(exposure).all() or (exposure<0).any():
        raise ValueError('Invalid probability or exposure.')
    stressed=p*odds_multiplier/(1-p+p*odds_multiplier)
    return pd.DataFrame({'application_id':scored.application_id.to_numpy(),'baseline_pd':p,'scenario_pd':stressed,
                         'scenario_exposure':exposure*exposure_multiplier,'scenario_expected_loss':stressed*exposure*exposure_multiplier*lgd})


def compare_selections(result, draws=1000):
    if draws<100: raise ValueError('Use at least 100 bootstrap draws.')
    y=result['scored_data'].default.to_numpy()
    names=[result['best_model_name'],result['ranking_model_name']]
    a,b=[result['test_probabilities'][name] for name in names]
    delta=(a-y)**2-(b-y)**2
    rng=np.random.default_rng(result['seed'])
    boot=np.array([rng.choice(delta,len(delta),replace=True).mean() for _ in range(draws)])
    return {'probability_choice':names[0],'ranking_choice':names[1],'brier_difference':float(delta.mean()),
            'lower_95':float(np.quantile(boot,.025)),'upper_95':float(np.quantile(boot,.975)),
            'test_applicants':len(y),'note':'Negative favours probability choice. Conditional on fixed models; iid borrower resampling, not retraining uncertainty.'}


def result_bundle(result):
    stream=io.BytesIO(); rows=[]
    for split,metrics in [('validation',result['validation']),('test',result['models'])]:
        for name,values in metrics.items(): rows.append({'split':split,'model':name,**{k:v for k,v in values.items() if np.isscalar(v)}})
    predictions=pd.DataFrame(result['test_probabilities'])
    predictions.insert(0,'default',result['scored_data'].default.to_numpy())
    predictions.insert(0,'application_id',result['scored_data'].application_id.to_numpy())
    metadata={'seed':result['seed'],'data_sha256':result['data_sha256'],'dataset':result['spec'],
              'selection_rule':'validation log loss','lgd':float(result['scored_data'].lgd.iloc[0]),'comparison':compare_selections(result)}
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for name,frame in [('metrics',pd.DataFrame(rows)),('splits',result['split_manifest']),('test_predictions',predictions),
                           ('heldout_portfolio',result['scored_data']),('reliability',result['reliability'])]:
            z.writestr(name+'.csv',frame.to_csv(index=False))
        z.writestr('settings.json',json.dumps(metadata,indent=2))
    return stream.getvalue()
