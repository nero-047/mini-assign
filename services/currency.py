# Mock conversion with fixed exchange rates
# Base currency = USD

EXCHANGE_RATES = {
    "USD": 1.0,          # US Dollar
    "INR": 87.996,       # Indian Rupee  
    "EUR": 0.8473,       # Euro  
    "GBP": 0.7348,       # British Pound 
    "JPY": 147.16,       # Japanese Yen  
    "AUD": 1.5074,       # Australian Dollar 
    "CAD": 1.3785,       # Canadian Dollar  
    "CHF": 0.7902,       # Swiss Franc  
    "CNY": 7.1074,       # Chinese Yuan 
    "SGD": 1.2796,       # Singapore Dollar
    "NZD": 1.6900,       # New Zealand Dollar
    "HKD": 7.7747,       # Hong Kong Dollar
    "KRW": 1382.3,       # South Korean Won
    "MXN": 18.328,       # Mexican Peso
    "BRL": 5.3005,       # Brazilian Real
    "ZAR": 18.055        # South African Rand
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