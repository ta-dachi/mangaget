@echo off

REM Allows the use of !var[%%x]! ! for expansion of variable.
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

pip install --upgrade requests
pip install --upgrade eventlet
pip install --upgrade click
pip install --upgrade natsort

REM Don't persist setlocals.
endlocal
