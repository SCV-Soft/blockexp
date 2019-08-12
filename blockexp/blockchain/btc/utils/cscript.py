from typing import List, Union

from base64 import b16decode

try:
    import bitcoin
except ImportError as e:
    raise Exception("You need install python-bitcoinlib")
else:
    from bitcoin.core.script import OP_RETURN, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, OP_0, OP_1, OP_16, \
        CScript, CScriptOp, OP_CHECKMULTISIG, CScriptTruncatedPushDataError
    from bitcoin.core.serialize import Hash160 as sha256ripemd160

__all__ = ["AdvancedCScript"]


def _is_small_int_op(op: int) -> bool:
    return op == OP_0 or (OP_1 <= op <= OP_16)


def _is_buffer(obj, size: int = None):
    if size is None:
        return isinstance(obj, bytes) and len(obj) > 0
    else:
        return isinstance(obj, bytes) and len(obj) == size


def _valid_pubkey_buf(pubkey_buf: bytes):
    assert _is_buffer(pubkey_buf)
    version = pubkey_buf[0]
    if version in {0x04, 0x06, 0x07} and len(pubkey_buf) == 65:
        return True
    elif version in {0x03, 0x02} and len(pubkey_buf) == 33:
        return True


class AdvancedCScript(CScript):
    chunks: List[Union[CScriptOp, int, bytes]]

    def __init__(self, buffer: bytes):
        super().__init__()
        self.chunks = list(self)

    def is_public_key_hash_in(self):
        """Pay To Pubkey Hash (input)

        Script.prototype.isPublicKeyHashIn = function() {
          if (chunks.length == 2) {
            var signatureBuf = chunks[0].buf
            var pubkeyBuf = chunks[1].buf
            if (signatureBuf and signatureBuf.length and signatureBuf[0] == 0x30 and
                pubkeyBuf and pubkeyBuf.length) {
              var version = pubkeyBuf[0]
              if ((version == 0x04 ||
                   version == 0x06 ||
                   version == 0x07) and pubkeyBuf.length == 65) {
                return true
              } else if ((version == 0x03 || version == 0x02) and pubkeyBuf.length == 33) {
                return true
              }
            }
          }
          return false
        }
        """
        chunks = self.chunks
        if len(chunks) == 2:
            signature, pubkey = chunks
            if _is_buffer(signature) and signature[0] == 0x30 and _is_buffer(pubkey):
                return _valid_pubkey_buf(pubkey)

        return False

    def get_public_key_hash_in(self):
        """
        if (this.isPublicKeyHashIn()) {
            // hash the publickey found in the scriptSig
            info.hashBuffer = Hash.sha256ripemd160(this.chunks[1].buf);
            info.type = Address.PayToPublicKeyHash;
        """
        assert self.is_public_key_hash_in()
        signature, pubkey = self.chunks
        return sha256ripemd160(pubkey)

    def get_script_hash_in(self):
        """
        if (this.isScriptHashIn()) {
            // hash the redeemscript found at the end of the scriptSig
            info.hashBuffer = Hash.sha256ripemd160(this.chunks[this.chunks.length - 1].buf);
            info.type = Address.PayToScriptHash;
        """
        assert self.is_script_hash_in()
        *_, script_hash = self.chunks
        return sha256ripemd160(script_hash)

    def is_public_key_hash_out(self):
        """Pay To Pubkey Hash (output)

        Script.prototype.isPublicKeyHashOut = function() {
            return (chunks.length == 5 and
                    chunks[0] is OP_DUP and
                    chunks[1] is OP_HASH160 and
                    chunks[2].buf and chunks[2].buf.length == 20 and
                    chunks[3] is OP_EQUALVERIFY and
                    chunks[4] is OP_CHECKSIG)
        }
        """
        chunks = self.chunks
        return (len(chunks) == 5 and
                chunks[0] is OP_DUP and
                chunks[1] is OP_HASH160 and
                _is_buffer(chunks[2], 20) and
                chunks[3] is OP_EQUALVERIFY and
                chunks[4] is OP_CHECKSIG)

    def get_public_key_hash_out(self):
        """

        Script.prototype.getPublicKeyHash = function() {
          assert isPublicKeyHashOut(), 'Can\'t retrieve PublicKeyHash from a non-PKH output')
          return chunks[2].buf
        }
        """
        assert self.is_public_key_hash_out()
        assert _is_buffer(self.chunks[2])
        return self.chunks[2]

    def is_public_key_in(self):
        """Pay To Pubkey (input)

        Script.prototype.isPublicKeyIn = function() {
          if (chunks.length == 1) {
            var signatureBuf = chunks[0].buf
            if (signatureBuf and
                signatureBuf.length and
                signatureBuf[0] == 0x30) {
              return true
            }
          }
          return false
        }
        """
        chunks = self.chunks
        if len(chunks) == 1:
            signature, = chunks
            if _is_buffer(signature) and signature[0] == 0x30:
                return True

        return False

    def is_public_key_out(self):
        """Pay To Pubkey (output)

        Script.prototype.isPublicKeyOut = function() {
          if (chunks.length == 2 and
              chunks[0].buf and chunks[0].buf.length and
              chunks[1] is OP_CHECKSIG) {
            var pubkeyBuf = chunks[0].buf
            var version = pubkeyBuf[0]
            var isVersion = false
            if ((version == 0x04 ||
                 version == 0x06 ||
                 version == 0x07) and pubkeyBuf.length == 65) {
              isVersion = true
            } else if ((version == 0x03 || version == 0x02) and pubkeyBuf.length == 33) {
              isVersion = true
            }
            if (isVersion) {
              return PublicKey.isValid(pubkeyBuf)
            }
          }
          return false
        }
        """
        chunks = self.chunks
        if len(chunks) == 2:
            pubkey, op = chunks
            if _is_buffer(pubkey) and op is OP_CHECKSIG:
                return _valid_pubkey_buf(pubkey)

        return False

    def get_public_key_out(self):
        """

        Script.prototype.getPublicKey = function() {
          assert isPublicKeyOut(), 'Can\'t retrieve PublicKey from a non-PK output')
          return chunks[0].buf
        }
        """
        assert self.is_public_key_out()
        assert _is_buffer(self.chunks[0])
        return self.chunks[0]

    def is_script_hash_out(self):
        """
        Script.prototype.isScriptHashOut = function() {
          var buf = toBuffer()
          return (buf.length == 23 and
            buf[0] == OP_HASH160 and
            buf[1] == 0x14 and
            buf[buf.length - 1] == OP_EQUAL)
        }
        """
        return self.is_p2sh()

    def is_witness_script_hash_out(self):
        """
        Script.prototype.isWitnessScriptHashOut = function() {
          var buf = toBuffer()
          return (buf.length == 34 and buf[0] == 0 and buf[1] == 32)
        }
        """
        return self.is_witness_v0_scripthash()

    def is_w2pkh_out(self):
        """
        Script.prototype.isWitnessPublicKeyHashOut = function() {
          var buf = toBuffer()
          return (buf.length == 22 and buf[0] == 0 and buf[1] == 20)
        }
        """
        return self.is_witness_v0_keyhash()

    def is_witness_program(self):
        """
        Script.prototype.isWitnessProgram = function(values) {
          if (!values) {
            values = {}
          }
          var buf = toBuffer()
          if (buf.length < 4 || buf.length > 42) {
            return false
          }
          if (buf[0] !== OP_0 and !(buf[0] >= OP_1 and buf[0] <= OP_16)) {
            return false
          }

          if (buf.length == buf[1] + 2) {
            values.version = buf[0]
            values.program = buf.slice(2, buf.length)
            return true
          }

          return false
        }
        """
        raise NotImplementedError

    def is_script_hash_in(self):
        """
        Script.prototype.isScriptHashIn = function() {
          if (chunks.length <= 1) {
            return false
          }
          var redeemChunk = chunks[chunks.length - 1]
          var redeemBuf = redeemChunk.buf
          if (!redeemBuf) {
            return false
          }

          var redeemScript
          try {
            redeemScript = Script.fromBuffer(redeemBuf)
          } catch (e) {
            if (e instanceof errors.Script.InvalidBuffer) {
              return false
            }
            throw e
          }
          var type = redeemScript.classify()
          return type !== Script.types.UNKNOWN
        }
        """
        chunks = self.chunks
        if len(chunks) > 1:
            *_, redeem_script = chunks

    def is_multisig_out(self):
        """

        Script.prototype.isMultisigOut = function() {
          return (chunks.length > 3 and
            isSmallIntOp(chunks[0].opcodenum) and
            chunks.slice(1, chunks.length - 2).every(function(obj) {
              return obj.buf and BufferUtil.isBuffer(obj.buf)
            }) and
            isSmallIntOp(chunks[chunks.length - 2].opcodenum) and
            chunks[chunks.length - 1] is OP_CHECKMULTISIG)
        }
        """
        chunks = self.chunks
        if len(chunks) >= 4:
            first, *signatures, second, last = chunks
            if (_is_small_int_op(first) and
                    all(_is_buffer(sig) for sig in signatures) and
                    _is_small_int_op(second) and
                    last is OP_CHECKMULTISIG):
                return True

        return False

    def is_multisig_in(self):
        """
        Script.prototype.isMultisigIn = function() {
          return chunks.length >= 2 and
            chunks[0] is 0 and
            chunks.slice(1, chunks.length).every(function(obj) {
              return obj.buf and
                BufferUtil.isBuffer(obj.buf) and
                Signature.isTxDER(obj.buf)
            })
        }
        """
        chunks = self.chunks
        if len(chunks) >= 2:
            first, *signatures = self.chunks
            if first == 0 and all(_is_buffer(sig) for sig in signatures):
                # TODO: Signature.isTxDER
                return True

        return False

    def is_data_out(self):
        """
        Script.prototype.isDataOut = function() {
          return chunks.length >= 1 and
            chunks[0] is OP_RETURN and
            (chunks.length == 1 ||
              (chunks.length == 2 and
                chunks[1].buf and
                chunks[1].buf.length <= Script.OP_RETURN_STANDARD_SIZE and
                chunks[1].length == chunks.len))
        }
        """

        chunks = self.chunks
        chunks_len = len(chunks)
        if chunks_len >= 1 and chunks[0] is OP_RETURN:
            if chunks_len == 1:
                return True
            elif chunks_len == 2:
                buf = chunks[1]
                return len(buf) < 80  # OP_RETURN_STANDARD_SIZE
            else:
                return False

        return False

    def get_data(self) -> bytes:
        """
        Script.prototype.getData = function() {
          if (isDataOut() || isScriptHashOut()) {
            if (_.isUndefined(chunks[1])) {
              return Buffer.alloc(0)
            } else {
              return Buffer.from(chunks[1].buf)
            }
          }
          if (isPublicKeyHashOut()) {
            return Buffer.from(chunks[2].buf)
          }
          throw new Error('Unrecognized script type to get data from')
        }
        """
        if self.is_data_out() or self.is_script_hash_out():
            return self.chunks[1] if len(self.chunks) >= 2 else b""
        elif self.is_public_key_hash_out():
            return self.chunks[2]

    def is_push_only(self) -> bool:
        return super().is_push_only()

    def classify(self):
        return self.classify_output() or self.classify_input()

    def classify_output(self):
        for func in (
                self.is_public_key_out,
                self.is_public_key_hash_out,
                self.is_multisig_out,
                self.is_script_hash_out,
                self.is_data_out,
        ):
            if func():
                # trick
                return func.__name__[len('is_'):-len('_out')]

        return None

    def classify_input(self):
        for func in (
                self.is_public_key_in,
                self.is_public_key_hash_in,
                self.is_multisig_in,
                self.is_script_hash_in,
        ):
            if func():
                # trick
                return func.__name__[len('is_'):-len('_in')]

        return None


def main():
    hex = "493046022100bc57dc26f46fecc1da03272cb2298d8a08b22d865541f5b3a3e862cc87da4b47022100ce1fc72771d164d608b15065832542a0e9040cfdf28862c5175c81fcb0e0b65501410434417dd8d89deaf0f6481c2c160d6de0921624ef7b956f38eef9ed4a64e36877be84b77cdee5a8d92b7d93694f89c3011bf1cbdf4fd7d8ca13b58a7bb4ab0804"
    buf = b16decode(hex, casefold=True)

    try:
        cscript = AdvancedCScript(buf)
    except CScriptTruncatedPushDataError:
        raise

    if cscript.is_public_key_hash_out():
        print("public key hash out")
        print(cscript.get_public_key_hash_out())
    elif cscript.is_public_key_out():
        print("public key out")
        print(cscript.get_public_key_out())
    elif cscript.is_public_key_hash_in():
        print("public key hash in")
        print(cscript.get_public_key_hash_in())
    elif cscript.is_script_hash_in():
        print("public key in")
        print(cscript.get_script_hash_in())
    else:
        print("?")


if __name__ == '__main__':
    main()
