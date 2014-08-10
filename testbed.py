import sys
sys.path.append('C:/Users/tadachi/Desktop/Dropbox/git/')
import urllibee.f
import re

def dashrepl(matchobj):
    if matchobj.group(0) == '\s': return ' '
    else: return '+'

def urlify(s):
    s = re.sub(r"[^\w\s-]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '+', s) # Replaces all runs of whitespace with a single +
    return s

def onlyNumbers(s):
    s = re.sub(r'[^\d.]+', '', s) # Remove all characters and whitespace
    return s

def onlyNumbersSplit(s):
    return s.split(' ', 1)[0]

def main():
    m = re.search('(?<=-)\w+', 'spam-egg')
    print(m.group(0))
    print( urlify('100   pro  gram  files') )
    print( urlify('blood-c') )
    print( onlyNumbers('100   pro  gram  files@#!!@#!') )
    print( onlyNumbersSplit('103 - chapter 103') )
    print( onlyNumbersSplit('93 - Bait') )

    urllibee.f.retrieve( 'http://z.mhcdn.net/store/manga/10375/001.0/compressed/o1.01.jpg?v=11325158350', 'manga/Tokyo_Ghoul_001/001.jpg' )


if __name__ == "__main__":
    main()
