import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import io
import json
import zipfile
import unittest
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from data_sources import synthetic_dataset, public_credit_dataset, validate_dataset
from modelling import train_credit_models, split_applicants, applicant_sensitivity
from research import loss_scenarios, compare_selections, result_bundle

class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df,cls.spec=synthetic_dataset(800,7)
        cls.parts=split_applicants(cls.df)
        cls.result=cls.fit(cls.df)
    @classmethod
    def fit(cls,df):
        return train_credit_models(df,cls.spec,models={'LR':LogisticRegression(max_iter=1500)},partitions=cls.parts)
    def test_test_labels_cannot_change_selection_or_predictions(self):
        changed=self.df.copy()
        changed.loc[self.parts['test'],'default']=1-changed.loc[self.parts['test'],'default']
        other=self.fit(changed)
        self.assertEqual(self.result['best_model_name'],other['best_model_name'])
        np.testing.assert_allclose(self.result['scored_data'].probability_default,other['scored_data'].probability_default)
        self.assertNotEqual(self.result['models'][self.result['best_model_name']]['log_loss'],other['models'][other['best_model_name']]['log_loss'])
    def test_splits_disjoint_and_predictions_only_holdout(self):
        all_rows=np.concatenate(list(self.parts.values()))
        self.assertEqual(len(np.unique(all_rows)),len(self.df))
        self.assertEqual(set(self.result['scored_data'].index),set(self.parts['test']))
    def test_overlapping_partitions_rejected(self):
        broken={k:v.copy() for k,v in self.parts.items()}
        broken['test'][0]=broken['train'][0]
        with self.assertRaisesRegex(ValueError,'overlap'): train_credit_models(self.df,self.spec,partitions=broken)
    def test_duplicate_applicants_rejected(self):
        df=self.df.copy(); df.loc[1,'application_id']=df.loc[0,'application_id']
        with self.assertRaisesRegex(ValueError,'unique'): self.fit(df)
    def test_scenario_math_and_boundaries(self):
        df=pd.DataFrame({'application_id':['a','b','c'],'probability_default':[0,.2,1.],'ead':[100,100,100]})
        scenario=loss_scenarios(df,2,.5,1)
        np.testing.assert_allclose(scenario.scenario_pd,[0,1/3,1])
        np.testing.assert_allclose(scenario.scenario_expected_loss,[0,50/3,50])
        with self.assertRaises(ValueError): loss_scenarios(df,lgd=1.1)
    def test_public_schema_keeps_currency_and_exposure_proxy(self):
        raw=pd.DataFrame({f'X{i}':np.ones(200)*100 for i in range(1,24)})
        raw['ID']=np.arange(200);raw['Y']=np.tile([0,1],100);raw.loc[0,'X12']=-5
        df,spec=public_credit_dataset(raw)
        self.assertEqual(spec['currency'],'TWD');self.assertEqual(df.exposure_proxy.iloc[0],0)
        self.assertNotIn('SEX',spec['numeric']+spec['categorical'])
    def test_model_sensitivity_and_research_exports(self):
        result=applicant_sensitivity(self.result,self.result['scored_data'].iloc[0])
        self.assertTrue(np.isfinite(result.pd_change).all())
        z=zipfile.ZipFile(io.BytesIO(result_bundle(self.result)))
        settings=json.loads(z.read('settings.json'))
        self.assertEqual(settings['data_sha256'],self.result['data_sha256'])
        self.assertIn('splits.csv',z.namelist())
        self.assertEqual(compare_selections(self.result,100),compare_selections(self.result,100))
    def test_reliability_counts_cover_holdout(self):
        self.assertEqual(self.result['reliability'].applicants.sum(),len(self.result['scored_data']))

class AppTests(unittest.TestCase):
    def test_dashboard_and_scenario_controls(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run(timeout=60)
        self.assertFalse(app.exception)
        app.slider[0].set_value(2.).run(timeout=60)
        self.assertFalse(app.exception)

if __name__=='__main__': unittest.main()
