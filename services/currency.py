# Mock conversion with fixed exchange rates
# Base currency = USD

EXCHANGE_RATES = {
    "USD": 1.0,
    "INR": 83.0,       # Indian Rupee
    "EUR": 0.92,       # Euro
    "GBP": 0.79,       # British Pound
    "JPY": 148.0,      # Japanese Yen
    "AUD": 1.55,       # Australian Dollar
    "CAD": 1.35,       # Canadian Dollar
    "CHF": 0.91,       # Swiss Franc
    "CNY": 6.95,       # Chinese Yuan
    "SGD": 1.38,       # Singapore Dollar
    "NZD": 1.68,       # New Zealand Dollar
    "HKD": 7.83,       # Hong Kong Dollar
    "SEK": 10.6,       # Swedish Krona
    "KRW": 1330.0,     # South Korean Won
    "MXN": 17.0,       # Mexican Peso
    "BRL": 5.0,        # Brazilian Real
    "ZAR": 18.0        # South African Rand
}

def convert_currency(amount: float, from_currency: str, to_currency: str):
    try:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency not in EXCHANGE_RATES or to_currency not in EXCHANGE_RATES:
            return {"error": f"Unsupported currency: {from_currency} or {to_currency}"}

        # Convert amount to USD first, then to target
        amount_in_usd = amount / EXCHANGE_RATES[from_currency]
        converted = amount_in_usd * EXCHANGE_RATES[to_currency]
        rate = EXCHANGE_RATES[to_currency] / EXCHANGE_RATES[from_currency]

        return {
            "amount": amount,
            "from": from_currency,
            "to": to_currency,
            "rate": round(rate, 4),
            "converted": round(converted, 2)
        }
    except Exception as e:
        return {"error": str(e)}