from typing import Union, List

from .jsonrpc import AsyncJsonRPC


# https://github.com/bitcoin/bitcoin/blob/master/test/functional/test_framework/authproxy.py

# noinspection SpellCheckingInspection
class AsyncBitcoreDeamon(AsyncJsonRPC):
    async def abandontransaction(self, *args):
        return await self.call('abandontransaction', *args)

    async def abortrescan(self, *args):
        return await self.call('abortrescan', *args)

    async def addmultisigaddress(self, *args):
        return await self.call('addmultisigaddress', *args)

    async def addnode(self, *args):
        return await self.call('addnode', *args)

    async def analyzepsbt(self, *args):
        return await self.call('analyzepsbt', *args)

    async def backupwallet(self, *args):
        return await self.call('backupwallet', *args)

    async def bumpfee(self, *args):
        return await self.call('bumpfee', *args)

    async def clearbanned(self, *args):
        return await self.call('clearbanned', *args)

    async def combinepsbt(self, *args):
        return await self.call('combinepsbt', *args)

    async def combinerawtransaction(self, *args):
        return await self.call('combinerawtransaction', *args)

    async def converttopsbt(self, *args):
        return await self.call('converttopsbt', *args)

    async def createmultisig(self, *args):
        return await self.call('createmultisig', *args)

    async def createpsbt(self, *args):
        return await self.call('createpsbt', *args)

    async def createrawtransaction(self, *args):
        return await self.call('createrawtransaction', *args)

    async def createwallet(self, *args):
        return await self.call('createwallet', *args)

    async def decodepsbt(self, *args):
        return await self.call('decodepsbt', *args)

    async def decoderawtransaction(self, *args):
        return await self.call('decoderawtransaction', *args)

    async def decodescript(self, *args):
        return await self.call('decodescript', *args)

    async def deriveaddresses(self, *args):
        return await self.call('deriveaddresses', *args)

    async def disconnectnode(self, *args):
        return await self.call('disconnectnode', *args)

    async def dumpprivkey(self, *args):
        return await self.call('dumpprivkey', *args)

    async def dumpwallet(self, *args):
        return await self.call('dumpwallet', *args)

    async def encryptwallet(self, *args):
        return await self.call('encryptwallet', *args)

    async def estimatesmartfee(self, *args):
        return await self.call('estimatesmartfee', *args)

    async def finalizepsbt(self, *args):
        return await self.call('finalizepsbt', *args)

    async def fundrawtransaction(self, *args):
        return await self.call('fundrawtransaction', *args)

    async def generate(self, *args):
        return await self.call('generate', *args)

    async def generatetoaddress(self, *args):
        return await self.call('generatetoaddress', *args)

    async def getaddednodeinfo(self, node: str = None):
        """
        Returns information about the given added node, or all added nodes
        (note that onetry addnodes are not listed here)
        """
        if node is None:
            return await self.call('getaddednodeinfo')
        else:
            return await self.call('getaddednodeinfo', node)

    async def getaddressesbylabel(self, label: str) -> dict:
        """
        Returns the list of addresses assigned the specified label.
        """
        return await self.call('getaddressesbylabel', label)

    async def getaddressinfo(self, address: str) -> dict:
        """
        Return information about the given bitcoin address. Some information requires the address
        to be in the wallet.
        """
        return await self.call('getaddressinfo', address)

    async def getbalance(self, dummy: str = "*", minconf: int = 0, include_watchonly: bool = False) -> float:
        """
        Returns the total available balance.
        The available balance is what the wallet considers currently spendable, and is
        thus affected by options which limit spendability such as -spendzeroconfchange.
        """
        return await self.call('getbalance', dummy, minconf, include_watchonly)

    async def getbestblockhash(self) -> str:
        """
        Returns the hash of the best (tip) block in the longest blockchain.
        """
        return await self.call('getbestblockhash')

    async def getblock(self, blockhash: str, verbosity: int = 1) -> Union[str, dict]:
        """
        If verbosity is 0, returns a string that is serialized, hex-encoded data for block 'hash'.
        If verbosity is 1, returns an Object with information about block <hash>.
        If verbosity is 2, returns an Object with information about block <hash> and information about each transaction.
        """
        return await self.call('getblock', blockhash, verbosity)

    async def getblockchaininfo(self) -> dict:
        """Returns an object containing various state info regarding blockchain processing."""
        return await self.call('getblockchaininfo')

    async def getblockcount(self) -> int:
        """Returns the number of blocks in the longest blockchain."""
        return await self.call('getblockcount')

    async def getblockhash(self, height: int) -> str:
        """Returns hash of block in best-block-chain at height provided."""
        return await self.call('getblockhash', height)

    async def getblockheader(self, blockhash: str, verbose: bool = True):
        """
        If verbose is false, returns a string that is serialized, hex-encoded data for blockheader 'hash'.
        If verbose is true, returns an Object with information about blockheader <hash>.
        """
        return await self.call('getblockheader', blockhash, verbose)

    async def getblockstats(self, hash_or_height: Union[str, int], stats: List[str] = None):
        """
        Compute per block statistics for a given window. All amounts are in satoshis.
        It won't work for some heights with pruning.
        It won't work without -txindex for utxo_size_inc, *fee or *feerate stats.
        """
        if stats is None:
            return await self.call('getblockstats', hash_or_height)
        else:
            return await self.call('getblockstats', hash_or_height, stats)

    async def getblocktemplate(self, template_request: dict) -> dict:
        """
        If the request parameters include a 'mode' key, that is used to explicitly select between the default 'template' request or a 'proposal'.
        It returns data needed to construct a block to work on.
        For full specification, see BIPs 22, 23, 9, and 145:
            https://github.com/bitcoin/bips/blob/master/bip-0022.mediawiki
            https://github.com/bitcoin/bips/blob/master/bip-0023.mediawiki
            https://github.com/bitcoin/bips/blob/master/bip-0009.mediawiki#getblocktemplate_changes
            https://github.com/bitcoin/bips/blob/master/bip-0145.mediawiki
        """
        return await self.call('getblocktemplate', template_request)

    async def getchaintips(self) -> List[dict]:
        """
        Return information about all known tips in the block tree, including the main chain as well as orphaned branches.
        """
        return await self.call('getchaintips')

    async def getchaintxstats(self, nblocks: int, blockhash: str = None) -> dict:
        """Compute statistics about the total number and rate of transactions in the chain."""
        if blockhash is None:
            return await self.call('getchaintxstats', nblocks)
        else:
            return await self.call('getchaintxstats', nblocks, blockhash)

    async def getconnectioncount(self) -> int:
        """Returns the number of connections to other nodes."""
        return await self.call('getconnectioncount')

    async def getdescriptorinfo(self, descriptor: str) -> dict:
        """Analyses a descriptor."""
        return await self.call('getdescriptorinfo', descriptor)

    async def getdifficulty(self) -> float:
        """Returns the proof-of-work difficulty as a multiple of the minimum difficulty."""
        return await self.call('getdifficulty')

    async def getmemoryinfo(self, mode: str = "stats") -> dict:
        """Returns an object containing information about memory usage."""
        return await self.call('getmemoryinfo', mode)

    async def getmempoolancestors(self, *args):
        return await self.call('getmempoolancestors', *args)

    async def getmempooldescendants(self, *args):
        return await self.call('getmempooldescendants', *args)

    async def getmempoolentry(self, *args):
        return await self.call('getmempoolentry', *args)

    async def getmempoolinfo(self, *args):
        return await self.call('getmempoolinfo', *args)

    async def getmininginfo(self, *args):
        return await self.call('getmininginfo', *args)

    async def getnettotals(self, *args):
        return await self.call('getnettotals', *args)

    async def getnetworkhashps(self, nblocks: int = 120, height: int = -1) -> int:
        """
        Returns the estimated network hashes per second based on the last n blocks.
        Pass in [blocks] to override # of blocks, -1 specifies since last difficulty change.
        Pass in [height] to estimate the network speed at the time when a certain block was found.
        """
        return await self.call('getnetworkhashps', nblocks, height)

    async def getnetworkinfo(self) -> dict:
        """Returns an object containing various state info regarding P2P networking."""
        return await self.call('getnetworkinfo')

    async def getnewaddress(self, *args):
        return await self.call('getnewaddress', *args)

    async def getnodeaddresses(self, *args):
        return await self.call('getnodeaddresses', *args)

    async def getpeerinfo(self) -> List[dict]:
        """Returns data about each connected network node as a json array of objects."""
        return await self.call('getpeerinfo')

    async def getrawchangeaddress(self, address_type: str) -> str:
        """
        Returns a new Bitcoin address, for receiving change.
        This is for use with raw transactions, NOT normal use.
        """
        return await self.call('getrawchangeaddress', address_type)

    async def getrawmempool(self, verbose: bool = False) -> Union[list, dict]:
        """
        Returns all transaction ids in memory pool as a json array of string transaction ids.

        Hint: use getmempoolentry to fetch a specific transaction from the mempool.
        """
        return await self.call('getrawmempool', verbose)

    async def getrawtransaction(self, txid: str, verbose: bool = True, blockhash: str = None) -> Union[str, dict]:
        """
        Return the raw transaction data.

        By default this function only works for mempool transactions. When called with a blockhash
        argument, getrawtransaction will return the transaction if the specified block is available and
        the transaction is found in that block. When called without a blockhash argument, getrawtransaction
        will return the transaction if it is in the mempool, or if -txindex is enabled and the transaction
        is in a block in the blockchain.

        Hint: Use gettransaction for wallet transactions.

        If verbose is 'true', returns an Object with information about 'txid'.
        If verbose is 'false' or omitted, returns a string that is serialized, hex-encoded data for 'txid'.
        """
        if blockhash is None:
            return await self.call('getrawtransaction', txid, verbose)
        else:
            return await self.call('getrawtransaction', txid, verbose, blockhash)

    async def getreceivedbyaddress(self, *args):
        return await self.call('getreceivedbyaddress', *args)

    async def getreceivedbylabel(self, *args):
        return await self.call('getreceivedbylabel', *args)

    async def getrpcinfo(self) -> dict:
        """Returns details of the RPC server."""
        return await self.call('getrpcinfo')

    async def gettransaction(self, txid: str, include_watchonly: bool = False) -> dict:
        """Get detailed information about in-wallet transaction <txid>"""
        return await self.call('gettransaction', txid, include_watchonly)

    async def gettxout(self, txid: str, n: int, include_mempool: bool = True):
        """Returns details about an unspent transaction output."""
        return await self.call('gettxout', txid, n, include_mempool)

    async def gettxoutproof(self, txids: List[str], blockhash: str = None):
        """
        Returns a hex-encoded proof that "txid" was included in a block.

        NOTE: By default this function only works sometimes. This is when there is an
        unspent output in the utxo for this transaction. To make it always work,
        you need to maintain a transaction index, using the -txindex command line option or
        specify the block in which the transaction is included manually (by blockhash).
        """
        if blockhash is None:
            return await self.call('gettxoutproof', txids)
        else:
            return await self.call('gettxoutproof', txids, blockhash)

    async def gettxoutsetinfo(self) -> dict:
        """
        Returns statistics about the unspent transaction output set.
        Note this call may take some time.
        """
        return await self.call('gettxoutsetinfo')

    async def getunconfirmedbalance(self) -> float:
        """Returns the server's total unconfirmed balance"""
        return await self.call('getunconfirmedbalance')

    async def getwalletinfo(self, *args):
        return await self.call('getwalletinfo', *args)

    async def help(self, command: str) -> str:
        return await self.call('help', command)

    async def importaddress(self, *args):
        return await self.call('importaddress', *args)

    async def importmulti(self, *args):
        return await self.call('importmulti', *args)

    async def importprivkey(self, *args):
        return await self.call('importprivkey', *args)

    async def importprunedfunds(self, *args):
        return await self.call('importprunedfunds', *args)

    async def importpubkey(self, *args):
        return await self.call('importpubkey', *args)

    async def importwallet(self, *args):
        return await self.call('importwallet', *args)

    async def joinpsbts(self, *args):
        return await self.call('joinpsbts', *args)

    async def keypoolrefill(self, *args):
        return await self.call('keypoolrefill', *args)

    async def listaddressgroupings(self, *args):
        return await self.call('listaddressgroupings', *args)

    async def listbanned(self, *args):
        return await self.call('listbanned', *args)

    async def listlabels(self, *args):
        return await self.call('listlabels', *args)

    async def listlockunspent(self, *args):
        return await self.call('listlockunspent', *args)

    async def listreceivedbyaddress(self, *args):
        return await self.call('listreceivedbyaddress', *args)

    async def listreceivedbylabel(self, *args):
        return await self.call('listreceivedbylabel', *args)

    async def listsinceblock(self, *args):
        return await self.call('listsinceblock', *args)

    async def listtransactions(self, *args):
        return await self.call('listtransactions', *args)

    async def listunspent(self, *args):
        return await self.call('listunspent', *args)

    async def listwalletdir(self, *args):
        return await self.call('listwalletdir', *args)

    async def listwallets(self, *args):
        return await self.call('listwallets', *args)

    async def loadwallet(self, *args):
        return await self.call('loadwallet', *args)

    async def lockunspent(self, *args):
        return await self.call('lockunspent', *args)

    async def logging(self, *args):
        return await self.call('logging', *args)

    async def ping(self) -> None:
        """
        Requests that a ping be sent to all other nodes, to measure ping time.
        Results provided in getpeerinfo, pingtime and pingwait fields are decimal seconds.
        Ping command is handled in queue with all other commands, so it measures processing backlog, not just network ping.
        """
        return await self.call('ping')

    async def preciousblock(self, *args):
        return await self.call('preciousblock', *args)

    async def prioritisetransaction(self, *args):
        return await self.call('prioritisetransaction', *args)

    async def pruneblockchain(self, *args):
        return await self.call('pruneblockchain', *args)

    async def removeprunedfunds(self, *args):
        return await self.call('removeprunedfunds', *args)

    async def rescanblockchain(self, *args):
        return await self.call('rescanblockchain', *args)

    async def savemempool(self, *args):
        return await self.call('savemempool', *args)

    async def scantxoutset(self, *args):
        return await self.call('scantxoutset', *args)

    async def sendmany(self, *args):
        return await self.call('sendmany', *args)

    async def sendrawtransaction(self, *args):
        return await self.call('sendrawtransaction', *args)

    async def sendtoaddress(self, *args):
        return await self.call('sendtoaddress', *args)

    async def setban(self, *args):
        return await self.call('setban', *args)

    async def sethdseed(self, *args):
        return await self.call('sethdseed', *args)

    async def setlabel(self, *args):
        return await self.call('setlabel', *args)

    async def setnetworkactive(self, *args):
        return await self.call('setnetworkactive', *args)

    async def settxfee(self, *args):
        return await self.call('settxfee', *args)

    async def signmessage(self, *args):
        return await self.call('signmessage', *args)

    async def signmessagewithprivkey(self, *args):
        return await self.call('signmessagewithprivkey', *args)

    async def signrawtransactionwithkey(self, *args):
        return await self.call('signrawtransactionwithkey', *args)

    async def signrawtransactionwithwallet(self, *args):
        return await self.call('signrawtransactionwithwallet', *args)

    async def stop(self, *args):
        return await self.call('stop', *args)

    async def submitblock(self, *args):
        return await self.call('submitblock', *args)

    async def submitheader(self, *args):
        return await self.call('submitheader', *args)

    async def testmempoolaccept(self, *args):
        return await self.call('testmempoolaccept', *args)

    async def unloadwallet(self, *args):
        return await self.call('unloadwallet', *args)

    async def uptime(self) -> int:
        """Returns the total uptime of the server."""
        return await self.call('uptime')

    async def utxoupdatepsbt(self, *args):
        return await self.call('utxoupdatepsbt', *args)

    async def validateaddress(self, *args):
        return await self.call('validateaddress', *args)

    async def verifychain(self, *args):
        return await self.call('verifychain', *args)

    async def verifymessage(self, *args):
        return await self.call('verifymessage', *args)

    async def verifytxoutproof(self, *args):
        return await self.call('verifytxoutproof', *args)

    async def walletcreatefundedpsbt(self, *args):
        return await self.call('walletcreatefundedpsbt', *args)

    async def walletlock(self, *args):
        return await self.call('walletlock', *args)

    async def walletpassphrase(self, *args):
        return await self.call('walletpassphrase', *args)

    async def walletpassphrasechange(self, *args):
        return await self.call('walletpassphrasechange', *args)

    async def walletprocesspsbt(self, *args):
        return await self.call('walletprocesspsbt', *args)
