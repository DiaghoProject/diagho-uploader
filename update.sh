#!/bin/bash

bash stop_uploader.sh 0

echo " "

git pull

echo " "

bash start_uploader.sh