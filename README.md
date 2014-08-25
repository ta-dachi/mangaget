mangaget
===========

#### Features
- Download all chapters of a manga on mangahere or mangabee
- Download in ranges (1-10, 14) or (3 ,5, 10, 2-10) *(3, 3) for a single chapter.
- Integrity files and checks for manga chapters, which re-downloads chapters with missing pages.
- Auto-updates and downloads the latest chapters upon searching again.
- Does not re-download chapters that are already downloaded.


Requires python_3.4.x

#### Dependencies:

Run build.bat or build.sh if you're on linux. It installs required python frameworks using pip.
```bash
./build.bat
```

```bash
./build.sh
```



#### Example usage for downloading all chapters:
```bash
python mangaget.py --manga_site=mangabee Dear
```

#### Example output:
```bash
Searching Dear on mangabee...

Pick a mangalink:
0. http://www.mangabee.com/akuma-ga-hallelujah/
1. http://www.mangabee.com/america/
2. http://www.mangabee.com/angel-onayami-soudanjo/
3. http://www.mangabee.com/boku-kara-kimi-ga-kienai/
4. http://www.mangabee.com/dear-boys/
5. http://www.mangabee.com/dear-boys-act-ii/
6. http://www.mangabee.com/dear-diary/
7. http://www.mangabee.com/dear-my-girls/
8. http://www.mangabee.com/dear-only-you-dont-know/
9. http://www.mangabee.com/hakoiri_devil_princess/
10. http://www.mangabee.com/shanimuni-go/
11. http://www.mangabee.com/star-children/
12. http://www.mangabee.com/tales-of-graces-f/
13. http://www.mangabee.com/tales-of-the-abyss/
14. http://www.mangabee.com/tokarev-no-ayaui-shiro/
Enter a number: 4
[2014-08-25 11:54:49] Buildling chapter integrity files. This can take awhile if there are many chapters. e.g 100+...
[2014-08-25 11:54:51] Created mangabee\dear-boys\dear-boys_001.json
[2014-08-25 11:54:52] Created mangabee\dear-boys\dear-boys_002.json
Downloading http://www.mangabee.com/dear-boys/1 ...
Done, now waiting 3 seconds to prevent being timedout by server...
Downloading http://www.mangabee.com/dear-boys/2 ...
Done, now waiting 3 seconds to prevent being timedout by server...
[2014-08-25 11:59:41] Finished... Usage: 13.498127MB
[2014-08-25 11:59:41] Finished... Usage: 13498.127KB
```

#### Example usage for download in ranges:
```bash
python mangaget.py --manga_site=mangabee --select 1 2 pokemon
```

#### Example output:
```bash
Searching pokemon on mangabee...

Pick a mangalink:
0. http://www.mangabee.com/pocket-monster-reburst/
1. http://www.mangabee.com/pokemon-adventures/
2. http://www.mangabee.com/pokemon-special/
Enter a number: 0
[2014-08-25 12:07:12] Buildling chapter integrity files. This can take awhile if there are many chapters. e.g 100+...
[2014-08-25 12:07:13] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_001.json
[2014-08-25 12:07:14] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_002.json
[2014-08-25 12:07:15] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_003.json
[2014-08-25 12:07:16] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_004.json
[2014-08-25 12:07:16] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_005.json
[2014-08-25 12:07:17] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_006.json
[2014-08-25 12:07:18] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_007.json
[2014-08-25 12:07:18] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_008.json
[2014-08-25 12:07:19] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_009.json
[2014-08-25 12:07:20] Created mangabee\pocket-monster-reburst\pocket-monster-reburst_010.json
Downloading http://www.mangabee.com/pocket-monster-reburst/1 ...
Downloaded, now waiting 5 seconds to prevent being timedout by server...
Downloading http://www.mangabee.com/pocket-monster-reburst/2 ...
Downloaded, now waiting 3 seconds to prevent being timedout by server...
[2014-08-25 12:13:58] Finished... Usage: 13.382147MB
[2014-08-25 12:13:58] Finished... Usage: 13382.147KB
```bash


#### Some other commands:
```bash
python mangaget.py --help
```

```bash
Usage: mangaget.py [OPTIONS] SEARCH_TERM

  A program that downloads manga from mangahere and mangabee.

Options:
  --manga_site TEXT    mangahere mangabee
                       Usage: mangaget.py --manga_site
                       mangabee bleach
  --check TEXT         Download ALL manga chapters you are missing. And
                       redownloads chapter if it is missing pages. Gives a
                       choice if there are similar manga names.
                       Usage:
                       mangaget.py --check=True naruto
  --no_dl INTEGER      Just searches but does not download. Gives a choice if
                       there are similar manga names.
                       Usage: mangaget
                       --no_dl=1 hajime_no_ippo
  --select INTEGER...  from chapter [INT] to chapter [INT]. If you want to
                       download only one chapter, make FROM and TO the same.
                       E.g (5, 5). Gives a choice if there are similar manga
                       names.
                       Usage: mangaget --select 1 3 naruto
  --help               Show this message and exit.
```

##### Future features:
* Easy customizable performance tuning via increasing maximum conccurrent requests, decrease download code generated delay.
* Other manga websites to download from: mangafox, etc.

##### Hopeful features:
* Accompanying Android/IOS manga viewer that uses mangaget to manage and download.
