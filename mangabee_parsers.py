from html.parser import HTMLParser

class mangabeeSearchParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inLink = False
        self.lastTag = None
        self.lastClass = None
        self.urls = []         # Where we store our results

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
            self.urls.append( attrs.get('href') )     #['http://www.mangabee.com/Tokyo_Ghoul', ...]

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
        self.first_occurrence_chapters = False
        self.first_occurrence_pages = False

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
                self.src.append(attrs.get('src')) # Add example src. Need lots of string manipulation to generate image urls

    def handle_endtag(self, tag):
        if (tag == 'select' and self.lastClass =='cbo_wpm_chp'): # The tag with chapter data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None
            self.first_occurrence_chapters = True # Chapter selection occurs twice so, only add chapters once.
        if (tag == 'select' and self.lastClass =='cbo_wpm_pag'): # The tag with chapter data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None
            self.first_occurrence_pages = True # Chapter selection occurs twice so, only add chapters once.
        if (tag == 'img'): # The tag with image data and location.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

    def handle_data(self, data):
        if (self.lastClass == 'cbo_wpm_chp' and self.first_occurrence_chapters == False):
            self.chapters.append(data)
        if (self.lastClass == 'cbo_wpm_pag' and self.lastTag == 'option' and self.first_occurrence_pages == False):
            self.pages.append(data)


class mangabeeHTMLGetImageUrls(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inLink = False
        self.lastTag = None
        self.lastClass = None
        self.page_numbers = []
        self.second_occurrence_pages = False

    def handle_starttag(self, tag, attrs):
        if (tag == 'select'): # The tag with pages data.
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'select'
            if (attrs.get('class') == 'cbo_wpm_pag'):
                self.lastClass = 'cbo_wpm_pag'

        if (tag == 'option' and self.lastClass == 'cbo_wpm_pag' and self.second_occurrence_pages == False):
            self.inLink = True
            self.lastTag = 'option'
            attrs = dict(attrs)
            self.page_numbers.append(attrs.get('value'))

        if (tag == 'div'):
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'div'
            if (attrs.get('class') == 'clr'):
                self.lastClass = 'clr'

    def handle_endtag(self, tag):
        if (tag == 'select'): # The tag with chapter data.
            self.inLink = False
            self.lastTag = None
            self.lastClass = None

        if (self.lastClass == 'clr'):
            self.second_occurrence_pages = True

    def handle_data(self, data):
        pass

class mangabeeHTMLGetImageSrcs(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.inLink = False
        self.lastTag = None
        self.lastClass = None
        self.src = None

    def handle_starttag(self, tag, attrs):
        if (tag == 'img'): # The tag with pages data.
            self.inLink = True
            attrs = dict(attrs)
            self.lastTag = 'section'
            if (attrs.get('class') == 'manga-page'):
                self.lastClass = 'manga-page'

        if (tag == 'img' and self.lastClass == 'manga-page'):
            self.inLink = True
            self.lastTag = 'img'
            attrs = dict(attrs)
            self.src = attrs.get('src')

    def handle_endtag(self, tag):
        if (tag == 'img'):
            self.inLink = False
            self.lastTag = None
            self.lastClass = None


    def handle_data(self, data):
        pass
