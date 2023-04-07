#!/bin/bash
ps aux | grep habapp | grep -v grep | awk '{print $2 }' | xargs kill -9
