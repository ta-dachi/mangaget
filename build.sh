#!/bin/bash

repo[0]='https://github.com/tadachi/urllibee.git'

directory[0]='urllibee'

for i in {0..1}
do
    if [ -d ${directory[$i]} ]; # -d checks if directory is empty
    then
        printf "Updating '%s'.... " ${directory[$i]}
        (cd ${directory[$i]} ; git pull); # git pull the latest version.
    else
        eval git clone ${repo[$i]}; # clone the latest version.
    fi
done
