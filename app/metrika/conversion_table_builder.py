PROPERTY_TO_SQL_DIC = {'start_date':'''Date >= '{res}' ''',\
                        'goals':'''has(GoalsID, {res}) != 0 '''}

# this is what generate_grouped_columns_sql does
'''

--         and Date > '2020-06-20'
--         and (
--             has(GoalsID, 46766122) != 0
--             or
--             has(GoalsID, 46765999) != 0
--             )

'''

def generate_grouped_columns_sql(restrictions):
    columns_claise = ''
    # delete empty restrictions, for the cases when you have no goals to filter with
    restrictions_not_empty = {k: v for k, v in restrictions.items() if v != ['']}
    for key,values in restrictions_not_empty.items():
        # every where state should be in (   )
        columns_claise += 'AND ('
        # every where state come as array
        for i,value in enumerate(values):
            # every where state has its own format in PROPERTY_TO_SQL_DIC
            state = PROPERTY_TO_SQL_DIC[key].format(res=value)
            # if it is last restrition in array we don't put OR
            if i != len(values)-1:
                columns_claise += (state + ' OR ')
            else:
                columns_claise+=state
        # close ) and add AND for the new WHERE state
        columns_claise += ') '
    return columns_claise
