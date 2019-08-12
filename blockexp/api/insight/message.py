from starlette.requests import Request

from . import api


# // Message routes
# var messages = new MessagesController(this.node);

@api.route('/messages/verify', methods=['GET'])
def get_messages_verify(request: Request):
    "app.get('/messages/verify', messages.verify.bind(messages));"
    pass


@api.route('/messages/verify', methods=['POST'])
def set_messages_verify(request: Request):
    "app.post('/messages/verify', messages.verify.bind(messages));"
    pass
