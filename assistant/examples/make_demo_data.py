"""Generate a synthetic KAP dataset (nurses, diabetes foot care) for testing the engine."""
import numpy as np, pandas as pd
rng = np.random.default_rng(2026)
n = 320
df = pd.DataFrame({
    "ID": range(1, n + 1),
    "age_group": rng.choice(["<30", "30-39", "40+"], n, p=[.35, .40, .25]),
    "gender": rng.choice(["Female", "Male"], n, p=[.7, .3]),
    "nationality": rng.choice(["Omani", "Non-Omani"], n, p=[.6, .4]),
    "education": rng.choice(["Diploma", "Bachelor", "Postgraduate"], n, p=[.3, .55, .15]),
    "experience": rng.choice(["<5 years", "5-10 years", ">10 years"], n, p=[.3, .4, .3]),
    "facility": rng.choice(["Hospital", "Health center"], n, p=[.45, .55]),
    "training": rng.choice(["Yes", "No"], n, p=[.4, .6]),
})
latent = (df.training.eq("Yes") * 0.9 + df.education.map({"Diploma": 0, "Bachelor": .4, "Postgraduate": .8})
          + rng.normal(0, 1, n))
for i in range(1, 11):   # knowledge: 1 correct / 0 wrong
    df[f"K{i}"] = (latent + rng.normal(0, 1.1, n) > -0.3 + i * 0.08).astype(int)
for i in range(1, 9):    # attitude: Likert 1-5
    df[f"A{i}"] = np.clip(np.round(3.4 + 0.5 * latent + rng.normal(0, .8, n)), 1, 5).astype(int)
df["A8"] = 6 - df["A8"]  # negatively worded item
for i in range(1, 8):    # practice: 1 done / 0 not done
    df[f"P{i}"] = (0.6 * latent + rng.normal(0, 1, n) > 0.1).astype(int)
df.to_excel("examples/demo_kap_data.xlsx", index=False)
print("saved", df.shape)
