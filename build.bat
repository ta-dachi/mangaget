@echo off

REM Allows the use of !var[%%x]! ! for expansion of variable.
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

set repo[1]=https://github.com/tadachi/urlibee.git

set directory[1]=urlibee

REM full path to current directory including drive.
REM set mypath=%~dp0

for /l %%i in (1, 1, 1) do (
    if exist !directory[%%i]! (
        echo Updating !directory[%%i]!.... & cd !directory[%%i]! & git pull
    ) else (
        call git clone !repo[%%i]!
    )
)

REM Don't persist setlocals.
endlocal
