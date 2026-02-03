from __future__ import annotations
from pathlib import Path
import re
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

# Paths
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "csv_data"
OUT_DIR = REPO_ROOT / "backend" / "ml_artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def norm_slot(d, t):
    return f"{re.sub('\\s+', '', str(d))}|{str(t).strip()}"


def load_and_prepare():
    """Load CSVs and perform data engineering up through notebook section 4f.

    Returns `df_engineer` containing engineered columns including `Slot`,
    `HasGE`, `Building`, `Term`, and `SemesterIndex`.
    """
    csvs = sorted(DATA_DIR.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSVs found in {DATA_DIR}")
    df = pd.concat([pd.read_csv(p, engine="python") for p in csvs], ignore_index=True)

    # Ensure string types and basic columns exist
    df["Section"] = df.get("Section", pd.Series([pd.NA] * len(df))).astype(str).str.strip()
    for c in ["Mode", "Type", "Days", "Times", "Instructor", "Year", "Semester", "Location", "Satifies", "Title", "Unit"]:
        if c not in df.columns:
            df[c] = pd.NA

    # Start engineering
    df_engineer = df.copy()

    # 4a. Section -> Dept, CourseNumber, CourseCode
    section = df_engineer["Section"].str.extract(r"^(\w+)\s+([^\s]+)")
    df_engineer["Dept"] = section[0]
    df_engineer["CourseNumber"] = section[1]
    df_engineer["CourseCode"] = df_engineer["Dept"].astype(str) + " " + df_engineer["CourseNumber"].astype(str)

    # 4b. Times -> StartMinutes, EndMinutes, DurationMinutes
    def parse_time_range(s):
        try:
            if s == "TBA" or "-" not in str(s):
                return -1, -1, -1
            start_str, end_str = str(s).split("-")
            start_dt = pd.to_datetime(start_str, format="%I:%M%p")
            end_dt = pd.to_datetime(end_str, format="%I:%M%p")
            start_min = start_dt.hour * 60 + start_dt.minute
            end_min = end_dt.hour * 60 + end_dt.minute
            return start_min, end_min, end_min - start_min
        except Exception:
            return -1, -1, -1

    df_engineer[["StartMinutes", "EndMinutes", "DurationMinutes"]] = df_engineer["Times"].apply(
        lambda s: pd.Series(parse_time_range(s))
    )

    # 4c. Slot from Days + StartMinutes/EndMinutes
    def make_slot(row):
        days = str(row.get("Days", "")).strip()
        start = int(row.get("StartMinutes", -1))
        end = int(row.get("EndMinutes", -1))
        if start == -1 or end == -1:
            return days + "_TBA"
        return f"{days}_{start}_{end}"

    df_engineer["Slot"] = df_engineer.apply(make_slot, axis=1)

    # 4d. HasGE from Satifies
    df_engineer["HasGE"] = df_engineer["Satifies"].astype(str).str.startswith("GE:").astype(int)

    # 4e. Building from Location
    def get_building(location):
        location = str(location).strip()
        if location in ["ONLINE", "Unknown"]:
            return location
        prefix = ""
        for ch in location:
            if ch.isalpha():
                prefix += ch
            else:
                break
        return prefix if prefix else "Unknown"

    df_engineer["Building"] = df_engineer["Location"].apply(get_building)

    # 4e (term): Term column
    df_engineer["Term"] = df_engineer["Year"].astype(str) + "_" + df_engineer["Semester"].astype(str)

    # 4f. SemesterIndex: sort (Year, Semester) and assign 0..N-1
    sem_order = {"Spring": 0, "Fall": 1}
    term_df = (
        df_engineer[["Year", "Semester"]]
        .drop_duplicates()
        .copy()
    )
    term_df["sem_order"] = term_df["Semester"].map(sem_order)
    term_df = term_df.sort_values(["Year", "sem_order"]).reset_index(drop=True)
    term_df["SemesterIndex"] = term_df.index
    df_engineer = df_engineer.merge(
        term_df[["Year", "Semester", "SemesterIndex"]],
        on=["Year", "Semester"],
        how="left",
    )

    return df_engineer


def train_svm_term_agnostic(df_engineer: pd.DataFrame):
    """Train a term-agnostic SVM model to predict whether a course combo was ever scheduled.

    This follows the notebook's "term agnostic" section but trains only a calibrated
    Linear SVM (so we get predicted probabilities).
    """
    df_combined = df_engineer.copy()
    df_combined["Scheduled"] = 1

    # key columns for a "complete course"             I had to add dept to make negative sampling work better
    key_cols = ["CourseCode", "Instructor", "Slot", "Type", "Dept"]

    pos_raw = df_combined.copy()
    pos = (
        pos_raw[key_cols]
        .dropna(subset=key_cols)
        .drop_duplicates()
        .reset_index(drop=True)
    )
    pos["ScheduledEver"] = 1
    pos_keys = set(map(tuple, pos[key_cols].values))

    # pools for generating negatives
    instr_pool = (
        pos[["Dept", "Instructor"]]
        .drop_duplicates()
        .groupby("Dept")["Instructor"]
        .apply(list)
    )
    slot_pool = (
        pos[["CourseCode", "Type", "Slot"]]
        .drop_duplicates()
        .groupby(["CourseCode", "Type"])["Slot"]
        .apply(list)
    )

    rng = np.random.default_rng(42)
    K = 3
    neg_rows = []
    for _, row in pos.iterrows():
        dept = row["Dept"] if "Dept" in row else None
        course = row["CourseCode"]
        typ = row["Type"]
        instr = row["Instructor"]
        slot = row["Slot"]

        i_pool = instr_pool.get(dept, []) if dept is not None else []
        s_pool = slot_pool.get((course, typ), [])
        if len(i_pool) < 2 and len(s_pool) < 2:
            continue

        generated = 0
        tries = 0
        MAX_TRIES = 25 * K
        while generated < K and tries < MAX_TRIES:
            tries += 1
            new = row.copy()
            r = rng.random()
            if r < 0.5 and len(i_pool) >= 2:
                choices = [i for i in i_pool if i != instr]
                if not choices:
                    continue
                new["Instructor"] = rng.choice(choices)
            elif r < 0.9 and len(s_pool) >= 2:
                choices = [s for s in s_pool if s != slot]
                if not choices:
                    continue
                new["Slot"] = rng.choice(choices)
            else:
                if len(i_pool) >= 2:
                    choices_i = [i for i in i_pool if i != instr]
                    if not choices_i:
                        continue
                    new["Instructor"] = rng.choice(choices_i)
                if len(s_pool) >= 2:
                    choices_s = [s for s in s_pool if s != slot]
                    if not choices_s:
                        continue
                    new["Slot"] = rng.choice(choices_s)

            key = (new["CourseCode"], new["Instructor"], new["Slot"], new["Type"])
            if key in pos_keys:
                continue
            new["ScheduledEver"] = 0
            neg_rows.append(new[key_cols + ["ScheduledEver"]])
            generated += 1

    neg = pd.DataFrame(neg_rows).drop_duplicates(subset=key_cols).reset_index(drop=True)
    df_term_agnostic = pd.concat([pos[key_cols + ["ScheduledEver"]], neg[key_cols + ["ScheduledEver"]]], ignore_index=True).drop_duplicates()

    # interactions as in notebook
    df_term_agnostic["Course_Instructor"] = df_term_agnostic["CourseCode"].astype(str) + "||" + df_term_agnostic["Instructor"].astype(str)
    df_term_agnostic["Course_Slot"] = df_term_agnostic["CourseCode"].astype(str) + "||" + df_term_agnostic["Slot"].astype(str)
    df_term_agnostic["Instructor_Slot"] = df_term_agnostic["Instructor"].astype(str) + "||" + df_term_agnostic["Slot"].astype(str)
    df_term_agnostic["Course_Type"] = df_term_agnostic["CourseCode"].astype(str) + "||" + df_term_agnostic["Type"].astype(str)

    cat_cols = ["CourseCode", "Instructor", "Slot", "Type", "Course_Instructor", "Course_Slot", "Instructor_Slot", "Course_Type"]
    X = df_term_agnostic[cat_cols]
    y = df_term_agnostic["ScheduledEver"].astype(int)

    # simple train/test split (stratify)
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    preprocess = ColumnTransformer(transformers=[('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols)], remainder='drop')

    svm = LinearSVC(max_iter=2000, C=1.0, class_weight='balanced', random_state=42)
    clf = CalibratedClassifierCV(estimator=svm, method='sigmoid', cv=3)

    pipe = Pipeline(steps=[('prep', preprocess), ('clf', clf)])
    pipe.fit(X_train, y_train)

    # basic eval
    try:
        proba = pipe.predict_proba(X_test)[:, 1]
        from sklearn.metrics import roc_auc_score, average_precision_score
        print("ROC AUC:", roc_auc_score(y_test, proba))
        print("PR AUC :", average_precision_score(y_test, proba))
    except Exception:
        print("Trained SVM but couldn't compute probabilistic metrics")

    # persist (unique name so it doesn't clash with `train.py` artifacts)
    artifact_path = OUT_DIR / 'train2_anthony_svm.joblib'
    joblib.dump({'model': pipe, 'features': cat_cols}, artifact_path)
    print("Saved SVM artifact to:", artifact_path)


# Functions to load Anthony's pre-trained models and run predictions


def main():
    df = load_and_prepare()
    train_svm_term_agnostic(df)


if __name__ == "__main__":
    main()
