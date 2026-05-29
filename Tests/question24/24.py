from bs4 import BeautifulSoup

def parse_articles(html):

    soup = BeautifulSoup(html, 'html.parser')
    

    articles = []
    
    selectors = [
        'article h2 a',
        '.tm-article-snippet h2 a',
        '.tm-title__link',
        'a.tm-title__link',
        '.post__title a',
        '.article-formatted-body h2 a'
    ]
    
    for selector in selectors:
        found = soup.select(selector)
        if found:
            for item in found[:5]:
                title = item.get_text(strip=True)
                if title:
                    articles.append({"title": title})
            break
    
    if not articles:
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            link = tag.find('a')
            if link:
                title = link.get_text(strip=True)
                if title and len(title) > 10:
                    articles.append({"title": title})
            if len(articles) >= 5:
                break
    
    if not articles:
        for link in soup.find_all('a'):
            text = link.get_text(strip=True)
            if len(text) > 20 and len(text) < 200:
                articles.append({"title": text})
            if len(articles) >= 5:
                break
    
    return articles[:5]

input_data = _items[0]['json']
html_content = input_data["data"]
result = parse_articles(html_content)
return [{"json": {"articles": result}}]
