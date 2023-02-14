from bs4 import BeautifulSoup
import requests, urllib, random, fitz, os, re

WORD_LIST_URL = 'https://www.goethe.de/pro/relaunch/prf/en/Goethe-Zertifikat_B1_Wortliste.pdf'
FREQ_DICT_URL = 'https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/A_Frequency_Dictionary_of_German'
RE_PATTERN = r'(der|die|das)\s|\([^\)]+\)\s|\(herunter-\)|sich\s|^\-|\-$|\s\(Sg.\)|\s\(Pl.\)'

def download_file(filename, url):
    os.system(f'wget -q -O {filename} {url}')

def extract_word_list(filename):
    word_list = []
    with fitz.open(filename) as infile:
        for i, page in enumerate(infile):
            text = page.get_text('blocks')
            blocks = []
            if 14 < i < 102:
                for block in text:
                    if 65 < block[1] < 790 and not re.findall(r'^[A-Z]$', block[-3]):
                        blocks.append(re.sub(r'\s+', ' ', block[-3]).strip())
                for i in range(len(blocks) // 2):
                    if u'\u2192' not in blocks[i]:
                        word_list.append(blocks[i])
    return word_list

def get_pronunciation(word):
    for w in (word, word.capitalize()):
        try:
            page = requests.get(f'https://de.wiktionary.org/wiki/{w}')
            soup = BeautifulSoup(page.text, 'html.parser')
            text = soup.find_all('span', {'class': 'ipa'})
            return text[0].getText()
        except (urllib.error.HTTPError, IndexError): pass
    return ''

if __name__ == '__main__':
    # download_file('wortliste.pdf', WORD_LIST_URL)
    # word_list = extract_word_list('wortliste.pdf')
    word_list = []
    with open('unsorted.txt') as infile:
        for entry in infile.readlines():
            word_list.append(entry.strip())
 
    page = requests.get(FREQ_DICT_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    text = soup.find_all('ol')[0].get_text().split('\n')
    freq_list = {word: i for i, word in enumerate(text, start=1)}

    word_freq, remainder = [], []
    for entry in word_list:
        base_word = re.sub(RE_PATTERN, '', re.split(r'[,/]', entry.strip())[0])
        if base_word in freq_list:
            word_freq.append((entry, freq_list[base_word]))
        else:
            print(base_word)
            remainder.append((entry, None))
    random.shuffle(remainder)

    print('Frequency Coverage: %0.2f %%' % (len(word_freq) / len(word_list) * 100))

    word_freq.sort(key=lambda x: x[1])
    with open('sorted.txt', 'w') as outfile:
        for i, (entry, _) in enumerate(word_freq):
            outfile.write(f'{entry}\n')
