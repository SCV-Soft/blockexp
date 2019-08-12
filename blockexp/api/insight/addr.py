from starlette.requests import Request

from . import api


# Address routes
# var addresses = new AddressController(this.node, this.translateAddresses);

@api.route('/addr/:addr', methods=['GET'])
def get_addr(request: Request):
    "app.get('/addr/:addr', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.show.bind(addresses));"
    pass


@api.route('/addr/:addr/utxo', methods=['GET'])
def get_addr_utxo(request: Request):
    "app.get('/addr/:addr/utxo', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.utxo.bind(addresses));"
    pass


@api.route('/addrs/:addrs/utxo', methods=['GET'])
def get_addrs_utxo(request: Request):
    "app.get('/addrs/:addrs/utxo', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.multiutxo.bind(addresses));"
    pass


@api.route('/addrs/utxo', methods=['POST'])
def set_addrs_utxo(request: Request):
    "app.post('/addrs/utxo', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.multiutxo.bind(addresses));"
    pass


@api.route('/addrs/:addrs/txs', methods=['GET'])
def get_addrs_txs(request: Request):
    "app.get('/addrs/:addrs/txs', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.multitxs.bind(addresses));"
    pass


@api.route('/addrs/txs', methods=['POST'])
def set_addr_txs(request: Request):
    "app.post('/addrs/txs', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.multitxs.bind(addresses));"
    pass


# Address property routes

@api.route('/addr/:addr/balance', methods=['GET'])
def get_addr_balance(request: Request):
    "app.get('/addr/:addr/balance', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.balance.bind(addresses));"
    pass


@api.route('/addr/:addr/totalReceived', methods=['GET'])
def get_addr_total_received(request: Request):
    "app.get('/addr/:addr/totalReceived', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.totalReceived.bind(addresses));"
    pass


@api.route('/addr/:addr/totalSent', methods=['GET'])
def get_addr_total_sent(request: Request):
    "app.get('/addr/:addr/totalSent', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.totalSent.bind(addresses));"
    pass


@api.route('/addr/:addr/unconfirmedBalance', methods=['GET'])
def get_addr_unconfirmed_balance(request: Request):
    "app.get('/addr/:addr/unconfirmedBalance', this.cacheShort(), addresses.checkAddrs.bind(addresses), addresses.unconfirmedBalance.bind(addresses));"
    pass
