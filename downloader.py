import sys
sys.path.append('C:/Users/tadachi/Desktop/Dropbox/git/')

import re
import os
import logging

import urllib.request
import urllib.parse
import gzip

import concurrent.futures
import requests
import eventlet

from mangabee_parsers import *
from mangahere_parsers import *

import time
from random import randint

import json
###
### Config
###
logging.basicConfig(filename='downloader.py.log', filemode='w', level=logging.DEBUG)
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING) #Disable logging for requests by setting it to WARNING which we won't use.

#
# Search for manga on specified manga site.
#
def search(manga_name, manga_site): # 1 request.
    mangabee_url = 'http://www.mangabee.com/manga-list/search/%s/name-az/1' % mangabee_urlify(manga_name)
    mangahere_url = 'http://www.mangahere.co/search.php?name=%s' % urllib.parse.quote(mangahere_urlify(manga_name))

    results = None
    parser = None

    if (manga_site == 'mangahere'):
        req = requestContentWithHeaders(mangahere_url)
        parser = mangahereSearchParser()
    elif (manga_site == 'mangabee'):
        req = requestContentWithHeaders(mangabee_url)
        parser = mangabeeSearchParser()
    else:
        print("".join(['Not a valid manga site: ', manga_site, '. Try \'mangabee\' or \'mangahere\'']))
        logging.info("".join(['Not a valid manga site: ', manga_site, '. Try \'mangabee\' or \'mangahere\'']))
        return False

    parser.feed(req)         # req contains all the html from url.
    results = parser.links   # Save our results.
    parser.close             # Free the parser resource.

    return results # ['http://www.mangabee.com/blood-c/'] ['http://www.mangahere.co/manga/blood_c/']


#
# Search for manga on specified manga site.
#
def download(url, manga_site): # 1 request.
    src = None # Mangabee
    chapters = None
    pages = None

    links = None # Mangahere
    if (manga_site == 'mangahere'):
        parser = mangahereVolumeChapterParser() # Grabs all the chapters from the manga's html page.
        req = requestWithHeaders(url)
        parser.feed(req.text)
        links = parser.links
        results = dict(links=links)
        parser.close

        return results # {['http://www.mangahere.co/manga/hack_legend_of_twilight/v03/c000.4/' ... 'http://www.mangahere.co/manga/hack_legend_of_twilight/v03/c000.3/'}
    elif (manga_site == 'mangabee'):
        url = url + '1/1'
        parser = mangabeeSetupParser()
        req = requestWithHeaders(url)

        parser.feed(req.text)

        src = parser.src
        pages = parser.pages

        chapters = [e for e in parser.chapters if 'Raw' not in e] # all chapters with Raw are untranslated so filter them out.
        chapters = [onlyNumbersSplit(e) for e in chapters] # Leave only the numbers and strip chracters
        chapters = sorted(chapters, key = lambda x: int(x.split('.')[0]))

        parser.close
        results = dict(url=[url], src=src, chapters=chapters, pages=pages)

        return results # {'chapters': ['1', ... '9'], 'src': ['http://i3.mangareader.net/blood-c/1/blood-c-2691771.jpg'], 'url': ['http://www.mangabee.com/blood-c/1/1'], 'pages': ['1', ...', '40']}
    else:
        print("".join(['Not a valid manga site: ', manga_site, '. Try \'mangabee\' or \'mangahere\'']))
        logging.info("".join(['Not a valid manga site: ', manga_site, '. Try \'mangabee\' or \'mangahere\'']))
        return False

def mangahereSetupAndDownload(setup_list): # 0 requests.
    chapter_urls = sorted(setup_list.get('links')) # They come in reversed from mangahere.

    first_chapter_url = chapter_urls[0] # http://www.mangahere.co/manga/hack_legend_of_twilight/v03/c000.4/
    # http://www.mangahere.co/manga/tora_kiss_a_school_odyssey/
    main_directory = 'mangahere'

    # volume based: ['http:', '', 'www.mangahere.co', 'manga', 'hack_legend_of_twilight', 'v01', 'c000', ''] count: 8
    # !volumebased: ['http:', '', 'www.mangahere.co', 'manga', 'tora_kiss_a_school_odyssey', 'c001.1', '']  count: 7
    if (len(first_chapter_url.split('/')) < 8):
        manga_name = first_chapter_url.rsplit('/',4)[2]  # parse the url for something like this this: 'tokyo_ghoul'
    else:
        manga_name = first_chapter_url.rsplit('/',4)[1]  # parse the url for something like this this: 'tokyo_ghoul'

    base_directory = manga_name                    # 'tokyo_ghoul'

    if not os.path.exists(main_directory): # directory: ..mangahere/
        os.mkdir(main_directory) # directory: ..mangahere/
        logging.info("".join(['Created directory: ', main_directory]))

    d = "".join([main_directory,'\\',base_directory]) # ..mangahere/tokyo_ghouls/
    if not os.path.exists(d):
        os.mkdir(d) # ..mangahere/tokyo_ghouls/
        logging.info("".join(['Created directory: ', d]))

    full_directory = "".join([main_directory,'\\',base_directory,'\\',manga_name]) # mangahere\Tokyo_Ghoul\Tokyo_Ghoul - chapter number will be appended.
    # for i in range( 0, len(chapter_urls) ):
    for i in range( 0, 1 ): # Testing
        chapter_number = chapter_urls[i].rsplit('/',2)[1]
        chapter_directory = "".join( [full_directory, '_', chapter_number] )  # 'mangahere\Tokyo_Ghoul\Tokyo_Ghoul\Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        if not os.path.exists(chapter_directory):
            os.mkdir(chapter_directory) # Create chapter directory: '../mangahere/Tokyo_Ghoul_001/'

        mangahereDownloadPagesForChapter(chapter_urls[i], chapter_directory, chapter_number)

    return True


def mangabeeSetupAndDownload(setup_list): # 0 requests.
    chapter_urls = []
    first_chapter_url = setup_list.get('url')[0].rsplit('/', 2)[0] # http://www.mangabee.com/Tokyo_Ghoul
    chapter_numbers = setup_list.get('chapters')
    main_directory = 'mangabee'

    for i in range(0, len(setup_list.get('chapters'))):
        chapter_urls.append( "".join([first_chapter_url, '/', setup_list.get('chapters')[i], '/', '1']) ) # [ http://www.mangabee.com/Tokyo_Ghoul/1/1, ..., http://www.mangabee.com/Tokyo_Ghoul/137/1 ]

    if ( len(setup_list.get('chapters')) == len(chapter_urls) ):
        # print ('Numbers of chapters and lists match.')
        pass
    else:
        logging.info("".join(['Number of chapters and chapter urls do not match. Check for HTML/CSS abnormalities on the website for that manga.', image_files_paths[0]]))
        return False

    manga_name = chapter_urls[0].rsplit('/',3)[1]  # parse the url for something like this this: 'tokyo_ghoul'
    base_directory = manga_name                    # 'tokyo_ghoul'

    if not os.path.exists(main_directory): # directory: ..mangabee/
        os.mkdir(main_directory) # directory: ..mangabee/
        logging.info("".join(['Created directory: ', main_directory]))

    d = "".join([main_directory,'\\',base_directory]) # manga/tokyo_ghouls/
    if not os.path.exists(d):
        os.mkdir(d) # manga/tokyo_ghouls/
        logging.info("".join(['Created directory: ', d]))

    full_directory = "".join([main_directory,'\\',base_directory,'\\',manga_name]) # manga\Tokyo_Ghoul\Tokyo_Ghoul  _0XX will be appended to this.
    # for i in range( 0, len(chapter_urls) ):
    for i in range( 0, 1 ): # Testing one chapter.
        chapter_directory = "".join( [full_directory, '_', mangaNumbering(chapter_numbers[i])] )  # 'manga\Tokyo_Ghoul\Tokyo_Ghoul\Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        if not os.path.exists(chapter_directory):
            os.mkdir(chapter_directory) # Create chapter directory: '../manga/Tokyo_Ghoul_001/'
        mangabeeDownloadPagesForChapter(chapter_urls[i], chapter_directory)
        break

    return True

def mangaNumbering(s):
    if (len(s) == 1):
        return "".join(['00',s])
    elif (len(s) == 2):
        return "".join(['0',s]) # 019, 020, 021 ...
    elif (len(s) == 3):
        return s                # 100, 211, 321 ... 599

    logging.info('Abnormal numbering encountered') # Multiple requests.
    return "".join(['0',s])

def mangahereDownloadPagesForChapter(chapter_url, directory, chapter_number):
    pages_and_src = []
    page_urls = [] # Holds a reference to the image on mangabee's CDN. You need to parse its HTML for that CDN image link.
    page_numbers = [] # Holds all the links to the images on Mangabee's CDN.
    pages_src = []
    image_files_paths = []

    req = requestWithHeaders(chapter_url) # 1 requests

    parser = mangahereHTMLGetImageLinks()
    parser.feed(req.text)

    page_urls = parser.page_links
    page_numbers = parser.page_numbers

    parser.close

    for page in page_numbers:
        file_path = "".join([directory, '\\', mangaNumbering(page), '.jpg'])
        image_files_paths.append( file_path )

    parser = mangahereHTMLGetImageSrcs()

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor: # Multiple requests.
        # download the load operations and mark each future with its URL
        future_to_url = {executor.submit(requestContentWithHeadersAndKey, url, page): [url,page] for url,page in zip(page_urls,page_numbers)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_data = future.result()
                # print(html_data)
                parser.feed(html_data.get('html'))
                pages_and_src.append( {'page': mangaNumbering(html_data['page']), 'src':parser.src + 'd'} )
                parser.reset # Clear contents of parser.
            except Exception as exc:
                logging.debug( '%r generated an exception: %s' % (url, exc) )

    pages_and_src = sorted(pages_and_src, key=lambda k: k['page'])

    for dic in pages_and_src:
        pages_src.append(dic.get('src'))

    # print(page_urls)
    # print(page_numbers)
    # print(image_files_paths)
    # print(pages_and_src)

    # Build manga chapter integrity json file.
    data = {}
    data['chapter_url'] = chapter_url
    data['image_files_paths'] = image_files_paths
    data['pages_and_src'] = pages_and_src
    data['len'] = len(image_files_paths)
    data['chapter_number'] = chapter_number
    data['downloaded'] = 'Not downloaded'
    writeToJson(data, "".join([directory, '.json']))

    # print(len(pages_and_src))
    # print(len(image_files_paths))
    # print(len(page_urls))

    if ( len(pages_and_src) == len(image_files_paths) == len(page_urls) ): # Number of items in each match so proceed.
        for src, file_path in zip(pages_src, image_files_paths): # Download all pages of the chapter.
            success = requestFile(file_path, src)
            if (success):
                randomSleep(0,1)
            else:
                return False
        randomSleep(5,10)
        data['downloaded'] = 'Downloaded'
        logging.info("".join([chapter_url, ' successfully downloaded.']))
        writeToJson(data, "".join([directory, 'data.txt']))
    else:
        logging.debug("".join(['Number of image_srcs, file_paths, and page_urls do not match. Check page numbering for that chapter on mangahere', image_files_paths[0]]))
        return False

def mangabeeDownloadPagesForChapter(chapter_url, directory): # Multiple requests.
    global bytes
    pages = None
    pages_and_src = []
    page_urls = [] # Holds a reference to the image on mangabee's CDN. You need to parse its HTML for that CDN image link.
    pages_src = [] # Holds all the links to the images on Mangabee's CDN.
    image_files_paths = []

    req = requestWithHeaders(chapter_url) # 1 requests
    parser = mangabeeSetupParser()
    parser.feed(req.text)
    pages = parser.pages #Setup pages for this chapter ['1'..'40']
    parser.close

    parser = mangabeeHTMLGetImageLink()

    # for page in pages: # Multiple requests.
    #     url = chapter_url.rsplit('/', 2)    # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '1']
    #     url[2] = page                       # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '2'] ... ['http://www.mangabee.com/Tokyo_Ghoul', '1', '40'] <-- example last page.
    #     url =  "".join([url[0], '/', url[1], '/', url[2]])
    #     req = requestWithHeaders( url )       # http://www.mangabee.com/Tokyo_Ghoul/1/1 ... http://www.mangabee.com/Tokyo_Ghoul/1/40
    #     bytes += sys.getsizeof(req)           # Add bandwidth usage (GZIP compressed.)
    #     parser.feed(req.text)
    #     file_path = "".join([directory, '\\', mangaNumbering(page), '.jpg'])
    #
    #     image_files_paths.append( file_path ) # manga/Tokyo_Ghoul/Tokyo_Ghoul_001/001.jpg ... manga/Tokyo_Ghoul_001/040.jpg
    #     pages_src.append(parser.src)                                                         # 'http://z.mhcdn.net/...001.0/compressed/o1.01.jpg?v=11325158350' ... 'http://z.mhcdn.net/...ssed/o1.40.jpg?v=11325158350'
    #     # Write image to respective chapter dir and tally the bandwidth usage.
    #     # bytes += urllibee.f.retrieve( parser.src, file ) # 'http://z.mhcdn.net/store/manga/10375/001.0/compressed/o1.01.jpg?v=11325158350', manga/Tokyo_Ghoul_001/001.jpg ... manga/Tokyo_Ghoul_001/040.jpg
    #
    #     parser.reset # Clear contents of parser.

    for page in pages:
        url = chapter_url.rsplit('/', 2)    # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '1']
        url[2] = page                      # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '2'] ... ['http://www.mangabee.com/Tokyo_Ghoul', '1', '40'] <-- example last page.
        url =  "".join([url[0], '/', url[1], '/', url[2]])
        page_urls.append(url)

        file_path = "".join([directory, '\\', mangaNumbering(page), '.jpg'])
        image_files_paths.append( file_path ) # manga/Tokyo_Ghoul/Tokyo_Ghoul_001/001.jpg ... manga/Tokyo_Ghoul_001/040.jpg

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # download the load operations and mark each future with its URL
        future_to_url = {executor.submit(requestContentWithHeadersAndKey, url, page): [url,page] for url,page in zip(page_urls,pages)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_data = future.result()
                # pages_and_src.append(html_data)
                parser.feed(html_data.get('html'))
                pages_and_src.append( {'page': html_data['page'], 'src':parser.src} )
                parser.reset # Clear contents of parser.
            except Exception as exc:
                logging.debug( '%r generated an exception: %s' % (url, exc) )

    print(pages_and_src)
    print(sorted(pages_and_src, key=lambda k: k['page']))
    # print(pages_src)
    # for x in pages_src:
    #     for k,v in x.items():
    #         print("".join([k, ' ', v]))

    # print(sorted(pages_src, key=lambda k: k['page']) )



    # print(len(page_urls))
    # print(len(image_files_paths))
    # print(len(pages_src))
    # if ( len(pages_src) == len(image_files_paths) == len(page_urls) ):
    #     print ('Numbers of image_srcs, file_paths, page_urls match.')
        # for src, file_path in zip(pages_src, image_files_paths):
        #     urllibee.f.retrieve( src, file_path)
    # else:
        # logging.debug("".join(['Number of image_srcs, file_paths, and page_urls do not match. Check page numbering for that chapter on mangabee', image_files_paths[0]]))
        # return False


    return True

def writeToJson(data, directory):
    with open(directory, 'w') as outfile: # This file is used to manage the integrity of the chapter downloaded.
        json.dump(data, outfile)

def requestFile(output, url):
    with open(output, 'wb') as f:
        response = requests.get(url, stream=True)
        writeBytes(int(response.headers.get('Content-Length')))

        if not response.ok:
            print("".join(['Could not download from: ', url]))
            logging.debug( "".join(['Could not download from: ', url]))
            return False

        for chunk in response.iter_content(1024):
            f.write(chunk)

    return True

def requestWithHeaders(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                'Content-Type':'text/plain; charset=utf-8', 'Accept':'*/*', 'Accept-Encoding':'gzip,deflate,sdch,text'}
    req = requests.get(url, headers = headers)

    writeBytes(sys.getsizeof(req)) # Add bandwidth usage (GZIP compressed.)

    return req

def requestContentWithHeaders(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                'Content-Type':'text/plain; charset=utf-8', 'Accept':'*/*', 'Accept-Encoding':'gzip,deflate,sdch,text'}
    req = requests.get(url, headers = headers)

    writeBytes(sys.getsizeof(req)) # Add bandwidth usage (GZIP compressed.)

    return req.text

def requestContentWithHeadersAndKey(url, key):
    global bytes
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
                'Content-Type':'text/plain; charset=utf-8', 'Accept':'*/*', 'Accept-Encoding':'gzip,deflate,sdch,text'}
    req = requests.get(url, headers = headers)

    writeBytes(sys.getsizeof(req)) # Add bandwidth usage (GZIP compressed.)

    return {'page':key, 'html': req.text}


def mangabee_urlify(s):
    s = re.sub(r"[^\w\s-]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '+', s)     # Replaces all runs of whitespace with a single +
    return s

def mangahere_urlify(s):
    s = re.sub(r"[^/.\:\w\s-]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '_', s)     # Replaces all runs of whitespace with a single _
    return s

def onlyNumbers(s):
    s = re.sub(r'[^\d.]+', '', s) # Remove all characters and whitespace
    return s

def onlyNumbersSplit(s):
    return s.split(' ', 1)[0]

def writeBytes(b):
    global bytes
    bytes += b

def resetBytesUsage():
    global bytes
    bytes = 0

def sizeMegs(bytes):
    return bytes/1000000


def sizeKilo(bytes):
    return bytes/1000

def randomSleep(start, to):
    time.sleep(randint(start,to))

bytes = 0 # Keep track of bytes used.
def main():
    global bytes
    logging.info('downloaded')
    # search_term = 'fairy tail'
    search_term = 'tora kiss'
    # search_term = '.hack//Legend'
    manga_site = 'mangahere'
    # manga_site = 'mangabee'
    search_results = search(search_term, manga_site)
    logging.info("".join(['Searching ', search_term, ' on ', manga_site, '...']))
    if search_results:
        print('Returned: ', search_results)

    else:
        print("".join(['Searching \'', search_term, '\' on mangahere did not return anything. Exiting...']))
        logging.info("".join(['Searching \'', search_term, '\' on mangahere did not return anything. Exiting...']))
        exit()
    setup_list = download(search_results[0], manga_site)
    mangahereSetupAndDownload(setup_list)
    #
    # if not search_results:
    #     print("".join(['Searching \'', search_term, '\' on mangabee did not return anything. Exiting...']))
    #     logging.info("".join(['Searching \'', search_term, '\' on mangabee did not return anything. Exiting...']))
    #     exit()
    #
    # print("".join(['Setting up ', search_results[0], '\'s directories and initiating downloads.']))
    # logging.info("".join(['Setting up ', search_results[0], '\'s directories and initiating downloads.']))
    #
    # setup_list = download(search_results[0])
    #
    # print(setup_list)
    #
    # print("".join(['Downloading ', search_results[0], '\'s chapters.']))
    # logging.info("".join(['Downloading ', search_results[0], '\'s chapters.']))
    # mangabeeSetupAndDownload(setup_list)
    #
    logging.info("".join(['Finished... ', 'Usage: ', str(sizeMegs(bytes)), 'M']))
    logging.info("".join(['Finished... ', 'Usage: ', str(sizeKilo(bytes)), 'KB']))

if __name__ == "__main__":
    main()
