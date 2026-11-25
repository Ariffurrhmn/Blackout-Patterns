"""Writes demo/notebook.ipynb (kept as code so the notebook is easy to review and regenerate)."""
import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
C = lambda s: nbf.v4.new_code_cell(s.strip("\n"))
M = lambda s: nbf.v4.new_markdown_cell(s.strip("\n"))
nb.cells = [
M("""
# Bangladesh daily demand: data to model

Loads the dataset CSV, looks at it, trains the same model as the HTML demo, compares it with "tomorrow = today" and the BPDB forecast issued that morning, and writes the model as JSON.

**Caveats.** This is the F3 recipe: it uses the same-day wind and cloud as they happened (NASA POWER, four zones: Dhaka, Chattogram, Rajshahi, Sylhet), which are not known the day before. The F1 model with weather forecasts could not be rebuilt. 2025 to 2026 was used earlier for load-shedding work, so it is not a clean holdout. This is a working result, not a final model.
"""),
M("## 1. Load the data\nOn Colab or Kaggle, upload `daily_demo.csv` with the file picker (Colab) or add it as a dataset (Kaggle). If neither is found, the cell tries the public GitHub copy."),
C('''
import os, io, urllib.request
import numpy as np, pandas as pd, sklearn
print("scikit-learn", sklearn.__version__)

URL = "https://raw.githubusercontent.com/Ariffurrhmn/Blackout-Patterns/claude/hopeful-ramanujan-uxbrjq/demo/data/daily_demo.csv"
CANDIDATES = ["daily_demo.csv", "data/daily_demo.csv", "demo/data/daily_demo.csv", "../demo/data/daily_demo.csv"]
for root, _, files in os.walk("/kaggle/input") if os.path.isdir("/kaggle/input") else []:
    CANDIDATES += [os.path.join(root, f) for f in files if f == "daily_demo.csv"]

# 1) a local or Kaggle copy, 2) the public GitHub copy, 3) upload (Colab) as the last resort.
# float_precision="round_trip" reads the numbers exactly; the default fast parser can be off by 1e-14,
# which is enough to change a retrained tree model.
path = next((p for p in CANDIDATES if os.path.exists(p)), None)
if path is not None:
    df = pd.read_csv(path, float_precision="round_trip")
else:
    try:
        text = urllib.request.urlopen(URL, timeout=60).read().decode()
        df = pd.read_csv(io.StringIO(text), float_precision="round_trip")
    except Exception as err:
        print("Could not download the CSV:", err)
        from google.colab import files          # only exists on Colab
        up = files.upload()
        df = pd.read_csv(io.BytesIO(next(iter(up.values()))), float_precision="round_trip")
df["date"] = pd.to_datetime(df["date"])
print(df.shape, df["date"].min().date(), "to", df["date"].max().date())
df.head()
'''),
M("## 2. Look at the data"),
C('''
import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(11, 9))
d = df.set_index("date")
d["demand_mw"].rolling(7, min_periods=4).mean().plot(ax=ax[0], title="Daily demand, 7-day average (MW)")
d["shed_mw"].rolling(7, min_periods=4).mean().plot(ax=ax[1], color="tab:red", title="Load shedding, 7-day average (MW)")
ax[2].scatter(d["ra_cloud_t"], d["demand_mw"], s=4, alpha=.4)
ax[2].set(xlabel="reanalysis cloud cover (%)", ylabel="demand (MW)", title="Demand vs cloud cover (correlation is not cause)")
plt.tight_layout(); plt.show()
print(df["quality_flag"].fillna("no flag").replace("", "no flag").value_counts())
print("\\nMissing values per column:"); print(df.isna().sum()[lambda s: s > 0])
'''),
M("## 3. Train the model\nSame settings and cutoff as the demo: gradient boosting, 300 trees, learning rate 0.05, at most 15 leaves, trained on days up to 2024-12-31. The target is `log(demand / 7-day mean)`; the prediction is `exp(output) x 7-day mean`."),
C('''
from sklearn.ensemble import HistGradientBoostingRegressor
FEATURES = ["lr1","lr7","lm7","dow","sin1","cos1","sin2","cos2","ramadan","eid_fitr_win","eid_adha_win","ra_wind_t","ra_cloud_t"]
TRAIN_END = pd.Timestamp("2024-12-31")

target = np.log(df["demand_mw"] / df["m7_mw"])
ok = (df["date"] <= TRAIN_END) & target.notna() & df[FEATURES].notna().all(axis=1)
model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                      early_stopping=False, random_state=0)
model.fit(df.loc[ok, FEATURES], target[ok])
print("trained on", int(ok.sum()), "days")

has = df[FEATURES].notna().all(axis=1) & df["m7_mw"].notna()
df["pred_retrained_mw"] = np.nan
df.loc[has, "pred_retrained_mw"] = np.exp(model.predict(df.loc[has, FEATURES])) * df.loc[has, "m7_mw"]
if "pred_mw" in df:
    diff = (df["pred_retrained_mw"] - df["pred_mw"]).abs()
    print("difference vs the exported model's predictions (MW): mean", round(diff.mean(), 3), ", max", round(diff.max(), 3))
    print("(near zero when scikit-learn versions match; another version can give small differences)")
'''),
M("## 4. Evaluate on the test period\nOne shared set of test days is used for every method. MAPE is mean absolute percentage error. Gain is the drop in mean absolute error versus yesterday."),
C('''
test = df[(df["date"] > TRAIN_END) & df[["demand_mw","pred_retrained_mw","demand_yesterday_mw","bpdb_forecast_mw"]].notna().all(axis=1)]
def score(col):
    e = (test[col] - test["demand_mw"]).abs()
    return pd.Series({"MAPE %": (e / test["demand_mw"]).mean() * 100, "MAE MW": e.mean()})
res = pd.DataFrame({"Yesterday": score("demand_yesterday_mw"), "Model (retrained here)": score("pred_retrained_mw"),
                    "BPDB forecast issued that morning": score("bpdb_forecast_mw")}).T
res["Gain vs yesterday MW"] = res.loc["Yesterday", "MAE MW"] - res["MAE MW"]
print(len(test), "test days"); display(res.round(2))
print("Original F3 run, docs/forecast_test.md (569 days): model 4.77%, yesterday 5.48%, BPDB 4.41%, gain +65 MW (95% CI +1 to +131). This dataset is a rebuild, so small differences are expected. The gain is small and its interval is near zero; the BPDB forecast, issued that morning, does better.")
by = test.assign(year=test["date"].dt.year).groupby("year").apply(lambda g: pd.Series({
    "days": len(g),
    "yesterday MAPE %": ((g["demand_yesterday_mw"]-g["demand_mw"]).abs()/g["demand_mw"]).mean()*100,
    "model MAPE %": ((g["pred_retrained_mw"]-g["demand_mw"]).abs()/g["demand_mw"]).mean()*100}))
display(by.round(2))
test.set_index("date")[["demand_mw","pred_retrained_mw","demand_yesterday_mw"]].iloc[-120:].plot(figsize=(11,4), title="Last 120 test days (MW)")
plt.show()
'''),
M("## 5. Export the model as JSON\nThe HTML demo walks these trees in JavaScript. `_predictors` is a private scikit-learn attribute, so the export is checked against `predict` before it is written."),
C('''
import json, math
def export(m):
    trees = []
    for pred in m._predictors:
        nodes = pred[0].nodes
        assert not nodes["is_categorical"].any()
        trees.append([{"v": float(n["value"]), "f": int(n["feature_idx"]), "t": float(n["num_threshold"]),
                       "l": int(n["left"]), "r": int(n["right"]), "leaf": bool(n["is_leaf"]),
                       "mgl": bool(n["missing_go_to_left"])} for n in nodes])
    return {"features": FEATURES, "baseline": float(m._baseline_prediction.ravel()[0]), "trees": trees}

def walk(mod, x):
    t = mod["baseline"]
    for tree in mod["trees"]:
        i = 0
        while not tree[i]["leaf"]:
            n = tree[i]; v = x[n["f"]]
            i = n["l"] if (math.isnan(v) and n["mgl"]) or (not math.isnan(v) and v <= n["t"]) else n["r"]
        t += tree[i]["v"]
    return t

exported = export(model)
sample = df.loc[has & ok].head(200)
mx = max(abs(walk(exported, r.tolist()) - p) for r, p in zip(sample[FEATURES].values, model.predict(sample[FEATURES])))
print("max difference, tree walk vs predict:", mx)
assert mx < 1e-9
with open("model_f3_retrained.json", "w") as f:
    json.dump(exported, f)
print("wrote model_f3_retrained.json (on Colab, download it from the file panel)")
'''),
]
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, Path(__file__).with_name("notebook.ipynb"))
