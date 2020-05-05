# Fine: run_app.py
# Programmer: Madison Lucas
# This runs the search engine in a web browser.

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

# This is used to write ID's from a tuple to a string so that it can be used in a MySQL query/
placeholders = ""

# These hold the IDs returned by a search result in a specific order.
IDsRelevance = []
IDsTitle = []
IDsAverageRating = []
IDsNumberReviews = []
IDsSalesRank = []

# words that are parsed out from any input text or product description fields
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

# This renders the intial launch page.
@app.route('/')
def home():
	return render_template('home.html')

# This renders the main page when the user requests another search.
@app.route('/landingPage', methods=['GET', 'POST'])
def returnToLandingPage():
	if "goToLanding" in request.form:
		return render_template('home.html')


# This is the route to display the results page.
@app.route('/goToResultsPage', methods=['GET', 'POST'])
def goToResultsPage():
	global placeholders
	global IDsRelevance
	global IDsSalesRank

	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current Time =", current_time)

	# resets values
	placeholders = ""
	IDsRelevance = []
	IDsTitle = []
	IDsAverageRating = []
	IDsNumberReviews = []
	IDsSalesRank = []


	# query response
	search = str(request.form["searchString"])
	tuplesToDisplay = resolveSearch(search)
	IDsRelevance = [i[0] for i in tuplesToDisplay]
	IDsRelevance = list(OrderedDict.fromkeys(IDsRelevance))
	placeholders= ', '.join(str(ID) for ID in IDsRelevance)

	# load up first 5
	passToWebPage = []
	if IDsRelevance:
		for i in range(0,5):
			if i < len(IDsRelevance):
				sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsRelevance[i])
				result = db_query(sql)
				passToWebPage = passToWebPage + result

	# send first 5 to web page
	dictionary = {}
	dictionary['results'] = passToWebPage

	# for diagnostic purposes
	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	print("Current Time =", current_time)

	return render_template('resultsPage.html', template_data=dictionary, index="0 relevance"), 400

# This is the route to display the results page, sorted by relevance.
@app.route('/sortByRelevance', methods=['GET', 'POST'])
def sortByRelevance():
	global placeholders
	global IDsRelevance

	# load up first 5
	passToWebPage = []
	if IDsRelevance:
		for i in range(0,5):
			if i < len(IDsRelevance):
				sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsRelevance[i])
				result = db_query(sql)
				passToWebPage = passToWebPage + result

	# send first 5 to web page
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index="0 relevance"), 400


# This is the route to display the results page, sorted by title in alphebetical order.
@app.route('/sortByTitle', methods=['GET', 'POST'])
def sortByTitle():
	global placeholders
	global IDsTitle

	# sort by title if not already
	if not IDsTitle:
		sql = "SELECT ID FROM product_information WHERE ID in (%s) ORDER BY title" % (placeholders)
		IDsTitle = db_query(sql)
	
	# load up first 5
	passToWebPage = []
	if IDsTitle:
		for i in range(0,5):
			if i < len(IDsTitle):
				sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsTitle[i])
				result = db_query(sql)
				passToWebPage = passToWebPage + result

	# send first 5 to web page
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index="0 title"), 400


# This is the route to display the results page, sorted by average rating.
@app.route('/sortAverageRating', methods=['GET', 'POST'])
def sortAverageRating():
	global placeholders
	global IDsAverageRating

	# sort by average rating if not already
	if not IDsAverageRating:
		sql = "SELECT ID FROM product_information WHERE ID in (%s) ORDER BY averageRating DESC" % (placeholders)
		IDsAverageRating = db_query(sql)
	
	# load up first 5
	passToWebPage = []
	if IDsAverageRating:
		for i in range(0,5):
			if i < len(IDsAverageRating):
				sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsAverageRating[i])
				result = db_query(sql)
				passToWebPage = passToWebPage + result

	# send first 5 to web page
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index="0 averageRating"), 400

# This is the route to display the results page, sorted by number of reviews.
@app.route('/sortByNumReviews', methods=['GET', 'POST'])
def sortByNumReviews():
	global placeholders
	global IDsNumberReviews

	# sort by number of reviews if not already
	if not IDsNumberReviews:
		sql = "SELECT ID FROM product_information WHERE ID in (%s) ORDER BY totalReviews DESC" % (placeholders)
		IDsNumberReviews = db_query(sql)
	
	# load up first 5
	passToWebPage = []
	if IDsNumberReviews:
		for i in range(0,5):
			if i < len(IDsNumberReviews):
				sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsNumberReviews[i])
				result = db_query(sql)
				passToWebPage = passToWebPage + result

	# send first 5 to web page
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index="0 numReviews"), 400


# This is the route to display the results page, sorted by sales rank.
@app.route('/sortBySalesRank', methods=['GET', 'POST'])
def sortBySalesRank():
	global placeholders
	global IDsSalesRank

	# sort by sales rank if not already
	if not IDsSalesRank:
		sql = "SELECT ID FROM product_information WHERE ID in (%s) AND salesRank > 0 ORDER BY salesRank" % (placeholders)
		IDsSalesRank = db_query(sql)
	
	# load up first 5
	passToWebPage = []
	if IDsSalesRank:
		for i in range(0,5):
			if i < len(IDsSalesRank):
				sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsSalesRank[i])
				result = db_query(sql)
				passToWebPage = passToWebPage + result

	# send first 5 to web page
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index="0 salesRank"), 400



# This is the route to display the the next five products when the user clicks "More Results".
@app.route('/goToResultsPageOverflowForward', methods=['GET', 'POST'])
def gotToResultsPageOverFlowForward():
	global IDsRelevance
	global IDsTitle
	global IDsAverageRating
	global IDsNumberReviews
	global IDsSalesRank

	# figure out where the last page left off
	index = request.form["index"]
	index = index.split()
	startingIndex = int(index[0])
	sortMethod = index[1]
	passToWebPage = []
	i = startingIndex +  5

	# display IDs according to current sorting method
	if sortMethod == "relevance":
		while i < len(IDsRelevance) - 1 and i < startingIndex + 10:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsRelevance[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1
	
	if sortMethod == "title":
		while i < len(IDsTitle) - 1 and i < startingIndex + 10:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsTitle[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "averageRating":
		while i < len(IDsAverageRating) - 1 and i < startingIndex + 10:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsAverageRating[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "numReviews":
		while i < len(IDsNumberReviews) - 1 and i < startingIndex + 10:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsNumberReviews[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "salesRank":
		while i < len(IDsSalesRank) - 1 and i < startingIndex + 10:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsSalesRank[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	# send next 5 to the page	
	newIndex = str(startingIndex + 5) + " " + sortMethod
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index=newIndex), 400

# This is the route to display the the previous five products when the user clicks "Back".
@app.route('/goToResultsPageOverflowBackward', methods=['GET', 'POST'])
def gotToResultsPageOverFlowBackward():
	global IDsRelevance
	global IDsTitle
	global IDsAverageRating
	global IDsNumberReviews
	global IDsSalesRank

	# figure out where the last page left off
	index = request.form["index"]
	index = index.split()
	startingIndex = int(index[0])
	sortMethod = index[1]
	passToWebPage = []
	i = startingIndex -  5

	# display IDs according to current sorting method
	if sortMethod == "relevance":
		while i > -1 and i < startingIndex:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsRelevance[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "title":
		while i > -1 and i < startingIndex:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsTitle[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "averageRating":
		while i > -1 and i < startingIndex:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsAverageRating[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "numReviews":
		while i > -1 and i < startingIndex:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsNumberReviews[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	if sortMethod == "salesRank":
		while i > -1 and i < startingIndex:
			sql = "SELECT * FROM product_information WHERE ID = %d" % (IDsSalesRank[i])
			result = db_query(sql)
			passToWebPage = passToWebPage + result
			i = i + 1

	# send previous 5 to the page	
	newIndex = str(startingIndex - 5) + " " + sortMethod
	dictionary = {}
	dictionary['results'] = passToWebPage
	return render_template('resultsPage.html', template_data=dictionary, index=newIndex), 400

# This is the route to display a specific product.
@app.route('/goToProductPage', methods=['GET', 'POST'])
def goToProductPage():

	# record what page in the search results you left off
	val = str(request.form["seeProductPage"])
	val = val.split()
	productID = int(val[0])
	rememberSpot = str(int(val[1]) - 5) + " " + str(val[2])

	# pull the product information from product_description
	resultsArray = []
	sql = "SELECT * FROM product_information WHERE ID = %d" % (productID)
	result = (db_query(sql))
	resultsArray.append(result[0])

	# send this to the template
	dictionary = {}
	dictionary['product'] = resultsArray
	return render_template('productPage.html', template_data=dictionary, index=rememberSpot), 400

# This removes stopwords and special characters from a string, returning the remaining words in an array.
def parseOutWordsKeepNumbers(s):
	s = strip_accents(s)
	s = s.translate({ord(c): "" for c in '\''})
	s = s.translate({ord(c): " " for c in '*@&#%|:?,.;`~!&[]-()[]\''})
	s = s.lower()
	sArray = s.split()

	# remove stop words, spaces, and empty strings
	for word in sArray:
		if word in stopWords or word == ' ' or word == '':
			sArray.remove(word)
	return sArray

# This removes accents caused by products written in other languages than English
def strip_accents(text):
    text = unicodedata.normalize('NFD', text)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")
    return str(text)

# This returns the IDs of the products associated with a search result in order of relavance.
def resolveSearch(search):
	searchArray = formatSearch(search)
	if not searchArray:
		sql = 'SELECT ID, SUM(weight) as totalWeight FROM product_weights WHERE keyword IN (\'asdfasdfasfdnoproducthere\') GROUP BY ID ORDER BY totalWeight DESC'
		return db_query(sql)
	else:
		placeholders = ', '.join(['%s']*len(searchArray))
		sql = 'SELECT ID, SUM(weight) as totalWeight FROM product_weights WHERE keyword IN ({}) GROUP BY ID ORDER BY totalWeight DESC'.format(placeholders) % tuple(searchArray)
		return db_query(sql)

# This formats the search string into an array that can be inserted into the MySQL statement.
def formatSearch(s):
	extraWords = []
	sArray = parseOutWordsKeepNumbers(s)

	for i in range(len(sArray)):
		# if no s at end, and no same word with s later, add that word
		if sArray[i].isdigit() == False:
			if sArray[i].endswith('s') == False and sArray[i] + 's' not in sArray:
				extraWords.append('\''+ sArray[i] + 's\'')
			if sArray[i].endswith('s') == True and sArray[i][:-1] not in sArray:
				extraWords.append('\'' + sArray[i][:-1]+ '\'')
			sArray[i] = '\'' + sArray[i] + '\''
	sArray.extend(extraWords)
	return sArray

# This launches the program.
if __name__ == '__main__':
    app.run()
