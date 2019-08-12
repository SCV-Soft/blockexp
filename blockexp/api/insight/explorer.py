from starlette.requests import Request

from . import api


# Other api endpoints

@api.route('/explorers', methods=['GET'])
def get_explorers(request: Request):
    "app.get('/explorers' , this._getExplorers.bind(this));"
    pass
