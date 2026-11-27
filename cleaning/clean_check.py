import pandas as pd
from config import OUTPUT_OK

df_clean = pd.read_csv(OUTPUT_OK, dtype={"cpcli": "str"})
cle = ["datcde", "codcde", "codobj"]

print(len(df_clean))                       # attendu : 134 945
print(df_clean.duplicated(cle).sum())      # attendu : 19
print(df_clean[df_clean.duplicated(cle, keep=False)].sort_values(cle).to_string())