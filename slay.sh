#!/bin/bash
ps aux | grep "python3 src/starter.py"  | grep -v grep | awk '{print $2 }' | xargs sudo kill -9
