from starlette.applications import Starlette


def init_app(*, debug=False) -> Starlette:
    app = Starlette(debug=debug)

    return app
