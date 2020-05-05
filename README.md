# DB-Project

# This is the program(s) to run the search engine, which will be integreated back into the 
# main store front.

Files Inlcuded:
* config.ini (please not that there is a second config setup on line 100 of preprocess.py)
* preprocess.py => fills tables in database testdb
	* assisted by product_information.txt, product_weights.txt, and amazon-meta.txt
* run_app.py => launches search engine in web browser
	* assisted by index.css, home.html, productPage.html, and resultsPage.html
* dump.sql => data dump of testdb
* Final_Report.txt => report evaluating search engine
* Demo.mov => Demo showing that the search engine works


To Initialize the Database:
* Method 1: preprocess.py (approx. 8 minutes)
	* This requires config.ini to be set up appropriately AND for testdb (or whatever you want to name it) to already exist
	* Please note that preprocess.py uses the LOAD DATA command, which requires my.cnf to have the appropriate permission
		* Ex. secure_file_priv=/Users/madisonlucas905/Desktop/DB-Project-master
* Method 2: dump.sql
	* I included a data dump in dump.sql. The configurations would still need to be set up, but this method will take longer due to sequential insertion statements, which uses an algorithm about 20 times slower than LOAD DATA.
