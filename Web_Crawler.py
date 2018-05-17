import bs4
import colorama
from random import randrange
import re
from random import randint
import requests
from requests.exceptions import SSLError, ReadTimeout, ConnectTimeout, ConnectionError
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit

colorama.init() # only necessary in windows
OK = colorama.Fore.GREEN
ERROR = colorama.Fore.RED
BLUE = colorama.Fore.BLUE
BACKRED = colorama.Back.RED
RESET = colorama.Style.RESET_ALL

MAX_TOKEN_LEN = 15
CLEAN_RE = re.compile('\W+')

#######################
## WORKING WITH URLS ##
#######################

def get_site(url):
    return urlsplit(url).netloc

###############################
## WORKING WITH HTML CONTENT ##
###############################

def download_web(url):
    print('Getting "%s" ... ' % url, end='')
    try:
        r = requests.get(url, timeout=1)
        print(OK + 'ok!' + RESET)
    except (SSLError, ReadTimeout, ConnectTimeout, ConnectionError) as err:
        print(ERROR + 'ERROR: %s' % err + RESET)
        return None
    return bs4.BeautifulSoup(r.text,  'lxml')#'html.parser')

def extract_urls(contenido, baseurl):
    url_list = []
    for link in contenido.find_all('a'):
        newurl = link.get('href')
        if newurl is None:
            continue
        full_new_url = urljoin(baseurl, newurl.strip())
        surl = urlsplit(full_new_url)
        if surl.scheme in ['http', 'https']:
            ext = surl.path[surl.path.rfind('.'):].lower()
            if ext not in [".pdf", ".jpg"]:
                newurl = urlunsplit((surl.scheme, surl.netloc, surl.path, '', ''))
                url_list.append(newurl)
    return url_list

def extract_text(content):
    return CLEAN_RE.sub(' ', content.text).lower()

############################
## WORKING WITH THE INDEX ##
############################

def add_processed_url(url_dic, url):
    """Add url to doc dictionary (url_dic)

    Args:
        url_dic: docs dictionary
        url: url to add

    Returns:
        int: dictionary url key

    """
    hs_url = hash(url)
    url_dic[hs_url] = url
    
    return (hs_url)

def get_next_url(url_queue):
    """Takes an url from the queue and it returns it

    Args:
        url_queue

    Returns:
        text: url

    """ 
    url_data = url_queue.pop()
    return url_data
    

def add_pending_url(url_queue, url, url_dic):
    """add url to the queue if there is no one here or in the dictionary

        Args:
            url_queue
            url
            url_dic: docs dictionary

        Returns:
            boolean: True if the url is correctly added. False if it already exist
        """
    hs_url = hash(url)
    aux = 1 
    for i in url_queue:
      if i == url:
        aux = 0
    if aux:
      try:
        value = url_dic[hs_url]
        return False
      except KeyError:
        url_queue.append(url)
        return True
      

def add_to_index(index, urlid, text):
    """Add the appropiate docid of an url to the posting list of text's terms

        Args:
            index: inverted index
            urlid: url's docid
            text

        Returns:
            int: terms number processed 
    """
    
    local_count = 0
    for word in text.split():
      try:
        old_data = [index[word]].append(urlid)
        index[word] = set(old_data)
        local_count += 1
      except:
        index[word] = [urlid]
        local_count += 1
    return local_count
  
def get_posting(index, dic, term):
    """Returns a list of url where the terms appears

        Args:
            index: inverted index
            dic: docs dictionary, necessary to take the urls from de key(docid)
            term

        Returns:
            list: list of url , None if the term does not exist in the inverted index
    """
    final_list = []
    try:
      url_list = index[term]
    except:
      return []
      
    for hs in url_list:
      final_list.append(dic[hs])
      
    return final_list

###############
## SHOW INFO ##
###############

def info(index, processed, pending):
    print("\n====\nINFO\n====")
    # about de index
    print('Number of tokens:', len(index))
    print('Number of processed urls:', len(processed))
    if len(processed) != len(set(processed.values())):
        print (BACKRED + "ERROR: SOME URLS ARE DUPLICATED" + RESET)
    print('Number of pending urls:', len(pending))
    print('-' * 50)
    # searching words
    words = ["computer", "enigma", "theory", "probability", "war",
             "victory", "died"]
    for word in words:
        refs = get_posting(index, processed, word)
        if refs is None:
            print ("%s'%s'%s is not indexed" % (ERROR, word, RESET))
        else:
            print ("%s'%s'%s is in:" % (BLUE, word, RESET), ', '.join(sorted(refs)))
    print('-' * 50)
    # about the sites
    l1 = sorted(set(get_site(url) for url in processed.values()))
    l2 = sorted(set(get_site(url) for url in pending_urls).difference(l1))
    max_len = max(len(s) for s in l1 + l2)
    l1 = ([s.ljust(max_len) for s in l1])
    l2 = ([s.ljust(max_len) for s in l2])
    print('Processed Sites (%d):' % len(l1))
    for i in range(int(len(l1)/4)+1):
        print('\t'+'\t'.join(l1[i*4:i*4+4]))
    print('-' * 50)
    print('Pending Sites (%d):' % len(l2))
    for i in range(int(len(l2)/4)+1):
        print('\t'+'\t'.join(l2[i*4:i*4+4]))


if __name__ == "__main__":
    MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    inverted_index, processed_urls, pending_urls = {}, {}, []
    add_pending_url(pending_urls, "https://es.wikipedia.org/wiki/Alan_Turing", processed_urls)
    countGlobal = 0
    for iter in range(MAX):
        url = get_next_url(pending_urls)
        print('(%d)' % iter, end=' ')
        page = download_web(url)
        if page is not None:
            urlid = add_processed_url(processed_urls, url)
            text = extract_text(page)
            add_to_index(inverted_index, urlid, text)
            url_list = extract_urls(page, url)
            for new_url in url_list:
                add_pending_url(pending_urls, new_url, processed_urls)
    info(inverted_index, processed_urls, pending_urls)
