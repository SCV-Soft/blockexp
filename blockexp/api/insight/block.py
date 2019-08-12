from starlette.requests import Request

from . import api


# Block routes
# var blockOptions = {
#   node: this.node,
#   blockSummaryCacheSize: this.blockSummaryCacheSize,
#   blockCacheSize: this.blockCacheSize
# };
# var blocks = new BlockController(blockOptions);

@api.route('/blocks', methods=['GET'])
def get_block_(request: Request):
    "app.get('/blocks', this.cacheShort(), blocks.list.bind(blocks));"
    pass


@api.route('/block/:blockHash', methods=['GET'])
def get_block_(request: Request):
    """
    app.get('/block/:blockHash', this.cacheShort(), blocks.checkBlockHash.bind(blocks), blocks.show.bind(blocks));
    app.param('blockHash', blocks.block.bind(blocks));
    """
    pass


@api.route('/rawblock/:blockHash', methods=['GET'])
def get_block_(request: Request):
    """
    app.get('/rawblock/:blockHash', this.cacheLong(), blocks.checkBlockHash.bind(blocks), blocks.showRaw.bind(blocks));
    app.param('blockHash', blocks.rawBlock.bind(blocks));
    """
    pass


@api.route('/block-index/:height', methods=['GET'])
def get_block_(request: Request):
    """
    app.get('/block-index/:height', this.cacheShort(), blocks.blockIndex.bind(blocks));
    app.param('height', blocks.blockIndex.bind(blocks));
    """
    pass
