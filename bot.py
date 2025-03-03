import asyncio
import json
import os
import sys
from aiohttp import ClientSession, ClientTimeout
from datetime import datetime, timezone
from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

class TeneoBot:
    def init(self):
        self.bearer_token = "YOUR_BEARER_TOKEN_HERE"  # Use the token from your image
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Authorization": f"Bearer {self.bearer_token}"
        }
        self.account_data = {}

    async def connect_websocket(self):
        """Connect WebSocket using Bearer token"""
        wss_url = f"wss://secure.ws.teneo.pro/websocket?accessToken={self.bearer_token}&version=v0.2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Upgrade": "websocket",
            "Connection": "Upgrade"
        }

        while True:
            try:
                async with ClientSession(timeout=ClientTimeout(total=300)) as session:
                    async with session.ws_connect(wss_url, headers=headers) as wss:
                        print(f"{Fore.GREEN}[ BOT ] ✅ WebSocket Connected{Style.RESET_ALL}")

                        async def send_heartbeat():
                            while True:
                                await asyncio.sleep(10)
                                await wss.send_json({"type": "PING"})
                                self.print_ping_log()
                                self.display_status()

                        asyncio.create_task(send_heartbeat())

                        async for msg in wss:
                            response = json.loads(msg.data)

                            if response.get("message") in ["Connected successfully", "Pulse from server"]:
                                self.account_data["BOT"] = {
                                    "Points Today": response.get("pointsToday", 0),
                                    "Total Points": response.get("pointsTotal", 0),
                                    "Last Update": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                                }

            except Exception as e:
                print(f"{Fore.RED}[ BOT ] ❌ WebSocket Disconnected, Reconnecting in 5s...{Style.RESET_ALL}")
                await asyncio.sleep(5)

    def print_ping_log(self):
        """Display PING log"""
        print(f"\n{Fore.CYAN}[ BOT ] 🔄 Sent PING to WebSocket{Style.RESET_ALL}")

    def display_status(self):
        """Display bot status"""
        os.system("cls" if os.name == "nt" else "clear")  # Auto clear log

        if not self.account_data:
            return

        table_data = [
            [
                Fore.YELLOW + str(v["Points Today"]) + Style.RESET_ALL,
                Fore.GREEN + str(v["Total Points"]) + Style.RESET_ALL,
                Fore.MAGENTA + v["Last Update"] + Style.RESET_ALL
            ]
            for v in self.account_data.values()
        ]

        print("\n" + Fore.YELLOW + "=" * 50)
        print(Fore.GREEN + "✨ TENEO BOT STATUS ✨".center(50))
        print(Fore.YELLOW + "=" * 50 + Style.RESET_ALL)
        print(tabulate(
            table_data,
            headers=[Fore.YELLOW + "Points Today" + Style.RESET_ALL, Fore.GREEN + "Total Points" + Style.RESET_ALL, Fore.MAGENTA + "Last Update" + Style.RESET_ALL],
            tablefmt="double_outline"
        ))
        print("\n" + Fore.YELLOW + "=" * 50)

    async def main(self):
        print(f"{Fore.YELLOW}[ INFO ] 🔢 Starting Bot...{Style.RESET_ALL}")
        await self.connect_websocket()

if name == "main":
    bot = TeneoBot()
    asyncio.run(bot.main())
