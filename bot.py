import asyncio
import json
import os
import sys
import requests
from aiohttp import ClientSession, ClientTimeout
from datetime import datetime, timezone
from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

class TeneoBot:
    def __init__(self):
        self.bearer_token = "YOUR_BEARER_TOKEN_HERE"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Authorization": f"Bearer {self.bearer_token}"
        }
        self.account_data = {}
        self.last_points = None  # Store last points to detect changes

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
                        self.send_telegram_message("✅ Teneo Bot Connected!")

                        async def send_heartbeat():
                            """Send PING every 10 seconds"""
                            while True:
                                await asyncio.sleep(10)
                                await wss.send_json({"type": "PING"})
                                self.print_ping_log()

                        async def process_messages():
                            """Process messages from WebSocket"""
                            async for msg in wss:
                                response = json.loads(msg.data)
                                if response.get("message") in ["Connected successfully", "Pulse from server"]:
                                    points_today = response.get("pointsToday", 0)
                                    total_points = response.get("pointsTotal", 0)
                                    last_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

                                    self.account_data["BOT"] = {
                                        "Points Today": points_today,
                                        "Total Points": total_points,
                                        "Last Update": last_update
                                    }

                                    # Check if points changed
                                    if self.last_points is None or self.last_points != total_points:
                                        self.last_points = total_points
                                        self.send_telegram_message(f"🔄 Points Updated!\n✨ Points Today: {points_today}\n💰 Total Points: {total_points}")

                                    self.display_status()

                        asyncio.create_task(send_heartbeat())
                        asyncio.create_task(self.send_periodic_updates())  # 15 min update task
                        await process_messages()

            except Exception as e:
                print(f"{Fore.RED}[ BOT ] ❌ WebSocket Disconnected, Reconnecting in 5s...{Style.RESET_ALL}")
                self.send_telegram_message("❌ WebSocket Disconnected! Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def send_periodic_updates(self):
        """Send points update every 15 minutes"""
        while True:
            await asyncio.sleep(900)  # 15 minutes
            if self.account_data:
                points_today = self.account_data["BOT"]["Points Today"]
                total_points = self.account_data["BOT"]["Total Points"]
                self.send_telegram_message(f"📢 15-Min Update:\n✨ Points Today: {points_today}\n💰 Total Points: {total_points}")

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

    def send_telegram_message(self, message):
        """Send a notification to Telegram"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, json=data)
        except Exception as e:
            print(f"{Fore.RED}[ ERROR ] ❌ Failed to send Telegram message: {e}{Style.RESET_ALL}")

    async def main(self):
        print(f"{Fore.YELLOW}[ INFO ] 🔢 Starting Bot...{Style.RESET_ALL}")
        self.send_telegram_message("🚀 Teneo Bot Started!")
        await self.connect_websocket()

if __name__ == "__main__":
    bot = TeneoBot()
    asyncio.run(bot.main())
