import stripe
import os
import csv
import pickle
from datetime import date


###################################################################################################
########################################## DEFINITIONS ############################################
###################################################################################################


### GLOBAL VARIABLES ##############################################################################
#																								  #	
DATE = date.today().strftime('%m_%d_%y')
USE_CUSTOM_PROPS = False													  #
#																								  #
### END GLOBAL VARIABLES ##########################################################################



### CUSTOM ERROR CLASSES ##########################################################################
#																								  #
class Error(Exception):													  					  	  #
	#Base class  																			      #
	pass 																					      #
#																								  #
class AuthError(Error):																		      #
#																								  #
	message = "Unable to complete authorization: Missing or Incorrect authorization token."       #																						  #
	def __init__(self, message):															      #
		self.message = message 																  #
#	
class FileError(Error):
	message = "Unable to open file. File may be corrupted."
	def __init__(self, message):
		self.message = message

class WriteError(Error):
	message = "Unable to write file. File or data may be incompatible and/or corrupted."
	def __init(self, message):
		self.message = message

class ParseError(Error):
	message = "Unable to parse values. Please check custom property constructors and input values."
	def __init(self, message):
		self.message = message
#																							      #
### END CUSTOM ERROR CLASSES ######################################################################



### CUSTOM DATA STRUCTURE CLASSES #################################################################
#																								  #
class TransactionRecord:
	def __init__(self, balance_transactions, charges):
		self.balance_transactions = balance_transactions
		self.charges = charges
#																							      #
### END CUSTOM DATA STRUCTURE CLASSES #############################################################



### CUSTOM PROPERTY CONSTRUCTORS ##################################################################
#
#|| FIELDS ||#

def FieldsProperty(values):

	##Data processing code goes here##
	fields = values
	return fields

#|| FILTERS ||#
def FilterProperty(values):
	##Filter processing code goes here##
	_filter = values
	return _filter

#|| SOURCES ||#
def SourcesProperty(values):
	##Source processing code goes here##
	sources = values
	return sources

#|| CUSTOM ||#
	#Your custom property constructor(s) here!#
#
### END CUSTOM PROPERTY CONSTRUCTORS ##############################################################



### CUSTOM PARAMETER CLASSES ######################################################################
#	
class StandardProperty:
	def __init__(self, prop):
		self.prop = prop

class FieldsProperty(StandardProperty):
	prop = FieldsProperty
	def __init__(self, prop, values):
		self.prop = prop
		self.values = values

class FilterProperty(StandardProperty):
	prop = FilterProperty
	def __init__(self, prop, values):
		self.prop = prop
		self.values = values

class SourcesProperty(StandardProperty):
	prop = SourcesProperty
	def __init__(self, prop, values):
		self.prop = prop
		self.values = values	

class CustomProperty(StandardProperty):
	#user must define custom property
	def __init__(self, prop, values):
		self.prop = prop
		self.values = values																						  #
#																							      #
### END CUSTOM PARAMETER CLASSES ##################################################################


###################################################################################################
##########################################  END DEFINITIONS #######################################
###################################################################################################


#build func to ask for auth key

def read():
	if os.path.exists('data/token.pickle'):
		try:
			#auth with saved key
			stripe.api_key = pickle.load(open('data/token.pickle', 'rb'))

			#pull txn_ and ch_ where limit is clamp on # of transactions returned
			balance_transactions = stripe.BalanceTransaction.list(limit=3)
			charges = stripe.Charge.list(limit=10)

			data = TransactionRecord(balance_transactions, charges)

			#return TransactionRecord
			return(data)

		#catch AuthError	
		except AuthError as e:
			print(e.message)
	else:
		print("Unable to complete authorization: token not found.")


def write(charges):
	#Prep vars
	headers = charges['data'][0].keys()
	values = []
	for i, val in enumerate(charges['data']):
		values.append(charges['data'][i].values())
	path = 'results/balance_transactions_%s.csv' % DATE


	try:
		file = open(path, 'w+')
		writer = csv.writer(file)
		try:
			## UNDER CONSTRUCTION ###
			#for h in headers:
			## UNDER CONSTRUCTION ###
			writer.writerow(headers)
			for v in values:
				writer.writerow(v)
		except WriteError as e:
			print(e.message) 
	except FileError as e:
		print(e.message)
		

### UNIT TESTS ###

def testRead():
	return read()

def testWrite():
	write(testRead())

def test_1():
	data = read()
	write(data.charges)



### UNCOMMENT FOR TESTING ###

test_1()





