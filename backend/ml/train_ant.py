from __future__ import annotations
from pathlib import Path
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report
import re
import joblib
import numpy as np
import pandas as pd


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


# ---------------------------------------------------------------------------
# History-feature helpers (ported from notebook)
# ---------------------------------------------------------------------------

def _make_prior_count_table(
    df_pos: pd.DataFrame, group_cols: list[str], term_col: str, out_col: str
) -> pd.DataFrame:
    """Cumulative positives strictly BEFORE each (group, term) pair."""
    tmp = (
        df_pos.groupby(group_cols + [term_col])
        .size()
        .reset_index(name="n_in_term")
        .sort_values(term_col, kind="mergesort")
    )
    tmp[out_col] = tmp.groupby(group_cols)["n_in_term"].cumsum() - tmp["n_in_term"]
    return tmp[group_cols + [term_col, out_col]]


def _make_last_seen_term_table(
    df_pos: pd.DataFrame, group_cols: list[str], term_col: str, out_col: str
) -> pd.DataFrame:
    """Previous term (strictly before) where each group was last seen."""
    tmp = (
        df_pos[group_cols + [term_col]]
        .drop_duplicates()
        .sort_values(group_cols + [term_col], kind="mergesort")
    )
    tmp[out_col] = tmp.groupby(group_cols)[term_col].shift(1)
    return tmp[group_cols + [term_col, out_col]]


def add_history_features_no_leak(
    df_labeled: pd.DataFrame,
    df_pos_hist: pd.DataFrame,
    term_col: str = "SemesterIndex",
) -> pd.DataFrame:
    """Add 13 history/recency features to df_labeled without data leakage.

    df_labeled : full dataset (train + test, positives + negatives)
    df_pos_hist: ONLY positive rows from TRAIN terms — these are the allowed history

    For every row in df_labeled the features answer:
      "given everything that happened strictly before this row's term,
       how strong is the historical signal for this (course, instructor, slot, type) combo?"

    Uses pd.merge_asof(..., allow_exact_matches=False) so a row at term T
    can only see history from terms < T.  Test rows therefore see only
    train-term history, which is exactly what happens at production inference time.
    """
    df = df_labeled.copy()
    df[term_col] = df[term_col].astype(int)

    hist = df_pos_hist.copy()
    hist[term_col] = hist[term_col].astype(int)

    # Preserve original row order so we can restore it after merge_asof sorts.
    df["_row_id"] = np.arange(len(df))

    # ---- 9 PRIOR-COUNT FEATURES ----
    # Each counts how many times a group appeared in history before this term.
    count_defs = [
        (["Instructor"],                              "instr_prior_count"),
        (["CourseCode"],                              "course_prior_count"),
        (["Slot"],                                    "slot_prior_count"),
        (["CourseCode", "Type"],                      "course_type_prior_count"),
        (["Instructor", "Dept"],                      "instr_dept_prior_count"),
        (["Instructor", "CourseCode"],                "instr_course_prior_count"),
        (["CourseCode", "Slot"],                      "course_slot_prior_count"),
        (["CourseCode", "Type", "Slot"],              "course_type_slot_prior_count"),
        (["CourseCode", "Instructor", "Slot", "Type"], "combo_prior_count"),
    ]

    for group_cols, out_col in count_defs:
        tmp = (
            hist.groupby(group_cols + [term_col])
            .size()
            .reset_index(name="n_in_term")
            .sort_values(term_col, kind="mergesort")
        )
        tmp["cum_inclusive"] = tmp.groupby(group_cols)["n_in_term"].cumsum()
        lookup = tmp[group_cols + [term_col, "cum_inclusive"]].rename(
            columns={"cum_inclusive": out_col}
        )

        left = df.sort_values(term_col, kind="mergesort").reset_index(drop=True)
        right = lookup.sort_values(term_col, kind="mergesort").reset_index(drop=True)

        left = pd.merge_asof(
            left,
            right,
            on=term_col,
            by=group_cols,
            direction="backward",
            allow_exact_matches=False,  # strictly before this term
        )

        left[out_col] = left[out_col].fillna(0).astype(int)
        df = left.sort_values("_row_id", kind="mergesort").reset_index(drop=True)

    # ---- 4 RECENCY FEATURES ----
    # Each captures how many terms have elapsed since the group was last seen.
    recency_defs = [
        (["Instructor"],                              "instr_last_term"),
        (["CourseCode"],                              "course_last_term"),
        (["Instructor", "CourseCode"],                "instr_course_last_term"),
        (["CourseCode", "Instructor", "Slot", "Type"], "combo_last_term"),
    ]

    for group_cols, out_col in recency_defs:
        seen = (
            hist[group_cols + [term_col]]
            .drop_duplicates()
            .sort_values(term_col, kind="mergesort")
            .reset_index(drop=True)
        )
        seen[out_col] = seen[term_col]  # payload column for merge_asof
        seen = seen[group_cols + [term_col, out_col]]

        left = df.sort_values(term_col, kind="mergesort").reset_index(drop=True)
        right = seen.sort_values(term_col, kind="mergesort").reset_index(drop=True)

        left = pd.merge_asof(
            left,
            right,
            on=term_col,
            by=group_cols,
            direction="backward",
            allow_exact_matches=False,
        )

        left[out_col] = left[out_col].fillna(-1).astype(int)

        gap_col = out_col.replace("last_term", "terms_since")
        left[gap_col] = np.where(
            left[out_col] == -1,
            left[term_col] + 1,           # never seen before — use max possible gap
            left[term_col] - left[out_col],
        ).astype(int)

        df = left.sort_values("_row_id", kind="mergesort").reset_index(drop=True)

    # ---- LOG TRANSFORMS on count columns ----
    # LinearSVC and most linear models benefit from compressing count skew (0,1,200…).
    count_cols = [c for c in df.columns if c.endswith("_prior_count")]
    for c in count_cols:
        df[c + "_log1p"] = np.log1p(df[c].astype(float))

    df.drop(columns=["_row_id"], inplace=True)
    return df


# ---------------------------------------------------------------------------
# Lookup-table builder for production inference
# ---------------------------------------------------------------------------

def _build_lookup_tables(
    df_pos_hist: pd.DataFrame, term_col: str = "SemesterIndex"
) -> dict:
    """Pre-aggregate the history tables needed at inference time.

    Returns a dict of DataFrames keyed by feature name.  At inference the
    router does a point-lookup into these tables instead of re-running the
    full merge_asof pipeline.
    """
    hist = df_pos_hist.copy()
    hist[term_col] = hist[term_col].astype(int)

    count_defs = [
        (["Instructor"],                              "instr_prior_count"),
        (["CourseCode"],                              "course_prior_count"),
        (["Slot"],                                    "slot_prior_count"),
        (["CourseCode", "Type"],                      "course_type_prior_count"),
        (["Instructor", "Dept"],                      "instr_dept_prior_count"),
        (["Instructor", "CourseCode"],                "instr_course_prior_count"),
        (["CourseCode", "Slot"],                      "course_slot_prior_count"),
        (["CourseCode", "Type", "Slot"],              "course_type_slot_prior_count"),
        (["CourseCode", "Instructor", "Slot", "Type"], "combo_prior_count"),
    ]

    recency_defs = [
        (["Instructor"],                              "instr_last_term"),
        (["CourseCode"],                              "course_last_term"),
        (["Instructor", "CourseCode"],                "instr_course_last_term"),
        (["CourseCode", "Instructor", "Slot", "Type"], "combo_last_term"),
    ]

    lookups: dict = {}

    for group_cols, out_col in count_defs:
        # Cumulative count per group — latest entry for each group is the
        # total-to-date, which is what we serve at inference.
        tmp = (
            hist.groupby(group_cols + [term_col])
            .size()
            .reset_index(name="n_in_term")
            .sort_values(term_col, kind="mergesort")
        )
        tmp[out_col] = tmp.groupby(group_cols)["n_in_term"].cumsum()
        # Keep every (group, term) snapshot so we can do exact-term lookups.
        lookups[out_col] = tmp[group_cols + [term_col, out_col]].copy()

    for group_cols, out_col in recency_defs:
        tbl = _make_last_seen_term_table(hist, group_cols, term_col, out_col)
        lookups[out_col] = tbl.copy()

    return lookups


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train_linear_svm(df_engineer: pd.DataFrame) -> None:
    """Train the notebook's Linear SVM with history/recency features.

    Key design choices (matching the notebook exactly):

    1. Term-aware negative sampling
       Instructor pool is scoped to (SemesterIndex, Dept) — so fake rows
       only use instructors who were actually active in that same term.
       Positive-key check includes SemesterIndex to avoid false negatives.

    2. Temporal train / test split
       Last 2 SemesterIndex values are held out as the test set.  This
       mirrors production: we always predict for a future term.

    3. No-leak history features
       add_history_features_no_leak() is called with train-term positives
       only (train_pos_hist).  Test rows see train history but not each
       other, so metrics are honest.

    4. Preprocessor
       OneHotEncoder on categoricals + StandardScaler(with_mean=False) on
       the 13 numerical history columns.  with_mean=False keeps the OHE
       output sparse, which LinearSVC requires.

    5. Artifact
       Saves model, feature lists, precomputed lookup tables, and
       max_train_term to 'train2_anthony_svm.joblib' so ml_router.py can
       hydrate the 13 num_cols at inference time without re-running the
       full feature-engineering pipeline.
    """
    df = df_engineer.copy()

    # ---- Build positive rows ----
    needed = ["SemesterIndex", "CourseCode", "Instructor", "Slot", "Type", "Dept"]
    df_pos = df.dropna(subset=needed).copy()
    df_pos["Scheduled"] = 1

    # Positive key set (term-aware) — used to filter accidental positives in negatives.
    pos_keys = set(
        zip(
            df_pos["SemesterIndex"].astype(int),
            df_pos["CourseCode"],
            df_pos["Instructor"],
            df_pos["Slot"],
            df_pos["Type"],
        )
    )

    # ---- Negative-sampling pools (term-scoped) ----
    # Instructor pool: instructors active in the same (term, dept)
    instr_pool = (
        df_pos[["SemesterIndex", "Dept", "Instructor"]]
        .drop_duplicates()
        .groupby(["SemesterIndex", "Dept"])["Instructor"]
        .apply(list)
    )
    # Slot pool: historically used slots for a (course, type) pair
    slot_pool = (
        df_pos[["CourseCode", "Type", "Slot"]]
        .drop_duplicates()
        .groupby(["CourseCode", "Type"])["Slot"]
        .apply(list)
    )

    rng = np.random.default_rng(42)
    K = 3  # negatives per positive row
    neg_rows: list = []

    preserve_cols = needed + ["Scheduled"]
    for _, row in df_pos[preserve_cols].iterrows():
        term  = int(row["SemesterIndex"])
        dept  = row["Dept"]
        course = row["CourseCode"]
        typ   = row["Type"]
        instr = row["Instructor"]
        slot  = row["Slot"]

        i_pool = instr_pool.get((term, dept), [])
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

            key = (int(new["SemesterIndex"]), new["CourseCode"], new["Instructor"], new["Slot"], new["Type"])
            if key in pos_keys:
                continue
            new["Scheduled"] = 0
            neg_rows.append(new[preserve_cols])
            generated += 1

    neg = (
        pd.DataFrame(neg_rows)
        .drop_duplicates(subset=["SemesterIndex", "CourseCode", "Instructor", "Slot", "Type"])
        .reset_index(drop=True)
    )
    df_labeled = pd.concat(
        [df_pos[preserve_cols], neg[preserve_cols]], ignore_index=True
    )
    print(f"Labeled dataset: {df_labeled['Scheduled'].value_counts().to_dict()}")

    # ---- Temporal train / test split ----
    # Last 2 terms are held out as the test set.
    all_terms  = sorted(df_labeled["SemesterIndex"].unique())
    test_terms = set(all_terms[-2:])
    train_mask = ~df_labeled["SemesterIndex"].isin(test_terms)
    test_mask  =  df_labeled["SemesterIndex"].isin(test_terms)
    print(f"Train terms: {sorted(set(all_terms) - test_terms)}  |  Test terms: {sorted(test_terms)}")

    # ---- No-leak history features ----
    # Only positives from train terms form the history that both train AND
    # test rows are allowed to look back into.
    train_pos_hist = df_labeled.loc[train_mask & (df_labeled["Scheduled"] == 1)].copy()
    df_feat = add_history_features_no_leak(df_labeled, train_pos_hist, term_col="SemesterIndex")

    cat_cols = ["CourseCode", "Instructor", "Slot", "Type"]
    num_cols = [
        "instr_prior_count_log1p",
        "course_prior_count_log1p",
        "slot_prior_count_log1p",
        "course_type_prior_count_log1p",
        "instr_dept_prior_count_log1p",
        "instr_course_prior_count_log1p",
        "course_slot_prior_count_log1p",
        "course_type_slot_prior_count_log1p",
        "combo_prior_count_log1p",
        "instr_terms_since",
        "course_terms_since",
        "instr_course_terms_since",
        "combo_terms_since",
    ]

    X = df_feat[cat_cols + num_cols]
    y = df_feat["Scheduled"].astype(int)

    X_train, X_test = X.loc[train_mask], X.loc[test_mask]
    y_train, y_test = y.loc[train_mask], y.loc[test_mask]
    print(f"X_train: {X_train.shape}  X_test: {X_test.shape}")

    # ---- Pipeline ----
    # StandardScaler(with_mean=False): sparse-safe scaler for count features.
    # LinearSVC is margin-based and sensitive to feature scale, so scaling
    # the numerical columns is important.
    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", StandardScaler(with_mean=False), num_cols),
        ],
        remainder="drop",
    )
    svm = LinearSVC(class_weight="balanced", max_iter=2000, C=1.0)
    clf = CalibratedClassifierCV(estimator=svm, method="sigmoid", cv=3)
    pipe = Pipeline(steps=[("prep", preprocess), ("clf", clf)])

    print("Fitting pipeline...")
    pipe.fit(X_train, y_train)

    # ---- Evaluation (on hold-out test set) ----
    proba = pipe.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    print("\n--- HOLD-OUT EVALUATION METRICS ---")
    print("ROC AUC :", round(roc_auc_score(y_test, proba), 4))
    print("PR  AUC :", round(average_precision_score(y_test, proba), 4))
    print(classification_report(y_test, preds, digits=3))

    # =======================================================================
    # PRODUCTION RETRAINING
    # =======================================================================
    print("\n--- RETRAINING ON FULL DATASET FOR PRODUCTION ---")
    
    # 1. Rebuild history features using ALL positives as historical context. 
    # (merge_asof direction="backward", allow_exact_matches=False still prevents leakage)
    all_pos_hist = df_labeled[df_labeled["Scheduled"] == 1].copy()
    df_feat_all = add_history_features_no_leak(df_labeled, all_pos_hist, term_col="SemesterIndex")

    # 2. Extract features for all data
    X_all = df_feat_all[cat_cols + num_cols]
    y_all = df_feat_all["Scheduled"].astype(int)

    print(f"X_all: {X_all.shape}")
    print("Fitting production pipeline on 100% of available data...")
    
    # 3. Retrain on the full dataset
    pipe.fit(X_all, y_all)

    # ---- Build and export LOOKUP tables for inference ----
    # These are baked into the artifact so ml_router.py can hydrate the
    # 13 num_cols at request time without re-running feature engineering.
    max_train_term = int(max(all_terms))
    lookups = _build_lookup_tables(all_pos_hist, term_col="SemesterIndex")

    artifact_path = OUT_DIR / "train2_anthony_svm.joblib"
    joblib.dump(
        {
            "model":          pipe,
            "cat_cols":       cat_cols,
            "num_cols":       num_cols,
            "features":       cat_cols + num_cols,   # kept for backward compat
            "lookups":        lookups,
            "max_train_term": max_train_term,
        },
        artifact_path,
    )
    print("Saved production artifact to:", artifact_path)


def main():
    df = load_and_prepare()
    train_linear_svm(df)


if __name__ == "__main__":
    main()
