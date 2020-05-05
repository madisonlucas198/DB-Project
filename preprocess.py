# Fine: preprocess.py
# Programmer: Madison Lucas
# This preprocesses the data from amazon-meta.txt and places it into testdb.

from __future__ import print_function
from mysql.connector import errorcode
from mysql.connector.constants import ClientFlag
from decimal import Decimal
import re
import unicodedata
from collections import OrderedDict
from datetime import datetime
import configparser
from flask import Flask, render_template, Response, request, redirect, url_for
import mysql.connector

# This reads the configuration from file corresponding file.
config = configparser.ConfigParser()
config.read('config.ini')

# This sets up application server.
app = Flask(__name__)

# These reference files product_information.txt and product_weights.txt.
f1 = []
f2 = []

# These are the stop words to be removed from product description fields.
stopWords = ["a", "about", "above", "above", "across", "after", "afterwards", "again", "against", "all", "almost", "alone", "along",
			"already", "also","although","always","am","among", "amongst", "amoungst", "amount",  "an", "and", "another", "any","anyhow",
			"anyone","anything","anyway", "anywhere", "are", "around", "as",  "at", "back","be","became", "because","become","becomes", 
			"becoming", "been", "before", "beforehand", "behind", "being", "below", "beside", "besides", "between", "beyond", "bill", 
			"both", "bottom","but", "by", "call", "can", "cannot", "cant", "co", "con", "could", "couldnt", "cry", "de", "describe", 
			"detail", "do", "done", "down", "due", "during", "each", "eg", "eight", "either", "eleven","else", "elsewhere", "empty", 
			"enough", "etc", "even", "ever", "every", "everyone", "everything", "everywhere", "except", "few", "fifteen", "fify", "fill", 
			"find", "fire", "first", "five", "for", "former", "formerly", "forty", "found", "four", "from", "front", "full", "further", 
			"get", "give", "go", "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", 
			"hers", "herself", "him", "himself", "his", "how", "however", "hundred", "ie", "if", "in", "inc", "indeed", "interest", "into", 
			"is", "it", "its", "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd", "made", "many", "may", "me", 
			"meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly", "move", "much", "must", "my", "myself", "name", 
			"namely", "neither", "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone", "nor", "not", "nothing", "now", 
			"nowhere", "of", "off", "often", "on", "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our", "ours", 
			"ourselves", "out", "over", "own","part", "per", "perhaps", "please", "put", "rather", "re", "same", "see", "seem", "seemed", 
			"seeming", "seems", "serious", "several", "she", "should", "show", "side", "since", "sincere", "six", "sixty", "so", "some", 
			"somehow", "someone", "something", "sometime", "sometimes", "somewhere", "still", "such", "system", "take", "ten", "than", "that", 
			"the", "their", "them", "themselves", "then", "thence", "there", "thereafter", "thereby", "therefore", "therein", "thereupon", 
			"these", "they", "thick", "thin", "third", "this", "those", "though", "three", "through", "throughout", "thru", "thus", "to", 
			"together", "too", "top", "toward", "towards", "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us", "very", "via", 
			"was", "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein", 
			"whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever", "whole", "whom", "whose", "why", "will", "with", 
			"within", "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves", "the"]


# This is the defintion for the function that queries the database. It returns the result of the query.
def db_query(sql):
	cnx = mysql.connector.connect(**config['mysql.connector'])
	cursor = cnx.cursor()

	cursor.execute(sql) 		# sql is the command, as a string literal
	result = cursor.fetchall() 	# returns all results of the query

	cursor.close()
	cnx.close()

	return result

# This is the defintion for the function that writes to the database.
def db_write(sql):
	cnx = mysql.connector.connect(**config['mysql.connector'])
	cursor = cnx.cursor()
	cursor.execute(sql)
	cnx.commit()
	cursor.close()
	cnx.close()

# This imports the amazon data from amazon-meta.txt.
def importAmazonData():
	global f1
	global f2

	f1 = [open("product_information.txt", 'w').close()]
	f2 = open("product_weights.txt", 'w').close()

	f1 = open("product_information.txt", "a")
	f2 = open("product_weights.txt", "a")
	createTables()
	fillTables()
	
	f1.close()
	f2.close()

	# optimizations for faster load
	sql = "SET autocommit=0"
	db_write(sql)
	sql = "SET unique_checks=0"
	db_write(sql)
	sql = "SET FOREIGN_KEY_CHECKS = 0"
	db_write(sql)

	mydb = mysql.connector.connect(host='localhost',user='testuser',passwd='password',database='testdb',client_flags=[ClientFlag.LOCAL_FILES])
	cursor = mydb.cursor()
	query1 = "LOAD DATA INFILE '/Users/madisonlucas905/Desktop/DB-Project-master/product_information.txt' INTO TABLE product_information"
	query2 = "LOAD DATA INFILE '/Users/madisonlucas905/Desktop/DB-Project-master/product_weights.txt' INTO TABLE product_weights"
	cursor.execute(query1)
	cursor.execute(query2)
	mydb.commit()
	cursor.close()
	mydb.close()

	# reset back to normal parameters
	sql = "COMMIT"
	db_write(sql)
	sql = "SET unique_checks=1"
	db_write(sql)
	sql = "SET FOREIGN_KEY_CHECKS = 1"
	db_write(sql)

	# optimization for run_app.py
	sql = "CREATE INDEX keyword ON product_weights(keyword)"
	db_write(sql)

# This creates the two tables product_information and product_weights.
def createTables():
	sql = "SET FOREIGN_KEY_CHECKS = 0"
	db_write(sql)

	sql = "DROP TABLE  IF EXISTS product_weights"
	db_write(sql)

	sql = "DROP TABLE  IF EXISTS product_information"
	db_write(sql)

	sql = "DROP TABLE  IF EXISTS product_result"
	db_write(sql)

	sql = "SET FOREIGN_KEY_CHECKS = 1"
	db_write(sql)

	sql = "CREATE TABLE product_information (\
				ID int(6) NOT NULL, \
				ASIN char(10) NOT NULL, \
				discontinued varchar(5) NOT NULL, \
				title varchar(300) DEFAULT NULL, \
				grp varchar(5) DEFAULT NULL, \
				salesRank int(6) DEFAULT NULL, \
				averageRating float(3) DEFAULT NULL, \
				totalReviews int(3) DEFAULT NULL, \
				similarList varchar(100) DEFAULT NULL, \
				keywords varchar(500) DEFAULT NULL, \
				PRIMARY KEY (ID)\
				) ENGINE=InnoDB DEFAULT CHARSET=latin1"
	db_write(sql)

	sql = "CREATE TABLE product_weights (\
				ID int(6) NOT NULL, \
				keyword varchar(50) NOT NULL, \
				weight int(10) NOT NULL, \
				PRIMARY KEY (ID, keyword), \
				FOREIGN KEY (ID) REFERENCES product_information(ID) \
				) ENGINE=InnoDB DEFAULT CHARSET=latin1"
	db_write(sql)
				
# This reads the text file line by line in order to enter the product into testdb.
def fillTables():

	file = open("amazon-meta.txt", 'r')
	line = file.readline()

	# reset values
	Id = None
	ASIN = None
	discontinued = False
	title =  None
	group = None
	salesrank = None
	numSimilar = None
	similarList = []
	numCategories = None
	categoryList = []
	numReviews = None
	averageRating = None

	# read each line in the text file
	while line or Id:
		line = line.strip()

		if line.startswith('Id:') == True:
			Id = int(line.split()[1])
		elif line.startswith('ASIN:') == True:
			ASIN = remove_prefix(line, 'ASIN: ')
		elif line.startswith('discontinued') == True:
			discontinued = True
		elif line.startswith('title:') == True:
			title = remove_prefix(line, 'title: ')
		elif line.startswith('group:') == True:
			group = remove_prefix(line, 'group: ')
		elif line.startswith('salesrank:') == True:
			salesrank = int(line.split()[1])
		elif line.startswith('similar:') == True:
			numSimilar = int(line[9])
			similarList = line[11:-1].split()
		elif line.startswith('categories:') == True:
			numCategories = int(line[-1])
			for count in range (0, numCategories):
				categoryList.append(file.readline().strip())
		elif line.startswith('reviews:') == True:
			result = re.search('total: (.*) down', line)
			result = line.split()
			numReviews = int(result[2])
			averageRating = float(result[7])
		elif line == '':
			writeProductToDatabase(Id, ASIN, discontinued, title, group, salesrank, numSimilar, similarList, numCategories, categoryList, numReviews, averageRating)
			Id = None
			ASIN = None
			discontinued = False
			title =  None
			group = None
			salesrank = None
			numSimilar = None
			similarList = []
			numCategories = None
			categoryList = []
			numReviews = None
			averageRating = None

		line = file.readline()
	
	file.close()

# This sums the weight of a keyword according to the nnumber of time it appears in the input array.
def sumWeight(sArray, pointVal, keyword):
	totalWeight = 0
	for word in sArray:
		if word == keyword:
			totalWeight += pointVal
	return totalWeight

# This writes the appropriate tuple to the text files product_information.txt and product_weights.txt.
def writeProductToDatabase(ID, ASIN, discontinued, title, group, salesrank, numSimilar, similarList, numCategories, categoryList, numReviews, averageRating):
	global f1
	global f2
	
	if discontinued == False:
		originalTitle = formatApostrophes(title)
		descriptionArray = createDescription(categoryList)
		titleArray = createTitle(title, group)
		keywordArray = descriptionArray + titleArray
		keywordArray.append(ASIN)
		keywordArray = list(dict.fromkeys(keywordArray))
		
		description = ' '.join([str(c) for c in descriptionArray])
		title = ' '.join([str(c) for c in titleArray])
		keywords = ' '.join([str(c) for c in keywordArray])

		sql = "%d\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%s\t%s\r\n" % (ID, ASIN, discontinued, originalTitle, group, salesrank, averageRating, numReviews, ','.join([str(c) for c in similarList]), keywords)
		f1.write(sql)
		for word in keywordArray:
			totalWeight = 0
			if ASIN == word:
				totalWeight += 100

			totalWeight += sumWeight(titleArray, 75, word)
			totalWeight += sumWeight(descriptionArray, 25, word)

			if totalWeight != 0:
				sql = "%d\t%s\t%d\r\n" % (ID, word, totalWeight)
				f2.write(sql)

	else:
		sql = "%d\t%s\t%s\tNULL\tNULL\tNULL\tNULL\tNULL\tNULL\t%s\r\n" % (ID, ASIN, discontinued, str(ASIN))
		f1.write(sql)

		sql = "%d\t%s\t%d\r\n" % (ID, ASIN, 100)
		f2.write(sql)

# This removes any special characters and numbers from the string, returning an array of words.
def parseOutWords(s):
	s = strip_accents(s)
	s = s.translate({ord(c): "" for c in '\''})
	s = s.translate({ord(c): " " for c in '*/\\@&#%|:?,.;`~!&[]-()[]0123456789'})
	s = s.lower()
	sArray = s.split()
	
	# delete any singular chars
	sArray = [i for i in sArray if len(i) > 1]
	return sArray

# This removes any special characters from the string, returning an array of words.
def parseOutWordsKeepNumbers(s):
	s = strip_accents(s)
	s = s.translate({ord(c): "" for c in '\''})
	s = s.translate({ord(c): " " for c in '*@&#%|:?,.;`~!&[]-()[]\''})
	s = s.lower()
	sArray = s.split()
	return sArray

def strip_accents(text):
    try:
        text = unicode(text, 'utf-8')
    except NameError:
        pass

    text = unicodedata.normalize('NFD', text)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")

    return str(text)

# This returns a string with the input prefix removed.
def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

# This creates an array of keywords according to the description.
def createDescription(categoryList):
	global stopWords

	descriptionArray = []

	for cell in categoryList:
		sArray = parseOutWords(cell)
		for word in sArray:
			if word not in stopWords and word not in descriptionArray:
				descriptionArray.append(word)
	return descriptionArray

# This creates an array of keywords according to the title.
def createTitle(title, group):
	global stopWords

	sArray = parseOutWordsKeepNumbers(title)
	titleArray = []
	titleArray.append(group.lower())
	for word in sArray:
		if word not in stopWords and word not in titleArray:
			titleArray.append(word)
	return titleArray

# This formats 's so that they can be correctly inserted into the database
def formatApostrophes(s):
	s = s.replace('\'', '\\\'')
	return s

# This runs the program
if __name__ == '__main__':

	#diagnostic tool
	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current Time =", current_time)

	importAmazonData()

	#diagnostic tool
	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current Time =", current_time)
