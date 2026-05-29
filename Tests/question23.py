import asyncio
import re
from locust import FastHttpUser, task, between
from bs4 import BeautifulSoup
import aiohttp

class TeacherUser(FastHttpUser):
    wait_time = between(1, 3)
    host = "https://atlas.herzen.spb.ru"

    @task
    async def get_teachers(self):
        try:
            async with self.client.get("/teachers", catch_response=True) as response:
                if response.status == 200:
                    response.success()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    
                    table = soup.find('table')
                    teacher_names = []
                    
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 1:
                                
                                name = cols[0].get_text(strip=True)
                                
                                if name and name != "ФИО" and len(name) > 4:
                                    teacher_names.append(name)
                    else:
                       
                        text = soup.get_text()
                        pattern = r'[А-Я][а-я]+(?:\s+[А-Я][а-я]+)+'
                        teacher_names = re.findall(pattern, text)[:30]
                    
                    teacher_names = teacher_names[:30] 
                    
                    if teacher_names:
                        print(f"Loaded {len(teacher_names)} teachers")
                        tasks = [self.print_teacher(name) for name in teacher_names]
                        await asyncio.gather(*tasks)
                    else:
                        print("No teachers found — check page structure")
                        
                else:
                    response.failure(f"Status: {response.status}")
                    print(f"HTTP error: {response.status}")
                    
        except aiohttp.ClientError as e:
            print(f"Network error: {e}")
        except Exception as e:
            print(f" Error: {e}")

    async def print_teacher(self, name: str):
        print(f"{name}")
        await asyncio.sleep(0.1)
