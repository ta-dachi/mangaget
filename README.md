mangaget
===========

Requires python_3.4.x

#### Dependencies:

Run build.bat or build.sh if you're on linux. It installs python frameworks using pip.
```bash
./build.bat
```

```bash
./build.sh
```

#### Example usage:
```bash
python mangaget.py pokemon_special
```

#### Example output:
```bash
Searching pokemon_special on mangahere...

Found http://www.mangahere.co/manga/pokemon_special_black_white/

Downloading 'http://www.mangahere.co/manga/pokemon_special_black_white/'...
http://www.mangahere.co/manga/pokemon_special_black_white/c001/ successfully downloaded.
...
http://www.mangahere.co/manga/pokemon_special_black_white/c008/ successfully downloaded.
```

#### Some other commands:
```bash
python mangaget.py --help
```

```bash
Usage: mangaget.py [OPTIONS] SEARCH_TERM

  A program that downloads manga from mangahere and mangabee.

Options:
  --manga_site TEXT  mangahere mangabee
  --no_dl INTEGER    Just searches but does not download. Usage: mangaget
                     --no_dl=1 hajime_no_ippo
  --help             Show this message and exit.
```

##### Future features:
* Easy customizable performance tuning via increasing maximum conccurrent requests, decrease download code generated delay.
* Accompanying
* Download via chapter range. E.g download chapters 1-10 or only 2.
* Other manga websites to download from.

##### Half-implemented:
* Integrity checks for manga chapters.
* Redownload chapters

##### Hopeful features:
* Accompanying Android/IOS manga viewer that uses mangaget to manage and download.
