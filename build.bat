@echo off

REM Allows the use of !var[%%x]! ! for expansion of variable.
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

pip install requests
pip install eventlet
pip install click
pip install natsort

REM Don't persist setlocals.
endlocal
