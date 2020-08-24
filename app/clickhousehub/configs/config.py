CONFIG = {
	"token" : "AgAAAAAOfQzUAAZsVJowlKqpKEEOvNCfAFr78lg",
	"counter_id": "65168419",
	"disable_ssl_verification_for_clickhouse": 1,
	"visits_fields": [
			"ym:s:visitID",
			"ym:s:counterID",
			"ym:s:watchIDs",
			"ym:s:dateTime",
			"ym:s:clientID",
	    "ym:s:UTMSource",
			"ym:s:startURL",
	    "ym:s:pageViews",
	    "ym:s:goalsID",
			"ym:s:goalsDateTime",
			"ym:s:date"
	],
	"hits_fields": [
		 "ym:pv:deviceCategory",
	   "ym:pv:operatingSystem",
	   "ym:pv:regionCity",
	   "ym:pv:regionCountry",
	   "ym:pv:dateTime",
	   "ym:pv:date",
	   "ym:pv:watchID",
	   "ym:pv:goalsID",
     "ym:pv:counterID",
     "ym:pv:clientID",
	   "ym:pv:URL",
	   "ym:pv:lastTrafficSource",
	   "ym:pv:link",
	   "ym:pv:httpError",
	   "ym:pv:browser",
	   "ym:pv:ipAddress",
	   "ym:pv:mobilePhone",
	   "ym:pv:mobilePhoneModel"
	],
	"log_level": "INFO",
	"retries": 1,
	"retries_delay": 60,
	"clickhouse": {
		"host": "https://rc1b-6wcv9d6xfzgvj459.mdb.yandexcloud.net:8443",
		"user": "user1",
		"password": "password",
		"visits_table": "",
		"hits_table": "",
		"database": "db1"
	}
}
