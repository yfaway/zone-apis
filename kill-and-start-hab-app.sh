#!/bin/bash
ps aux | grep habapp | grep -v grep | awk '{print $2 }' | xargs sudo kill -9
./bin/habapp -c ./habapp/ &
