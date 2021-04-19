import moneybot as src
import json

### UNIT TESTS ###


def generate():
	data = open("testbenchdata/t_data.json", "r")
	data = data.read()
	data = json.loads(data)
	return data


def testRead():
	return src.read()

def testWrite():
	src.write(t_data)

def testFieldsIngest():
	testFieldIngest = src.FieldsProperty(FieldsIngest, t_fields_2)
	for f in testFieldIngest.values:
		x = f.description
		y = f.internal_name
		z = f.external_name
	return testFieldIngest

def testMatchFields():
	data = t_data
	fields = t_processed_fields
	x = src.matchFields(data, fields)
	for i in x:
		y = i.internal_name


def testIterSelect():
	data = t_data
	values = t_values
	keys = data['data'][0].keys()
	result = src.iterSelect(keys, values)


	

###|| TEST DATA ||###

t_fields_1 = [
	{"description": "Test description 1", "internal_name": "Test internal name 1", "external_name": "Test external name 1"},
	{"description": "Test description 2", "internal_name": "Test internal name 2", "external_name": "Test external name 3"},
	{"description": "Test description 3", "internal_name": "Test internal name 3", "external_name": "Test external name 3"}
]

t_fields_2 = [
	{"description": "Net donation amount.", "internal_name": "amount", "external_name": "amount"},
	{"description": "Name of donor.", "internal_name": "billing_details", "external_name": "donor name"},
	{"description": "Unique ID of Stripe charge object.", "internal_name": "id", "external_name": "charge id"}
]

t_values = ["amount", "billing_details", "id"]

t_processed_fields = src.FieldsProperty(src.FieldsIngest, t_fields_2)

t_data = generate()
###|| END TEST DATA ||###



### UNCOMMENT FOR TESTING ###
#generate()
#testRead()
#testWrite()
#testRun()
#testFieldsIngest()
#testMatchFields()
testIterSelect()


