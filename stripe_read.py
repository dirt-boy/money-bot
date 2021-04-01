import stripe

stripe.api_key = "SECRET"
balance_transactions = stripe.BalanceTransaction.list(limit=3)
print(balance_transactions)