#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess, sys
BOXRED = "#F9303D"
BGBROWN = "#6F6D51"

#list comprehension to get a file's animations
#./anura --no-debug --utility=query modules/frogatto/data/objects/enemies/bugs/maggot_white.cfg '[x.animation | x <- visit_objects(doc)]' 2>/dev/null
#./anura --utility=query modules/frogatto/data/objects/enemies/bugs/maggot_white.cfg '[x.animation | x <- visit_objects(doc)]' 2>/dev/null
#find the thrown animation
#./anura --utility=query modules/frogatto/data/objects/enemies/bugs/maggot_white.cfg '[find(x.animation, value.id = "thrown") | x <- visit_objects(doc)]'

def mainRead(cfgFile, anim):
    pwd = "".join(bash("pwd")).split('\n')[0]
    isRightFolder = bash("echo " + pwd + " | grep frogatto$ | wc -l")
    if isRightFolder[0] != '1':
        print "Run this script from the frogatto module's folder!"
        return
    animations = "cd ../.. ; ./anura --utility=query modules/frogatto/" + cfgFile + " '[x.animation | x <- visit_objects(doc)]' 2>/dev/null"
    #print bash(animations)
    bash("cd " + pwd)
    
    animations = bash(animations)
    animations = "".join(animations)
    animations = animations.replace('{','').split('}')
    try:
        baseAnim = [x for x in animations if "@base" in x][0]
    except IndexError:
        baseAnim = ""
        
    try:
        anim = [x for x in animations if anim in x][0]
    except IndexError:
        print "ERROR: '" + anim + "' animation was not found for " + cfgFile
        return
    
    anim = baseAnim + anim
    print anim
    image = [x.split(':')[1].split('"')[1] for x in anim.split('\n') if "\"image\"" in x][0]
    image = pwd + "/images/" + image
    print image
    try:
        pad = int([x.split(': ')[1].replace(',','') for x in anim.split('\n') if "\"pad\"" in x][0])
    except IndexError:
        pad = 0
    print pad
    #duration is multiplied by 2, since each frame is 20ms but imagemagick uses cs (thus, 2cs)
    duration = int([x.split(': ')[1].replace(',','') for x in anim.split('\n') if "\"duration\"" in x][0]) * 2
    print duration
    
    #also could be frames_per_row, with additional rows value
    frames = int([x.split(': ')[1].replace(',','') for x in anim.split('\n') if "\"frames\"" in x][0])
    print frames
    
    rect = [x.split(':')[1] for x in anim.split('\n') if "\"rect\"" in x][0][:-1]
    rect = [int(x) for x in rect.replace('[','').replace(']','').replace(' ','').split(',')]
    boxID = 20
    pngW = str(rect[2] - rect[0] + 1)
    pngH = str(rect[3] - rect[1] + 1)
    pngX = str(rect[0])
    pngY = str(rect[1])
    cropBox = "convert -crop " + pngW + "x" + pngH + "+" + \
                                pngX + "+" + pngY + " +repage " + image + \
                                " make-gif-temp" + ("%03d" % boxID) + ".png"
    bash(cropBox)
    print pwd

def mainBoxes(image):
    #global BOXRED, BGBROWN
    
    colors = "convert " + image + " -format %c histogram:info:- | sort -n -r -k 1"
    colors = bash(colors)
    print colors
    
    bashCommand = "convert " + image + " -depth 8 txt:-"
    output = bash(bashCommand)
    output = "".join(output)
    output = output.split('\n')
    output = output[1:] #discard the header line: "#Image"

    sizeCheck = "identify -format \"%w,%h\" " + image
    sizeCheck = bash(sizeCheck)
    sizeCheck = sizeCheck.split(',')
    imgW = int(sizeCheck[0])
    imgH = int(sizeCheck[1])
    
    pixArray = linesToArray(output, imgH, imgW)
    boxID = 0
    for i in range(imgH):
        j = 0
        while j < imgW:
            if pixArray[i][j] == BOXRED:
                thisBox = findBox(pixArray, i, j)
                if thisBox is None: 
                    j += 1
                else:
                    j = thisBox[3] + 1 #continue the search *after* this box
                    pngX = str(thisBox[1])
                    pngY = str(thisBox[0])
                    pngW = str(thisBox[3] - thisBox[1] + 1)
                    pngH = str(thisBox[2] - thisBox[0] + 1)
                    cropBox = "convert -crop " + pngW + "x" + pngH + "+" + \
                                pngX + "+" + pngY + " +repage " + image + \
                                " make-gif-temp" + ("%03d" % boxID) + ".png"
                    boxID += 1
                    print cropBox
                    bash(cropBox)
            else:
                j += 1
    makeAnim = "convert -adjoin -delay 10 -layers optimize" + \
               " make-gif-temp[0-9][0-9][0-9].png make-gif-output.gif"
    bash(makeAnim)
    bash("rm make-gif-temp*") #cleanup
    
def linesToArray(imageTxt, height, width):
    #newA = [[None] * width] * height #this fails in really unusual ways - all lines are the same as the last one
    newA = [[0 for x in range(width)] for y in range(height)] 
    for i in range(height):
        for j in range(width):
            newA[i][j] = simplify(imageTxt[width * i + j])
    return newA


def findBox(array, line, col):
    line2 = line + 1
    col2 = col + 1
    boxFound = 0
    
    try:
        #see if we're on the first line/column of a box, by checking
        #if the pixels at offsets 1,0 and 0,1 are also red
        if array[line][col + 1] != BOXRED or array[line + 1][col] != BOXRED:
            return None
            
        #scan the pixels going down, starting at offset +1,+1 from the red pixel in the args
        while array[line2][col2] != BOXRED:
            line2 += 1
        while array[line + 1][col2] != BOXRED:
            col2 += 1
    except IndexError:
        return None
    
    #if line2 or col2 didn't change at all, no box was found
    if (line2 - line == 1) or (col2 - col == 1):
        return None
    return (line, col, line2, col2) 
    
def simplify(line):
    return '#' + line.split('#')[1][:6]

def bash(arg):
    return subprocess.check_output(['bash','-c', arg])

#this script can either work directly with images, detecting individual sprite boxes,
#or read animations from a cfg file
if __name__ == "__main__":
	if len(sys.argv) == 2:
		if sys.argv[1][-4:] == ".png":
		    mainBoxes(sys.argv[1])
		elif sys.argv[1][-4:] == ".cfg":
		    mainRead(sys.argv[1], "stand")
	elif len(sys.argv) == 3:
		if sys.argv[1][-4:] == ".cfg":
		    mainRead(sys.argv[1], sys.argv[2])
		#print "Incorrect number of arguments, 1 required"
