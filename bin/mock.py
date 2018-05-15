#!/usr/bin/env python3
import time
import sys
bar = 0
count = 0
while True:
    sys.stdout.write("#")
    sys.stdout.flush()
    bar += 1
    time.sleep(.1)
    if bar == 10:
        bar = 0
        count += 1
        if count == 3:
            count = 0
            sys.stdout.write("\n")
            sys.stdout.flush()
        else:
            sys.stdout.write("\r")
            sys.stdout.flush()
