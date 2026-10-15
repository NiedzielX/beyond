#!/usr/bin/env python3
"""Five-season point-in-time feature builder for Beyond Structural Prior v1.

Consumes the validated 2021/22-2024/25 and 2025/26 canonical match CSVs and
emits exactly one snapshot per match/horizon. Demand history may carry across
seasons; sporting state is strictly season-local. Match state is applied only
after kickoff + 3h, so a target never enters its own feature state.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

SEASONS = ["2021/2022","2022/2023","2023/2024","2024/2025","2025/2026"]
HORIZONS = {"T-30":30,"T-14":14,"T-7":7,"T-3":3,"T-1":1}
WARSAW_TZ = "Europe/Warsaw"
COMPLETION_BUFFER_HOURS = 3
FEATURE_SET_VERSION = "structural-prior-pit-v1"

CAPACITY_MAPS = {
"2021/2022":{"termalica":4666,"cracovia":15114,"gornik_leczna":7464,"gornikzabrze":24563,"jagiellonia":22432,"lech":43269,"lechiagdansk":43615,"legia":31800,"piastgliwice":10037,"pogonszczecin":9300,"radomiak_radom":4501,"rakow":5500,"stal_mielec":6864,"slask_wroclaw":45105,"warta_poznan":5383,"wisla_krakow":33326,"wisla_plock":3500,"zaglebie_lubin":16068},
"2022/2023":{"cracovia":15114,"gornikzabrze":24563,"jagiellonia":22432,"koronakielce":15550,"lech":43269,"lechiagdansk":43615,"legia":31800,"miedz_legnica":6864,"piastgliwice":10037,"pogonszczecin":21163,"radomiak_radom":4501,"rakow":5500,"stal_mielec":6864,"slask_wroclaw":45105,"warta_poznan":5383,"widzewlodz":18018,"wisla_plock":4300,"zaglebie_lubin":16068},
"2023/2024":{"cracovia":15114,"gornikzabrze":24563,"jagiellonia":22432,"koronakielce":15550,"lech":43269,"legia":31800,"lks_lodz":18029,"piastgliwice":10037,"pogonszczecin":21163,"puszcza_niepolomice":15114,"radomiak_radom":8840,"rakow":5500,"stal_mielec":6864,"slask_wroclaw":45105,"warta_poznan":5383,"widzewlodz":18018,"zaglebie_lubin":16068},
"2024/2025":{"cracovia":15016,"gornikzabrze":24563,"jagiellonia":22372,"koronakielce":15700,"lech":42837,"lechiagdansk":41620,"legia":31006,"motorlublin":15247,"piastgliwice":9913,"pogonszczecin":21163,"radomiak_radom":8840,"rakow":5500,"stal_mielec":7000,"slask_wroclaw":42771,"widzewlodz":18018,"zaglebie_lubin":16086},
"2025/2026":{"arkagdynia":15139,"termalica":4666,"cracovia":15016,"gkskatowice":15048,"gornikzabrze":28236,"jagiellonia":22372,"koronakielce":15700,"lech":42837,"lechiagdansk":41620,"legia":31006,"motorlublin":15247,"piastgliwice":9913,"pogonszczecin":21163,"radomiak_radom":14440,"rakow":5500,"widzewlodz":18018,"wisla_plock":15004,"zaglebie_lubin":16086},
}

COMMON_COLUMNS = [
    "season","round","date","kickoff_time_local","home_team","away_team",
    "home_club_key","away_club_key","home_goals","away_goals","attendance","match_key",
]

IMPORTANCE_COLUMNS = {
    "combined_ppg","abs_ppg_gap","abs_position_gap","combined_table_strength",
    "top4_any","top4_both","bottom4_any","late_season_top4","late_season_bottom4",
    "combined_form5","abs_form5_gap","rest_gap","congestion_sum",
    "opponent_demand_x_progress","opponent_demand_x_weekend",
}

def capacity_for(row: dict) -> int | None:
    season = row["season"]
    home = row["home_club_key"]
    date = pd.Timestamp(row["date"])
    round_no = int(row["round"])
    if season == "2023/2024" and home == "ruch_chorzow":
        return 10037 if round_no <= 12 else 55211
    if season == "2024/2025" and home == "gkskatowice":
        return 6710 if date < pd.Timestamp("2025-03-30") else 15048
    if season == "2024/2025" and home == "puszcza_niepolomice":
        return 15016 if date < pd.Timestamp("2025-03-02") else 2000
    return CAPACITY_MAPS.get(season, {}).get(home)

def load_historical(old_path: Path, new_path: Path) -> pd.DataFrame:
    old = pd.read_csv(old_path)
    new = pd.read_csv(new_path)
    missing_old = sorted(set(COMMON_COLUMNS) - set(old.columns))
    missing_new = sorted(set(COMMON_COLUMNS) - set(new.columns))
    if missing_old or missing_new:
        raise RuntimeError(f"Missing columns old={missing_old} new={missing_new}")
    data = pd.concat([old[COMMON_COLUMNS], new[COMMON_COLUMNS]], ignore_index=True)
    data["round"] = data["round"].astype(int)
    data["date"] = pd.to_datetime(data["date"])
    local = pd.to_datetime(
        data["date"].dt.strftime("%Y-%m-%d") + " " + data["kickoff_time_local"].astype(str),
        format="mixed",
    )
    data["kickoff_at"] = (
        local.dt.tz_localize(WARSAW_TZ, ambiguous="raise", nonexistent="raise").dt.tz_convert("UTC")
    )
    data["completed_at"] = data["kickoff_at"] + pd.Timedelta(hours=COMPLETION_BUFFER_HOURS)
    data = data.sort_values(["kickoff_at","home_club_key"]).reset_index(drop=True)
    data["training_eligible"] = ~data["attendance"].eq(0)
    return data

def calendar_features(kickoff_utc: pd.Timestamp, round_no: int) -> dict:
    local = kickoff_utc.tz_convert(WARSAW_TZ)
    month = int(local.month); weekday = int(local.weekday())
    minutes = int(local.hour * 60 + local.minute); doy = int(local.dayofyear)
    return {
        "round_no": int(round_no),
        "season_progress": (int(round_no)-1)/33.0,
        "month": month, "weekday": weekday, "kickoff_minutes": minutes,
        "is_weekend": int(weekday >= 5),
        "month_sin": float(np.sin(2*np.pi*month/12.0)),
        "month_cos": float(np.cos(2*np.pi*month/12.0)),
        "doy_sin": float(np.sin(2*np.pi*doy/365.25)),
        "doy_cos": float(np.cos(2*np.pi*doy/365.25)),
        "kickoff_sin": float(np.sin(2*np.pi*minutes/1440.0)),
        "kickoff_cos": float(np.cos(2*np.pi*minutes/1440.0)),
    }

def history_stats(values, times, as_of_at: pd.Timestamp) -> dict:
    values = list(values)
    if not values:
        return dict(n=0,mean=np.nan,median=np.nan,last=np.nan,r3=np.nan,r5=np.nan,r10=np.nan,
                    std=np.nan,p90=np.nan,days_since=np.nan)
    arr = np.asarray(values, dtype=float)
    return {
        "n": len(arr), "mean": float(arr.mean()), "median": float(np.median(arr)),
        "last": float(arr[-1]), "r3": float(arr[-3:].mean()),
        "r5": float(arr[-5:].mean()), "r10": float(arr[-10:].mean()),
        "std": float(arr.std(ddof=0)) if len(arr)>1 else 0.0,
        "p90": float(np.quantile(arr,0.9)),
        "days_since": float((as_of_at-times[-1]).total_seconds()/86400.0),
    }

def match_points(gf: int, ga: int) -> int:
    return 3 if gf > ga else (1 if gf == ga else 0)

def build_feature_store(data: pd.DataFrame) -> pd.DataFrame:
    if data["match_key"].nunique() != 1530:
        raise RuntimeError(f"Expected 1530 unique matches, got {data['match_key'].nunique()}")
    home_vals=defaultdict(list); home_times=defaultdict(list)
    season_home_vals=defaultdict(list); season_home_times=defaultdict(list)
    opp_ratios=defaultdict(list); opp_raw=defaultdict(list)
    pair_ratios=defaultdict(list); pair_raw=defaultdict(list)
    league_attendance=[]
    sport=defaultdict(lambda:{
        "played":0,"points":0.0,"gf":0.0,"ga":0.0,
        "last5":deque(maxlen=5),"last_kickoff":None,"match_times":deque()
    })
    prev_season={SEASONS[i]:SEASONS[i-1] if i>0 else None for i in range(len(SEASONS))}
    events=[]
    for idx,row in data.iterrows():
        for horizon,days in HORIZONS.items():
            events.append((row["kickoff_at"]-pd.Timedelta(days=days),0,"snapshot",(idx,horizon)))
        events.append((row["completed_at"],1,"complete",idx))
    events.sort(key=lambda x:(x[0],x[1]))
    rows=[]
    for timestamp,_,event_type,payload in events:
        if event_type=="complete":
            row=data.iloc[payload]
            season=row["season"]; home=row["home_club_key"]; away=row["away_club_key"]
            if row["attendance"]>0:
                prior_mean=np.mean(home_vals[home]) if home_vals[home] else np.nan
                ratio=float(row["attendance"])/prior_mean if prior_mean and not np.isnan(prior_mean) else np.nan
                if not np.isnan(ratio):
                    opp_ratios[away].append(ratio)
                    pair_ratios[(home,away)].append(ratio)
                opp_raw[away].append(float(row["attendance"]))
                pair_raw[(home,away)].append(float(row["attendance"]))
                home_vals[home].append(float(row["attendance"])); home_times[home].append(row["kickoff_at"])
                season_home_vals[(season,home)].append(float(row["attendance"]))
                season_home_times[(season,home)].append(row["kickoff_at"])
                league_attendance.append(float(row["attendance"]))
            for club,gf,ga in [
                (home,int(row["home_goals"]),int(row["away_goals"])),
                (away,int(row["away_goals"]),int(row["home_goals"]))
            ]:
                state=sport[(season,club)]
                pts=match_points(gf,ga)
                state["played"]+=1; state["points"]+=pts; state["gf"]+=gf; state["ga"]+=ga
                state["last5"].append((pts,gf-ga)); state["last_kickoff"]=row["kickoff_at"]
                state["match_times"].append(row["kickoff_at"])
            continue

        idx,horizon=payload
        row=data.iloc[idx]
        season=row["season"]; home=row["home_club_key"]; away=row["away_club_key"]; as_of=timestamp
        hstat=history_stats(home_vals[home],home_times[home],as_of)
        shstat=history_stats(season_home_vals[(season,home)],season_home_times[(season,home)],as_of)
        prev=prev_season[season]
        prev_values=season_home_vals[(prev,home)] if prev else []
        prev_mean=float(np.mean(prev_values)) if prev_values else np.nan
        league_median=float(np.median(league_attendance)) if league_attendance else np.nan

        baseline_r3=hstat["r3"]; baseline_r5=hstat["r5"]; baseline_mean=hstat["mean"]
        baseline_season=shstat["mean"] if shstat["n"]>0 else (
            hstat["mean"] if hstat["n"]>0 else league_median
        )

        def team_features(club):
            state=sport[(season,club)]
            played=state["played"]; last5=list(state["last5"])
            n14=sum(1 for t in state["match_times"] if t>=as_of-pd.Timedelta(days=14))
            return {
                "matches_played": played, "points": state["points"],
                "ppg": state["points"]/played if played else np.nan,
                "gdpg": (state["gf"]-state["ga"])/played if played else np.nan,
                "form5_points": sum(x[0] for x in last5) if last5 else np.nan,
                "form5_gd": sum(x[1] for x in last5) if last5 else np.nan,
                "days_since_last": float((as_of-state["last_kickoff"]).total_seconds()/86400.0)
                    if state["last_kickoff"] is not None else np.nan,
                "matches_last14": n14,
            }
        home_f=team_features(home); away_f=team_features(away)

        clubs={club for ss,club in sport.keys() if ss==season}
        table=[]
        for club in clubs:
            st=sport[(season,club)]
            table.append((club,st["points"],st["gf"]-st["ga"],st["gf"]))
        table=sorted(table,key=lambda x:(-x[1],-x[2],-x[3],x[0]))
        positions={club:i+1 for i,(club,*_) in enumerate(table)}
        home_pos=positions.get(home,np.nan); away_pos=positions.get(away,np.nan)

        opponent_ratios=opp_ratios[away]; pair_ratio_values=pair_ratios[(home,away)]
        opponent_raw=opp_raw[away]; pair_raw_values=pair_raw[(home,away)]
        capacity=capacity_for(row.to_dict())
        if capacity is None:
            raise RuntimeError(f"Missing capacity for {row['match_key']}")

        out={
            "feature_set_version":FEATURE_SET_VERSION,
            "match_key":row["match_key"],"season":season,"horizon":horizon,
            "as_of_at":as_of,"kickoff_at":row["kickoff_at"],
            "home_club_key":home,"away_club_key":away,
            "target_attendance":float(row["attendance"]),
            "target_eligible":bool(row["training_eligible"]),
            "capacity":float(capacity),
            **calendar_features(row["kickoff_at"],row["round"]),
            "home_history_n":hstat["n"],"home_attendance_mean":hstat["mean"],
            "home_attendance_median":hstat["median"],"home_attendance_last":hstat["last"],
            "home_attendance_rolling3":hstat["r3"],"home_attendance_rolling5":hstat["r5"],
            "home_attendance_rolling10":hstat["r10"],"home_attendance_std":hstat["std"],
            "home_attendance_p90":hstat["p90"],
            "home_attendance_trend3_vs_mean":hstat["r3"]/hstat["mean"]
                if hstat["mean"] and not np.isnan(hstat["mean"]) else np.nan,
            "days_since_last_home":hstat["days_since"],
            "season_home_n":shstat["n"],"season_home_mean":shstat["mean"],
            "season_home_last":shstat["last"],"season_home_r3":shstat["r3"],
            "season_vs_long_ratio":shstat["mean"]/hstat["mean"]
                if shstat["mean"] and hstat["mean"] and not np.isnan(shstat["mean"]) and not np.isnan(hstat["mean"]) else np.nan,
            "prev_season_home_mean":prev_mean,
            "home_demand_vs_league_median":hstat["mean"]/league_median
                if hstat["mean"] and league_median and not np.isnan(hstat["mean"]) else np.nan,
            "opponent_draw_n":len(opponent_ratios),
            "opponent_draw_ratio_mean":float(np.mean(opponent_ratios)) if opponent_ratios else np.nan,
            "opponent_draw_ratio_recent3":float(np.mean(opponent_ratios[-3:])) if opponent_ratios else np.nan,
            "opponent_raw_attendance_mean":float(np.mean(opponent_raw)) if opponent_raw else np.nan,
            "pair_n":len(pair_ratio_values),
            "pair_ratio_mean":float(np.mean(pair_ratio_values)) if pair_ratio_values else np.nan,
            "pair_ratio_recent2":float(np.mean(pair_ratio_values[-2:])) if pair_ratio_values else np.nan,
            "pair_attendance_mean":float(np.mean(pair_raw_values)) if pair_raw_values else np.nan,
            "baseline_r3":baseline_r3,"baseline_r5":baseline_r5,
            "baseline_mean":baseline_mean,"baseline_season":baseline_season,
        }
        for prefix,features in [("home",home_f),("away",away_f)]:
            for key,value in features.items():
                out[f"{prefix}_{key}"]=value
        out["home_position"]=home_pos; out["away_position"]=away_pos
        out["position_gap"]=away_pos-home_pos if not(pd.isna(home_pos) or pd.isna(away_pos)) else np.nan
        out["ppg_gap"]=home_f["ppg"]-away_f["ppg"] if not(pd.isna(home_f["ppg"]) or pd.isna(away_f["ppg"])) else np.nan
        out["form5_points_gap"]=home_f["form5_points"]-away_f["form5_points"] if not(pd.isna(home_f["form5_points"]) or pd.isna(away_f["form5_points"])) else np.nan
        out["gdpg_gap"]=home_f["gdpg"]-away_f["gdpg"] if not(pd.isna(home_f["gdpg"]) or pd.isna(away_f["gdpg"])) else np.nan

        out["combined_ppg"]=home_f["ppg"]+away_f["ppg"] if not(pd.isna(home_f["ppg"]) or pd.isna(away_f["ppg"])) else np.nan
        out["abs_ppg_gap"]=abs(out["ppg_gap"]) if not pd.isna(out["ppg_gap"]) else np.nan
        out["abs_position_gap"]=abs(out["position_gap"]) if not pd.isna(out["position_gap"]) else np.nan
        out["combined_table_strength"]=home_pos+away_pos if not(pd.isna(home_pos) or pd.isna(away_pos)) else np.nan
        out["top4_any"]=int((not pd.isna(home_pos) and home_pos<=4) or (not pd.isna(away_pos) and away_pos<=4))
        out["top4_both"]=int((not pd.isna(home_pos) and home_pos<=4) and (not pd.isna(away_pos) and away_pos<=4))
        out["bottom4_any"]=int((not pd.isna(home_pos) and home_pos>=15) or (not pd.isna(away_pos) and away_pos>=15))
        out["late_season_top4"]=out["season_progress"]*out["top4_any"]
        out["late_season_bottom4"]=out["season_progress"]*out["bottom4_any"]
        out["combined_form5"]=home_f["form5_points"]+away_f["form5_points"] if not(pd.isna(home_f["form5_points"]) or pd.isna(away_f["form5_points"])) else np.nan
        out["abs_form5_gap"]=abs(out["form5_points_gap"]) if not pd.isna(out["form5_points_gap"]) else np.nan
        out["rest_gap"]=home_f["days_since_last"]-away_f["days_since_last"] if not(pd.isna(home_f["days_since_last"]) or pd.isna(away_f["days_since_last"])) else np.nan
        out["congestion_sum"]=home_f["matches_last14"]+away_f["matches_last14"]
        out["opponent_demand_x_progress"]=out["opponent_draw_ratio_mean"]*out["season_progress"] if not pd.isna(out["opponent_draw_ratio_mean"]) else np.nan
        out["opponent_demand_x_weekend"]=out["opponent_draw_ratio_mean"]*out["is_weekend"] if not pd.isna(out["opponent_draw_ratio_mean"]) else np.nan
        rows.append(out)
    store=pd.DataFrame(rows)
    store["training_eligible"]=store["target_eligible"] & (store["home_history_n"]>=3)
    return store.sort_values(["as_of_at","match_key","horizon"]).reset_index(drop=True)

def quality_report(store: pd.DataFrame) -> dict:
    by_season_horizon=store.groupby(["season","horizon"]).size().unstack(fill_value=0)
    invalid_time=int((pd.to_datetime(store["as_of_at"],utc=True)>=pd.to_datetime(store["kickoff_at"],utc=True)).sum())
    failures=[]
    if len(store)!=7650: failures.append(f"expected 7650 snapshots, got {len(store)}")
    if store["match_key"].nunique()!=1530: failures.append(f"expected 1530 matches, got {store['match_key'].nunique()}")
    if store["capacity"].isna().any(): failures.append("missing capacity")
    if invalid_time: failures.append(f"{invalid_time} snapshots at/after kickoff")
    for season in SEASONS:
        for horizon in HORIZONS:
            if int(by_season_horizon.loc[season,horizon])!=306:
                failures.append(f"{season}/{horizon} != 306")
    return {
        "feature_set_version":FEATURE_SET_VERSION,
        "rows":int(len(store)),
        "matches":int(store["match_key"].nunique()),
        "training_eligible_rows":int(store["training_eligible"].sum()),
        "capacity_missing":int(store["capacity"].isna().sum()),
        "invalid_time_rows":invalid_time,
        "rows_by_season_horizon":{s:{h:int(by_season_horizon.loc[s,h]) for h in HORIZONS} for s in SEASONS},
        "status":"PASS" if not failures else "FAIL",
        "failures":failures,
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--historical-2021-25",type=Path,required=True)
    p.add_argument("--historical-2025-26",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    data=load_historical(a.historical_2021_25,a.historical_2025_26)
    store=build_feature_store(data)
    report=quality_report(store)
    a.output.parent.mkdir(parents=True,exist_ok=True); store.to_csv(a.output,index=False)
    a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if report["status"]!="PASS": raise SystemExit("feature store quality gate failed")

if __name__=="__main__":
    main()
