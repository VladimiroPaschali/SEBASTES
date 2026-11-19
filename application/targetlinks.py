"""Fish identities are chains of (frame number, target number) in one deployment."""
from bisect import bisect_left
from contextlib import contextmanager

from dbConnection import execute


FISH = """
WITH RECURSIVE fish(frame, target) AS (
    SELECT frame_number, target_number FROM targets
    WHERE deployment_id=? AND frame_number=? AND target_number=?
    UNION
    SELECT t.target_link_frame, t.target_link FROM targets t JOIN fish
      ON (t.frame_number, t.target_number)=(fish.frame, fish.target)
    WHERE t.deployment_id=? AND t.target_link_frame IS NOT NULL
    UNION
    SELECT t.frame_number, t.target_number FROM targets t JOIN fish
      ON (t.target_link_frame, t.target_link)=(fish.frame, fish.target)
    WHERE t.deployment_id=?
) """


def members(db, deployment, observation):
    query = execute(db, FISH + 'SELECT frame, target FROM fish ORDER BY frame, target',
                    (deployment, *observation, deployment, deployment))
    result = []
    while query.next():
        result.append((query.value(0), query.value(1)))
    return result


def fish_name(db, deployment, observation):
    query = execute(db, FISH + """
        SELECT name FROM (
            SELECT fish_name AS name, frame, target, 0 AS sequence FROM targets
            JOIN fish ON (frame_number,target_number)=(frame,target) WHERE deployment_id=?
            UNION ALL
            SELECT name, frame, target, lines.rowid FROM lines
            JOIN fish ON (frame_number,target_number)=(frame,target) WHERE deployment_id=?
        ) WHERE trim(name)<>'' ORDER BY frame, target, sequence LIMIT 1
        """, (deployment, *observation, deployment, deployment, deployment, deployment))
    return query.value(0) if query.next() else ''


def has_identity(db, deployment, observation):
    query = execute(db, """SELECT 1 FROM targets WHERE deployment_id=? AND (
        ((frame_number,target_number)=(?,?) AND (target_link_frame IS NOT NULL OR fish_name IS NOT NULL))
        OR (target_link_frame,target_link)=(?,?)) LIMIT 1""", (deployment, *observation, *observation))
    return query.next()


def next_name(db, deployment, observation):
    query = execute(db, 'SELECT species_group FROM targets WHERE deployment_id=? AND frame_number=? AND target_number=?',
                    (deployment, *observation))
    species = (query.value(0) if query.next() else '') or 'Fish'
    prefix = species + ' '
    names = execute(db, """SELECT name FROM lines WHERE deployment_id=? AND name IS NOT NULL
        UNION SELECT fish_name FROM targets WHERE deployment_id=? AND fish_name IS NOT NULL""", (deployment, deployment))
    highest = 0
    while names.next():
        name = names.value(0)
        if name.startswith(prefix) and name[len(prefix):].isdecimal():
            highest = max(highest, int(name[len(prefix):]))
    return prefix + str(highest + 1)


def rename(db, deployment, observation, name):
    with transaction(db):
        for table, column in [('targets', 'fish_name'), ('lines', 'name')]:
            execute(db, FISH + f"""
                UPDATE {table} SET {column}=? WHERE deployment_id=?
                AND (frame_number,target_number) IN (SELECT frame,target FROM fish)
                AND {column} IS NOT ?
                """, (deployment, *observation, deployment, deployment, name, deployment, name))


@contextmanager
def transaction(db):
    execute(db, 'SAVEPOINT edit_fish_links')
    try:
        yield
        execute(db, 'RELEASE edit_fish_links')
    except Exception:
        execute(db, 'ROLLBACK TO edit_fish_links')
        execute(db, 'RELEASE edit_fish_links')
        raise


def set_parent(db, deployment, child, parent):
    execute(db, """UPDATE targets SET target_link_frame=?, target_link=?
        WHERE deployment_id=? AND frame_number=? AND target_number=?""",
        (*parent, deployment, *child))


def link(db, deployment, source, destination):
    """Merge both fish in chronological order, including an observation inserted in a gap."""
    with transaction(db):
        first = members(db, deployment, source)
        second = members(db, deployment, destination)
        if not first or not second:
            raise ValueError('Select a fish that exists in this deployment.')
        if source[0] == destination[0]:
            raise ValueError('Choose the same fish in a different frame.')
        if destination in first:
            return fish_name(db, deployment, source)
        chain = sorted(first + second)
        if len({frame for frame, target in chain}) != len(chain):
            raise ValueError('These fish already have different targets in the same frame.')
        name = fish_name(db, deployment, source) or fish_name(db, deployment, destination) or next_name(db, deployment, source)
        for parent, child in zip(chain, chain[1:]):
            set_parent(db, deployment, child, parent)
        rename(db, deployment, source, name)
        return name


def delete_target(connection, deployment, observation):
    """Keep the remaining observations connected when their middle target is deleted."""
    db = connection.db
    with transaction(db):
        query = execute(db, """SELECT target_link_frame,target_link FROM targets
            WHERE deployment_id=? AND frame_number=? AND target_number=?""", (deployment, *observation))
        if not query.next():
            return
        parent = (None, None) if query.isNull(0) else (query.value(0), query.value(1))
        query.finish()
        execute(db, """UPDATE targets SET target_link_frame=?, target_link=?
            WHERE deployment_id=? AND target_link_frame=? AND target_link=?""",
            (*parent, deployment, *observation))
        execute(db, 'DELETE FROM targets WHERE deployment_id=? AND frame_number=? AND target_number=?',
                (deployment, *observation))


def migrate(db, deployment, frames):
    """Legacy target_link referred to a target in the previous available image."""
    with transaction(db):
        fields = execute(db, 'PRAGMA table_info(targets)')
        columns = set()
        while fields.next():
            columns.add(fields.value(1).lower())
        if 'target_link_frame' not in columns:
            execute(db, 'ALTER TABLE targets ADD COLUMN target_link_frame INTEGER')
        if 'fish_name' not in columns:
            execute(db, 'ALTER TABLE targets ADD COLUMN fish_name TEXT')
        execute(db, 'CREATE INDEX IF NOT EXISTS target_observation ON targets(deployment_id,frame_number,target_number)')
        execute(db, 'CREATE INDEX IF NOT EXISTS target_predecessor ON targets(deployment_id,target_link_frame,target_link)')
        pending = execute(db, """SELECT frame_number,target_number,target_link FROM targets
            WHERE deployment_id=? AND target_link IS NOT NULL AND target_link_frame IS NULL""", (deployment,))
        legacy = []
        while pending.next():
            legacy.append(tuple(pending.value(i) for i in range(3)))
        resolved = set()
        for frame, target, parent in legacy:
            index = bisect_left(frames, frame)
            if 0 < index < len(frames) and frames[index] == frame:
                previous = (frames[index - 1], parent)
                exists = execute(db, 'SELECT 1 FROM targets WHERE deployment_id=? AND frame_number=? AND target_number=?',
                                 (deployment, *previous)).next()
                if exists:
                    set_parent(db, deployment, (frame, target), previous)
                    resolved.add((frame, target))
        while resolved:
            observation = resolved.pop()
            name = fish_name(db, deployment, observation)
            rename(db, deployment, observation, name or next_name(db, deployment, observation))
            resolved.difference_update(members(db, deployment, observation))
