from starlette.requests import Request

from . import api


# Transaction routes
# var transactions = new TxController(this.node, this.translateAddresses);

@api.route('/tx/:txid', methods=['GET'])
def get_tx(request: Request):
    """
    app.get('/tx/:txid', this.cacheShort(), transactions.show.bind(transactions));
    app.param('txid', transactions.transaction.bind(transactions));
    """
    pass


@api.route('/txs', methods=['GET'])
def get_txs(request: Request):
    "app.get('/txs', this.cacheShort(), transactions.list.bind(transactions));"
    pass


@api.route('/tx/send', methods=['POST'])
def send_tx(request: Request):
    "app.post('/tx/send', transactions.send.bind(transactions));"
    pass


# Raw Routes

@api.route('/rawtx/:txid', methods=['GET'])
def get_rawtx(request: Request):
    """
    app.get('/rawtx/:txid', this.cacheLong(), transactions.showRaw.bind(transactions));
    app.param('txid', transactions.rawTransaction.bind(transactions));
    """
    pass
