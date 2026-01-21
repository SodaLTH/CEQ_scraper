class CEQTool:
    def __init__(self, inputs, settings):
        self.data = {}
        self.soup = None
        self.webscrape_done = True

        self.select_categories(settings)
        self.generate_urls(inputs)
        counter = 0 # Check if any webscraping has occured
        for url, year in self.url_dict.items():
            self.load_soup(url)
            if self.soup is None or self.CEQ_check() == -1:
                continue
            self.extract_yearly_data(year)
            self.categories = self.base_categories
            counter += 1

        if counter == 0:
            self.webscrape_done = False
        else:
            self.plot_data()

    # Select categories
    def select_categories(self, settings):
        self.plot_titles = [
            pair[settings['plot_titles']] for pair in [
                ['Pass Rate', 'Godkännandegrad'], 
                ['Good Teaching', 'God undervisning'], 
                ['Clear Goals and Standards', 'Tydliga mål'], 
                ['Appropriate Assessment', 'Förståelseinriktad examination'],
                ['Appropriate Workload', 'Lämplig arbetsbelastning'],
                ['Course Relevance', 'Kursrelevans'],
                ['Course Satisfaction', 'Kursnöjdhet']]]

        keys = ['Antal godkända/andel av registrerade',
                'God undervisning',
                'Tydliga mål',
                'Förståelseinriktad examination',
                'Lämplig arbetsbelastning',
                'Kursen känns angelägen för min utbildning',
                'Överlag är jag nöjd med den här kursen']
        
        self.categories = dict(zip(keys, self.plot_titles))
        
        self.plot_settings = {}

        for key in list(self.categories.keys()):
            if settings[key] == 0:
                del self.categories[key]
            else:
                self.plot_settings[self.categories[key]] = settings[key]
        self.base_categories = self.categories

    # Construct all urls for each course year
    def generate_urls(self, input_list):
        url_shell = 'https://www.ceq.lth.se/rapporter/ceq/{}_slutrapport.html'
        
        self.url_dict= {}
        for inputs in input_list:
            code = inputs[0]
            period = inputs[1]
            if period in ['LP3', 'LP4']:
                term = 'VT'
                period = 'LP1' if period == 'LP3' else 'LP2'
            else:
                term = 'HT'

            for year in range(int(inputs[2]), int(inputs[3]) + 1):
                url_insert = f"{str(year)}_{term}/{period}/{code}_{str(year)}_{term}_{period}"
                url = url_shell.format(url_insert)
                self.url_dict[url] = year

    # Load page and initiate soup
    def load_soup(self, url):
        from bs4 import BeautifulSoup
        import requests
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, 'lxml')
        except requests.exceptions.RequestException:
            self.soup = None

    # Check if CEQ is done
    def CEQ_check(self):
        CEQ_exists = self.soup.find('h3', string='CEQ-enkäten fylldes i')
        if not CEQ_exists:
            if 'Antal godkända/andel av registrerade' in self.categories:
                self.categories = {'Antal godkända/andel av registrerade': 'Pass Rate'}
            else: 
                return -1

    # Extract yearly data from specified tablerows
    def extract_yearly_data(self, year):
        for key, title in self.categories.items():
            row = self.soup.find('td', string=lambda s: key in s).parent
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if title not in self.data:
                self.data[title] = {}
            if len(cells) == 2:
                values = cells[1].split()
                self.data[title][year] = [int(values[0]), int(values[2])]
            else:
                self.data[title][year] = [int(cells[1]), int(cells[2])]

    # Plot data
    def plot_data(self):
        import matplotlib.pyplot as plt
        self.figs = []
        for title, yearly_data in self.data.items():
            years = [*yearly_data]
            value1 = [yearly_data[year][0] for year in years]
            value2 = [yearly_data[year][1] for year in years]

            fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
            if title == 'Pass Rate':
                if self.plot_settings[title] == 1:
                    ax.plot(years, value1, marker='o')
                    ax.set_ylabel('Amount of Students') 
                else:
                    ax.plot(years, value2, marker='o')
                    ax.set_ylabel('Percentage (%)')
                    ax.set_ylim(0, 100)
            else:
                if self.plot_settings[title] == 1:
                    ax.plot(years, value1, marker='o', label='Mean')
                else:
                    ax.errorbar(years, value1, yerr=value2, fmt='o-', capsize=5, ecolor='red', elinewidth=1.5, label='Mean ± Std dev')
                ax.set_ylabel('Score')
                ax.legend()
                ax.legend(fontsize=15)
            ax.set_xlabel('Year')
            ax.set_xticks(years)
            ax.set_title(title)
            ax.title.set_fontsize(19)
            ax.xaxis.label.set_fontsize(17)
            ax.yaxis.label.set_fontsize(17)
            ax.tick_params(axis='both', labelsize=15)
            ax.grid(True)
            self.figs.append(fig)

if __name__ == '__main__':
    input_list = [['KBK050', 'LP1', '2016', '2016']]
    settings = {'Antal godkända/andel av registrerade': 0, 
                'God undervisning': 2,
                'Tydliga mål': 2,
                'Förståelseinriktad examination': 1,
                'Lämplig arbetsbelastning': 2,
                'Kursen känns angelägen för min utbildning': 2,
                'Överlag är jag nöjd med den här kursen': 2}
    CEQTool(input_list, settings)
