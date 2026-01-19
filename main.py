from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt

# course_codes = ['KBKN05']
# course_period = ['LP1']
# course_start_year = ['2023']
# course_end_year = ['2024']

# Construct all urls for each course year
def generate_urls(inputs):
    "https://www.ceq.lth.se/rapporter/ceq/2024_HT/LP1/KBKN05_2024_HT_LP1_slutrapport.html"
    url_shell = "https://www.ceq.lth.se/rapporter/ceq/{}_slutrapport.html"
    code = inputs[0]
    period = inputs[1]
    if period in ["LP3", "LP4"]:
        term = "VT"
        period = "LP1" if period == "LP3" else "LP2"
    else:
        term = "HT"

    url_dict= {}
    for year in range(int(inputs[2]), int(inputs[3]) + 1):
        url_insert = f"{str(year)}_{term}/{period}/{code}_{str(year)}_{term}_{period}"
        url = url_shell.format(url_insert)
        url_dict[url] = year
    return url_dict

# Load page and initiate soup
def load_soup(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.exceptions.RequestException:
        return None

# Check if CEQ is done
def CEQ_check(soup):
    check = soup.find("h3", string='CEQ-enkäten fylldes i')
    if not check:
        return "No CEQ done"
    else:
        return "CEQ done"

# Extract yearly data from specified tablerows
def extract_yearly_data(data, soup, rows, year):
    for key, title in rows.items():
        row = soup.find("td", string=lambda s: key in s).parent
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if title not in data:
            data[title] = {}
        if len(cells) == 2:
            values = cells[1].split()
            data[title][year] = [int(values[0]), int(values[2])]
        else:
            data[title][year] = [int(cells[1]), int(cells[2])]
    return data

# Plot data
def plot_data(data):
    for title, yearly_data in data.items():
        years = [*yearly_data]
        values = [yearly_data[year][0] for year in years]

        plt.plot(years, values, marker='o')
        plt.xlabel("År")
        plt.xticks(years)
        plt.ylabel("Poäng")
        plt.title(title)
        plt.grid(True)
        plt.show()


input_list = ['KBKN05', 'LP1', '2022', '2024']
url_dict = generate_urls(input_list)
rows = {"Antal godkända/andel av registrerade": "Godkänd ratio", 'God undervisning': "God undervisning"}
data = {}
for url, year in url_dict.items():
    soup = load_soup(url)
    if soup is None:
        continue
    data = extract_yearly_data(data, soup, rows, year)

plot_data(data)
# # Webscrape data
# soup = BeautifulSoup(requests.get(url).text, "lxml")
# godkanda = extract_data(soup, 'Antal godkända/andel av registrerade')
# undervisning = extract_data(soup, 'God undervisning')