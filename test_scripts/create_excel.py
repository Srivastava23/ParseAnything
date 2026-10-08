import pandas as pd
df = pd.DataFrame({"Name": ["A", "B", ""], "Age": [10, 20, 30]})
df.to_excel("test.xlsx", index=False)
