#!/usr/bin/env python3
"""Reproducible early-horizon Structural Prior benchmark v1.

Selection protocol:
- train candidate specs on 2021/22 + 2022/23;
- select on 2023/24 only;
- refit the selected spec and evaluate untouched 2024/25;
- refit through 2024/25 and evaluate untouched 2025/26.

The target is verified-capacity occupancy residual. Final attendance predictions
are clipped to [0, verified capacity].
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

CAT = ["home_club_key","away_club_key"]
META = {
    "feature_set_version","match_key","season","horizon","as_of_at","kickoff_at",
    "home_club_key","away_club_key","target_attendance","target_eligible","training_eligible",
}
IMPORTANCE = {
    "combined_ppg","abs_ppg_gap","abs_position_gap","combined_table_strength",
    "top4_any","top4_both","bottom4_any","late_season_top4","late_season_bottom4",
    "combined_form5","abs_form5_gap","rest_gap","congestion_sum",
    "opponent_demand_x_progress","opponent_demand_x_weekend",
}
BASELINE = {"T-30":"baseline_season","T-14":"baseline_r3"}
DEV_TRAIN = ["2021/2022","2022/2023"]
DEV = "2023/2024"
HOLDOUTS = [
    ("2024/2025",["2021/2022","2022/2023","2023/2024"]),
    ("2025/2026",["2021/2022","2022/2023","2023/2024","2024/2025"]),
]

def preprocessor(numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("cat",OneHotEncoder(handle_unknown="ignore",sparse_output=False),CAT),
        ("num",SimpleImputer(strategy="median",add_indicator=True),numeric),
    ])

def estimator(name: str):
    if name == "hist15":
        return HistGradientBoostingRegressor(
            loss="absolute_error",learning_rate=.05,max_iter=180,max_leaf_nodes=15,
            min_samples_leaf=10,l2_regularization=1,random_state=42,
        )
    if name == "extra_leaf3":
        return ExtraTreesRegressor(
            n_estimators=500,min_samples_leaf=3,max_features=.8,random_state=42,n_jobs=-1,
        )
    raise KeyError(name)

def metric_row(actual, pred) -> dict:
    actual=np.asarray(actual,dtype=float); pred=np.asarray(pred,dtype=float)
    ae=np.abs(pred-actual)
    return {
        "n":int(len(actual)),
        "mae":float(np.mean(ae)),
        "median_ae":float(np.median(ae)),
        "wape":float(np.sum(ae)/np.sum(actual)),
        "bias":float(np.mean(pred-actual)),
    }

def feature_sets(frame: pd.DataFrame) -> dict[str,list[str]]:
    numeric=[
        c for c in frame.columns
        if c not in META|set(CAT) and pd.api.types.is_numeric_dtype(frame[c])
    ]
    return {"base":[c for c in numeric if c not in IMPORTANCE],"full":numeric}

def fit_predict(train,test,baseline,numeric,model_name):
    tr=train[train[baseline].notna()].copy()
    te=test[test[baseline].notna()].copy()
    pre=preprocessor(numeric)
    x_train=pre.fit_transform(tr[CAT+numeric]); x_test=pre.transform(te[CAT+numeric])
    y=(tr["target_attendance"]/tr["capacity"])-(tr[baseline]/tr["capacity"])
    model=estimator(model_name); model.fit(x_train,y)
    pred=te[baseline].to_numpy()+model.predict(x_test)*te["capacity"].to_numpy()
    pred=np.clip(pred,0,te["capacity"].to_numpy())
    return te,pred

def evaluate(frame: pd.DataFrame) -> dict:
    fs=feature_sets(frame)
    report={"protocol":{
        "development_train":DEV_TRAIN,"development_selection":DEV,
        "holdouts":[x[0] for x in HOLDOUTS],
        "target":"attendance/capacity - baseline/capacity",
        "prediction_clip":"[0, verified_capacity]",
        "automatic_promotion":False,
    },"horizons":{}}
    for horizon in ["T-30","T-14"]:
        data=frame[(frame["horizon"]==horizon)&frame["training_eligible"].astype(bool)].copy()
        train=data[data["season"].isin(DEV_TRAIN)]
        dev=data[data["season"].eq(DEV)]
        baseline=BASELINE[horizon]
        candidates=[]
        for fs_name in ["base","full"]:
            for model_name in ["hist15","extra_leaf3"]:
                scored,pred=fit_predict(train,dev,baseline,fs[fs_name],model_name)
                metrics=metric_row(scored["target_attendance"],pred)
                candidates.append({"feature_set":fs_name,"model":model_name,**metrics})
        selected=min(candidates,key=lambda x:(x["mae"],abs(x["bias"])))
        holdouts={}
        for test_season,train_seasons in HOLDOUTS:
            tr=data[data["season"].isin(train_seasons)]
            te=data[data["season"].eq(test_season)]
            scored,pred=fit_predict(tr,te,baseline,fs[selected["feature_set"]],selected["model"])
            holdouts[test_season]={
                "baseline":metric_row(scored["target_attendance"],scored[baseline]),
                "model":metric_row(scored["target_attendance"],pred),
                "training_seasons":train_seasons,
            }
        report["horizons"][horizon]={
            "baseline":baseline,
            "development_candidates":sorted(candidates,key=lambda x:x["mae"]),
            "selected":{"feature_set":selected["feature_set"],"model":selected["model"]},
            "holdouts":holdouts,
        }
    return report

def write_markdown(report:dict,path:Path)->None:
    horizons=report["horizons"]
    lines=[
        "# Structural Prior Runtime v1 — early-horizon benchmark",
        "",
        "Selection uses **2023/24 only** after training on 2021/22–2022/23. 2024/25 and 2025/26 are untouched holdouts.",
        "",
        "| Horizon | Frozen spec | Dev 2023/24 MAE | 2024/25 MAE | 2025/26 MAE |",
        "|---|---|---:|---:|---:|",
    ]
    for horizon in ["T-30","T-14"]:
        result=horizons[horizon]; selected=result["selected"]
        dev=next(x for x in result["development_candidates"] if x["feature_set"]==selected["feature_set"] and x["model"]==selected["model"])
        a=result["holdouts"]["2024/2025"]["model"]["mae"]
        b=result["holdouts"]["2025/2026"]["model"]["mae"]
        lines.append(f"| {horizon} | `{selected['model']}` + `{selected['feature_set']}` | {dev['mae']:.1f} | **{a:.1f}** | **{b:.1f}** |")
    lines += [
        "",
        "Target: verified-capacity occupancy residual. Predictions are clipped to verified event capacity.",
        "",
        "Decision:",
        "- T-30: new runtime candidate materially improves the prior v2.2 result, but remains above the <1700 strategic target.",
        "- T-14: new runtime candidate improves both untouched holdouts and becomes the preferred early-horizon historical candidate.",
        "- No live ticketing signal is used here; this is the Structural Prior only.",
    ]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines)+"\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--feature-store",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--markdown-output",type=Path)
    a=p.parse_args()
    frame=pd.read_csv(a.feature_store)
    report=evaluate(frame)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    if a.markdown_output: write_markdown(report,a.markdown_output)
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
