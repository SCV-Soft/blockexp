from starlette.requests import Request

from . import api


# Currency
# var currency = new CurrencyController({
#   node: this.node,
#   currencyRefresh: this.currencyRefresh,
#   currency: this.currency
# });


@api.route('/currency', methods=['GET'])
def get_currency(request: Request):
    "app.get('/currency', currency.index.bind(currency));"
    pass
