# additional readme file
Code of this module mostly written by Yandex
I add a few fuctions to metrica_logs_api.py and clickhouse custom request
It was fast ugly way solution
Main purpose was to make this code works on the server side
The entry point to the whole process is:

handle_integration(integration_obj, user_obj, params)

It lives in metrica_logs_api.py

I dream to made this module as a blueprint with OOP structure
But first we need to catch data flow before it stores to ClickHouse
This will allow us to make better ClickHouse DB structures
Like separated ClientID - Email tables and so on