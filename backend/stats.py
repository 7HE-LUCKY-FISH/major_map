from db_module import get_db_connection

def top3_instructors_last4_semesters(course_number: str) -> list[dict]:
    """
    Top 3 instructors (by count) who taught `course_number` in the most recent
    4 semesters (Spring/Fall only), with probability = count / total.
    """
    sql = """
    WITH recent_terms AS (
      SELECT DISTINCT
        (year * 2 + CASE semester
          WHEN 'Spring' THEN 0
          WHEN 'Fall'   THEN 1
          ELSE 0
        END) AS term_idx
      FROM schedule_flat
      WHERE course_number = %s
        AND semester IN ('Spring','Fall')
      ORDER BY term_idx DESC
      LIMIT 4
    ),
    recent_rows AS (
      SELECT
        instructor_name
      FROM schedule_flat sf
      JOIN recent_terms rt
        ON (sf.year * 2 + CASE sf.semester
              WHEN 'Spring' THEN 0
              WHEN 'Fall'   THEN 1
              ELSE 0
            END) = rt.term_idx
      WHERE sf.course_number = %s
        AND sf.semester IN ('Spring','Fall')
        AND sf.instructor_name IS NOT NULL
        AND sf.instructor_name <> ''
    ),
    counts AS (
      SELECT instructor_name, COUNT(*) AS teach_count
      FROM recent_rows
      GROUP BY instructor_name
    ),
    total AS (
      SELECT SUM(teach_count) AS total_count FROM counts
    )
    SELECT
      c.instructor_name,
      c.teach_count,
      (c.teach_count * 1.0 / t.total_count) AS probability
    FROM counts c
    CROSS JOIN total t
    ORDER BY c.teach_count DESC
    LIMIT 3;
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (course_number, course_number))
        return cur.fetchall()
    finally:
        conn.close()

def unique_time_slots_last4_semesters(course_number: str) -> list[dict]:
    """
    Returns unique time slots for `course_number` from the most recent 4 semesters
    (Spring/Fall only), INCLUDING TBA rows (where time_start or time_end is NULL).

    Output keys:
      - days_text
      - start_time  (e.g. '09:00AM' or 'TBA')
      - end_time    (e.g. '10:15AM' or 'TBA')
      - slot_label  (e.g. 'MW 09:00AM-10:15AM' or 'MW TBA')
    """
    sql = """
    SELECT
      t.days_text,
      t.start_time,
      t.end_time,
      t.slot_label
    FROM (
      SELECT DISTINCT
        sf.days_text,
        sf.time_start AS raw_start,
        sf.time_end AS raw_end,
        CASE
          WHEN sf.time_start IS NULL OR sf.time_end IS NULL THEN 'TBA'
          ELSE TIME_FORMAT(sf.time_start, '%h:%i%p')
        END AS start_time,
        CASE
          WHEN sf.time_start IS NULL OR sf.time_end IS NULL THEN 'TBA'
          ELSE TIME_FORMAT(sf.time_end, '%h:%i%p')
        END AS end_time,
        CASE
          WHEN sf.time_start IS NULL OR sf.time_end IS NULL THEN
            CONCAT(COALESCE(NULLIF(sf.days_text,''), 'TBD'), ' TBA')
          ELSE
            CONCAT(
              sf.days_text, ' ',
              TIME_FORMAT(sf.time_start, '%h:%i%p'),
              '-',
              TIME_FORMAT(sf.time_end, '%h:%i%p')
            )
        END AS slot_label
      FROM schedule_flat sf
      JOIN (
        SELECT DISTINCT
          (year * 2 + CASE semester
            WHEN 'Spring' THEN 0
            WHEN 'Fall'   THEN 1
            ELSE 0
          END) AS term_idx
        FROM schedule_flat
        WHERE course_number = %s
          AND semester IN ('Spring','Fall')
        ORDER BY term_idx DESC
        LIMIT 4
      ) recent_terms
      ON (sf.year * 2 + CASE sf.semester
            WHEN 'Spring' THEN 0
            WHEN 'Fall'   THEN 1
            ELSE 0
          END) = recent_terms.term_idx
      WHERE sf.course_number = %s
        AND sf.semester IN ('Spring','Fall')
        AND sf.days_text IS NOT NULL
        AND sf.days_text <> ''
    ) t
    ORDER BY t.days_text, t.raw_start, t.raw_end;
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (course_number, course_number))
        return cur.fetchall()
    finally:
        conn.close()