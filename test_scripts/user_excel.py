import pandas as pd
df = pd.DataFrame({"Name": ["Alice", "Bob", "Charlie"], "Age": [25, 30, 35]})
df.to_excel("user_test.xlsx", index=False)
