
TIME_SERIES_QUERY = \
"""
    select b.Date,
    sum(case when 1
        {grouped_columns}
        then length(GoalsID) else 0 end) as total_goals,
    sum(case when has(b.res, ClientID)
                    {grouped_columns}
            then length(GoalsID) else 0 end) as goals_with_email,
    sum(case when extractURLParameter(StartURL, 'mxm') != ''
        {grouped_columns}
        then length(GoalsID) else 0 END) as goals_just_after_email
    from {clickhouse_table_name} a
    join (
        select Date, runningAccumulate(shit) as res
            from (
                select Date,
                    groupArrayState(case when extractURLParameter(StartURL, 'mxm') != '' then ClientID else Null end )  as shit
                from ihatemyself.visits_raw_1
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
            CASE  when extractURLParameter(StartURL, 'mxm') != ''
                  then base64Decode(extractURLParameter(StartURL, 'mxm'))
                  else concat('no-email',toString(ClientID)) end as email,

            sum(case when Date >= '{start_date}'
                then 1 else 0 end) as total_visits,

            sum(case when extractURLParameter(StartURL, 'mxm') != ''
                and (Date >= '{start_date}')
                then 1 else 0 end) as total_visits_from_newsletter,

            sum(case when 1
                {grouped_columns}
                then length(GoalsID) else 0 end) as total_goals,

            sum(case when extractURLParameter(StartURL, 'mxm') != ''
                {grouped_columns}
                then length(GoalsID) else 0 end) as total_goals_from_newsletter,

            multiply(intDivOrZero(total_goals, total_visits),100) as conversion,
            multiply(intDivOrZero(total_goals_from_newsletter, total_goals),100) as emailpower
        FROM {clickhouse_table_name}
        group by email
    )
    where total_visits != 0
'''
TIME_SERIES_DF_COLUMNS = ['Date','total_goals','goals_with_email','goals_just_after_email']
COLUMNS = ['Email', \
            'Total Visits', \
            'Total Visits From Newsletter', \
            'Total Goals Complited', \
            'Total Goals From Newsletter', \
            'Conversion (TG/TV)', \
            'Email power proportion']
