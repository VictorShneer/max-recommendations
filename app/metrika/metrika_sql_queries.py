"""
here are SQL queries templates
and order of table columns
if you need to change columns or their order
you should do it here 
"""

TIME_SERIES_QUERY = \
"""
    select b.Date,
    sum({goals_filter_clause}) as total_goals,
    sum(case when has(b.res, ClientID)
             then {goals_filter_clause} 
             else 0 
             end) as goals_with_email,
    sum(case when notEmpty(extractURLParameter(StartURL, 'mxm'))
             then {goals_filter_clause} 
             else 0 
             end) as goals_just_after_email
    from {clickhouse_table_name} a
    join (
        select Date, runningAccumulate(shit) as res
            from (
                select Date,
                groupArrayState(case when notEmpty(extractURLParameter(StartURL, 'mxm')) 
                                     then ClientID 
                                     else Null 
                                     end)  as shit
                from {clickhouse_table_name}
                where Date >= '{start_date}'
                group by Date
            ) as crazy
    ) as b using Date
    where b.Date >= '{start_date}'
    group by b.Date
"""

VISITS_RAW_QUERY = \
'''
    select * from(
        SELECT
            CASE  when isNotNull(id_email_table.shit)
                  then id_email_table.shit
                  else concat('no-email',toString(ClientID)) 
                  end as email,
            sum(1) as total_visits,
            sum({goals_filter_clause}) as total_goals,
            sum(case when notEmpty(extractURLParameter(StartURL, 'mxm'))
                     then {goals_filter_clause} 
                     else 0 
                     end) as goals_just_after_email,
            any(ClientID) as clientid
        FROM {clickhouse_table_name} as base
            left join (select ClientID, 
                              any(case when notEmpty(extractURLParameter(StartURL, 'mxm'))
                                       then base64Decode(extractURLParameter(StartURL, 'mxm'))
                                       else Null end) as shit
            FROM {clickhouse_table_name} 
            group by ClientID) as id_email_table on 
                id_email_table.ClientID = base.ClientID
            where Date >= '{start_date}'
        group by email
        order by email
    )
    where total_visits != 0
'''
TIME_SERIES_DF_COLUMNS = ['Date','total_goals','goals_with_email','goals_just_after_email']

# order of columns here
# related to oreder of columns in VISITS_RAW_QUERY
COLUMNS = [ 
            'Email', \
            'Визитов всего', \
            'Всего целей выполнено', \
            'Кол-во целей после прямого перехода из email', \
            'ClientID'
            ]

