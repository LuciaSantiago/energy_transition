from __future__ import annotations

from pathlib import Path

import pandas as pd


INPUT_FILE = Path(__file__).with_name("MES_0126.csv")
OUTPUT_FILE = Path(__file__).with_name("MES_0126_clean.csv")

COUNTRY_RENAMES = {
	"People's Republic of China": "China",
	"Republic of Turkiye": "Turquía",
}

NON_COUNTRY_PATTERN = r"^(OECD|IEA)\b"


def load_data() -> pd.DataFrame:
	return pd.read_csv(INPUT_FILE)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
	cleaned = df.loc[~df["Country"].str.match(NON_COUNTRY_PATTERN, na=False)].copy()
	cleaned["Country"] = cleaned["Country"].replace(COUNTRY_RENAMES)
	return cleaned


def main() -> None:
	data = load_data()
	cleaned = clean_data(data)
	cleaned.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

	removed_rows = len(data) - len(cleaned)
	removed_countries = sorted(
		set(data.loc[data["Country"].str.match(NON_COUNTRY_PATTERN, na=False), "Country"])
	)

	print(f"Saved {OUTPUT_FILE.name}")
	print(f"Rows removed: {removed_rows}")
	print("Removed aggregate entries: " + ", ".join(removed_countries))


if __name__ == "__main__":
	main()
