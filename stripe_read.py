import stripe
stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
balance_transactions = stripe.BalanceTransaction.list(limit=3)
print(balance_transactions)