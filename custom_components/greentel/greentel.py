# Imports
import requests                 # Perform http/https requests
from bs4 import BeautifulSoup   # Parse HTML pages
import json                     # Needed to print JSON API data
import datetime
import calendar
import logging
from .const import (
	BASE_URL,
	GET_INFO_PAGE_URL,
	GET_INFO_PAGE_ID,
	GET_PACKAGE_PAGE_URL,
	GET_DETAILS_PAGE_URL,
	GET_DETAILS_PAGE_ID,
	INPUT_TOKEN_NAME,
	DATA_STR,
	SUCCESS_STR,
	TOKEN_STR,
	GROUP_FIELDS,
)

_LOGGER = logging.getLogger(__name__)

class greentelClient:
	def __init__(self, phoneNo, password):
		self._session = None
		self._phoneNo = phoneNo
		self._password = password
		self._token = None
		self._subscriptions = []
		self._subscribers = {}
		self._consumptionPackage = {}
		self._consumptionPackageUser = {}

	# Repeated function testing if the reponse is OK
	def _responseOK(self, response):
		return (response[SUCCESS_STR] and len(response[DATA_STR]) > 0)

	# Login, what else...
	def login(self):
		# Prepare a new session and get the webpage with the login form (BASE_URL)
		self._session = requests.Session()
		url = BASE_URL
		response = self._session.get(url)

		"""
		Parse the HTML code.
		Initialize payload containing the name of the <INPUT> of the given token
		and the phonenumber and password from the configuration

		Extract the URL of the form and append it to the BASE_URL
		Loop through the <INPUT> tags until we find the one with our token
		Append the token to our payload and break the loop

		POST our payload to the loginpage
		"""
		html = BeautifulSoup(response.text, "html.parser")
		payload = {INPUT_TOKEN_NAME: '', 'PhoneNo': self._phoneNo, 'Password': self._password }
		url = url + html.form['action']
		for input in html.find_all('input'):
			if (input.has_attr('name') and input['name'] == INPUT_TOKEN_NAME):
				payload[INPUT_TOKEN_NAME] = input['value']
				break
		response = self._session.post(url, data = payload)

		"""
		Prepare a new payload with the PageId of the landing page
		GET the response from the payload
		If the response is successful, store the token anf return true
		"""
		payload = { 'PageId': GET_INFO_PAGE_ID }
		response = self._session.get(BASE_URL + GET_INFO_PAGE_URL, params = payload).json()
		if self._responseOK(response):
#		if response[SUCCESS_STR] and len(response[DATA_STR]) > 0:
			self._token = response[DATA_STR][0][TOKEN_STR]
			return True

	def getData(self):
		# If the token is not set, then login
		if not self._token:
			self.login()

		# Call the subfunctions and extract the data
		self._getSubscriptions()
		self._getConsumptionPackage()
#        self._getConsumptionAllUsers()

	# Retrieve all our subscriptions and the users attached to the subscription
	def _getSubscriptions(self):
		# Prepare the payload and GET the response
		payload = { 'PageId': GET_INFO_PAGE_ID }
		response = self._session.get(BASE_URL + GET_INFO_PAGE_URL, params = payload).json()

		if self._responseOK(response):
			# Prepare a dict of uniqueId of subscritions and a placeholder for the current index.
			uniqueIdList = {}
			idx = 0
			# Loop through all our subsciptions
			for subscription in response[DATA_STR]:
				# If the subscription is NOT in the list of uniqueIds
				if subscription['Subscription'] not in uniqueIdList:
					# Update the index
					idx = len(uniqueIdList)
					# Add the index at the subscriptions place in 
					uniqueIdList[subscription['Subscription']] = idx

					# Create a empty dictionary and append it to our list of subscriptions
					# Make a empty array at the current index for our users
					aDict = {}
					self._subscriptions.append(aDict)
					self._subscriptions[idx]['Users'] = []

				# Get the index of current subscription and populate it with:
				# Name of the subscription, the balance and append the users phonenumber
				idx = uniqueIdList[subscription['Subscription']]
				self._subscriptions[idx]['Name'] = subscription['Subscription']
				self._subscriptions[idx]['Balance'] = subscription['Balance']
				self._subscriptions[idx]['Users'].append(subscription['PhoneNumber'])
				# Store the username in a dictionary with the phonenumber as key
				self._subscribers[subscription['PhoneNumber']] = subscription['User']['Username']

	# Get the total consumption in the package
	def _getConsumptionPackage(self):
		# Prepare and POST the payload
		payload = { 'PageId': GET_INFO_PAGE_ID, 'Token': self._token, 'PhoneNo': '' }
		response = self._session.post(BASE_URL + GET_PACKAGE_PAGE_URL, data = payload).json()

		if self._responseOK(response):
			# Loop through the different elements of consumption
			for group in response['Data']['Consumption']:
				# Extract the name and uppercase the first char
				groupName = group['TextGauge'].split()[0].title()
				# Prepare a dictionary for the group
				self._consumptionPackage[groupName] = {}
				# Extract the fields and populate the dictionary
				for groupField in GROUP_FIELDS:
					self._consumptionPackage[groupName][groupField] = group[groupField]

	# Get a users consumption in the current month
	# Supply the phonenumber of the user
	def _getConsumptionUser(self, phoneNo):
		# Prepare some DATE variables for the payload
		now = datetime.datetime.now()
		year = now.strftime("%Y")
		month = now.strftime("%m")
		payload = {
			'PageId': GET_DETAILS_PAGE_ID,
			'Token': self._token,
			'PhoneNo': phoneNo,
			'Type': 'Normal',
			'FromDate': year + "-" + month + "-01",
			'ToDate': year + "-" + month + "-" + str(calendar.monthrange(int(year), int(month))[1])
		}
		# Get the reponse
		response = self._session.get(BASE_URL + GET_DETAILS_PAGE_URL, params = payload).json()

		if self._responseOK(response):
			# Loop through the different elements of consumption
			for group in response['Data']['Consumption']['Items']:
				# Extract the name and quantity of the consumption
				groupName = group['Description']
				Qty = group['Qty']
				# If this the first time we are using this consumption
				# Prepare a dictionary at its place
				if phoneNo not in self._consumptionPackageUser:
					self._consumptionPackageUser[phoneNo] = {}
				# Ignore "Abonnement"
				if groupName != 'Abonnement':
					# If the consumption is Voice, then overrule the name and
					# convert the HH:MM:SS to seconds
					if groupName == 'Opkald og samtaler':
						groupName = 'Tale'
						QtySplit = Qty.split(':')
						Qty = (int(QtySplit[0]) * 3600) + (int(QtySplit[1]) * 60) + int(QtySplit[2])
					# Add the quantity of the consumption to the user
					self._consumptionPackageUser[phoneNo][groupName] = int(Qty)

	# Get the consumption of all the users
	def _getConsumptionAllUsers(self):
		for user in self._subscribers:
			self._getConsumptionUser(user)