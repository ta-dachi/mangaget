import sys
import os
import re
import json
import time
import logging
import datetime
import glob
from pprint import pprint
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
logging.basicConfig(filename='mangaget.py.log', filemode='w+', level=logging.DEBUG)
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING) #Disable logging for requests by setting it to WARNING which we won't use.

###
### Functions
###

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
        printAndLogInfo("".join(['Not a valid manga site: ', manga_site, '. Try \'mangabee\' or \'mangahere\'']))
        return False

    parser.feed(req)         # req contains all the html from url.
    results = parser.links   # Save our results.
    parser.close             # Free the parser resource.

    return results # ['http://www.mangahere.co/manga/boku_to_kanojo_no_game_sensou/', 'http://www.mangahere.co/manga/no_game_no_life/', 'http://www.mangahere.co/manga/ore_to_ichino_no_game_doukoukai_katsudou_nisshi/']

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
        chapters = [e[:3] for e in parser.chapters]

        chapters = [onlyNumbers(e) for e in chapters] # Leave only the numbers and strip chracters

        chapters = sorted(filter(None, chapters), key=int)

        parser.close
        results = dict(url=[url], src=src, chapters=chapters, pages=pages)

        return results # {'chapters': ['1', ... '9'], 'src': ['http://i3.mangareader.net/blood-c/1/blood-c-2691771.jpg'], 'url': ['http://www.mangabee.com/blood-c/1/1'], 'pages': ['1', ...', '40']}
    else:
        printAndLogInfo("".join(['Not a valid manga site: ', manga_site, '. Try \'mangabee\' or \'mangahere\'']))
        return False

def mangahereSetupAndDownload(setup): # 0 http requests.
    chapter_urls        = sorted(setup.get('links')) # They come in reversed from mangahere.
    chapter_directories = []
    chapter_numbers     = []
    first_chapter_url   = chapter_urls[0] # http://www.mangahere.co/manga/hack_legend_of_twilight/v03/c000.4/
    main_directory      = 'mangahere'
    base_directory      = None
    manga_name          = None
    directory           = None
    data                = {} # For our json integrity file that manages all the chapters.


    ### Create directories ###
    # volume based: ['http:', '', 'www.mangahere.co', 'manga', 'hack_legend_of_twilight', 'v01', 'c000', ''] count: 8
    # !volumebased: ['http:', '', 'www.mangahere.co', 'manga', 'tora_kiss_a_school_odyssey', 'c001.1', '']  count: 7
    if (len(first_chapter_url.split('/')) < 8):
        manga_name = first_chapter_url.rsplit('/',4)[2]  # parse the url for something like this this: 'tokyo_ghoul'
    else:
        manga_name = first_chapter_url.rsplit('/',4)[1]  # parse the url for something like this this: 'tokyo_ghoul'

    base_directory = manga_name # 'tokyo_ghoul'

    if not os.path.exists(main_directory): # directory: ..mangahere/
        os.mkdir(main_directory)           # directory: ..mangahere/
        logging.info("".join([timestamp(), ' Created directory: ', main_directory]))

    directory = os.path.join(main_directory, base_directory) # ..mangahere/tokyo_ghouls/
    if not os.path.exists(directory):
        os.mkdir(directory) # ..mangahere/tokyo_ghouls/
        logging.info("".join([timestamp(), ' Created directory: ', directory]))

    full_directory = os.path.join(main_directory, base_directory)  # mangahere\Tokyo_Ghoul\Tokyo_Ghoul - chapter number will be appended.
    for i in range( 0, len(chapter_urls) ):
        chapter_number = chapter_urls[i].rsplit('/',2)[1] # Use the part of the url for chapter numbering instead of var i in the for loop.
        chapter_directory = os.path.join( full_directory, "".join( [manga_name, '_', chapter_number] ) )  # 'mangahere\Tokyo_Ghoul\Tokyo_Ghoul\Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        chapter_directories.append(chapter_directory)
        chapter_numbers.append(chapter_number)

    ### Write integrity json file ###
    data['chapter_urls'] = chapter_urls
    data['chapter_directories'] = chapter_directories
    data['chapter_numbers'] = chapter_numbers
    data['main_directory'] = main_directory

    writeToJson(data, os.path.join( main_directory, "".join([manga_name, '_', 'chapters.json']) ))

    ### Download each chapter ###
    for i in range( 0, len(chapter_urls) ):
    # for i in range( 0, 1 ): # Download only one chapter for testing
        if not os.path.exists(chapter_directories[i]):
            os.mkdir(chapter_directories[i]) # Create chapter directory: '../mangahere/Tokyo_Ghoul_001/'
        print("".join(['Downloading ', chapter_urls[i], ' ...']), end='')
        mangahereDownloadPagesForChapter(chapter_urls[i], chapter_directories[i], chapter_number)

    return True

def mangabeeSetupAndDownload(setup): # 0 requests.
    chapter_urls        = []
    chapter_directories = []
    chapter_numbers     = setup.get('chapters')
    first_chapter_url   = setup.get('url')[0].rsplit('/', 2)[0] # http://www.mangabee.com/Tokyo_Ghoul
    main_directory      = 'mangabee'
    base_directory      = None
    manga_name          = None
    data                = {} # For our json integrity file that manages all the chapters.

    for i in range(0, len(chapter_numbers)):
        chapter_urls.append( "".join([first_chapter_url, '/', chapter_numbers[i], '/', '1']) ) # [ http://www.mangabee.com/Tokyo_Ghoul/1/1, ..., http://www.mangabee.com/Tokyo_Ghoul/137/1 ]

    ### Create directories ###
    manga_name = chapter_urls[0].rsplit('/',3)[1]  # parse the url for something like this this: 'tokyo_ghoul'
    base_directory = manga_name                    # 'tokyo_ghoul'

    if not os.path.exists(main_directory): # directory: ..mangabee/
        os.mkdir(main_directory)           # directory: ..mangabee/
        logging.info("".join([timestamp(), ' Created directory: ', main_directory]))

    directory = os.path.join(main_directory, base_directory) # ../manga/tokyo_ghouls/
    if not os.path.exists(directory):
        os.mkdir(directory) # manga/tokyo_ghouls/
        logging.info("".join([timestamp(), ' Created directory: ', directory]))

    for i in range( 0, len(chapter_urls) ):
        chapter_number = (i+1) # Add one because chapters start at 1 not 0.
        chapter_directory = os.path.join( directory, "".join( [manga_name, '_', mangaNumbering(str(chapter_number))]) ) # 'manga/Tokyo_Ghoul/Tokyo_Ghoul/Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        chapter_directories.append(chapter_directory)


    #### Write Integrity File ###
    data['chapter_urls'] = chapter_urls
    data['chapter_directories'] = chapter_directories
    data['chapter_numbers'] = chapter_numbers
    data['main_directory'] = main_directory

    writeToJson(data, os.path.join( main_directory, "".join([manga_name, '_', 'chapters.json']) ))

    ### Download each chapter ###
    full_directory = os.path.join(main_directory, base_directory) # manga/Tokyo_Ghoul/Tokyo_Ghoul  _0XX will be appended to this.
    for i in range( 0, (len(chapter_urls)) ):
    # for i in range( 0, 1 ): # Testing one chapter.
        if not os.path.exists(chapter_directories[i]):
            os.mkdir(chapter_directories[i]) # Create chapter directory: '../manga/Tokyo_Ghoul_001/'
        print("".join(['Downloading ', chapter_urls[i], ' ...']), end='')
        mangabeeDownloadPagesForChapter(chapter_urls[i], chapter_directories[i], chapter_number)

    return True

def mangahereDownloadPagesForChapter(chapter_url, directory, chapter_number): # Uses 99% of the bandwidth.
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

    ### Concurrently find image src on each html page. ###
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor: # Multiple requests.
        # Download the load operations and mark each future with its URL
        future_to_url = {executor.submit(requestContentWithHeadersAndKey, url, page): [url,page] for url,page in zip(page_urls,page_numbers)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_data = future.result()
                parser.feed(html_data.get('html'))
                pages_and_src.append( {'page': mangaNumbering(html_data['page']), 'src':parser.src + 'd'} )
                parser.reset # Clear contents of parser.
            except Exception as exc:
                printAndLogDebug( timestamp(), ' %r generated an exception: %s' % (url, exc) )

    pages_and_src = sorted(pages_and_src, key=lambda k: k['page'])

    for dic in pages_and_src:
        pages_src.append(dic.get('src'))

    if ( len(pages_and_src) == len(image_files_paths) == len(page_urls) == len(page_numbers) ): # Number of items in each match so proceed.
        ### Build a manga chapter integrity json file. ###
        data = {}
        data['directory'] = directory
        data['chapter_url'] = chapter_url
        data['image_files_paths'] = image_files_paths
        data['pages_and_src'] = pages_and_src
        data['len'] = len(image_files_paths)
        data['chapter_number'] = chapter_number
        data['downloaded'] = 'Not Downloaded'
        writeToJson(data, "".join([directory, '.json']))

        ### Queue image src list and output file directories list ###
        downloadConcurrently(pages_src, image_files_paths) # Parameter examples: http://z.mhcdn.net/store/manga/3249/01-001.0/compressed/gokko_story01_w.s_001.jpg?v=11216726214d, "mangahere\\gokko\\gokko_c001\\001.jpg" ...
        data['downloaded'] = 'Downloaded'
        logging.info("".join([timestamp(),' ', chapter_url, ' successfully downloaded.']))
        seconds = str(randomSleep(3,5)) # Introduce a longer delay after you downloaded a whole chapter.
        print(' Success!')
        print("".join(['waiting ', seconds, ' seconds...']))
        writeToJson(data, "".join([directory, '.json']))
    else:
        logging.debug("".join([timestamp(), ' Number of image_srcs, file_paths, and page_urls do not match. Check page numbering for that chapter on mangahere', image_files_paths[0]]))
        return False

    return True

def mangabeeDownloadPagesForChapter(chapter_url, directory, chapter_number): # Multiple requests. Uses 99% of the bandwidth.
    pages_and_src     = []
    page_urls         = [] # Holds a reference to the image on mangabee's CDN. You need to parse its HTML for that CDN image link.
    page_numbers      = []
    pages_src         = [] # Holds all the url links to the just the images on Mangabee's CDN.
    image_files_paths = [] # Holds the path to each image file.

    req = requestWithHeaders(chapter_url) # 1 request.

    parser = mangabeeSetupParser()
    parser.feed(req.text)

    page_numbers = parser.pages # Setup pages for this chapter ['1'..'40'].

    parser.close

    for page in page_numbers:
        url = chapter_url.rsplit('/', 2)    # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '1'].
        url[2] = page                       # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '2'] ... ['http://www.mangabee.com/Tokyo_Ghoul', '1', '40'] <-- example last page.
        url =  "".join([url[0], '/', url[1], '/', url[2]])
        page_urls.append(url)

        file_path = "".join([directory, '\\', mangaNumbering(page), '.jpg'])
        image_files_paths.append( file_path ) # manga/Tokyo_Ghoul/Tokyo_Ghoul_001/001.jpg ... manga/Tokyo_Ghoul_001/040.jpg

    parser = mangabeeHTMLGetImageLink()

    ### Concurrently find image src on each html page. ###
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_url = {executor.submit(requestContentWithHeadersAndKey, url, page): [url,page] for url,page in zip(page_urls,page_numbers)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_data = future.result()
                parser.feed(html_data.get('html'))
                pages_and_src.append( {'page': mangaNumbering(html_data['page']), 'src':parser.src} )
                parser.reset # Clear contents of parser.
            except Exception as exc:
                logging.debug( timestamp(), ' %r generated an exception: %s' % (url, exc) )

    pages_and_src = sorted(pages_and_src, key=lambda k: k['page']) # Since the files were downloaded concurrently, the ordering is not correct so sort them by page.

    for dic in pages_and_src:
        pages_src.append(dic.get('src'))

    if ( len(pages_and_src) == len(image_files_paths) == len(page_urls) == len(page_numbers) ): # Number of items in each match so proceed.
        # Build a manga chapter integrity json file.
        data = {}
        data['directory'] = directory
        data['chapter_url'] = chapter_url
        data['image_files_paths'] = image_files_paths
        data['pages_and_src'] = pages_and_src
        data['len'] = len(image_files_paths)
        data['chapter_number'] = chapter_number
        data['downloaded'] = 'Not Downloaded'
        writeToJson(data, "".join([directory, '.json']))

        ### Queue image src list and output file directories list ###
        downloadConcurrently(pages_src, image_files_paths) # Parameter examples: http://z.mhcdn.net/store/manga/3249/01-001.0/compressed/gokko_story01_w.s_001.jpg?v=11216726214d, "mangahere\\gokko\\gokko_c001\\001.jpg" ...
        data['downloaded'] = 'Downloaded'
        logging.info("".join([timestamp(),' ', chapter_url, ' successfully downloaded.']))
        seconds = str(randomSleep(1,3)) # Introduce a longer delay after you downloaded a whole chapter.
        print(' Success!')
        print("".join(['waiting ', seconds, ' seconds...']))
        writeToJson(data, "".join([directory, '.json']))
    else:
        logging.debug("".join([timestamp(), 'Number of image_srcs, file_paths, and page_urls do not match. Check page numbering for that chapter on mangabee', image_files_paths[0]]))
        return False

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

def writeToJson(data, directory):
    with open(directory, 'w') as outfile: # This file is used to manage the integrity of the chapter downloaded.
        json.dump(data, outfile)

def requestFile(output, url):
    with open(output, 'wb') as f:
        response = requests.get(url, stream=True)
        writeBytes(int(response.headers.get('Content-Length')))

        if not response.ok:
            print("".join(['Could not download from: ', url]))
            logging.debug( "".join([timestamp(), ' Could not download from: ', url]))
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
    num = randint(start,to)
    time.sleep(num)
    return num

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

def printAndLogInfo(string):
    print(string)
    logging.info(string)
    pass

def printAndLogDebug(string):
    print(string)
    logging.debug(string)
    pass

def timestamp():
    return str(datetime.datetime.fromtimestamp(time.time()).strftime('[%Y-%m-%d %H:%M:%S]'))

def imageFileCount(path):
    img_files = glob.glob(os.path.join(path, '*.jpg'))
    return len(img_files)

def downloadConcurrently(urls, paths):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor: # Multiple requests.
        for path,url in zip(paths, urls):
            executor.submit(requestFile, path, url)
            randomSleep(0,1)
    return True

def downloadConcurrentlyAdhoc(json_file, ):
    pass

def checkChapterIntegrity(search_string, manga_site):
    def verify(json_file):
        json_data = open(json_file).read()
        data = json.loads(json_data)
        print(json_file)
        printAndLogInfo( "".join([timestamp(), ' Verifying ', data.get('directory') , '...']) )

        img_file_count = imageFileCount(data.get('directory'))

        if ( data.get('downloaded') == 'Not Downloaded' or int(img_file_count) != int(data.get('len')) ):
            pages_src = []
            for dic in data.get('pages_and_src'):
                pages_src.append(dic.get('src'))

            downloadConcurrently(pages_src, data.get('image_files_paths')) # Parameter examples: http://z.mhcdn.net/store/manga/3249/01-001.0/compressed/gokko_story01_w.s_001.jpg?v=11216726214d, "mangahere\\gokko\\gokko_c001\\001.jpg" ...
            data['downloaded'] = 'Downloaded'
            printAndLogInfo( "".join([data.get('chapter_url'), ' Chapter downloaded successfully.']) )
            writeToJson(data, json_file) # Write again and specify that the whole chapter is downloaded successfully.
        else:
            if ( int(img_file_count) == int(data.get('len')) ):
                printAndLogInfo( "".join([timestamp(), ' ', data.get('directory'), ' Integrity check is good for this chapter.']) )
            else:
                printAndLogDebug( "".join([timestamp(), ' ', data.get('directory'), ' Integrity check failed. Something went deeply wrong. File a bug report please.']) )


    search_string = "".join(['*',search_string,'*'])
    if (manga_site == 'mangahere'):
        search_results = glob.glob("".join(os.path.join('mangahere',search_string)))
    elif (manga_site == 'mangabee'):
        print(search_string)
        search_results = glob.glob("".join(os.path.join('mangabee',search_string)))
    else:
        printAndLogInfo( "".join(['No such manga site.']) )

    index = 888
    if (len(search_results) == 1): # only one choice so..
        json_files = glob.glob(os.path.join(search_results[0], '*.json'))
        for json_file in json_files:
            verify(json_file)
    elif (len(search_results) > 1):
        for i in range(0, len(search_results)): # Make sure it's within our search results.
            print("".join([str(i), '. ', search_results[i]])) # Display choices of manga to check its integrity.

        try: # Ask for which manga to check.
            index = int(input('Enter a number: ')) # Get the number.
        except (KeyboardInterrupt, SystemExit): # This catches empty strings and makes it so it keeps asking for input.
            raise
        except ValueError: # This catches empty strings and makes it so it keeps asking for input.
            index = index
        except: # Catch-all particularly KeyboardInterrupt.
            print('\nCancelling...')
            exit()

        json_files = glob.glob(os.path.join(search_results[index], '*.json'))
        if (json_files):
            for json_file in json_files:
                verify(json_file)
        else:
            printAndLogInfo("".join([timestamp(), ' No integrity json file found in ',search_results[index], '.']))
    else:
        printAndLogInfo("".join([timestamp(), ' No such manga found.']))


###
### Main
###
def main(): # For debugging specific functions
    pass

bytes = 0 # Keep track of bytes used.
@click.command()
@click.option('--manga_site', default='mangahere', help='mangahere mangabee\n Usage: mangaget.py --manga_site mangabee bleach')
@click.option('--check', default=False, help='Download manga chapters you are missing. And download missing pages for each chapter.\n Usage: mangaget.py --check=True naruto')
@click.option('--no_dl', default=0, help='Just searches but does not download.\n Usage: mangaget --no_dl=1 hajime_no_ippo')
@click.argument('search_term')

def mangaget(search_term, manga_site, no_dl, check):
    """A program that downloads manga from mangahere and mangabee."""
    global bytes
    index = 888

    if (check): ## --check integrity of selected manga.
        if (manga_site == 'mangahere'):
            checkChapterIntegrity(search_term,'mangahere')
        elif (manga_site == 'mangabee'):
            checkChapterIntegrity(search_term,'mangabee')
        else:
            printAndLogInfo('Not a valid manga site')
    else:
        ### Search for manga on manga site ###
        search_results = search(search_term, manga_site)
        printAndLogInfo("".join(['Searching ', search_term, ' on ', manga_site, '...\n']))
        if (search_results):
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
                    except (KeyboardInterrupt, SystemExit): # This catches empty strings and makes it so it keeps asking for input.
                        raise
                    except ValueError: # This catches empty strings and makes it so it keeps asking for input.
                        index = index
                    except: # Catch-all particularly KeyboardInterrupt.
                        print('\nCancelling...')
                        exit()
            logging.info("".join([timestamp(), ' Search Returned: ', search_results[0]]))
        else:
            printAndLogInfo("".join(['Searching \'', search_term, '\' did not return anything. Exiting...']))
            exit()

        if (no_dl): # Don't download if set.
            exit()

        setup = beginDownloading(search_results[index], manga_site) # Initialize the downloading process.

        printAndLogInfo("".join(['Downloading \'', search_results[index], '\'...']))

        if (manga_site == 'mangahere'):
            mangahereSetupAndDownload(setup) # Does all the downloading.
        elif (manga_site == 'mangabee'):
            mangabeeSetupAndDownload(setup)
        else:
            pass

    print("".join(['Finished... ', 'Usage: ', str(sizeMegs(bytes)), 'M']))
    print("".join(['Finished... ', 'Usage: ', str(sizeKilo(bytes)), 'KB']))
    printAndLogInfo("".join([timestamp(), ' Finished... ', 'Usage: ', str(sizeMegs(bytes)), 'M']))
    printAndLogInfo("".join([timestamp(), ' Finished... ', 'Usage: ', str(sizeKilo(bytes)), 'KB', '\n']))

if __name__ == "__main__":
    # main() # For debugging specific functions
    mangaget()
