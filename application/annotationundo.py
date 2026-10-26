"""Typed snapshots of the current frame's annotations for click-by-click undo."""
from PySide6 import QtSql

TABLES = ('targets', 'points', 'lines')
WHERE = 'PROJECT = ? AND DEPLOYMENT_ID = ? AND FRAME_NUMBER = ?'


def execute(db, statement, values=()):
    query = QtSql.QSqlQuery(db)
    query.prepare(statement)
    for value in values:
        query.addBindValue(value)
    if not query.exec():
        raise RuntimeError(query.lastError().text())
    return query


def capture(db, scope):
    result = {}
    for table in TABLES:
        query = execute(db, 'SELECT * FROM ' + table + ' WHERE ' + WHERE + ' ORDER BY rowid', scope)
        rows = []
        while query.next():
            rows.append(tuple(None if query.isNull(i) else query.value(i) for i in range(query.record().count())))
        result[table] = rows
    return result


def restore(db, scope, snapshot):
    execute(db, 'SAVEPOINT undo_annotation')
    try:
        for table in reversed(TABLES):
            execute(db, 'DELETE FROM ' + table + ' WHERE ' + WHERE, scope)
        for table in TABLES:
            for row in snapshot[table]:
                execute(db, 'INSERT INTO ' + table + ' VALUES (' + ','.join('?' for _ in row) + ')', row)
        execute(db, 'RELEASE SAVEPOINT undo_annotation')
    except RuntimeError:
        execute(db, 'ROLLBACK TO SAVEPOINT undo_annotation')
        execute(db, 'RELEASE SAVEPOINT undo_annotation')
        raise
