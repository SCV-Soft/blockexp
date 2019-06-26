from typing import Union

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

    async def getaddednodeinfo(self, *args):
        return await self.call('getaddednodeinfo', *args)

    async def getaddressesbylabel(self, *args):
        return await self.call('getaddressesbylabel', *args)

    async def getaddressinfo(self, *args):
        return await self.call('getaddressinfo', *args)

    async def getbalance(self, *args):
        return await self.call('getbalance', *args)

    async def getbestblockhash(self, *args):
        return await self.call('getbestblockhash', *args)

    async def getblock(self, blockhash: str, verbosity: int = 1) -> Union[str, dict]:
        return await self.call('getblock', blockhash, verbosity)

    async def getblockchaininfo(self, *args):
        return await self.call('getblockchaininfo', *args)

    async def getblockcount(self, *args):
        return await self.call('getblockcount', *args)

    async def getblockhash(self, *args):
        return await self.call('getblockhash', *args)

    async def getblockheader(self, *args):
        return await self.call('getblockheader', *args)

    async def getblockstats(self, *args):
        return await self.call('getblockstats', *args)

    async def getblocktemplate(self, *args):
        return await self.call('getblocktemplate', *args)

    async def getchaintips(self, *args):
        return await self.call('getchaintips', *args)

    async def getchaintxstats(self, *args):
        return await self.call('getchaintxstats', *args)

    async def getconnectioncount(self, *args):
        return await self.call('getconnectioncount', *args)

    async def getdescriptorinfo(self, *args):
        return await self.call('getdescriptorinfo', *args)

    async def getdifficulty(self, *args):
        return await self.call('getdifficulty', *args)

    async def getmemoryinfo(self, *args):
        return await self.call('getmemoryinfo', *args)

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

    async def getnetworkhashps(self, *args):
        return await self.call('getnetworkhashps', *args)

    async def getnetworkinfo(self, *args):
        return await self.call('getnetworkinfo', *args)

    async def getnewaddress(self, *args):
        return await self.call('getnewaddress', *args)

    async def getnodeaddresses(self, *args):
        return await self.call('getnodeaddresses', *args)

    async def getpeerinfo(self, *args):
        return await self.call('getpeerinfo', *args)

    async def getrawchangeaddress(self, *args):
        return await self.call('getrawchangeaddress', *args)

    async def getrawmempool(self, *args):
        return await self.call('getrawmempool', *args)

    async def getrawtransaction(self, *args):
        return await self.call('getrawtransaction', *args)

    async def getreceivedbyaddress(self, *args):
        return await self.call('getreceivedbyaddress', *args)

    async def getreceivedbylabel(self, *args):
        return await self.call('getreceivedbylabel', *args)

    async def getrpcinfo(self, *args):
        return await self.call('getrpcinfo', *args)

    async def gettransaction(self, *args):
        return await self.call('gettransaction', *args)

    async def gettxout(self, *args):
        return await self.call('gettxout', *args)

    async def gettxoutproof(self, *args):
        return await self.call('gettxoutproof', *args)

    async def gettxoutsetinfo(self, *args):
        return await self.call('gettxoutsetinfo', *args)

    async def getunconfirmedbalance(self, *args):
        return await self.call('getunconfirmedbalance', *args)

    async def getwalletinfo(self, *args):
        return await self.call('getwalletinfo', *args)

    async def help(self, *args):
        return await self.call('help', *args)

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

    async def ping(self, *args):
        return await self.call('ping', *args)

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

    async def uptime(self, *args):
        return await self.call('uptime', *args)

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
