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