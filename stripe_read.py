import stripe
import os
import pickle

class Error(Exception):
	#Base Class
	pass

class AuthError(Error):

	message = "Unable to complete authorization: Missing or Incorrect authorization token."

	def __init__(self, message):
		self.message = message


if os.path.exists('data/token.pickle'):
	try:
		stripe.api_key = pickle.load(open('data/token.pickle', 'rb'))
		balance_transactions = stripe.BalanceTransaction.list(limit=3)
		print(balance_transactions)
	except AuthError as e:
		print(e.message)
else:
	print("Unable to complete authorization: unknown error.")
