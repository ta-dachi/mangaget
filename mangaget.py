import sys
import os
import re
import json
import time
import logging
from random import randint

import concurrent.futures
import urllib.request
import urllib.parse
import gzip

# Pip install frameworks.
import requests
import eventlet
import click

# Custom parsers.
from mangabee_parsers import *
from mangahere_parsers import *

###
### Config
###
logging.basicConfig(filename='mangaget.py.log', filemode='w', level=logging.DEBUG)
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING) #Disable logging for requests by setting it to WARNING which we won't use.

###
### Functions
###

#
# Search for manga on specified manga site.
#
def search(manga_name, manga_site): # 1 request.
    mangabee_url  = 'http://www.mangabee.com/manga-list/search/%s/name-az/1' % mangabee_urlify(manga_name)
    mangahere_url = 'http://www.mangahere.co/search.php?name=%s' % urllib.parse.quote(mangahere_urlify(manga_name))
    results       = None
    parser        = None

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

    return results # ['http://www.mangahere.co/manga/boku_to_kanojo_no_game_sensou/', 'http://www.mangahere.co/manga/no_game_no_life/', 'http://www.mangahere.co/manga/ore_to_ichino_no_game_doukoukai_katsudou_nisshi/']

#
# Begin the process of downloading
#
def beginDownloading(url, manga_site): # 1 request.
    src      = None # Mangabee
    chapters = None
    pages    = None
    links    = None # Mangahere

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

def mangahereSetupAndDownload(setup): # 0 requests.
    chapter_urls = sorted(setup.get('links')) # They come in reversed from mangahere.
    first_chapter_url = chapter_urls[0] # http://www.mangahere.co/manga/hack_legend_of_twilight/v03/c000.4/
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
    for i in range( 0, len(chapter_urls) ):
    # for i in range( 0, 1 ): # Testing
        chapter_number = chapter_urls[i].rsplit('/',2)[1] # Use the part of the url for chapter numbering instead of var i in the for loop.
        chapter_directory = "".join( [full_directory, '_', chapter_number] )  # 'mangahere\Tokyo_Ghoul\Tokyo_Ghoul\Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        if not os.path.exists(chapter_directory):
            os.mkdir(chapter_directory) # Create chapter directory: '../mangahere/Tokyo_Ghoul_001/'

        mangahereDownloadPagesForChapter(chapter_urls[i], chapter_directory, chapter_number)

    return True


def mangabeeSetupAndDownload(setup): # 0 requests.
    chapter_urls      = []
    first_chapter_url = setup.get('url')[0].rsplit('/', 2)[0] # http://www.mangabee.com/Tokyo_Ghoul
    chapter_numbers   = setup.get('chapters')
    main_directory    = 'mangabee'
    base_directory    = None
    manga_name        = None

    for i in range(0, len(setup.get('chapters'))):
        chapter_urls.append( "".join([first_chapter_url, '/', setup.get('chapters')[i], '/', '1']) ) # [ http://www.mangabee.com/Tokyo_Ghoul/1/1, ..., http://www.mangabee.com/Tokyo_Ghoul/137/1 ]

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
    for i in range( 0, (len(chapter_urls)) ):
    # for i in range( 0, 1 ): # Testing one chapter.
        chapter_number = (i+1) # Add one because chapters start at 1 not 0.
        chapter_directory = "".join( [full_directory, '_', mangaNumbering(chapter_numbers[i])] )  # 'manga\Tokyo_Ghoul\Tokyo_Ghoul\Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        if not os.path.exists(chapter_directory):
            os.mkdir(chapter_directory) # Create chapter directory: '../manga/Tokyo_Ghoul_001/'
        mangabeeDownloadPagesForChapter(chapter_urls[i], chapter_directory, chapter_number)
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
    pages_and_src     = []
    page_urls         = [] # Holds a reference to the image on mangahere's CDN. You need to parse its HTML for that CDN image link.
    page_numbers      = []
    pages_src         = [] # Holds all the links to the images on Mangahere's CDN.
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

    # Concurrently finds image src on each html page.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor: # Multiple requests.
        # download the load operations and mark each future with its URL
        future_to_url = {executor.submit(requestContentWithHeadersAndKey, url, page): [url,page] for url,page in zip(page_urls,page_numbers)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_data = future.result()
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

    # print(len(pages_and_src))
    # print(len(image_files_paths))
    # print(len(page_urls))

    if ( len(pages_and_src) == len(image_files_paths) == len(page_urls) == len(page_numbers) ): # Number of items in each match so proceed.
        # Build a manga chapter integrity json file.
        data = {}
        data['chapter_url'] = chapter_url
        data['image_files_paths'] = image_files_paths
        data['pages_and_src'] = pages_and_src
        data['len'] = len(image_files_paths)
        data['chapter_number'] = chapter_number
        data['downloaded'] = 'Not downloaded'
        writeToJson(data, "".join([directory, '.json']))

        for src, file_path in zip(pages_src, image_files_paths): # Download all pages of the chapter.
            image_file = requestFile(file_path, src)
            if (image_file):
                randomSleep(0,1) # Don't make the server think we're downloading too fast so introduce a delay.
            else:
                print("".join([chapter_url, ' could not be downloaded.']))
                logging.info("".join([chapter_url, ' could not be downloaded.']))
                return False
        randomSleep(5,10) # Introduce a longer delay after you downloaded a whole chapter.
        data['downloaded'] = 'Downloaded'
        print("".join([chapter_url, ' successfully downloaded.']))
        logging.info("".join([chapter_url, ' successfully downloaded.']))
        writeToJson(data, "".join([directory, '.json']))
    else:
        logging.debug("".join(['Number of image_srcs, file_paths, and page_urls do not match. Check page numbering for that chapter on mangahere', image_files_paths[0]]))
        return False

def mangabeeDownloadPagesForChapter(chapter_url, directory, chapter_number): # Multiple requests.
    pages_and_src     = []
    page_urls         = [] # Holds a reference to the image on mangabee's CDN. You need to parse its HTML for that CDN image link.
    page_numbers      = []
    pages_src         = [] # Holds all the url links to the just the images on Mangabee's CDN.
    image_files_paths = []

    req = requestWithHeaders(chapter_url) # 1 requests
    parser = mangabeeSetupParser()
    parser.feed(req.text)
    page_numbers = parser.pages #Setup pages for this chapter ['1'..'40']
    parser.close

    parser = mangabeeHTMLGetImageLink()

    for page in page_numbers:
        url = chapter_url.rsplit('/', 2)    # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '1']
        url[2] = page                      # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '2'] ... ['http://www.mangabee.com/Tokyo_Ghoul', '1', '40'] <-- example last page.
        url =  "".join([url[0], '/', url[1], '/', url[2]])
        page_urls.append(url)

        file_path = "".join([directory, '\\', mangaNumbering(page), '.jpg'])
        image_files_paths.append( file_path ) # manga/Tokyo_Ghoul/Tokyo_Ghoul_001/001.jpg ... manga/Tokyo_Ghoul_001/040.jpg

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # download the load operations and mark each future with its URL
        future_to_url = {executor.submit(requestContentWithHeadersAndKey, url, page): [url,page] for url,page in zip(page_urls,page_numbers)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_data = future.result()
                # pages_and_src.append(html_data)
                parser.feed(html_data.get('html'))
                pages_and_src.append( {'page': mangaNumbering(html_data['page']), 'src':parser.src} )
                parser.reset # Clear contents of parser.
            except Exception as exc:
                logging.debug( '%r generated an exception: %s' % (url, exc) )

    pages_and_src = sorted(pages_and_src, key=lambda k: k['page']) # Since the files were downloaded concurrently, the ordering is not correct so sort them by page.

    for dic in pages_and_src:
        pages_src.append(dic.get('src'))

    # print(page_urls)
    # print(page_numbers)
    # print(image_files_paths)
    # print(pages_and_src)
    # print(pages_src)

    if ( len(pages_and_src) == len(image_files_paths) == len(page_urls) == len(page_numbers) ): # Number of items in each match so proceed.
        # Build a manga chapter integrity json file.
        data = {}
        data['chapter_url'] = chapter_url
        data['image_files_paths'] = image_files_paths
        data['pages_and_src'] = pages_and_src
        data['len'] = len(image_files_paths)
        data['chapter_number'] = chapter_number
        data['downloaded'] = 'Not downloaded'
        writeToJson(data, "".join([directory, '.json']))

        for src, file_path in zip(pages_src, image_files_paths): # Download all pages of the chapter.
            image_file = requestFile(file_path, src)
            if (image_file):
                randomSleep(0,1) # Don't make the server think we're downloading too fast so introduce a delay.
            else:
                print("".join([chapter_url, ' could not be downloaded.']))
                logging.info("".join([chapter_url, ' could not be downloaded.']))
                return False
        randomSleep(5,10) # Introduce a longer delay after you downloaded a whole chapter.
        data['downloaded'] = 'Downloaded'
        print("".join([chapter_url, ' successfully downloaded.']))
        logging.info("".join([chapter_url, ' successfully downloaded.']))
        writeToJson(data, "".join([directory, '.json']))
        pass
    else:
        logging.debug("".join(['Number of image_srcs, file_paths, and page_urls do not match. Check page numbering for that chapter on mangabee', image_files_paths[0]]))
        return False

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

###
### Main
###
bytes = 0 # Keep track of bytes used.
@click.command()
@click.option('--manga_site', default='mangahere', help='mangahere mangabee')
@click.option('--no_dl', default=0, help='Just searches but does not download. Usage: mangaget --no_dl=1 hajime_no_ippo')
@click.argument('search_term')

def mangaget(search_term, manga_site, no_dl):
    """A program that downloads manga from mangahere and mangabee."""
    global bytes
    index = None

    search_results = search(search_term, manga_site)
    print("".join(['Searching ', search_term, ' on ', manga_site, '...\n']))
    logging.info("".join(['Searching ', search_term, ' on ', manga_site, '...']))
    if search_results:
        index = 888
        if (len(search_results) == 1): # only one choice so..
            print("".join(['Found ', search_results[0], '\n']))
            logging.info("".join(['Found ', search_results[0]]))
            index = 0
        else:
            while index >= len(search_results):
                print('pick a mangalink: ')
                for i in range(0, len(search_results)): # Make sure it's within our search results.
                    print("".join([str(i), '. ', search_results[i]]))
                try:
                    index = int(input('Enter a number: ')) # Get the number.
                except ValueError: # This catches empty strings and makes it so it keeps asking for input.
                    index = index
        logging.info("".join(['Search Returned: ', search_results[0]]))
    else:
        print("".join(['Searching \'', search_term, '\' did not return anything. Exiting...']))
        logging.info("".join(['Searching \'', search_term, '\' did not return anything. Exiting...']))
        exit()
    if (no_dl): # Don't download if set.
        exit()

    setup = beginDownloading(search_results[index], manga_site) # Creates all the directories for the manga.

    print("".join(['Downloading \'', search_results[index], '\'...']))
    logging.info("".join(['Downloading \'', search_results[index], '\'...']))
    if (manga_site == 'mangahere'):
        mangahereSetupAndDownload(setup) # Does all the downloading and integrity checks.
    elif (manga_site == 'mangabee'):
        mangabeeSetupAndDownload(setup)
    else:
        pass


    print("".join(['Finished... ', 'Usage: ', str(sizeMegs(bytes)), 'M']))
    print("".join(['Finished... ', 'Usage: ', str(sizeKilo(bytes)), 'KB']))
    logging.info("".join(['Finished... ', 'Usage: ', str(sizeMegs(bytes)), 'M']))
    logging.info("".join(['Finished... ', 'Usage: ', str(sizeKilo(bytes)), 'KB', '\n']))

if __name__ == "__main__":
    mangaget()
