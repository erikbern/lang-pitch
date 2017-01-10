import base64, bs4, json, requests, scrapy, sys

def extract_audio(soup):
    for p in soup.find_all('article', {'class': 'pronunciations'}): # should just be 0 or 1
        if not p.find('abbr'):
            continue
        lang = p.find('abbr').attrs['title']
        lang_code = p.find('abbr').text
        for q in p.find('ul').find_all('li'):
            if not q.find('span', {'class': 'from'}):
                continue
            origin = q.find('span', {'class': 'from'}).text
            username_tag = q.find('a', {'class': 'uLink'})
            username = username_tag and username_tag.text or None
            play_args = q.find('a', {'class': 'play'}).attrs['onclick'].split(',')
            url = 'https://audio00.forvo.com/mp3/' + base64.b64decode(play_args[1])
            f = open('clips.jsons', 'a')
            f.write(json.dumps({'lang': lang, 'lang_code': lang_code, 'username': username, 'origin': origin, 'url': url}) + '\n')
            f.close()


class ForvoSpider(scrapy.Spider):
    name = 'forvo'
    start_urls = ['https://forvo.com/']
    allowed_domains = ['forvo.com']

    def parse(self, response):
        soup = bs4.BeautifulSoup(response.body)
        extract_audio(soup)

        for a in soup.find_all('a'):
            url = response.urljoin(a.attrs['href'])
            if url.startswith('https://forvo.com/') \
               and not url.startswith('https://forvo.com/word-report') \
               and not url.startswith('https://forvo.com/download') \
               and not url.startswith('https://forvo.com/word-modify'):
                yield scrapy.Request(url, callback=self.parse)


if __name__ == '__main__':
    res = requests.get(sys.argv[1])
    extract_audio(bs4.BeautifulSoup(res.content))
