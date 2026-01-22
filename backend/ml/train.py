from __future__ import annotations
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier

from .features import (
    SemesterIndexConfig, SEM_ORDER,
    parse_time_range, get_building, section_to_course_code, make_slot, has_ge
)
#idk why I did relative for python -m backend.ml.train


# Adjust paths if needed (prob broken I didn't relaly check)
REPO_ROOT = Path(__file__).resolve().parents[2]          # .../backend/ml/train.py -> repo root
DATA_DIR = REPO_ROOT / "data" / "csv_data"             
OUT_DIR = REPO_ROOT / "backend" / "ml_artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CAT_AB = ["Dept", "CourseCode", "Mode", "Type", "Semester", "Building"]
NUM_AB = ["Unit", "Year", "SemesterIndex", "DurationMinutes", "HasGE"]

CAT_C = ["Instructor", "Mode", "Type", "Semester", "Building"]
NUM_C = ["Year", "SemesterIndex"]

def make_pipeline(cat_cols: list[str], num_cols: list[str]) -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )
    model = RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=42)
    return Pipeline([("pre", pre), ("rf", model)])

def load_raw() -> pd.DataFrame:
    csvs = sorted(DATA_DIR.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSVs found in {DATA_DIR}")
    df = pd.concat([pd.read_csv(p) for p in csvs], ignore_index=True)
    df["Satifies"] = df["Satifies"].fillna("MajorOnly")
    df["Location"] = df["Location"].fillna("Unknown")
    return df

def engineer(df: pd.DataFrame) -> tuple[pd.DataFrame, SemesterIndexConfig]:
    base_val = (df["Year"].astype(int) * 2 + df["Semester"].map(SEM_ORDER).fillna(0).astype(int)).min()
    sem_cfg = SemesterIndexConfig(base=int(base_val))

    # CourseCode
    dept_course = df["Section"].astype(str).str.strip().str.extract(r"^(\w+)\s+([^\s]+)")
    df["Dept"] = dept_course[0].fillna("Unknown")
    df["CourseNumber"] = dept_course[1].fillna("Unknown")
    df["CourseCode"] = df["Dept"].astype(str) + " " + df["CourseNumber"].astype(str)

    # time features
    t = df["Times"].apply(lambda s: pd.Series(parse_time_range(str(s))))
    df["StartMinutes"] = t[0]
    df["EndMinutes"] = t[1]
    df["DurationMinutes"] = t[2]

    # Slot, Building, HasGE
    df["Slot"] = [make_slot(d, sm) for d, sm in zip(df["Days"], df["StartMinutes"])]
    df["Building"] = df["Location"].apply(get_building)
    df["HasGE"] = df["Satifies"].apply(has_ge)

    # SemesterIndex formula
    df["SemesterIndex"] = (df["Year"].astype(int) * 2 + df["Semester"].map(SEM_ORDER).fillna(0).astype(int)) - sem_cfg.base

    return df, sem_cfg

def main():
    df = load_raw()
    df, sem_cfg = engineer(df)

    # same split as notebook (last two terms)
    all_terms = sorted(df["SemesterIndex"].unique())
    test_terms = all_terms[-2:]
    train_mask = ~df["SemesterIndex"].isin(test_terms)

    # Train targets as STRINGS => API returns human-readable labels directly
    pipe_A = make_pipeline(CAT_AB, NUM_AB)
    pipe_A.fit(df.loc[train_mask, CAT_AB + NUM_AB], df.loc[train_mask, "Instructor"].astype(str))

    pipe_B = make_pipeline(CAT_AB, NUM_AB)
    pipe_B.fit(df.loc[train_mask, CAT_AB + NUM_AB], df.loc[train_mask, "Slot"].astype(str))

    pipe_C = make_pipeline(CAT_C, NUM_C)
    pipe_C.fit(df.loc[train_mask, CAT_C + NUM_C], df.loc[train_mask, "CourseCode"].astype(str))

    joblib.dump({"pipeline": pipe_A, "sem_cfg": sem_cfg, "cat": CAT_AB, "num": NUM_AB},
                OUT_DIR / "scenario_A_instructor.joblib")
    joblib.dump({"pipeline": pipe_B, "sem_cfg": sem_cfg, "cat": CAT_AB, "num": NUM_AB},
                OUT_DIR / "scenario_B_slot.joblib")
    joblib.dump({"pipeline": pipe_C, "sem_cfg": sem_cfg, "cat": CAT_C, "num": NUM_C},
                OUT_DIR / "scenario_C_course.joblib")

    print("Saved ML artifacts to:", OUT_DIR)

if __name__ == "__main__":
    main()
