from bs4 import BeautifulSoup
import requests, urllib, random, fitz, json, tqdm, os, re

WORD_LIST_URL = 'https://www.goethe.de/pro/relaunch/prf/en/Goethe-Zertifikat_B1_Wortliste.pdf'
FREQ_DICT_URL = 'https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/A_Frequency_Dictionary_of_German'

def download_file(filename, url):
    os.system(f'wget -q -O {filename} {url}')

def extract_word_list(filename):
    word_list = {}
    with fitz.open(filename) as infile:
        for i, page in enumerate(infile):
            text = page.get_text('blocks')
            blocks = []
            if 14 < i < 102:
                for block in text:
                    if 65 < block[1] < 790 and not re.findall(r'^[A-Z]$', block[-3]):
                        blocks.append(re.sub(r'\s+', ' ', block[-3]).strip())
                N = len(blocks) // 2
                for i in range(N):
                    word_list[blocks[i]] = blocks[i + N]
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', action='store_true', help='construct word_list')
    parser.add_argument('-f', action='store_true', help='construct freq_list')
    parser.add_argument('-p', action='store_true', help='include pronunciation')
    args = parser.parse_args()

    if args.w:
        download_file('word_list.pdf', WORD_LIST_URL)
        word_list = extract_word_list('word_list.pdf')
        with open('word_list.json', 'w') as outfile:
            json.dump(word_list, outfile)
 
    if args.f:
        page = requests.get(FREQ_DICT_URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        text = soup.find_all('ol')[0].get_text().split('\n')
        freq_list = {word: i for i, word in enumerate(text, start=1)}
        with open('freq_list.json', 'w') as outfile:
            json.dump(freq_list, outfile)

    with open('word_list.json') as word_file, open('freq_list.json') as freq_file:
        word_list = json.load(word_file)
        freq_list = json.load(freq_file)
        pattern = r'(der|die|das)\s|\(sich\)\s|sich\s|\-$|\s\(Pl.\)'

        word_freq = []
        remainder = []
        for entry in word_list:
            word = re.sub(pattern, '', re.split(r'[,/]', entry)[0])
            if word in freq_list:
                word_freq.append((entry, word, freq_list[word]))
            else:
                remainder.append((entry, word, None))
        random.shuffle(remainder)
        print('Frequency Coverage: %0.2f %%' % (len(word_freq) / len(word_list) * 100))

    word_freq.sort(key=lambda x: x[1])
    word_freq.extend(remainder)
    with open('word_list.txt', 'w') as outfile:
        for i, (entry, word, _) in tqdm.tqdm(list(enumerate(word_freq))):
            pronunciation = get_pronunciation(word) if args.p else ''
            outfile.write(f'{i} [TODO] ;; {entry} ;; {pronunciation} ;; {word_list[entry]}\n')
