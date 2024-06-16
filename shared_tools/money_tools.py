from requests import get
from bs4 import BeautifulSoup


def currency_exchange(amount: float, currency_from: str, currency_to: str = "LKR") -> float:
    currency_page = f'http://www.xe.com/currencyconverter/convert/?' \
                    f'Amount={amount}&From={currency_from}&To={currency_to}'

    currency = get(currency_page).text
    currency_data = BeautifulSoup(currency, 'html.parser')

    val = currency_data.find('span', attrs={'class': 'uccResultUnit'})
    return float(val.text.strip())
