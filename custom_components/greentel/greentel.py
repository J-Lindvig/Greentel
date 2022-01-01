# Imports
import requests                 # Perform http/https requests
from bs4 import BeautifulSoup   # Parse HTML pages
import json                     # Needed to print JSON API data
import datetime
import calendar
import logging
from .const import (
  BASE_URL,
  GET_INFO,
  GET_INFO_PAGE_ID,
  GET_PACKAGE,
  GET_DETAILS,
  GET_DETAILS_PAGE_ID,
  DATA_STR,
  SUCCESS_STR,
  TOKEN_STR,
)

_LOGGER = logging.getLogger(__name__)

class greentelClient:
    def __init__(self, phoneNo, password):
        self._phoneNo = phoneNo
        self._password = password
        self._session = None
        self._token = None
        self._subscriptions = []
        self._subscribers = {}
        self._consumptionPackage = {}
        self._consumptionPackageUser = {}

    def login(self):
        self._session = requests.Session()
        url = BASE_URL
        response = self._session.get(url)

        payload = { '__RequestVerificationToken': '', 'PhoneNo': self._phoneNo, 'Password': self._password }
        html = BeautifulSoup(response.text, "html.parser")
        url = url + html.form['action']
        for input in html.find_all('input'):
            if (input.has_attr('name') and input['name'] == '__RequestVerificationToken'):
                payload['__RequestVerificationToken'] = input['value']
        response = self._session.post(url, data = payload)

        payload = {
          'PageId': GET_INFO_PAGE_ID
        }
        response = self._session.get(BASE_URL + GET_INFO, params = payload).json()
        if response[SUCCESS_STR] and len(response[DATA_STR]) > 0:
            self._token = response[DATA_STR][0][TOKEN_STR]
            return True

    def getData(self):
        _LOGGER.debug("LOGIN: ")
        if not self._token:
            self.login()

        self._getSubscriptions()
#        self._getConsumptionPackage()
#        self._getConsumptionAllUsers()

    def _getSubscriptions(self):
        payload = {
          'PageId': GET_INFO_PAGE_ID
        }
        response = self._session.get(BASE_URL + GET_INFO, params = payload).json()

        if response[SUCCESS_STR] and len(response[DATA_STR]) > 0:
            uniqueIdList = {}
            idx = 0
            for subscription in response[DATA_STR]:
                if subscription['Subscription'] not in uniqueIdList:
                    idx = len(uniqueIdList)
                    uniqueIdList[subscription['Subscription']] = idx
                    aDict = {}
                    self._subscriptions.append(aDict)
                    self._subscriptions[idx]['Users'] = []
                idx = uniqueIdList[subscription['Subscription']]
                self._subscriptions[idx]['Name'] = subscription['Subscription']
                self._subscriptions[idx]['Balance'] = subscription['Balance']
                self._subscriptions[idx]['Users'].append(subscription['PhoneNumber'])
                self._subscribers[subscription['PhoneNumber']] = subscription['User']['Username']

    def _getConsumptionPackage(self):
        payload = {
          'PageId': GET_INFO_PAGE_ID,
          'Token': self._token,
          'PhoneNo': ''
        }
        response = self._session.post(BASE_URL + GET_PACKAGE, data = payload).json()
        if response[SUCCESS_STR] and len(response[DATA_STR]) > 0:
            groupFields = ['AmountTotal', 'AmountLeft', 'AmountUsed', 'UnitGauge', 'FreeConsumption']
            for group in response['Data']['Consumption']:
                groupName = group['TextGauge'].split()[0]
                if len(groupName) > 3:
                    groupName = groupName.title()
                self._consumptionPackage[groupName] = {}
                for groupField in groupFields:
                    self._consumptionPackage[groupName][groupField] = group[groupField]

    def _getConsumptionUser(self, phoneNo):
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
        response = self._session.get(BASE_URL + GET_DETAILS, params = payload).json()
        if response[SUCCESS_STR] and len(response[DATA_STR]) > 0:
            for group in response['Data']['Consumption']['Items']:
                groupName = group['Description']
                Qty = group['Qty']
                if phoneNo not in self._consumptionPackageUser:
                    self._consumptionPackageUser[phoneNo] = {}
                if groupName != 'Abonnement':
                    if groupName == 'Opkald og samtaler':
                        groupName = 'Tale'
                        QtySplit = Qty.split(':')
                        Qty = (int(QtySplit[0]) * 3600) + (int(QtySplit[1]) * 60) + int(QtySplit[2])
                    self._consumptionPackageUser[phoneNo][groupName] = int(Qty)

    def _getConsumptionAllUsers(self):
        for user in self._subscribers:
            self._getConsumptionUser(user)