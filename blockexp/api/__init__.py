from starlette.routing import Router

api = Router()
api.mount('/', bitcore.api)
