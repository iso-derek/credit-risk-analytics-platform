"""Credit decisions, probability evidence and reproducible research."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import pandas as pd
import plotly.express as px
import streamlit as st
from data_sources import synthetic_dataset, download_public_credit
from modelling import train_credit_models, model_feature_importance, applicant_sensitivity
from research import compare_selections, loss_scenarios, result_bundle

st.set_page_config(page_title='Credit Risk Research',layout='wide')
st.title('Credit Risk Analytics & Research')
st.caption('Compare default probabilities, loss assumptions and evidence on unseen applicants.')
source=st.sidebar.selectbox('Dataset',['Synthetic demonstration','UCI public credit-card benchmark'])

@st.cache_data(show_spinner='Fitting and evaluating credit models…')
def study(source):
    df,spec=synthetic_dataset() if source.startswith('Synthetic') else download_public_credit()
    return train_credit_models(df,spec)

try: result=study(source)
except (ValueError,OSError,RuntimeError) as exc:
    st.error(f'Dataset or study could not be loaded: {exc}')
    st.stop()
spec,df=result['spec'],result['scored_data']
if spec['synthetic']: st.warning('Synthetic data: results demonstrate the experiment, not real lending performance.')
st.caption(f"{spec['source']} · {spec['target_horizon']}")
st.info(f"Loss assumption: {spec['exposure_assumption']}; LGD is assumed at 45%. Amounts are {spec['currency']}. These are not observed recovery losses.")
cols=st.columns(4)
cols[0].metric('Untouched test applicants',f'{len(df):,}')
cols[1].metric('Mean predicted default risk',f'{df.probability_default.mean():.1%}')
cols[2].metric('Observed test defaults',f'{df.default.mean():.1%}')
cols[3].metric('Expected loss (assumed LGD)',f"{spec['currency']} {df.expected_loss.sum():,.0f}")
overview,evidence,applicant,scenarios,research=st.tabs(['Portfolio','Model evidence','Applicant sensitivity','Loss scenarios','Research exports'])
with overview:
    st.plotly_chart(px.histogram(df,x='probability_default',color='credit_score_band',nbins=30),width='stretch')
    st.dataframe(df[['application_id','credit_score_band','probability_default','ead','expected_loss']],hide_index=True)
with evidence:
    st.write('Probability model selected using validation log loss:',result['best_model_name'])
    st.caption('55% training → 15% calibration → 15% model selection → 15% final testing. Final test results do not choose the model.')
    table=pd.DataFrame({name:{k:v for k,v in m.items() if k in ['roc_auc','pr_auc','brier','log_loss','loss_proxy_error']} for name,m in result['models'].items()}).T
    st.dataframe(table)
    fig=px.scatter(result['reliability'],x='predicted_pd',y='observed_default_rate',size='applicants',hover_data=['bin'])
    fig.add_shape(type='line',x0=0,y0=0,x1=1,y1=1,line={'dash':'dash'})
    st.plotly_chart(fig,width='stretch')
    st.caption('The dashed line represents matching predicted and observed rates. Brier score and log loss measure more than calibration alone.')
    if st.button('Compute validation permutation importance'): st.dataframe(model_feature_importance(result))
with applicant:
    choice=st.selectbox('Held-out applicant',df.application_id.tolist())
    row=df[df.application_id==choice].iloc[0]
    st.metric('Predicted default probability',f'{row.probability_default:.1%}')
    st.dataframe(applicant_sensitivity(result,row).head(10),hide_index=True)
    st.caption('PD change replaces one input with its training reference. Correlated inputs can make replacements unrealistic. This is model sensitivity, not a causal explanation or lending recommendation.')
with scenarios:
    odds=st.slider('Default odds multiplier (assumed)',.25,4.,1.,.25)
    lgd=st.slider('Loss given default (assumed)',0.,1.,.45,.05)
    exposure=st.slider('Exposure multiplier (assumed)',0.,2.,1.,.1)
    scenario=loss_scenarios(df,odds,lgd,exposure)
    st.metric('Scenario expected loss',f"{spec['currency']} {scenario.scenario_expected_loss.sum():,.0f}",delta=f'{scenario.scenario_expected_loss.sum()-df.expected_loss.sum():,.0f}',delta_color='inverse')
    st.caption('Sensitivity assumptions, not a forecast of how a recession changes borrower risk.')
    st.download_button('Download scenario',scenario.to_csv(index=False),'credit_scenario.csv','text/csv')
with research:
    st.write('Does the best ranking model also give the most useful default probabilities?')
    st.json(compare_selections(result))
    st.caption('Both selection rules can choose the same model. A null result is valid. Fixed-loss proxies cannot establish realised recovery accuracy.')
    st.download_button('Download reproducible research bundle',result_bundle(result),'credit_research.zip','application/zip')
