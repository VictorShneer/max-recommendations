import json
import numpy as np
from pprint import pprint


def generate_filter_goals_sql_clause(filter_goals):
    if filter_goals:
        filter_clause = f'length(arrayIntersect({str(filter_goals)}, GoalsID))'
    else:
        filter_clause = 'length(GoalsID)'
    return filter_clause
