import json


def chdb_adapter(session):
    def run_query(sql: str):
        result = session.query(sql, "JSONEachRow")
        rows = []
        for line in str(result).strip().splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows
    return run_query


def clickhouse_connect_adapter(client):
    def run_query(sql: str):
        res = client.query(sql)
        cols = res.column_names
        return [dict(zip(cols, row)) for row in res.result_rows]
    return run_query
