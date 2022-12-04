# Tescrow
Escrow for Tezos games


### Escrow Contract
<a href= "https://smartpy.io/explorer?address=KT1Jrdfsv624AcySv3mXSCVxNLeAEb5VFWwN">KT1Jrdfsv624AcySv3mXSCVxNLeAEb5VFWwN </a>

### Token Contract
<a href= "https://smartpy.io/explorer?address=KT1G7XLYu4C1cbk7BjdUy8PWcCJ3MLPBq7Kf">KT1G7XLYu4C1cbk7BjdUy8PWcCJ3MLPBq7Kf </a>

### Escrow  Contract:
Escrow means "place in custody or trust until a specified condition has been fulfilled."
As the Tezos ecosystem is growing especially in the NFTs and gaming area, a robust escrow standard is required in that area.

So I have designed an Escrow contract with the following functionalities

#### 1. Support for Tez, FA1.2 and FA2 tokens. 

Escrow contract has a "Token Registry" to support Tez, FA1.2, and FA2. All tokens to be used in games are to be added token registry with their name, token address, and token id . Once added token details can be retrieved using the token name itself.  Since some of the Gaming projects like "Dogami" have issued FA1.2 $DOGA tokens and all other NFTs and some of the stablecoins project use FA2 Token Standard, it becomes necessary to provide support for all token types.

#### 2. Escrow is timed.
Tescrow has a time limit for each escrow. Meaning the player needs to deposit the required amount in Tez or FA1.2 tokens or FA2 tokens in a specified time. Else they will not be able to take part in the game. A time limit is needed to bring all the players in the decentralized environment to assemble at the same time. 

#### 3.  Flexibility for players:
Usually, escrow contracts are created with all the required players at the beginning but  Tescrow allows people to be added at a later stage as well. This feature will help people play teams in MMORPGs. 

#### 4. Username for Players.
Just to keep consistency with the games, the Tescrow provides an option to use the same game username in the escrow contract as well. So the player will be identified by username rather than wallet id.  This also means players can use any wallet to stake the required tokens.

#### 5. Usage of Proxy assets.
In Tescrow when a player deposits tokens, he receives an equal amount of tescrow tokens in return.  The token Id of the tescrow tokens will be the combination of the game id and player id. Since tescrow contract doesn't track the wallet ids, all the winnings of the game will be provided based on the tescrow tokens.

##### Example
Lets go through an example to understand the concept better.
Lets say player A and player B  are planning to take part in a game XYZ which requires a deposit of 100 USDT
Player A deposits  100 USDT tokens and in turn, receives 100 "XYZ - A" tokensPlayer B deposits  100 USDT tokens and in turn, receives 100 "XYZ - B" tokens
The conversion ratio of  "XYZ - A" tokens into USDT is 1:1 i.e 1 XYZ-A token yields 1USDT which is also same for "XYZ-B" at the beginning of the game
In the end, A wins game XYZ which is a "winner takes all" game, then the conversion ratio of  "XYZ - A" tokens to  USDT becomes 1:2 i.e 1 XYZ-A token yields 2 USDTs, and the value XYZ-B becomes 0 USDT. If In a game , there are mulitple winners with different degrees of winnings, the game engine just needs to provide tescrow contract with the winner and their respective conversion ratio.
Player A can redeem the USDT whenever he chooses to.
Though in the current submission, FA2 contract is used for generating proxy assets, it will be modified into Tickets, once the feature to transfer tickets to the user wallet is enabled. 

#### 6. Result provider:
Tescrow assumes there is a trusted third party or oracle to provide the results.If there is none, then holders of proxy assets can take part in the token voting of the result which needs to be incorporated in the tescrow.
