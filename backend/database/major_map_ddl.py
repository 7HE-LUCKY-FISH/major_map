from db_module import get_server_connection_with_retry
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


mydb = get_server_connection_with_retry()


mycursor = mydb.cursor()


cursor = mydb.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS major_map_db")
cursor.execute("USE major_map_db")

cursor.execute("""
    create table IF NOT EXISTS users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(64) NOT NULL UNIQUE,
    password_hash  VARCHAR(128) NOT NULL,
    email          VARCHAR(128) NOT NULL UNIQUE,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")


cursor.execute("""
    create table IF NOT EXISTS admins(
    admin_id       INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(64) NOT NULL,
    password_hash  VARCHAR(128) NOT NULL,
    email          VARCHAR(128) NOT NULL
    )
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS term (
    term_id        INT PRIMARY KEY,
    name           VARCHAR(40) NOT NULL,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    UNIQUE KEY uq_term_name (name)
    )ENGINE=InnoDB;
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS department (
    dept_id        INT AUTO_INCREMENT PRIMARY KEY,
    code           VARCHAR(16) NOT NULL,
    name           VARCHAR(128) NOT NULL,
    UNIQUE KEY uq_dept_code (code)
    )ENGINE=InnoDB;
""")

# courses belong to departments; store course code and human-readable name
cursor.execute("""
    CREATE TABLE courses (
    course_id      INT AUTO_INCREMENT PRIMARY KEY,
    dept_id        INT NOT NULL,
    code           VARCHAR(16) NOT NULL,     -- e.g. "101", "CS50"
    name           VARCHAR(255) NOT NULL,    -- full course title
    FOREIGN KEY (dept_id) REFERENCES department(dept_id),
    UNIQUE KEY uq_dept_course (dept_id, code)
    )ENGINE=InnoDB;
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS instructor (
    instructor_id  INT AUTO_INCREMENT PRIMARY KEY,
    dept_id        INT,
    first_name     VARCHAR(80) NOT NULL,
    last_name      VARCHAR(80) NOT NULL,
    display_name   VARCHAR(180) GENERATED ALWAYS AS (CONCAT(first_name,' ',last_name)) STORED,
    external_key   VARCHAR(64) NULL,               -- scrape key if any
    FOREIGN KEY (dept_id) REFERENCES department(dept_id),
    KEY idx_instr_last (last_name)
    )ENGINE=InnoDB;
""")

# mass storage for all the schedule data we have
# Section,Number,Mode,Title,Satisfies,Unit,Type,Days,Times,Instructor,Location,Dates,Seats,Year,Semester
cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_flat (
        id               BIGINT AUTO_INCREMENT PRIMARY KEY,
        section_code     VARCHAR(16)  NOT NULL,   -- from "Section"
        course_number    VARCHAR(16)  NOT NULL,   -- from "Number"
        mode             ENUM('InPerson','Online','Hybrid') NOT NULL, -- from "Mode"
        title            VARCHAR(255) NOT NULL,   -- "Title"
        satisfies        VARCHAR(255) NULL,       -- fixed spelling of "Satifies"
        units            DECIMAL(4,1) NULL,       -- "Unit"
        component_type   ENUM('LEC','LAB','SEM','ACT','DIS','ONL') NULL, -- from "Type"
        days_text        VARCHAR(16)  NULL,       -- "Days" (raw, e.g., "MWF")
        time_start       TIME         NULL,       -- parsed from "Times"
        time_end         TIME         NULL,       -- parsed from "Times"
        instructor_name  VARCHAR(160) NULL,       -- "Instructor"
        location_text    VARCHAR(160) NULL,       -- "Location"
        date_start       DATE         NULL,       -- parsed from "Dates"
        date_end         DATE         NULL,       -- parsed from "Dates"
        seats_available  INT          NULL,       -- "Seats"
        year             SMALLINT     NOT NULL,   -- "Year"
        semester         ENUM('Spring','Summer','Fall','Winter') NOT NULL, -- "Semester"
        UNIQUE KEY uq_term_section (year, semester, section_code, time_start))ENGINE=InnoDB;
""")


cursor.execute("""
  CREATE TABLE IF NOT EXISTS visitors (
  visitor_id CHAR(36) PRIMARY KEY,
  first_seen DATETIME NOT NULL,
  last_seen DATETIME NOT NULL,
  user_agent_hash CHAR(64),
  ip_prefix VARBINARY(8), -- store truncated IPv4/6
  country CHAR(2)
) ENGINE=InnoDB;

""")


cursor.execute("""
  CREATE TABLE IF NOT EXISTS generation_jobs (
  job_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  input_hash CHAR(64) NOT NULL,
  status ENUM('queued','running','succeeded','failed') NOT NULL,
  error_text TEXT,
  started_at DATETIME NULL,
  finished_at DATETIME NULL,
  cost_cents INT NULL
) ENGINE=InnoDB;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules (
  schedule_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  term_id INT,
  sections JSON NOT NULL,  -- Store array of section codes
  input_hash CHAR(64),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (term_id) REFERENCES term(term_id)
) ENGINE=InnoDB;
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_planner_state (
  user_id INT PRIMARY KEY,
  major_data JSON NOT NULL,
  roadmap_data JSON NOT NULL,
  schedule_data JSON NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
""")

mydb.commit()
