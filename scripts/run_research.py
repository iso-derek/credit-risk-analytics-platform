"""Run: python scripts/run_research.py --dataset uci --output outputs/uci_study.zip"""
from pathlib import Path
import sys
import argparse
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from data_sources import synthetic_dataset, download_public_credit
from modelling import train_credit_models
from research import result_bundle, compare_selections

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',choices=['synthetic','uci'],default='synthetic')
    parser.add_argument('--output',type=Path,default=Path('outputs/credit_study.zip'))
    args=parser.parse_args()
    df,spec=synthetic_dataset() if args.dataset=='synthetic' else download_public_credit()
    result=train_credit_models(df,spec)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(result_bundle(result))
    print(json.dumps({'source':spec['source'],'rows':len(df),'data_sha256':result['data_sha256'],
                      'comparison':compare_selections(result)},indent=2))
