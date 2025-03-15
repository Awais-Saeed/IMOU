# IMOU
- First step, **pip install imouapi**

## Batch script to make a scheduler
```
@echo off
echo Running Python script...
python "C:\Users\Awais Saeed\Documents\Web Scraping\onepager.py"
exit
```

## Note:
- The "sign" is a concatenation of key-value pairs of three parameters: time, nonce, and appSecret, combined in the order of time, nonce, and appSecret, separated by commas.
- Perform MD5 processing on the "sign" and convert it to a 32-bit lowercase string in hexadecimal as the sign (note: the encoding format is UTF-8).
