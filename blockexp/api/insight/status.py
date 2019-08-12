from starlette.requests import Request

from . import api


# Status route
# var status = new StatusController(this.node);


@api.route('/status', methods=['GET'])
def get_status(request: Request):
    "app.get('/status', this.cacheShort(), status.show.bind(status));"
    pass


@api.route('/sync', methods=['GET'])
def get_sync(request: Request):
    "app.get('/sync', this.cacheShort(), status.sync.bind(status));"
    pass


@api.route('/peer', methods=['GET'])
def get_peer(request: Request):
    "app.get('/peer', this.cacheShort(), status.peer.bind(status));"
    pass


@api.route('/version', methods=['GET'])
def get_version(request: Request):
    "app.get('/version', this.cacheShort(), status.version.bind(status));"
    pass
