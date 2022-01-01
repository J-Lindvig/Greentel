# Home Assistant constants
DOMAIN = "greentel"
ATTRIBUTION = "Data provided by greentel.dk"

# Greentel Client constants
BASE_URL = 'https://www.greentel.dk'
GET_INFO_PAGE_URL = '/umbraco/Surface/MyPage/GetInfo'
GET_INFO_PAGE_ID = 6292
GET_PACKAGE_PAGE_URL = '/umbraco/api/MyPageApi/GetPackageGauge'
GET_DETAILS_PAGE_URL = '/umbraco/api/MyPageApi/GetConsumptionDetails'
GET_DETAILS_PAGE_ID = 6297

# Greentel Client String constants
INPUT_TOKEN_NAME = '__RequestVerificationToken'
DATA_STR = 'Data'
SUCCESS_STR = 'Success'
TOKEN_STR = 'Token'
GROUP_FIELDS = ['AmountTotal', 'AmountLeft', 'AmountUsed', 'UnitGauge', 'FreeConsumption']