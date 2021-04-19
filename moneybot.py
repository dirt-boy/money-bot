import stripe
import os
import csv
import pickle
import json
from datetime import date

###################################################################################################
########################################## DEFINITIONS ############################################
###################################################################################################


### GLOBAL VARIABLES #############################################################################
#																								  #	
DATE = date.today().strftime('%m_%d_%y')
USE_CUSTOM_PROPS = False	
SOURCES_PATH = "data/sources.json"												  #
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
	headerKey = ""
	headerIndex = 0
	path = ""
	def __init__(self, description, url, headerKey, headerIndex):
		self.description = description
		self.url = url
		self.headerKey = headerKey
		self.headerIndex = headerIndex
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
def SourcesIngest(file):
	#basic sources ingest takes in dict of sources from file
	sourceList = []
	f = open(file, "r")
	data = f.read()
	data = json.loads(data)["sources"]
	for s in data:
		sourceList.append(Source(s['description'], s['url'], s['headerKey'], s['headerIndex']))
	return sourceList


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
		self.values = self.prop(values)	

class CustomProperty(StandardProperty):
	#user must define custom property
	def __init__(self, prop, values):
		self.prop = prop
		self.values = values																						  #
#																							      #
### END CUSTOM PARAMETER CLASSES ##################################################################



### METHODS #######################################################################################
#	
def getHeaders(data, key, index):
	headers = data[key][index].keys()
	return headers
																							  
#if an ingested field object has the same internal name as a header, pull data for that field
def matchFields(data, fields, source):
	headers = getHeaders(data, source.headerKey, source.headerIndex)
	fieldNames = []
	for f in fields:
		fieldNames.append(f.internal_name)
	matchFields = iterSelect(headers, fieldNames)	
	return matchFields

def iterSelect(data, values):
#iterative selection
	result = [] 
	for x in data:
		if x in values:
			result.append(x)
		else:
			pass
	return result

##write will have to be redone!!! to work with the current values schema!!!
def write(data, source):
	path = 'results/balance_transactions_%s.csv' % DATE
	headers = getHeaders(data, source.headerKey, source.headerIndex)
	file = open(path, 'w+')
	writer = csv.writer(file)
	writer.writerow(headers)
	try:
		for d in data[source.headerKey]:
			for key in d:
				writer.writerow(key)
	except WriteError as e:
		print(e.message)

def getValues(data, fields, source):
	result = []
	fieldNames = []
	for f in fields:
		fieldNames.append(f.internal_name) 
		result.append({})
	for i, d in enumerate(data[source.headerKey]):
		for key in d:
			if key in fieldNames and i<len(result):
				result[i][key] = d[key]
	return result





#																								  #
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