import sys
sys.path.append('C:/Users/tadachi/Desktop/Dropbox/git/')
import urllibee.f

import re
import os
import logging

from html.parser import HTMLParser
import urllib.request
import gzip

import concurrent.futures
import requests

###
### Config
###
logging.basicConfig(filename='downloader.py.log', filemode='w', level=logging.DEBUG)

def urlify(s):
    s = re.sub(r"[^\w\s-]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '+', s) # Replaces all runs of whitespace with a single +
    return s

def onlyNumbers(s):
    s = re.sub(r'[^\d.]+', '', s) # Remove all characters and whitespace
    return s

def onlyNumbersSplit(s):
    return s.split(' ', 1)[0]

class mangabeeSearchParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inLink = False
        self.lastTag = None
        self.lastClass = None
        self.links = []         # Where we store our results

    def handle_starttag(self, tag, attrs):
        if (tag == 'div'):
            attrs = dict(attrs)
            self.lastTag = 'div'
            if (attrs.get('class') == 'nde'):
                self.inLink = True
                self.lastClass ='nde'
        if (self.lastClass == 'nde'):
            if (tag == 'div'):
                attrs = dict(attrs)
                if (attrs.get('class') == 'cvr'):
                    self.lastClass ='cvr'
        if (self.lastTag == 'div' and tag == 'a' and self.lastClass == 'cvr'):
            self.lastTag = 'a'
            attrs = dict(attrs)                       # example output: {'href': 'http://www.mangabee.com/Tokyo_Ghoul/'}
            self.links.append( attrs.get('href') )     #['http://www.mangabee.com/Tokyo_Ghoul', ...]

    def handle_endtag(self, tag):
        if (tag == 'div'):
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

    def handle_data(self, data):
        pass

class mangabeeSetupParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inLink = False
        self.lastTag = None
        self.lastClass = None
        self.pages = []
        self.chapters = []
        self.src = []
        self.first_occurrence = False

    def handle_starttag(self, tag, attrs):
        if (tag == 'select'): # The tag with pages data.
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'select'
            if (attrs.get('class') == 'cbo_wpm_pag'):
                self.lastClass = 'cbo_wpm_pag'

        if (tag == 'option' and self.lastClass == 'cbo_wpm_pag'):
            self.inLink = True
            self.lastTag = 'option'

        if (tag == 'select'):  # The tag with chapter data.
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'select'
            if (attrs.get('class') == 'cbo_wpm_chp'):
                self.lastClass = 'cbo_wpm_chp'

        if (tag == 'img'): # Wade through html to find img tag.
            self.inLink = True
            attrs = dict(attrs)  # The tag with image data and location.
            self.lastTag = 'img'
            if (attrs.get('class') == 'manga-page'): # Found tag with manga image.
                self.lastClass = 'manga-page'
                self.src.append(attrs.get('src')) # Add example src. Need lots of string manipulation to generate image links

    def handle_endtag(self, tag):
        if (tag == 'select' and self.lastClass =='cbo_wpm_chp'): # The tag with chapter data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None
            self.first_occurrence = True # Chapter selection occurs twice so, only add chapters once.
        if (tag == 'select'): # The tag with chapter data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None
        if (tag == 'img'): # The tag with image data and location.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

    def handle_data(self, data):
        if (self.lastClass == 'cbo_wpm_chp' and self.first_occurrence == False):
            self.chapters.append(data)
        if (self.lastClass == 'cbo_wpm_pag' and self.lastTag == 'option'):
            self.pages.append(data)


class mangabeeHTMLGetImageLink(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inLink = False
        self.lastTag = None
        self.lastClass = None
        self.pages = []
        self.src = None

    def handle_starttag(self, tag, attrs):
        if (tag == 'select'): # The tag with pages data.
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'select'
            if (attrs.get('class') == 'cbo_wpm_pag'):
                self.lastClass = 'cbo_wpm_pag'

        if (tag == 'option' and self.lastClass == 'cbo_wpm_pag'):
            self.inLink = True
            self.lastTag = 'option'

        if (tag == 'img'): # Wade through html to find img tag.
            self.inLink = True
            attrs = dict(attrs)  # The tag with image data and location.
            self.lastTag = 'img'
            if (attrs.get('class') == 'manga-page'): # Found tag with manga image.
                self.lastClass = 'manga-page'
                self.src = attrs.get('src') # Add example src.

    def handle_endtag(self, tag):
        if (tag == 'select'): # The tag with chapter data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

        if (tag == 'img'): # The tag with image data and location.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

    def handle_data(self, data):
        if (self.lastClass == 'cbo_wpm_pag' and self.lastTag == 'option'):
            self.pages.append(data)

        pass

def search(manga_name):
    global bytes
    url = 'http://www.mangabee.com/manga-list/search/%s/name-az/1' % urlify(manga_name)

    results = None
    req = urllib.request.Request(url) # Need headers so that the server does not deny request.
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36')
    req.add_header('Content-Type', 'text/plain; charset=utf-8 ')
    req.add_header('Accept', '*/*')
    req.add_header('Accept-Encoding', 'gzip,deflate,sdch')

    res = urllib.request.urlopen(req)
    bytes += sys.getsizeof(res) # Add bandwidth usage (GZIP compressed.)

    if res.info().get('Content-Encoding') == 'gzip':
        with gzip.open(res, 'rb') as f: #rb readbinary
            content = f.read().decode('utf-8')
            # bytes += sys.getsizeof(content) # Add bandwidth usage. (UNCOMPRESSED adds way more bytes by 100x)
            parser = mangabeeSearchParser()
            parser.feed(content)
            results = parser.links # Save our results
            parser.close
            f.close()
    return results

def setup(url):
    global bytes
    url = url + '1/1'
    src = None
    chapters = None
    pages = None

    res = requestHTMLWithPageImage(url)
    bytes += sys.getsizeof(res) # Add bandwidth usage (GZIP compressed.)
    if res.info().get('Content-Encoding') == 'gzip':
        with gzip.open(res, 'rb') as f: #rb readbinary

            parser = mangabeeSetupParser()
            content = f.read().decode('utf-8')
            # bytes += sys.getsizeof(content) # Add bandwidth usage. (UNCOMPRESSED adds way more bytes by 100x)
            parser.feed(content)

            src = parser.src
            pages = parser.pages
            chapters = [e for e in parser.chapters if 'Raw' not in e] # all chapters with Raw are untranslated so filter them out.
            chapters = [onlyNumbersSplit(e) for e in chapters] # Leave only the numbers and strip chracters
            chapters = sorted(chapters, key = lambda x: int(x.split('.')[0]))

            parser.close

    return dict(url=[url], src=src, chapters=chapters, pages=pages, ) # url comes in as string but we want it as a string in a list

def downloadMangaChapters(setupList):
    chapter_urls = []
    first_chapter_url = setupList.get('url')[0].rsplit('/', 2)[0] # http://www.mangabee.com/Tokyo_Ghoul
    chapter_numbers = setupList.get('chapters')
    main_directory = 'manga'

    for i in range(0, len(setupList.get('chapters'))):
        chapter_urls.append( "".join([first_chapter_url, '/', setupList.get('chapters')[i], '/', '1']) ) # [ http://www.mangabee.com/Tokyo_Ghoul/1/1, ..., http://www.mangabee.com/Tokyo_Ghoul/137/1 ]

    # if ( len(setupList.get('chapters')) == len(chapter_urls) ):
    #     print ('Numbers of chapters and lists match.')

    manga_name = chapter_urls[0].rsplit('/',3)[1]
    base_directory = manga_name
    full_directory = "".join([main_directory,'\\',base_directory,'\\',manga_name])

    if not os.path.exists(main_directory): # manga/
        os.mkdir(main_directory) # manga/
        logging.info("".join(['Created directory: ', main_directory]))


    d = "".join([main_directory,'\\',base_directory]) # manga/tokyo_ghouls/
    if not os.path.exists(d):
        os.mkdir(d) # manga/tokyo_ghouls/
        logging.info("".join(['Created directory: ', d]))

    # for i in range( 0, len(chapter_urls) ):
    for i in range( 0, 1 ):
        chapter_directory = "".join( [full_directory, '_', mangaNumbering(chapter_numbers[i])] )  # 'Tokyo_Ghoul_001 ... Tokyo_Ghoul_019 ... Tokyo_Ghoul_135'
        if not os.path.exists(chapter_directory):
            os.mkdir(chapter_directory) # Create chapter directory: '../manga/Tokyo_Ghoul_001/'
        downloadPagesForChapter(chapter_urls[i], chapter_directory)

    # print(setupList.get('src'))
    # print(setupList.get('src')[0].rsplit('/', 3))

    return True

def mangaNumbering(s):
    if (len(s) == 1):
        return "".join(['00',s])
    elif (len(s) == 2):
        return "".join(['0',s]) # 019, 020, 021 ...
    elif (len(s) == 3):
        return s                # 100, 211, 321 ... 599

    logging.info('Abnormal numbering encountered')
    return "".join(['0',s])


def downloadPagesForChapter(chapterUrl, directory):
    # print(chapterId + ':' + chapterUrl)
    global bytes
    pages = None
    pages_src = []
    image_files_paths = []
    parser = mangabeeHTMLGetImageLink()

    res = requestHTMLWithPageImage(chapterUrl)

    if res.info().get('Content-Encoding') == 'gzip':
        with gzip.open(res, 'rb') as f: #rb is read as binary.

            content = f.read().decode('utf-8');
            parser.feed(content)

            pages = parser.pages
            parser.close

    parser = mangabeeHTMLGetImageLink()

    for page in pages:
        url = chapterUrl.rsplit('/', 2)    # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '1']
        url[2] = page                      # ['http://www.mangabee.com/Tokyo_Ghoul', '1', '2'] ... ['http://www.mangabee.com/Tokyo_Ghoul', '1', '40'] <-- example last page.
        url =  "".join([url[0], '/', url[1], '/', url[2]])
        res = requestHTMLWithPageImage( url ) # http://www.mangabee.com/Tokyo_Ghoul/1/1 ... http://www.mangabee.com/Tokyo_Ghoul/1/40
        bytes += sys.getsizeof(res)           # Add bandwidth usage (GZIP compressed.)
        if res.info().get('Content-Encoding') == 'gzip':
            with gzip.open(res, 'rb') as f: #rb is read as binary.
                content = f.read().decode('utf-8')
                parser.feed(content)

                image_files_paths.append( "".join([directory, '\\', mangaNumbering(page), '.jpg']) )
                pages_src.append(parser.src)
                # Write image to respective chapter dir and tally the bandwidth usage.
                # bytes += urllibee.f.retrieve( parser.src, file ) # 'http://z.mhcdn.net/store/manga/10375/001.0/compressed/o1.01.jpg?v=11325158350', manga/Tokyo_Ghoul_001/001.jpg ... manga/Tokyo_Ghoul_001/040.jpg

                parser.reset # Clear contents of parser.
                f.close()    # Clear file handle for next one.
    # print(image_files_paths)

    if ( len(pages_src) == len(image_files_paths) ):
        print ('Numbers of chapters and lists match.')

    return True

def requestHTMLWithPageImage(url):
    req = urllib.request.Request(url) # example chapterUrl: 'http://www.mangabee.com/Tokyo_Ghoul/115/1/' Chapter 115, page 1.
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36')
    req.add_header('Content-Type', 'text/plain; charset=utf-8 ')
    req.add_header('Accept', '*/*')
    req.add_header('Accept-Encoding', 'gzip,deflate,sdch')

    res = urllib.request.urlopen(req)

    return res


bytes = 0

def resetBytesUsage():
    global bytes
    bytes = 0

def sizeMegs(bytes):
    return bytes/1000000

def sizeKilo(bytes):
    return bytes/1000

def main():
    global bytes
    logging.info('Started')
    search_results = search('blood-c')
    setupList = setup(search_results[0])
    downloadMangaChapters(setupList)
    logging.info("".join(['Finished... ', 'Usage: ', str(sizeMegs(bytes)), 'M']))
    logging.info("".join(['Finished... ', 'Usage: ', str(sizeKilo(bytes)), 'KB']))

if __name__ == "__main__":
    main()
