from requests import get
from bs4 import BeautifulSoup

from shared_tools.logger import log


def currency_exchange(amount: float, currency_from: str, currency_to: str = "LKR") -> float:
    currency_page = f'http://www.xe.com/currencyconverter/convert/?' \
                    f'Amount={amount}&From={currency_from}&To={currency_to}'

    currency = get(currency_page).text

    currency_data = BeautifulSoup(currency, 'html.parser')

    val = currency_data.find('p', attrs={'class': 'sc-295edd9f-1 jqMUXt'})
    log(msg=f"{currency_page} returned {val}.")
    f_value = float(val.text.split(" ")[0].replace(",", "").strip())
    log(msg=f"{currency_from} {amount} converted to {currency_to} {f_value}.")
    return f_value
