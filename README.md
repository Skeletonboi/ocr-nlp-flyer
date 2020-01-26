# ocr-nlp-flyer
**Top 6 Submission at 2020 Daisy Hackathon @ UofT**
## Problem Scope
**Goal: Given high-resolution flyer image, the objective is to return a table of products and their accompanying promotion details.**
**Data: 212 Flyer Images w/ no labels, Product + Unit-of-Measure Dictionary**

## Solution:
The program utilizes OpenCV to process and segment the flyer image into bounding boxes for each product. PyTesseract, a LSTM enabled image-to-text engine, then extracts characters from each box, and the text is then parsed by empirical methods such as RegEx to extract specific pricing, discount, product name, and organic-status information.
