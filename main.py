from bs4 import BeautifulSoup
import requests

# Get html file and parse it
page = requests.get("https://www.ceq.lth.se/rapporter/ceq/2024_HT/LP1/KBKN05_2024_HT_LP1_slutrapport.html")
soup = BeautifulSoup(page.text, "lxml")

# Find relevant data
table = soup.find_all("table")[6]
rows = table.find_all("tr")
cells = rows[1].find_all("td")

print(rows)