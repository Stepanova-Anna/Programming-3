import asyncio
import aiohttp

async def fetch_data(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                print("Request successful")
            else:
                print(f"Request failed with status: {response.status}")
    except aiohttp.ClientError as e:
        print(f"Network error: {e}")

async def main():
    url = "https://atlas.herzen.spb.ru/teachers"
    async with aiohttp.ClientSession() as session:
        await fetch_data(session, url)

if __name__ == "__main__":
    asyncio.run(main())
