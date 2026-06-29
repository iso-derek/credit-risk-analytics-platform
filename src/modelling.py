"""Credit risk model training and scoring."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from data_generation import load_or_create_credit_data
from preprocessing import build_preprocessor, engineer_features, feature_columns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCORED_PATH = PROCESSED_DIR / "scored_credit_risk.csv"


def _optional_xgboost_model():
    try:
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=150,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )
    except Exception:
        return None


def build_models() -> dict[str, object]:
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=180, max_depth=8, min_samples_leaf=20, class_weight="balanced", random_state=42),
    }
    xgb = _optional_xgboost_model()
    if xgb is not None:
        models["XGBoost"] = xgb
    return models


def train_credit_models(df: pd.DataFrame | None = None) -> dict[str, object]:
    df = engineer_features(df if df is not None else load_or_create_credit_data())
    X = df[feature_columns()]
    y = df["default"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)

    results = {}
    best_name = None
    best_auc = -np.inf
    for name, model in build_models().items():
        pipe = Pipeline([("preprocessor", build_preprocessor()), ("model", model)])
        pipe.fit(X_train, y_train)
        pd_pred = pipe.predict_proba(X_test)[:, 1]
        y_pred = (pd_pred >= 0.5).astype(int)
        auc = roc_auc_score(y_test, pd_pred)
        results[name] = {
            "pipeline": pipe,
            "roc_auc": auc,
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, y_pred),
        }
        if auc > best_auc:
            best_name = name
            best_auc = auc

    best_pipeline = results[best_name]["pipeline"]
    scored = score_credit_applications(df, best_pipeline)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    scored.to_csv(SCORED_PATH, index=False)
    return {"models": results, "best_model_name": best_name, "best_pipeline": best_pipeline, "scored_data": scored}


def score_band(probability_default: float) -> str:
    if probability_default < 0.05:
        return "A - Very Low Risk"
    if probability_default < 0.10:
        return "B - Low Risk"
    if probability_default < 0.18:
        return "C - Moderate Risk"
    if probability_default < 0.30:
        return "D - High Risk"
    return "E - Very High Risk"


def score_credit_applications(df: pd.DataFrame, pipeline: Pipeline, lgd: float = 0.45) -> pd.DataFrame:
    output = engineer_features(df)
    output["probability_default"] = pipeline.predict_proba(output[feature_columns()])[:, 1]
    output["credit_score_band"] = output["probability_default"].apply(score_band)
    output["ead"] = output["loan_amount"]
    output["lgd"] = lgd
    output["expected_loss"] = output["probability_default"] * output["lgd"] * output["ead"]
    return output


def model_feature_importance(result: dict[str, object]) -> pd.DataFrame:
    pipeline = result["best_pipeline"]
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]
    try:
        names = preprocessor.get_feature_names_out()
    except Exception:
        names = feature_columns()
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
    elif hasattr(model, "coef_"):
        values = np.abs(model.coef_[0])
    else:
        values = np.zeros(len(names))
    return pd.DataFrame({"feature": names, "importance": values}).sort_values("importance", ascending=False).head(20)


if __name__ == "__main__":
    result = train_credit_models()
    best = result["best_model_name"]
    metrics = result["models"][best]
    print(f"Best model: {best}")
    print(f"ROC-AUC: {metrics['roc_auc']:.3f}")
    print(f"Saved scored data to {SCORED_PATH}")
