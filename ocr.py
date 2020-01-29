from PIL import Image, ImageFilter, ImageOps
import pytesseract
import torch
import numpy
import cv2
import pandas as pd
from fuzzywuzzy import process, fuzz
from glob import glob
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
img_mask = 'flyer_images/*.jpg'
img_names = glob(img_mask)

final = pd.DataFrame(columns=['flyer_name','product_name','unit_promo_price','uom','least_unit_for_promo','save_per_unit','discount','organic'])
idx = 0
idx_arr = []
for fn in img_names:

    print('processing %s...' % fn,)
    flyer_name = fn.replace('flyer_images\\','')
    flyer_name = flyer_name.replace('.jpg','')
    idx += 1
    idx_arr.append(flyer_name)
    image = cv2.imread(fn)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # edge = cv2.Canny(gray, 100, 200)
    blur = cv2.GaussianBlur(gray, (7,7), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=8)

    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    ROI_number = 0
    roi_arr = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 10000:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 3)
            ROI = image[y:y+h, x:x+w]
            # cv2.imwrite('ROI_{}.png'.format(ROI_number), ROI)
            roi_arr.append(ROI)
            ROI_number += 1

    flyer_str = []
    for i in roi_arr:
        i_gray = cv2.cvtColor(i, cv2.COLOR_BGR2GRAY)
        i_gray = cv2.resize(i_gray,None,fx=2,fy=2)
        # cv2.imshow('test',i_gray)
        # cv2.waitKey(0)
        string = pytesseract.image_to_string(i_gray)
        if len(string)>40:
            # img_txt = []
            # for line in string.splitlines():
            #     if len(line) > 0:
            #         img_txt.append(line)
            # flyer_str.append(img_txt)
            string = string.replace('Ib','lb')
            string = string.replace('1b', 'lb')
            string = string.replace('0z', 'oz')
            string = string.replace('02z', 'oz')
            flyer_str.append(string)

    # print(flyer_str)

    products = pd.read_csv('product_dictionary.csv')
    units = pd.read_csv('units_dictionary.csv')
    prodOptions = products.to_numpy()
    unitOptions = units.to_numpy()

    for prod in flyer_str:
        # for line in prod:
        #     Ratios = process.extract(line, strOptions, scorer=fuzz.token_set_ratio)
        #     print('String: ', line)
        #     print('Guess: ', Ratios)
        guess_p = process.extractOne(prod,prodOptions,scorer=fuzz.token_set_ratio)
        if guess_p[1] < 100:
            continue
        guess_prod = guess_p[0][0]
        guess_u = process.extractOne(prod,unitOptions, scorer=fuzz.token_set_ratio)
        guess_unit = guess_u[0][0]
        guess_o = fuzz.token_set_ratio(prod,'organic')
        if guess_o > 80:
            guess_org = 1
        else:
            guess_org = 0

        prod_spl = prod.splitlines()
        line_counter = 0
        guess_price = 8.99
        guess_save = 1
        guess_least = 1
        # print('String: ', prod)
        for line in prod_spl:
            if ('SAVE' or 'AVE') in line:
                nums = re.findall('\d+(?:\.\d+)?', line)
                if len(nums) > 1:
                    if float(nums[1]) != 0:
                        guess_save = float(nums[0])/float(nums[1])
                        guess_least = float(nums[1])
                    else:
                        guess_save = float(nums[0])
                elif len(nums) == 1:
                    guess_save = float(nums[0])
                    guess_least = 1
            elif line_counter < 5:
                nums = re.findall('\d+(?:\.\d+)?', line)
                if len(nums) > 1:
                    if float(nums[0]) != 0:
                        guess_price = float(nums[1])/float(nums[0])
                    else:
                        guess_price = float(nums[1])
                elif len(nums) == 1:
                    guess_price = float(nums[0])
                    while guess_price >= 10:
                        guess_price = guess_price/10
            # print(line)
            # print('Guess Price: ', guess_price)
            line_counter += 1
        if guess_price != 0:
            guess_disc = guess_save/guess_price
        else:
            guess_disc = guess_save
        final.loc[len(final)] = [flyer_name,guess_prod,round(guess_price,2),guess_unit,guess_least,round(guess_save,2),round(guess_disc,2),guess_org]
        # print('String: ', prod)
        # print('String: ', prod)
    pd.set_option('display.max_columns', 500)
    print(final.tail(15))
    print('Done Adding Flyer #',idx)
    print('Finished List: ', idx_arr)
    final.to_csv('output.csv', index=False)

final.to_csv('output.csv', index=False)

