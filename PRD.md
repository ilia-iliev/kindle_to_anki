# Project Purpose

Application that reads user highlights (tap and hold on words) on Kindle. These are probable unknown words and the application prepares them into AnkIDroid-importable format.

# Features

## 1. Reading of probable unknown words
1.1 On trigger, the application detects if a kindle is attached and readable. If not attached, show helpful message.

1.2 After verification, open the correct database file with word lookups. The lookup words since last open are returned. 

## 2. Filter out words
2 Filter obvious user miclicks (words like 'the', 'they', etc... eveyrthing in the top 1000 words in the english language)

## 3. Import into existing anki list
3.1 Match the filtered words to the correct language

3.2 For each word, add definition from cambridge dictionary

3.3 Import the words into .csv format word;definition

