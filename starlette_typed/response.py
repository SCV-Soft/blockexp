class HTTPException(Exception):
    def __init__(self, code: int):
        super().__init__(code)
        self.code = code
