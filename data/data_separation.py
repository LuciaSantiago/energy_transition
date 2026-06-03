from __future__ import annotations

from pathlib import Path

import pandas as pd


# Añadimos los datos ya limpios.
INPUT_FILE = Path(__file__).with_name("MES_0126_clean.csv")
OUTPUT_DIR = Path(__file__).resolve().parent

# Aquí las fuentes que son interesantes de estudiar:
PRODUCTS_TO_STUDY = [
	"Hydro",
	"Solar",
	"Wind",
	"Geothermal",
	"Nuclear",
	"Natural Gas",
	"Coal Peat and Manufactured Gases",
]
# Aquí se seleccionan las fuentes totales fósiles y renovables:
ENERGY_TOTAL_PRODUCTS = ["Total Combustible Fuels", "Total Renewables"]


# Definimos diferentes funciones de interés.
def load_data() -> pd.DataFrame:
	# Carga de datos.
	return pd.read_csv(INPUT_FILE)


def drop_jan_26(df: pd.DataFrame) -> pd.DataFrame:
	# Eliminamos enero de 2026.
	return df[df["Time"] != "Jan-26"].copy()


def remove_unit_column(df: pd.DataFrame) -> pd.DataFrame:
	# Eliminamos la columna Unit.
	return df.drop(columns=["Unit"], errors="ignore")


def build_percentage_dataset(df: pd.DataFrame) -> pd.DataFrame:
	# Calculamos la proporción de energías renovables.
	totals = df[df["Product"].isin(ENERGY_TOTAL_PRODUCTS)].copy()

	pivot = (
		totals.pivot_table(
			index=["Country", "Time"],
			columns="Product",
			values="Value",
			aggfunc="first",
		)
		.reset_index()
		.rename_axis(None, axis=1)
	)

	pivot["Value"] = (
		pivot["Total Renewables"]
		/ (pivot["Total Combustible Fuels"] + pivot["Total Renewables"])
	) * 100

	result = pivot[["Country", "Time", "Value"]].copy()
	result.insert(2, "Product", "Renewables share (%)")
	return result


def build_yearly_percentage_dataset(df: pd.DataFrame) -> pd.DataFrame:
	# El output de la función build_percentage_dataset se promedia anualmente.
	percentage_dataset = build_percentage_dataset(df).copy()
	percentage_dataset["Year"] = ("20" + percentage_dataset["Time"].str[-2:]).astype(int)

	yearly = (
		percentage_dataset.groupby(["Country", "Year"], as_index=False)["Value"]
		.mean()
		.pivot(index="Country", columns="Year", values="Value")
		.reset_index()
		.rename_axis(None, axis=1)
	)

	return yearly


def build_yearly_products_sum_dataset(df: pd.DataFrame) -> pd.DataFrame:
	# Calculamos el total por año para cada país.
	filtered = df[df["Product"].isin(PRODUCTS_TO_STUDY)].copy()
	filtered["Year"] = ("20" + filtered["Time"].str[-2:]).astype(int)

	yearly = (
		filtered.groupby(["Year", "Product"], as_index=False)["Value"]
		.sum()
		.pivot(index="Year", columns="Product", values="Value")
		.reindex(columns=PRODUCTS_TO_STUDY)
		.reindex(range(2015, 2026))
		.reset_index()
		.rename_axis(None, axis=1)
	)

	return yearly


def build_world_percentage_dataset(df: pd.DataFrame) -> pd.DataFrame:
	# Se calcula el total de renovables y fósiles a nivel mundial.
	filtered = df[df["Product"].isin(ENERGY_TOTAL_PRODUCTS)].copy()
	filtered["Year"] = ("20" + filtered["Time"].str[-2:]).astype(int)

	yearly = (
		filtered.groupby(["Year", "Product"], as_index=False)["Value"]
		.sum()
		.pivot(index="Year", columns="Product", values="Value")
		.reindex(columns=ENERGY_TOTAL_PRODUCTS)
		.reindex(range(2015, 2026))
		.reset_index()
		.rename_axis(None, axis=1)
	)

	yearly["Renewables share (%)"] = (
		yearly["Total Renewables"]
		/ (yearly["Total Combustible Fuels"] + yearly["Total Renewables"])
	) * 100

	return yearly[["Year", "Renewables share (%)"]]


def build_2025_top_product_dataset(df: pd.DataFrame) -> pd.DataFrame:
	# Calculamos el producto más importante para cada país en 2025.
	filtered = df[
		(df["Balance"] == "Net Electricity Production")
		& (df["Time"].str.endswith("25"))
		& (df["Product"].isin(PRODUCTS_TO_STUDY))
	].copy()
	filtered["Year"] = ("20" + filtered["Time"].str[-2:]).astype(int)

	yearly = (
		filtered.groupby(["Country", "Year", "Product"], as_index=False)["Value"]
		.sum()
	)

	top_products = yearly.loc[yearly.groupby(["Country", "Year"])['Value'].idxmax()].copy()
	top_products = top_products[["Country", "Year", "Product", "Value"]].sort_values("Country")
	top_products = top_products.reset_index(drop=True)
	return top_products


def save_dataset(df: pd.DataFrame, filename: str) -> None:
	# Guardamos el dataset generado.
	output_path = OUTPUT_DIR / filename
	try:
		df.to_csv(output_path, index=False)
	except PermissionError:
		# Si no se puede escribir el archivo (por ejemplo, si está abierto en Excel), guardamos un backup.
		fallback_path = OUTPUT_DIR / f"{output_path.stem}_clean{output_path.suffix}"
		df.to_csv(fallback_path, index=False)


def main() -> None:
	# Generamos los datasets.
	data = load_data()
	data = drop_jan_26(data)
	data = remove_unit_column(data)

	yearly_percentage_dataset = build_yearly_percentage_dataset(data)
	yearly_products_sum_dataset = build_yearly_products_sum_dataset(data)
	world_percentage_dataset = build_world_percentage_dataset(data)
	top_product_2025_dataset = build_2025_top_product_dataset(data)

	# Guardamos:
	save_dataset(yearly_percentage_dataset, "renewables_share_percentage_yearly.csv") # Para el mapa de Flourish
	save_dataset(yearly_products_sum_dataset, "yearly_products_sum.csv") # Gráfica de barras carrera
	save_dataset(world_percentage_dataset, "world_renewables_share_percentage_yearly.csv") # Para la gráfica de barras del total de renovables mundial
	save_dataset(top_product_2025_dataset, "top_net_electricity_production_product_2025_by_country.csv") # Para la gráfica de burbujas


if __name__ == "__main__":
	main()
