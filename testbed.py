import re

def dashrepl(matchobj):
    if matchobj.group(0) == '\s': return ' '
    else: return '+'

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '+', s) # Replaces all runs of whitespace with a single +
    return s

def main():
    m = re.search('(?<=-)\w+', 'spam-egg')
    print(m.group(0))
    print( urlify('pro  gram  files') )

if __name__ == "__main__":
    main()
