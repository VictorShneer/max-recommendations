"""
Here we store 
some consts and SQL query templates for 
analytics blueprint
"""
COLUMNS = ["ClientID",'Email','Операционная система','Город','Марка мобильного телефона', 'Модель мобильного телефона','Браузер']
INITIAL_QUERY_COLUMNS = ['Date','mxm','OperatingSystem','RegionCity','cutQueryString(URL)','MobilePhone','MobilePhoneModel', 'Browser']
INITIAL_QUERY = '''
  SELECT
  		Date, 
  		extractURLParameter(StartURL, 'mxm'), 
  		OperatingSystem,
  		RegionCity,
  		cutQueryString(URL),
  		MobilePhone,
  		MobilePhoneModel, 
  		Browser
  FROM {hits_table_name} h
  JOIN {visits_table_name} v ON v.ClientID = h.ClientID 
  WHERE has(v.WatchIDs, h.WatchID) AND notEmpty(extractURLParameter(StartURL, 'mxm'))
'''

ANALITICS_SEARCH_QUERY = '''
  SELECT h.ClientID, 
         tryBase64Decode(extractURLParameter(v.StartURL, 'mxm')) as emails, 
         OperatingSystem, 
         RegionCity, 
         MobilePhone, 
         MobilePhoneModel, 
         Browser
  FROM {hits_table_name} h
  JOIN {visits_table_name} v on v.ClientID = h.ClientID
    {where_clause}
  GROUP BY emails, ClientID, OperatingSystem, RegionCity, MobilePhone, MobilePhoneModel, Browser
    {having_clause};
'''

INT_COMPARISON_DIC = {'1': '>', '2':'<','3':'=='}
COMPARISON_FIELDS = ['clause_visits', 'clause_visits_from_to', 'clause_goals']