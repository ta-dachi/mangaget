mangaget
===========

#### Features
- Download all chapters of a manga on mangahere or mangabee
- Integrity files and checks for manga chapters, which redownloads chapters with missing pages.
- Logging of download errors.

Requires python_3.4.x

#### Dependencies:

Run build.bat or build.sh if you're on linux. It installs required python frameworks using pip.
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
  A program that downloads manga from mangahere and mangabee.

Options:
  --manga_site TEXT  mangahere mangabee
                     Usage: mangaget.py --manga_site
                     mangabee bleach
  --check TEXT       Download manga chapters you are missing. And download
                     missing pages for each chapter.
                     Usage: mangaget.py
                     --check=True naruto
  --no_dl INTEGER    Just searches but does not download.
                     Usage: mangaget
                     --no_dl=1 hajime_no_ippo
  --help             Show this message and exit.
```

##### Future features:
* Easy customizable performance tuning via increasing maximum conccurrent requests, decrease download code generated delay.
* Other manga websites to download from: mangafox, etc.

##### Half-implemented:
* Download in ranges (1-10, 14) or (3 ,5, 10 2-10)

##### Hopeful features:
* Accompanying Android/IOS manga viewer that uses mangaget to manage and download.
