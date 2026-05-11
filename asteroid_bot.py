import asyncio
import requests
from web3 import Web3
from datetime import datetime
import os

# ================== 配置（从 Railway 读取） ==================
TOKEN_ADDRESS = "0xf280b16ef293d8e534e370794ef26bf312694126"
DECIMALS = 9
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
RPC_URL = os.getenv("RPC_URL")
MIN_USD = 1000
PAIR_ADDRESS = "0x76a411f14a704099ba476ce8dffc288a53295218"
# =====================================================

w3 = Web3(Web3.HTTPProvider(RPC_URL))

ABI = [{
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": False, "name": "value", "type": "uint256"}
    ],
    "name": "Transfer",
    "type": "event"
}]

contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=ABI)

def get_price():
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/ethereum/{PAIR_ADDRESS}", timeout=10)
        return float(r.json()["pair"]["priceUsd"])
    except:
        return 0.00033

async def send_alert(tx, fr, to, amount, usd):
    msg = f"""🚨 **ASTEROID 大额转账提醒**
**金额**: {amount:,.2f} ASTEROID (**${usd:,.0f}**)
**From**: `{fr}`
**To**: `{to}`
**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**交易**: https://etherscan.io/tx/{tx}"""
    requests.post(DISCORD_WEBHOOK, json={"content": msg})

async def main():
    print("🚀 ASTEROID 鲸鱼监控机器人已启动...")
    print(f"当前价格 ≈ ${get_price():.8f}")
    
    event_filter = contract.events.Transfer.create_filter(fromBlock="latest")
    
    while True:
        try:
            for event in event_filter.get_new_entries():
                tx = event.transactionHash.hex()
                fr = event.args["from"]
                to = event.args["to"]
                amount = event.args["value"] / (10 ** DECIMALS)
                usd_value = amount * get_price()
                
                if usd_value >= MIN_USD:
                    print(f"✅ 检测到大额交易 ${usd_value:,.0f}")
                    await send_alert(tx, fr, to, amount, usd_value)
            await asyncio.sleep(0.8)
        except Exception as e:
            print("错误:", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
