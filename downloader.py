import sys
sys.path.append('C:/Users/tadachi/Desktop/Dropbox/git/urllibee/')
import urllibee

import urllib.request
import gzip
from html.parser import HTMLParser

import re

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '+', s) # Replaces all runs of whitespace with a single +
    return s

class mangabeeHTMLParser(HTMLParser):
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
        if (tag == 'select'):
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'select'
            if (attrs.get('class') == 'cbo_wpm_pag'):
                print(attrs)
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
                print(attrs.get('src'))

        if (tag == 'h2'): # The tag with all the page data.
            self.inLink = True
            attrs = dict(attrs) # Makes it easier to iterate through tag.
            self.lastTag = 'h2'
            if (attrs.get('class') == 'wpm_tip lnk_cnr'): # Found tag with manga image.
                self.lastClass = 'wpm_tip lnk_cnr'

        if (tag == 'a' and self.lastClass == 'wpm_tip lnk_cnr'):
            self.inLink = True
            self.lastTag = 'a'

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
        if (tag == 'h2'): # The tag with all the page data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

        pass

    def handle_data(self, data):
        if (self.lastClass == 'cbo_wpm_chp' and self.first_occurrence == False):
            self.chapters.append(data)
        if (self.lastClass == 'wpm_tip lnk_cnr' and self.lastTag == 'a'):
            print(data)
            self.pages.append(data)
        pass

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
        pass

    def handle_data(self, data):
        if (self.inLink == True):
            pass
        pass

def search(manga_name):
    url = 'http://www.mangabee.com/manga-list/search/%s/name-az/1' % urlify(manga_name)
    results = None

    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36')
    req.add_header('Content-Type', 'text/plain; charset=utf-8 ')
    req.add_header('Accept', '*/*')
    req.add_header('Accept-Encoding', 'gzip,deflate,sdch')

    res = urllib.request.urlopen(req)

    if res.info().get('Content-Encoding') == 'gzip':
        with gzip.open(res, 'rb') as f: #rb readbinary
            content = f.read().decode('utf-8')
            parser = mangabeeSearchParser()
            parser.feed(content)
            results = parser.links # Save our results
            parser.close

    return results

def main():
    bytes = 0
    event_types = ("start", "end")
    # urllibee.test()
    # urllibee.retrieve('https://archive.org/download/testmp3testfile/testmp3testfile_64kb_mp3.zip', '')
    req = urllib.request.Request('http://www.mangabee.com/Tokyo_Ghoul/2/1/')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36')
    req.add_header('Content-Type', 'text/plain; charset=utf-8 ')
    req.add_header('Accept', '*/*')
    req.add_header('Accept-Encoding', 'gzip,deflate,sdch')

    res = urllib.request.urlopen(req)

    if res.info().get('Content-Encoding') == 'gzip':
        with gzip.open(res, 'rb') as f: #rb readbinary

            parser = mangabeeHTMLParser()
            content = f.read().decode('utf-8');
            bytes += sys.getsizeof(content)
            parser.feed(content)

            pass

    # print( search('Tokyo Ghoul') )

if __name__ == "__main__":
    main()
