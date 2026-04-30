import pandas as pd


def extract_master(path: str) -> dict:
    """Read the MASTER sheet and map field labels to their values."""
    df = pd.read_excel(path, sheet_name="MASTER")

    data = {}
    for _, row in df.iterrows():
        key = str(row.iloc[1]).strip().lower()
        value = row.iloc[2]

        if key and key != "nan":
            data[key] = value
    return data
