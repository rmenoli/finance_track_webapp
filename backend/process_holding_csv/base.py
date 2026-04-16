from __future__ import annotations

import csv
from dataclasses import dataclass, fields
from pathlib import Path

COUNTRY_MAP: dict[str, str] = {
    # Italian names (WSML / DWS)
    "Australia": "Australia",
    "Austria": "Austria",
    "Belgio": "Belgium",
    "Bulgaria": "Bulgaria",
    "Canada": "Canada",
    "Cina": "China",
    "Croazia": "Croatia",
    "Danimarca": "Denmark",
    "Estonia": "Estonia",
    "Finlandia": "Finland",
    "Francia": "France",
    "Germania": "Germany",
    "Giappone": "Japan",
    "Grecia": "Greece",
    "Hong Kong": "Hong Kong",
    "Irlanda": "Ireland",
    "Israele": "Israel",
    "Italia": "Italy",
    "Jersey": "Jersey",
    "Lettonia": "Latvia",
    "Lituania": "Lithuania",
    "Lussemburgo": "Luxembourg",
    "Messico": "Mexico",
    "Norvegia": "Norway",
    "Nuova Zelanda": "New Zealand",
    "Paesi Bassi": "Netherlands",
    "Paesi Bassi (Olanda)": "Netherlands",
    "Polonia": "Poland",
    "Portogallo": "Portugal",
    "Regno Unito": "United Kingdom",
    "Regno unito": "United Kingdom",
    "Repubblica Ceca": "Czech Republic",
    "Romania": "Romania",
    "Slovacchia (Repubblica Slovacca)": "Slovakia",
    "Slovenia": "Slovenia",
    "Spagna": "Spain",
    "Stati Uniti": "United States",
    "Stati Uniti d'America": "United States",
    "Sudafrica": "South Africa",
    "Svezia": "Sweden",
    "Svizzera": "Switzerland",
    "Turchia": "Turkey",
    "Ungheria": "Hungary",
    "Unione Europea": "European Union",
    # ISO-2 codes (Vanguard)
    "AE": "United Arab Emirates",
    "AT": "Austria",
    "AU": "Australia",
    "BE": "Belgium",
    "BR": "Brazil",
    "CA": "Canada",
    "CH": "Switzerland",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "EG": "Egypt",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GR": "Greece",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IN": "India",
    "IS": "Iceland",
    "IT": "Italy",
    "JP": "Japan",
    "KR": "South Korea",
    "KW": "Kuwait",
    "MX": "Mexico",
    "MY": "Malaysia",
    "NL": "Netherlands",
    "NO": "Norway",
    "NZ": "New Zealand",
    "PH": "Philippines",
    "PL": "Poland",
    "PT": "Portugal",
    "QA": "Qatar",
    "RO": "Romania",
    "RU": "Russia",
    "SA": "Saudi Arabia",
    "SE": "Sweden",
    "SG": "Singapore",
    "TH": "Thailand",
    "TR": "Turkey",
    "TW": "Taiwan",
    "US": "United States",
    "ZA": "South Africa",
    # Fallbacks
    "-": "Unknown",
}

SECTOR_MAP: dict[str, str] = {
    # WSML Italian sectors
    "Comunicazione": "Communication Services",
    "Consumi Discrezionali": "Consumer Discretionary",
    "Energia": "Energy",
    "Finanziari": "Financials",
    "Generi di largo consumo": "Consumer Staples",
    "IT": "Technology",
    "Immobili": "Real Estate",
    "Imprese di servizi di pubblica utilità": "Utilities",
    "Industriali": "Industrials",
    "Liquidità e/o derivati": "Cash",
    "Materiali": "Basic Materials",
    "Salute": "Health Care",
    # DWS Italian sectors
    "Governo": "Government",
    "sconosciuta": "Unknown",
    # Vanguard English sectors (passthrough)
    "Basic Materials": "Basic Materials",
    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Energy": "Energy",
    "Financials": "Financials",
    "Health Care": "Health Care",
    "Industrials": "Industrials",
    "Real Estate": "Real Estate",
    "Technology": "Technology",
    "Telecommunications": "Telecommunications",
    "Utilities": "Utilities",
}


COUNTRY_CURRENCY_MAP: dict[str, str] = {
    "Australia": "AUD",
    "Austria": "EUR",
    "Belgium": "EUR",
    "Brazil": "BRL",
    "Bulgaria": "BGN",
    "Canada": "CAD",
    "Chile": "CLP",
    "China": "CNY",
    "Colombia": "COP",
    "Croatia": "EUR",
    "Czech Republic": "CZK",
    "Denmark": "DKK",
    "Egypt": "EGP",
    "Estonia": "EUR",
    "European Union": "EUR",
    "Finland": "EUR",
    "France": "EUR",
    "Germany": "EUR",
    "Greece": "EUR",
    "Hong Kong": "HKD",
    "Hungary": "HUF",
    "Iceland": "ISK",
    "India": "INR",
    "Indonesia": "IDR",
    "Ireland": "EUR",
    "Israel": "ILS",
    "Italy": "EUR",
    "Japan": "JPY",
    "Jersey": "GBP",
    "Kuwait": "KWD",
    "Latvia": "EUR",
    "Lithuania": "EUR",
    "Luxembourg": "EUR",
    "Malaysia": "MYR",
    "Mexico": "MXN",
    "Netherlands": "EUR",
    "New Zealand": "NZD",
    "Norway": "NOK",
    "Philippines": "PHP",
    "Poland": "PLN",
    "Portugal": "EUR",
    "Qatar": "QAR",
    "Romania": "RON",
    "Russia": "RUB",
    "Saudi Arabia": "SAR",
    "Singapore": "SGD",
    "Slovakia": "EUR",
    "Slovenia": "EUR",
    "South Africa": "ZAR",
    "South Korea": "KRW",
    "Spain": "EUR",
    "Sweden": "SEK",
    "Switzerland": "CHF",
    "Taiwan": "TWD",
    "Thailand": "THB",
    "Turkey": "TRY",
    "United Arab Emirates": "AED",
    "United Kingdom": "GBP",
    "United States": "USD",
}


def currency_from_country(country: str) -> str:
    return COUNTRY_CURRENCY_MAP.get(country, "USD")


def standardize_country(value: str) -> str:
    return COUNTRY_MAP.get(value, value)


def standardize_sector(value: str) -> str:
    return SECTOR_MAP.get(value, value)


@dataclass
class HoldingRow:
    ticker: str
    country: str
    sector: str
    currency: str
    weight_pct: float


def write_csv(rows: list[HoldingRow], output_path: Path) -> None:
    fieldnames = [f.name for f in fields(HoldingRow)]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "ticker": row.ticker,
                "country": row.country,
                "sector": row.sector,
                "currency": row.currency,
                "weight_pct": row.weight_pct,
            })
