import stripe
import os
import csv
import pickle
import json
import secrets
import bcrypt
import gspread
import requests
from simple_salesforce import Salesforce
from wtforms import Form, SelectField, SelectMultipleField, SubmitField, validators
from flask import Flask, request, render_template, session, url_for, Response, send_file, redirect
from datetime import date, datetime

###################################################################################################
########################################## DEFINITIONS ############################################
###################################################################################################


### SECURITY ######################################################################################
#
def getHashedKey(plain_text_key):
    # Hash a key for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_key, bcrypt.gensalt())

def checkKey(plain_text_key, hashed_key):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_key, hashed_key)
#																								  #
### END SECURITY ##################################################################################	



### GLOBAL VARIABLES #############################################################################
#																								  #	
DATE = date.today().strftime('%m_%d_%y')
USE_CUSTOM_PROPS = False	
SOURCES_PATH = "static/sources.json"
app = Flask(__name__, static_folder="static")
PRESETS = ["stripe", "none"]
TOKEN = getHashedKey(secrets.token_urlsafe(36))
PERSIST = {}
SERVICE_ACCOUNT_PATH = "/Users/gg/NerdStuff/money-bot-web/venv/lib/python3.8/site-packages/gspread/service_account.json"
DRIVE_EXPORT_FOLDER_ID = "1OrJ_sqt2xI9tPnttTNMBJ_1cf4WNW0XC"
SALESFORCE_AUTH = json.loads(pickle.load(open('static/salesforce_creds.pickle', 'rb')))
#																								  #
### END GLOBAL VARIABLES ##########################################################################



### GSPREAD #######################################################################################
#
exp = gspread.service_account(SERVICE_ACCOUNT_PATH)
#																								  #
### END GSPREAD ###################################################################################	



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
#								
class MakeError(Error):
	message = "Unable to make csv. Please check data formatting"
	def __init__(self, message):
		self.message = message															      #
### END CUSTOM ERROR CLASSES ######################################################################



### CUSTOM DATA STRUCTURE CLASSES #################################################################
#	
#|| DATA TYPES ||#																							  #
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
	name = ""
	description = ""
	url = ""
	headerKey = ""
	headerIndex = 0
	path = ""
	def __init__(self, name, description, url, headerKey, headerIndex):
		self.name = name
		self.description = description
		self.url = url
		self.headerKey = headerKey
		self.headerIndex = headerIndex

#|| WTFORMS CLASSES ||#
class SourceForm(Form):
	source = SelectField('Source', choices=PRESETS)
	submitSource = SubmitField("submit")

class FieldForm(Form):
	fields = SelectMultipleField("Fields", coerce=str)
	submitFields = SubmitField("submit")

class DownloadForm(Form):
	download = SubmitField("download")

class ExportForm(Form):
	export = SubmitField("export to sheets")

class SalesforceForm(Form):
	salesforce = SubmitField("Manual Upload to Salesforce")
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

def FieldsIngestFromDict(values):
	fieldList = []
	for v in values:
		try:
			fieldList.append(Field(v["description"], v["internal_name"], v["external_name"]))
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
		sourceList.append(Source(s['name'], s['description'], s['url'], s['headerKey'], s['headerIndex']))
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



### PRESETS #################### ##################################################################
#
STRIPE_PRESET = SourcesProperty(SourcesIngest, "static/sources.json")
#																							      #
### END PRESETS ###################################################################################


### METHODS #######################################################################################
#	
def getHeaders(data, key, index):
	data = data[key][index]
	headers = list(data.items())
	result = []
	for h in headers:
		if type(data[h[0]]) != stripe.stripe_object.StripeObject:
			result.append(h[0])
		else:
			result.extend(data[h[0]].keys())
			processSubkey(data, h[0])
	return result
																							  
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

##refactor to work with mutable headers
def write(data, source):
	path = 'results/balance_transactions_%s.csv' % DATE
	headers = getHeaders(data, source.headerKey, source.headerIndex)
	file = open(path, 'w+')
	writer = csv.writer(file)
	writer.writerow(headers)
	try:
		for d in data[source.headerKey]:
			row = []
			for key in d:
				row.append(d[key])
			writer.writerow(row)
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
			if type(d[key]) == stripe.stripe_object.StripeObject:
				for subKey in d[key]:
					if subKey in fieldNames and i<len(result):
						result[i][subKey] = d[key][subKey]
			if key in fieldNames and i<len(result):
				result[i][key] = d[key]
	print(result)
	return result


def getData(source):
	if source=="stripe":
		if os.path.exists('static/token.pickle'):
			try:
				stripe.api_key = pickle.load(open('static/token.pickle', 'rb'))
				balance_transactions = stripe.BalanceTransaction.list(limit=10)
				charges = stripe.Charge.list(limit=10)
				data = TransactionRecord(balance_transactions, charges)
				return(data)
			except AuthError as e:
				print(e.message)
		else:
			print("Unable to complete authorization: token not found.")	
	else:
		return "Source not found."

def loadSourcePreset(source):
	if source=="stripe":
		for s in SourcesProperty(SourcesIngest, "static/sources.json").values:
			if s.name == "stripe":
				return s
			else:
				return "Source stripe: string incorrect"
	else:
		return "Source not found"


def loadFieldPreset(source):
	path = "static/field_presets_"+source.name+".json"
	if os.path.exists(path):
		fieldPresets = open(path, "r")
		fieldData = json.loads(fieldPresets.read())
		fieldData = fieldData["fields"]
		fields = FieldsProperty(FieldsIngestFromDict, fieldData)
		return fields


def addToPersistentMem(key, value):
	PERSIST[key.upper()] = value
	#setup for positional access
	pos = list(PERSIST.values()).index(value)
	k = list(PERSIST.keys())[pos]
	#save key for persistent data in sesh mem
	session[key.lower()] = k

def loadFromPersistentMem(key):
	val = PERSIST[session[key]]
	return val

def processSubkey(subDict, subkey):
	res = []
	subVals = subDict[subkey]
	print(subVals.keys())
	for key in subVals:
		if type(subVals[key]) == stripe.stripe_object.StripeObject:
			return processSubkey(subVals, key)
	return res



def makeCSV(data, source):
	headers = [h for h in getHeaders(data, source.headerKey, source.headerIndex)]
	sep = ","
	csv = sep.join(headers)
	csv+="\n"
	try:
		for d in data[source.headerKey]:
			row = ""
			for key in d:
				row+= str(d[key])+","
			csv+= row[:len(row)-1]+"\n"
		return csv
	except MakeError as e:
		print(e.message)
#																								  #
### END METHODS ###################################################################################



### DATABASE ####################################################################################
#
#|| SALESFORCE ||#

def getService(SALESFORCE_AUTH):
	username = SALESFORCE_AUTH["username"]
	password = SALESFORCE_AUTH["password"]
	token = SALESFORCE_AUTH["token"]
	sf = Salesforce(username=username, password=password, security_token=token)
	return sf

def createContact():
	#do stuff
	pass

def createOpp(sf, data, contacts):
	for d in data:
		close_date_UTC = d["created"]
		close_date = datetime.fromtimestamp(close_date_UTC)
		close_date_sf = str(close_date)[:10]
		fy = getFY(close_date)
		amount = d["amount"]/100
		status = d["paid"]
		name = d["name"]
		for contact in contacts:
			vals = contact[2]
			c_name = contact[0][1:len(contact[0])-1]+" "+contact[1][1:len(contact[1])-1]
			if vals != False and status != False and c_name == name:
				region = vals["region"]
				stage = "Posted"
				contact_id = vals["contact_id"]
				account_id = vals["account_id"]
				donation_platform = loadSourcePreset(session["source"]).name
				name = contact[0]+" "+contact[1]+" Donation "+fy
				opp = sf.Opportunity.create({'Name': name,'Region_Allocation__c':region, "CloseDate": close_date_sf, "StageName": stage, "npsp__Primary_Contact__c": contact_id, "AccountId":account_id, "Donation_Platform__c": donation_platform, "Amount": amount})
			else:
				pass
	return "complete."


def checkExists(fname, lname, sf):
	q = sf.query_all("SELECT Id, Region__c, AccountId FROM Contact WHERE LastName = "+lname+" AND FirstName = "+fname)
	if q["totalSize"] == 1:
		Id = q["records"][0]["Id"]
		Region = q["records"][0]["Region__c"]
		AccountId = q["records"][0]["AccountId"]
		return {"contact_id":Id, "region":Region, "account_id": AccountId}
	else:
		##should route to optional contact creation?
		return False

def makeSfString(string):
	return "'"+string+"'"

def getOppName(opp):
	return

def getFY(closeDate):
	if closeDate.month > 7:
		return str(date.today().year + 1)[-2:]
	else:
		return str(date.today().year)[-2:]

def getCloseDate(opp):
	return

def getAmount(opp):
	return




#																								  #
### END DATABASE ################################################################################




### FLASK #######################################################################################
#

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

@app.route("/", methods=["GET", "POST"])
def index():
	sourceForm = SourceForm()
	fieldForm = FieldForm()
	return render_template("index.html", sourceForm=sourceForm)

@app.route("/configure", methods=["GET", "POST"])
def config():
	sourceForm = SourceForm()
	source = request.args.get('source')
	return render_template("index.html", source=source, sourceForm=sourceForm)


@app.route("/configure/get-headers", methods=["GET", "POST"])
def configureSource():
	sourceForm = SourceForm()
	fieldForm = FieldForm()
	source = request.args.get('source')
	if source in PRESETS:
		loadSource = loadSourcePreset(source)
		data = getData(loadSource.name).charges
		addToPersistentMem("data", data)
		session["source"] = source
		session.modified = True
		headers =getHeaders(data, loadSource.headerKey, loadSource.headerIndex)
		fieldForm.fields.choices = [(h, h) for h in headers]
	else:
		print("Custom source identified.")
	return render_template("index.html", sourceForm=sourceForm, fieldForm=fieldForm)

@app.route("/configure/send-values", methods=["GET", "POST"])
def sendValuesFromInput():
	sourceForm = SourceForm()
	fieldForm = FieldForm()
	downloadForm = DownloadForm()
	exportForm = ExportForm()
	salesforceForm = SalesforceForm()
	fieldList = []
	fields = request.form.getlist("fields")
	data = PERSIST[session["data"]]
	source = loadSourcePreset(session["source"])
	fieldsPreset = loadFieldPreset(source)
	for f in fields:
		for p in fieldsPreset.values:
			if f == p.internal_name:
				fieldList.append(p)
	#returns valid json data for requested fields
	data = getValues(data, fieldList, source)
	addToPersistentMem("userrequest", data)
	csv = makeCSV(data={"data": loadFromPersistentMem("userrequest")}, source=source)
	addToPersistentMem("csv", csv)
	return render_template("index.html", data=data, sourceForm=sourceForm, downloadForm=downloadForm, exportForm=exportForm, salesforceForm=salesforceForm)

@app.route("/download")
def download():
	name = "balance_transactions_"+DATE
	data = {"data": loadFromPersistentMem("userrequest")}
	source = loadSourcePreset(session["source"])
	csv = makeCSV(data, source)
	addToPersistentMem("csv", csv)
	return Response(csv, mimetype="text/csv", headers={"Content-disposition":"attachment; filename="+name+".csv"})

@app.route("/export", methods=["GET", "POST"])
def export():
	name = "balance_transactions_"+DATE
	loc = exp.create(name, DRIVE_EXPORT_FOLDER_ID)
	data = {"data": loadFromPersistentMem("userrequest")}
	source = loadSourcePreset(session["source"])
	csv = makeCSV(data, source)
	addToPersistentMem("csv", csv)
	exp.import_csv(loc.id, csv)
	link = "https://docs.google.com/spreadsheets/d/"+loc.id
	return redirect(link, 301)

@app.route("/salesforce", methods=["GET", "POST"])
def salesforce_test():
	data = loadFromPersistentMem("userrequest")
	sf = getService(SALESFORCE_AUTH)
	names = [d["name"] for d in data]
	splitNames = []
	for name in names:
		first, *last = name.split()
		last = " ".join(last)
		splitNames.append((first, last))
		exist = []
	for fname, lname in splitNames:
		fname = makeSfString(fname)
		lname = makeSfString(lname)
		status = checkExists(fname, lname, sf)
		exist.append((fname, lname, status))
	return createOpp(sf, data, exist)

	
#																								  #
### END FLASK ###################################################################################


###################################################################################################
##########################################  END DEFINITIONS #######################################
###################################################################################################	

if __name__ == "__main__":
	#uncomment for live debug vvv
	app.secret_key = TOKEN
	app.run(host="127.0.0.1", port=8080, debug=True)