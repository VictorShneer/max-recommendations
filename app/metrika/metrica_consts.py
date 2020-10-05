
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
            -- if email exists store it, else store no-email6la6la6la
            CASE  when isNotNull(id_email_table.shit)
                  then id_email_table.shit
                  else concat('no-email',toString(ClientID)) end as email,
            -- simply count all visits for this email
            sum(1) as total_visits,
            -- if mxm in StartURL then this visit was directly from email
            sum(case when extractURLParameter(StartURL, 'mxm') != ''
                then 1 else 0 end) as total_visits_from_newsletter,
            -- ??? what should we count here ??? 
            -- how many exact goals was reached by this person
            -- or what ???
            sum(case when 1
                {grouped_columns}
                then 1 else 0 end) as total_goals,
            -- ??? the same question
            sum(case when extractURLParameter(StartURL, 'mxm') != ''
                {grouped_columns}
                then 1 else 0 end) as total_goals_from_newsletter,

            case when total_visits == 0 
                    then 0 
                    else round(multiply(divide(total_goals,total_visits),100)) end as conversion,

            
            case when total_goals == 0
                 then 0
                 else round(multiply(divide(total_goals_from_newsletter, total_goals),100)) end as emailpower
        FROM {clickhouse_table_name} as base
            -- 
            left join (select ClientID, 
                any(    case when extractURLParameter(StartURL, 'mxm') != '' 
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
COLUMNS = ['Email', \
            'Total Visits', \
            'Total Visits From Newsletter', \
            'Total Goals Complited', \
            'Total Goals From Newsletter', \
            'Conversion (TG/TV)', \
            'Email power proportion']
