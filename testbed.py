import re

def dashrepl(matchobj):
    if matchobj.group(0) == '\s': return ' '
    else: return '+'

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s) # Remove all non-word characters (everything except numbers and letters)
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
    print( onlyNumbers('100   pro  gram  files@#!!@#!') )
    print( onlyNumbersSplit('103 - chapter 103') )
    print( onlyNumbersSplit('93 - Bait') )

if __name__ == "__main__":
    main()
