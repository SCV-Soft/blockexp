from starlette.requests import Request

from . import api


# Utils route
# var utils = new UtilsController(this.node);

@api.route('/utils/estimatefee')
def get_estimatefee(request: Request):
    "app.get('/utils/estimatefee', utils.estimateFee.bind(utils));"
    pass
