import asyncio
import json
import os
import sys
from aiohttp import ClientSession, ClientTimeout
from datetime import datetime, timezone, timedelta
from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

class TeneoBot:
    def __init__(self):
        self.email = "YOUR_EMAIL_HERE"
        self.password = "YOUR_PASSWORD_HERE"
        self.bearer_token = None  # Token will be set after login
        self.token_expiry = None  # Track token expiry
        self.account_data = {}

    async def user_login(self):
        """Login to get a new access token"""
        url = "https://auth.teneo.pro/api/login"
        data = json.dumps({"email": self.email, "password": self.password})
        headers = {"Content-Type": "application/json"}

        async with ClientSession(timeout=ClientTimeout(total=120)) as session:
            try:
                async with session.post(url, headers=headers, data=data) as response:
                    result = await response.json()
                    if response.status == 200 and "access_token" in result:
                        self.bearer_token = result["access_token"]
                        self.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
                        print(f"{Fore.GREEN}[ LOGIN ] ✅ Token acquired!{Style.RESET_ALL}")
                        return True
                    else:
                        print(f"{Fore.RED}[ LOGIN ] ❌ Failed: {result}{Style.RESET_ALL}")
                        return False
            except Exception as e:
                print(f"{Fore.RED}[ LOGIN ] ❌ Error: {e}{Style.RESET_ALL}")
                return False

    async def auto_refresh_token(self):
        """Refresh the token before it expires"""
        while True:
            if self.token_expiry:
                remaining_time = (self.token_expiry - datetime.now(timezone.utc)).total_seconds()
                if remaining_time <= 300:  # Refresh 5 minutes before expiry
                    print(f"{Fore.YELLOW}[ REFRESH ] 🔄 Refreshing token...{Style.RESET_ALL}")
                    success = await self.user_login()
                    if success:
                        print(f"{Fore.GREEN}[ REFRESH ] ✅ Token refreshed successfully!{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}[ REFRESH ] ❌ Token refresh failed!{Style.RESET_ALL}")
            await asyncio.sleep(60)  # Check every minute

    async def connect_websocket(self):
        """Connect WebSocket using Bearer token"""
        while True:
            if not self.bearer_token:
                print(f"{Fore.RED}[ ERROR ] ❌ No valid token! Trying to login...{Style.RESET_ALL}")
                await self.user_login()

            wss_url = f"wss://secure.ws.teneo.pro/websocket?accessToken={self.bearer_token}&version=v0.2"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Upgrade": "websocket",
                "Connection": "Upgrade"
            }

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
                print(f"{Fore.RED}[ BOT ] ❌ WebSocket Disconnected, retrying in 5s...{Style.RESET_ALL}")
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
        
        # First login to get a token
        login_success = await self.user_login()
        if not login_success:
            print(f"{Fore.RED}[ ERROR ] ❌ Failed to obtain token. Exiting...{Style.RESET_ALL}")
            return

        # Start auto-refresh in the background
        asyncio.create_task(self.auto_refresh_token())

        # Start WebSocket connection
        await self.connect_websocket()

if __name__ == "__main__":
    bot = TeneoBot()
    asyncio.run(bot.main())
