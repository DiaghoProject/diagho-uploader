#!/bin/bash

bash stop_uploader.sh

echo " "

git pull

echo " "

bash start_uploader.sh