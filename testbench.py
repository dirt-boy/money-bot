import moneybot as src

### UNIT TESTS ###


def generate():
	data = open("testbenchdata/t_data.json", "r")
	return(data.read())

def testRead():
	return src.read()

def testWrite():
	src.write(t_data)

def testFieldsIngest():
	testFieldIngest = src.FieldsProperty(FieldsIngest, t_fields)
	for f in testFieldIngest.values:
		x = f.description
		y = f.internal_name
		z = f.external_name
	return testFieldIngest

def testMatchFields():
	data = t_data
	fields = t_processed_fields
	x = src.matchFields(data, fields)
	

###|| TEST DATA ||###

t_fields = [
	{"description": "Test description 1", "internal_name": "Test internal name 1", "external_name": "Test external name 1"},
	{"description": "Test description 2", "internal_name": "Test internal name 2", "external_name": "Test external name 3"},
	{"description": "Test description 3", "internal_name": "Test internal name 3", "external_name": "Test external name 3"}
]

t_processed_fields = src.FieldsProperty(src.FieldsIngest, t_fields)

t_data = generate()
###|| END TEST DATA ||###



### UNCOMMENT FOR TESTING ###
#testRead()
#testWrite()
#testRun()
#testFieldsIngest()
testMatchFields()


