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
from subgroup import add_audit_groups, available_group_columns, subgroup_diagnostics

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
with st.container(horizontal=True):
    st.metric('Untouched test applicants',f'{len(df):,}',border=True)
    st.metric('Mean predicted default risk',f'{df.probability_default.mean():.1%}',border=True)
    st.metric('Observed test defaults',f'{df.default.mean():.1%}',border=True)
    st.metric('Expected loss (assumed LGD)',f"{spec['currency']} {df.expected_loss.sum():,.0f}",border=True)
overview,evidence,subgroups,applicant,scenarios,research=st.tabs(['Portfolio','Model evidence','Subgroup diagnostics','Applicant sensitivity','Loss scenarios','Research exports'])
with overview:
    st.plotly_chart(px.histogram(df,x='probability_default',color='credit_score_band',nbins=30),width='stretch',alt='Held-out applicant default probabilities by credit score band')
    st.dataframe(df[['application_id','credit_score_band','probability_default','ead','expected_loss']],hide_index=True,alt='Held-out applicant probability and expected-loss details')
with evidence:
    st.write('Probability model selected using validation log loss:',result['best_model_name'])
    st.caption('55% training → 15% calibration → 15% model selection → 15% final testing. Final test results do not choose the model.')
    table=pd.DataFrame({name:{k:v for k,v in m.items() if k in ['roc_auc','pr_auc','brier','log_loss','loss_proxy_error']} for name,m in result['models'].items()}).T
    st.dataframe(table,alt='Final-test metrics for each fitted probability model')
    fig=px.scatter(result['reliability'],x='predicted_pd',y='observed_default_rate',size='applicants',hover_data=['bin'])
    fig.add_shape(type='line',x0=0,y0=0,x1=1,y1=1,line={'dash':'dash'})
    st.plotly_chart(fig,width='stretch',alt='Predicted and observed default rates across probability bins')
    st.caption('The dashed line represents matching predicted and observed rates. Brier score and log loss measure more than calibration alone.')
    if st.button('Compute validation permutation importance'): st.dataframe(model_feature_importance(result),alt='Validation permutation importance by model feature')
with subgroups:
    st.subheader('Held-out subgroup diagnostics')
    st.warning('Diagnostic evidence only — not a regulatory fairness assessment or lending-policy approval. Group fields are excluded from the UCI model inputs, but exclusion alone does not establish fairness.')
    audit_df=add_audit_groups(df)
    group_options=available_group_columns(audit_df)
    if not group_options:
        st.info('No supported subgroup field is available in this dataset.')
    else:
        labels={'employment_status':'Employment status','home_ownership':'Home ownership','loan_purpose':'Loan purpose','age_band':'Age band','SEX':'Sex code','EDUCATION':'Education code','MARRIAGE':'Marital-status code'}
        group_column=st.selectbox('Evaluation group',group_options,format_func=lambda value:labels.get(value,value),key='audit_group')
        threshold=st.slider('High-risk flag threshold',.05,.80,.20,.05,key='audit_threshold')
        min_group_size=st.slider('Minimum group size',10,100,30,5,key='audit_minimum')
        audit=subgroup_diagnostics(audit_df,group_column,threshold,min_group_size,bootstrap_draws=500,seed=result['seed'])
        reported=audit[audit.status=='Reported']
        with st.container(horizontal=True):
            st.metric('Groups reported',f'{len(reported):,}',border=True)
            st.metric('Groups suppressed',f'{len(audit)-len(reported):,}',border=True)
            st.metric('Decision threshold',f'{threshold:.0%}',border=True)
        if not reported.empty:
            chart=reported[['group','mean_predicted_pd','observed_default_rate']].melt('group',var_name='measure',value_name='rate')
            st.bar_chart(chart,x='group',y='rate',color='measure',y_label='Rate',alt='Mean predicted and observed default rates by reported subgroup')
        st.dataframe(
            audit,
            hide_index=True,
            alt='Held-out subgroup calibration, discrimination and threshold-error diagnostics',
            column_config={
                column:st.column_config.NumberColumn(format='percent') for column in [
                    'mean_predicted_pd','observed_default_rate','observed_rate_ci_low','observed_rate_ci_high',
                    'calibration_gap','calibration_gap_ci_low','calibration_gap_ci_high','brier_score',
                    'roc_auc','flag_rate','true_positive_rate','false_positive_rate','precision']
            },
        )
        st.caption('Intervals are 95% applicant-level bootstrap intervals conditional on the fitted model and this final-test cohort. Groups below the minimum size or with one observed outcome are suppressed; results do not establish transfer, causal or legal fairness.')
        st.download_button('Download subgroup diagnostics',audit.to_csv(index=False),f'credit_subgroup_{group_column}.csv','text/csv')
with applicant:
    choice=st.selectbox('Held-out applicant',df.application_id.tolist())
    row=df[df.application_id==choice].iloc[0]
    st.metric('Predicted default probability',f'{row.probability_default:.1%}')
    st.dataframe(applicant_sensitivity(result,row).head(10),hide_index=True,alt='Top model sensitivity changes for the selected held-out applicant')
    st.caption('PD change replaces one input with its training reference. Correlated inputs can make replacements unrealistic. This is model sensitivity, not a causal explanation or lending recommendation.')
with scenarios:
    odds=st.slider('Default odds multiplier (assumed)',.25,4.,1.,.25,key='scenario_odds')
    lgd=st.slider('Loss given default (assumed)',0.,1.,.45,.05,key='scenario_lgd')
    exposure=st.slider('Exposure multiplier (assumed)',0.,2.,1.,.1,key='scenario_exposure')
    scenario=loss_scenarios(df,odds,lgd,exposure)
    st.metric('Scenario expected loss',f"{spec['currency']} {scenario.scenario_expected_loss.sum():,.0f}",delta=f'{scenario.scenario_expected_loss.sum()-df.expected_loss.sum():,.0f}',delta_color='inverse')
    st.caption('Sensitivity assumptions, not a forecast of how a recession changes borrower risk.')
    st.download_button('Download scenario',scenario.to_csv(index=False),'credit_scenario.csv','text/csv')
with research:
    st.write('Does the best ranking model also give the most useful default probabilities?')
    st.json(compare_selections(result))
    st.caption('Both selection rules can choose the same model. A null result is valid. Fixed-loss proxies cannot establish realised recovery accuracy.')
    st.download_button('Download reproducible research bundle',result_bundle(result),'credit_research.zip','application/zip')
