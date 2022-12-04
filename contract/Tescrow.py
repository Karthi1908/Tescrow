import smartpy as sp

def string_of_nat(params):
    id = window.smartpyContext.nextId()
    c   = sp.map({x : str(x) for x in range(0, 10)})
    x   = sp.local('x %s' % id, params)
    res = sp.local('res %s' % id, [])
    sp.if x.value == 0:
        res.value.push('0')
    sp.while 0 < x.value:
        res.value.push(c[x.value % 10])
        x.value //= 10
    return sp.concat(res.value)

FA2 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")
FA12 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA1.2.py")

class EToken(FA2.FA2):
    pass

class FAToken(FA12.FA12):
    pass


class Error_message:
    def __init__(self):
        self.prefix = "PRED_"
    def make(self, s): return (self.prefix + s)
    def not_admin(self):             return self.make("NOT_ADMIN")
    def invalid_status(self):        return self.make("INVALID_STATUS")
    def not_registered(self):        return self.make("NOT_REGISTERED")
    def check_fee(self):             return self.make("INCORRECT_FEE")
    def dup_token_details(self):     return self.make("DUP_TOKEN_DETAILS")



class Client(sp.Contract):
    def __init__(self, admin, tokenAddress):
        self.error_message = Error_message()
        self.init(
            admin                   = admin,
            admins                  = sp.set([admin]),
            tokenAddress            = tokenAddress,
            oracleAddress           = admin,
            proposerCut             = sp.nat(50),
            commission              = sp.nat(2),
            Id                      = sp.nat(10),
            escrowFee           = sp.mutez(2000000),
            tokenRegister         = sp.map(tkey = sp.TString, tvalue = sp.TRecord(address = sp.TAddress, id = sp.TNat, type = sp.TString, balance = sp.TNat)),
            escrows             = sp.big_map(tkey = sp.TNat, tvalue = sp.TRecord( endTime= sp.TTimestamp,
                                        resultRef= sp.TString,
                                        gameRef= sp.TString,
                                        players= sp.TList(sp.TString),
                                        playerCount =sp.TNat,
                                        escrowRef= sp.TString,
                                        escrowStatus= sp.TString,
                                        gameResult= sp.TString,
                                        proposer= sp.TAddress,
                                        startTime= sp.TTimestamp,
                                        tokenEscrowed  = sp.TString,
                                        tokenAmount    =  sp.TNat)),
            player_snapshot           = sp.map(tkey = sp.TString,tvalue = sp.TNat),
            escrowSnapshot      = sp.big_map(tkey = sp.TNat, tvalue =sp.TMap(sp.TString, sp.TNat)),
            tokenDetails     = sp.big_map(tkey = sp.TRecord(option = sp.TString, escrow = sp.TNat), tvalue = sp.TNat),
            tokenMultiplier         = sp.big_map(tkey = sp.TNat, tvalue = sp.TNat),
            tempCounter             = 0,
            )
     
    @sp.entry_point
    def addTokenAddress(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.tokenAddress = params.tokenContract
    
    @sp.entry_point
    def addOracleAddress(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.oracleAddress = params.oracle

    @sp.entry_point
    def setCommission(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.commission = params

    @sp.entry_point
    def setProposerCut(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.proposerCut = params

    @sp.entry_point
    def setescrowFee(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.escrowFee = params

    @sp.entry_point
    def updateTokenRegister(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.updateTokenRegistry(params)

    def updateTokenRegistry(self, params):
    
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        sp.verify(~ self.data.tokenRegister.contains(params.tokenName), message = self.error_message.dup_token_details()) # 'Duplicate Token Details'
        self.data.tokenRegister[params.tokenName] = sp.record( address = params.tokenContract,
                                                                id    = params.tokenId,
                                                                type   = params.tokenType,
                                                                balance = 0)

    @sp.entry_point
    def addAdmins(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.admins.add(params)

    @sp.entry_point
    def removeAdmins(self, params):
        sp.verify(sp.sender == self.data.admin, message = self.error_message.not_admin())
        self.data.admins.remove(params)

    @sp.entry_point
    def newEscrow(self,
                    gameRef      = sp.TString,
                    start               = sp.TTimestamp,
                    end                 = sp.TTimestamp,
                    players   = [],
                    amount   = sp.TNat,
                    playerCount = sp.TNat,
                    resultRef = sp.TString,
                    tname =sp.TString,
                    tamount = sp.TNat
                    ):
        
        sp.verify(sp.amount >= self.data.escrowFee, message = self.error_message.check_fee())
        escrowId = self.data.Id
        ref = string_of_nat(self.data.Id)
        currTime   = sp.now
        escrow   = sp.record(
                               gameRef        = gameRef,
                               proposer       = sp.sender,
                               startTime      = start,
                               endTime        = end,
                               players        = players,
                               playerCount    = playerCount,
                               escrowStatus   = "",
                               gameResult     = "",
                               resultRef      = resultRef,
                               escrowRef      = ref,
                               tokenEscrowed  = tname,
                               tokenAmount    = tamount
                            )
        self.data.escrows[escrowId] = escrow
        self.checkEscrowStatus(escrowId)
        self.initializeStakingParams(escrowId)
        self.data.Id = self.data.Id + 1
        sp.send(self.data.admin, sp.amount - sp.mutez(500000))


    @sp.entry_point
    def addPlayers(self, escrowId, player):
        sp.verify(self.data.escrows[escrowId].playerCount >= sp.len(self.data.escrows[escrowId].players), message = self.error_message.check_fee())
        self.data.escrows[escrowId].players.push(player)
        
    @sp.entry_point
    def checkStatus(self, escrowId):
        self.checkEscrowStatus(escrowId)


    
    def checkEscrowStatus(self, escrowId):

        sp.if self.data.escrows[escrowId].startTime <= sp.now:
            sp.if self.data.escrows[escrowId].endTime > sp.now:
                sp.if ((self.data.escrows[escrowId].escrowStatus == "Preparing") | (self.data.escrows[escrowId].escrowStatus == "")):
                    self.updateEscrowStatus(escrowId = escrowId, escrowStatus = "Open")
            sp.else:
                sp.if (self.data.escrows[escrowId].escrowStatus == "Open"):
                    self.updateEscrowStatus(escrowId = escrowId, escrowStatus = "Closed")
        sp.else:
            self.updateEscrowStatus(escrowId = escrowId, escrowStatus = "Preparing")

    @sp.entry_point
    def updateStatus(self, escrowId, escrowStatus):
        _user = sp.set([self.data.admin, self.data.oracleAddress])
        sp.verify(_user.contains(sp.sender), message = self.error_message.not_admin() )
        self.updateEscrowStatus(escrowId = escrowId, escrowStatus = escrowStatus )
        _user=sp.set()



    def updateEscrowStatus(self, escrowId, escrowStatus):
        
        sp.if escrowStatus == "Cancelled" :
            self.data.escrows[escrowId].endTime = sp.now
        self.data.escrows[escrowId].escrowStatus = escrowStatus
      


   
    def initializeStakingParams(self, pID):
        x              =""

        sp.for x in self.data.escrows[pID].players:
            self.data.player_snapshot[x]         = 0
            key                                = sp.record(escrow = pID, option = x)
            self.data.tokenDetails[key] = self.data.tempCounter + pID * 10
            self.data.tokenMultiplier[self.data.tokenDetails[key]] = 0
            self.data.tempCounter             += 1

        self.data.player_snapshot['Total']       = 0
        self.data.escrowSnapshot [pID]  = self.data.player_snapshot
        self.data.player_snapshot                = sp.map(tkey = sp.TString, tvalue = None)
        x=""
        self.data.tempCounter                  = 0
  
    @sp.entry_point
    def stakeOnEscrow(self, pID, player):


        self.checkEscrowStatus(pID)
        sp.verify(self.data.escrows[pID].escrowStatus == "Open", message = self.error_message.invalid_status())
        tokenName =self.data.escrows[pID].tokenEscrowed
        amount = self.data.escrows[pID].tokenAmount

        sp.if tokenName == 'Tez':
           sp.verify(self.data.escrows[pID].tokenAmount == sp.utils.mutez_to_nat(sp.amount) / 10000, message = self.error_message.invalid_status())
            
        sp.else: 
            sp.if self.data.tokenRegister[tokenName].type == 'FA2':
                self.transferToken( _tokenAddress = self.data.tokenRegister[tokenName].address, 
                                    _from         = sp.sender, 
                                    _to           = sp.self_address, 
                                    _amount       = amount ,
                                    _tokenID      = self.data.tokenRegister[tokenName].id)               
            sp.else:              
                self.transferFA1( _tokenAddress   = self.data.tokenRegister[tokenName].address, 
                                    _from         = sp.sender, 
                                    _to           = sp.self_address, 
                                    _amount       = amount
                                  )
        
        self.data.escrowSnapshot [pID][player]           += amount
        self.data.escrowSnapshot [pID]['Total']        += amount
        
        a      = string_of_nat(self.data.tokenDetails[sp.record(escrow = pID, option = player)])
        
        b      = sp.pack(player)
        enplayer = sp.slice(b, 6, sp.as_nat(sp.len(b) - 6)).open_some()

        c      = sp.pack("Pid: " + self.data.escrows[pID].escrowRef + " Token ID: " + a)
               
        enPID  = sp.slice(c, 6, sp.as_nat(sp.len(c) - 6)).open_some() 
        
        tokenMetadata = sp.map(l = {
            # Remember that michelson wants map already in ordered
            "decimals" : sp.utils.bytes_of_string("%d" % 0),
            "name"     : enPID,
            "symbol"   : enplayer
        })
        self.mintNewToken(clientAddress  = sp.sender,
                          tokenId        = self.data.tokenDetails[sp.record(escrow = pID, option = player)],
                          tokenAmount    = sp.utils.mutez_to_nat(sp.amount)/10000, #100 tokens for 1 tez
                          tokenMetadata  = tokenMetadata)
    
    
    def mintNewToken(self, clientAddress, tokenId, tokenAmount, tokenMetadata):
        
        datatype   = sp.TRecord(address = sp.TAddress,
                               token_id = sp.TNat,
                               amount   = sp.TNat,
                               metadata = sp.TMap(sp.TString, sp.TBytes))
        
        tContract  = sp.contract(datatype, self.data.tokenAddress, "mint").open_some()

        params     = sp.record(address  = clientAddress,
                             token_id   = tokenId,
                             amount     = tokenAmount,
                             metadata   = tokenMetadata)
        sp.transfer(params, sp.mutez(0), tContract)

    @sp.entry_point
    def gameResults(self, pID, result , multiplier):
    
        _user = sp.set([self.data.admin, self.data.oracleAddress])
        sp.verify(_user.contains(sp.sender), message = self.error_message.not_admin() )
        sp.verify(self.data.escrows[pID].escrowStatus == "Closed", message = self.error_message.invalid_status())
        _temp    = self.data.escrowSnapshot [pID][result]
        #_multi   = self.data.escrowSnapshot [pID]['Total'] * abs(100 - self.data.commission) / (self.data.escrowSnapshot [pID][result] + 1)
        _key     = sp.record(escrow = pID, option = result)
        self.data.tokenMultiplier[self.data.tokenDetails[_key]] = multiplier
        self.data.escrows[pID].escrowStatus         = "Result Declared"
        self.data.escrows[pID].gameResult     =  result
        _proposerCut = sp.utils.nat_to_mutez(self.data.proposerCut * self.data.escrowSnapshot [pID]['Total'] )
        sp.send(self.data.escrows[pID].proposer, _proposerCut)

    @sp.entry_point
    def redeemTokens(self, params) :
       
        self.transferToken( _tokenAddress = self.data.tokenAddress, 
                            _from = sp.sender,
                            _to = sp.self_address,
                            _amount   = params.amount,
                            _tokenID = params.tokenID)
        amountRedeemed = sp.utils.nat_to_mutez(params.amount * self.data.tokenMultiplier[params.tokenID] * 100)
        sp.send(sp.sender, amountRedeemed)
         
    def transferToken(self, _tokenAddress, _from, _to, _amount, _tokenID) :

        transferType = self.transfer_type()
        ttContract   = sp.contract(transferType, _tokenAddress, "transfer").open_some()
        tx           = [sp.record(to_     = _to,
                                 token_id = _tokenID,
                                 amount   = _amount)]
        payload       = [sp.record( from_ = _from,
                                    txs   = tx)]
        sp.transfer(payload, sp.mutez(0), ttContract)
    
    def transferFA1(self, _tokenAddress, _from, _to, _amount):
    
        transferTypeFA1 = sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value")))
        ttContract      = sp.contract(transferTypeFA1, _tokenAddress, "transfer").open_some()
        tx              = sp.record(from_ = _from,
                                     to_  = _to,
                                    value = _amount)
        sp.transfer(tx, sp.mutez(0), ttContract)


    def get_transfer_type(self):
        tx_type = sp.TRecord(to_ = sp.TAddress,
                             token_id = sp.TNat,
                             amount = sp.TNat).layout(
                ("to_", ("token_id", "amount"))
            )
        transfer_type = sp.TRecord(from_ = sp.TAddress,
                                   txs = sp.TList(tx_type)).layout(
                                       ("from_", "txs"))
        return transfer_type

    def transfer_type(self):
        return sp.TList(self.get_transfer_type())


    

@sp.add_test(name = "Escrow")
def test():
    scenario = sp.test_scenario()

    admin = sp.address("tz1gRxoWf9uLmGrqpv3Knkdhr64QcUu8C9zs")
    alice   = sp.test_account("Alice")
    bob     = sp.test_account("Robert")
    clark   = sp.test_account("Clark")
    daisy   = sp.test_account("Daisy")
    eve     = sp.test_account("Eve")
    frank   = sp.test_account("Frank")
    garrett = sp.test_account("Garrett")
    honey   = sp.test_account("Honey")
    irene   = sp.test_account("Irene")
    james   = sp.test_account("James")
    karen   = sp.test_account("Karen")
    love    = sp.test_account("Love")
   
    mark = sp.test_account("Mark")
    elon = sp.test_account("Mars")
    
    eToken = EToken(FA2.FA2_config(assume_consecutive_token_ids = False), admin = admin, metadata = sp.big_map({"": sp.utils.bytes_of_string("tezos-storage:content"),"content": sp.utils.bytes_of_string("""{"name" : "Escrow", "version" : "01"}""")}))
    scenario += eToken

    client = Client(admin = admin, tokenAddress = admin)
    scenario += client
    scenario += client.addTokenAddress(tokenContract = eToken.address).run(sender =admin)



    scenario += eToken.set_administrator(client.address).run(sender =admin)
    scenario += client.newEscrow(
                    gameRef      = "Fantasy Cricket Tournament",
                    start               = sp.now,
                    end                 = sp.now.add_seconds(1000),
                    players   = ["CSK","MI","DC","RCB","SRH"],
                    playerCount = 5,
                    resultRef = "Oracle",
                    tname = 'Tez',
                    tamount = 100).run(sender = alice.address, amount = sp.tez(2))
    scenario += client.stakeOnEscrow(pID= sp.nat(10) , player = "CSK").run(sender = admin, amount = sp.mutez(1000000))
    scenario += client.stakeOnEscrow(pID= sp.nat(10) , player = "MI").run(sender = alice, amount = sp.mutez(1000000))
    scenario += client.stakeOnEscrow(pID= sp.nat(10) , player = "DC").run(sender = bob, amount = sp.mutez(1000000))
    scenario += client.stakeOnEscrow(pID= sp.nat(10) , player = "RCB").run(sender = clark, amount = sp.mutez(1000000))
    scenario += client.stakeOnEscrow(pID= sp.nat(10) , player = "SRH").run(sender = daisy, amount = sp.mutez(1000000))
  
    
    
    scenario += client.newEscrow(
                    gameRef      = "Assassin Creed",
                    start               = sp.now,
                    end                 = sp.now.add_seconds(1000),
                    players   = ["YaYa","NoNo"],
                    playerCount = 5,
                    resultRef = "oracle",
                    tname = 'Tez',
                    tamount = 100).run(sender = alice, amount = sp.tez(2))

   
   
    scenario += client.stakeOnEscrow(pID= sp.nat(11) , player = "YaYa").run(sender = admin, amount = sp.mutez(1000000))
    scenario += client.stakeOnEscrow(pID= sp.nat(11) , player = "NoNo").run(sender = bob, amount = sp.mutez(1000000))
    scenario += client.updateStatus(escrowId = 11, escrowStatus = "Closed").run(sender = admin)
    scenario += client.gameResults(pID = 10, result = "MI", multiplier = 90).run(sender = admin, valid = False)
    scenario += client.updateStatus(escrowId = 10, escrowStatus = "Closed").run(sender = admin)
    scenario += client.gameResults(pID = 10, result = "DC",multiplier = 90).run(sender = admin)
    scenario += client.gameResults(pID = 11, result = "NoNo" ,multiplier = 90).run(sender = admin)
    scenario += client.redeemTokens(amount = 100, tokenID = 102).run(sender = bob)

    scenario.h1("FA12 Contract")
    token_metadata = {
            "decimals"    : "18",               # Mandatory by the spec
            "name"        : "My Great Token",   # Recommended
            "symbol"      : "MGT",              # Recommended
            # Extra fields
            "icon"        : 'https://smartpy.io/static/img/logo-only.svg'
        }
    contract_metadata = {
            "" : "ipfs://QmaiAUj1FFNGYTu8rLBjc3eeN9cSKwaF8EGMBNDmhzPNFd",
        }
    fa1 = FAToken(
            admin,
            config              = FA12.FA12_config(support_upgradable_metadata = True),
            token_metadata      = token_metadata,
            contract_metadata   = contract_metadata
        )
    scenario += fa1

    scenario += fa1.mint(address = alice.address, value = 120000).run(sender = admin)
    
    daoToken  = EToken(FA2.FA2_config(assume_consecutive_token_ids = False), admin = admin, metadata = sp.big_map({"": sp.utils.bytes_of_string("tezos-storage:content"),"content": sp.utils.bytes_of_string("""{"name" : "Multisig", "version" : "01"}""")}))
    scenario += daoToken

    dummyToken  = EToken(FA2.FA2_config(assume_consecutive_token_ids = False), admin = admin, metadata = sp.big_map({"": sp.utils.bytes_of_string("tezos-storage:content"),"content": sp.utils.bytes_of_string("""{"name" : "Dummy", "version" : "01"}""")}))
    scenario   += dummyToken

    scenario += client.updateTokenRegister(tokenName = "Multipurpose", tokenContract = daoToken.address, tokenId =0, tokenType = 'FA2').run(sender = admin)
    scenario += client.updateTokenRegister(tokenName = "Dummy", tokenContract = dummyToken.address, tokenId =0, tokenType = 'FA2').run(sender = admin)
    scenario += client.updateTokenRegister(tokenName = "Great Token", tokenContract = fa1.address, tokenId =0, tokenType = 'FA1').run(sender = admin)
    scenario += client.updateTokenRegister(tokenName = "Tez", tokenContract = sp.address("KT1Tezooo1zzSmartPyzzSTATiCzzzyfC8eF"), tokenId =0, tokenType = 'FA2').run(sender = admin)
