import stripe
import os
import csv
import pickle
from datetime import date

### GLOBAL VARIABLES ##############################################################################
#																								  #	
DATE = date.today().strftime('%m_%d_%y')													  #
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


#build func to ask for auth key

def read():
	if os.path.exists('data/token.pickle'):
		try:
			#auth with saved key
			stripe.api_key = pickle.load(open('data/token.pickle', 'rb'))

			#pull txn_ and ch_ where limit is clamp on # of transactions returned
			balance_transactions = stripe.BalanceTransaction.list(limit=3)
			charges = stripe.Charge.list(limit=3)

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
			writer.writerow(headers)
			for v in values:
				writer.writerow(v)
		except WriteError as e:
			print(e.message) 
	except FileError as e:
		print(e.message)
		







data = read()
write(data.charges)



