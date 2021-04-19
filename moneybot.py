import stripe
import os
import csv
import pickle
from datetime import date

###################################################################################################
##?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?# TEST MODE #?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?#?##
###################################################################################################
"""
"""

###################################################################################################
########################################## DEFINITIONS ############################################
###################################################################################################


### GLOBAL VARIABLES #############################################################################
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
	def __init__(self, message):
		self.message = message

class ParseError(Error):
	message = "Unable to parse values. Please check custom property constructors and input values."
	def __init__(self, message):
		self.message = message
#																							      #
### END CUSTOM ERROR CLASSES ######################################################################



### CUSTOM DATA STRUCTURE CLASSES #################################################################
#																								  #
class TransactionRecord:
	def __init__(self, balance_transactions, charges):
		self.balance_transactions = balance_transactions
		self.charges = charges

class Field:
	description = ""
	internal_name = ""
	external_name = ""
	def __init__(self, description, internal_name, external_name):
		self.description = description
		self.internal_name = internal_name
		self.external_name = external_name

class Filter:
	description = ""
	parameters = ""
	def __init__(self, description, parameters):
		self.description = description
		self.parameters = parameters

class Source:
	description = ""
	url = ""
	def __init__(self, description, url):
		self.description = description
		self.url = url
#																							      #
### END CUSTOM DATA STRUCTURE CLASSES #############################################################



### CUSTOM PROPERTY CONSTRUCTORS ##################################################################
#
#|| FIELD INGEST NODES ||#

def FieldsIngest(values):
	##Data processing code goes here##
	# assume the data comes as a list of strings
	#that must be converted into Field objects
	fieldList = []
	for v in values:
		try:
			fieldList.append(Field(v['description'], v['internal_name'], v['external_name']))
		except ParseError as e:
			print(e.message)
	fields = fieldList
	return fields

#|| FILTER INGEST NODES ||#
def FilterIngest(values):
	##Filter processing code goes here##
	_filter = values
	return _filter

#|| SOURCE INGEST NODES ||#
def SourcesIngest(values):
	##Source processing code goes here##
	sources = values
	return sources

#|| CUSTOM INGEST NODES ||#
	#Your custom property constructor(s) here!#
#
### END CUSTOM PROPERTY CONSTRUCTORS ##############################################################



### CUSTOM PARAMETER CLASSES ######################################################################
#	
class StandardProperty:
	def __init__(self, prop):
		self.prop = prop

class FieldsProperty(StandardProperty):
	prop = FieldsIngest
	def __init__(self, prop, values):
		self.prop = prop
		self.values = self.prop(values)

class FilterProperty(StandardProperty):
	prop = FilterIngest
	def __init__(self, prop, values):
		self.prop = prop
		self.values = values

class SourcesProperty(StandardProperty):
	prop = SourcesIngest
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


### METHODS #######################################################################################

#if an ingested field object has the same internal name as a header, pull data for that field
def matchFields(data, fields):
	headers = data['data'][0].keys()
	matchFields = []
	for f in fields.values:
		if f.internal_name in headers:
			matchFields.append(f)
	return matchFields

def write(charges):
	path = 'results/balance_transactions_%s.csv' % DATE
	file = open(path, 'w+')
	writer = csv.writer()
	writer.writerow(headers)
	try:
		for v in values:
			writer.writerow(v)
	except WriteError as e:
		print(e.message)

### END METHODS ###################################################################################

###################################################################################################
##########################################  END DEFINITIONS #######################################
###################################################################################################

	
def main():
				
	if os.path.exists('data/token.pickle'):
		try:
			stripe.api_key = pickle.load(open('data/token.pickle', 'rb'))
			balance_transactions = stripe.BalanceTransaction.list(limit=3)
			charges = stripe.Charge.list(limit=10)
			data = TransactionRecord(balance_transactions, charges)
			return(data)
		except AuthError as e:
			print(e.message)
	else:
		print("Unable to complete authorization: token not found.")


if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   main()