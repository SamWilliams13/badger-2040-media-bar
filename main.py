import badger2040
import sys
import jpegdec
import os
import time

def split(t):
    l = 0
    tsplit = t.split(" ")
    t1 = ""
    i = 0
    while(l <= 16):
        if((l + len(tsplit[i])) <= 16):
            t1 += tsplit[i] + " "
            l += (len(tsplit[i]) + 1)
            i += 1
        else:
            break
    t2 = t[l:]
    if(len(t2) > 16):
        t2 = t2[0:16] + "..."
    return (t1,t2)

def refresh():
    badger = badger2040.Badger2040()
    badger.set_pen(0)
    badger.clear()
    j = jpegdec.JPEG(badger.display)
    j.open_file("mono.jpg")
    j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=False)
    f = open("desc.txt")
    t = f.readline()
    (t1, t2) = (t, "")
    if(len(t) > 16):
        (t1,t2) = split(t)
    ar = f.readline()
    (ar1, ar2) = (ar, "")
    if(len(ar) > 16):
        (ar1, ar2) = split(ar)
    al = f.readline()
    (al1, al2) = (al, "")
    if(len(al) > 16):
        (al1, al2) = split(al)
    badger.set_pen(15)
    badger.set_font("serif")
    badger.set_thickness(2)
    badger.text(t1, 138, 28 if (t2 == "") else 20, scale=0.5)
    badger.text(t2, 138, 35, scale=0.5)
    badger.text(ar1, 138, 63 if (ar2 == "") else 55, scale=0.5)
    badger.text(ar2, 138, 70, scale=0.5)
    badger.text(al1, 138, 98 if (al2 == "") else 90, scale=0.5)
    badger.text(al2, 138, 105, scale=0.5)
    badger.update()