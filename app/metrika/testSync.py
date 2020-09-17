from pandahouse import read_clickhouse

connection = {'host': 'https://rc1b-6wcv9d6xfzgvj459.mdb.yandexcloud.net:8443',
              'database': 'db1',
              'user': 'user1',
              'password': 'password',
              'verify':'/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt'
             }

df = read_clickhouse('SELECT * FROM visits_all', index_col='id',
                     connection=connection)
print(df)
