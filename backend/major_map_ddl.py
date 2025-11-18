import mysql.connector
from mysql.connector import Error
import os
import time
import dotenv
dotenv.load_dotenv()    




for _ in range(10):
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),   #we can change to port vs socket if needed
            password=os.getenv('DB_PASSWORD', 'adminpass'),#change password here or grab from env  DO ENV!!!!!!!!!!!!
            auth_plugin='mysql_native_password'
        )
        break
    except Error:
        print("Waiting for database connection...")
        time.sleep(5)
else:
    print("Could not connect to the database.")
    exit(1)


mycursor = mydb.cursor()


cursor = mydb.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS major_map_db")
cursor.execute("USE major_map_db")

cursor.execute("""
    create table users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(64) NOT NULL,
    password_hash  VARCHAR(128) NOT NULL,
    email          VARCHAR(128) NOT NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,               
""")


cursor.execute("""
    create table admins(
    admin_id       INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(64) NOT NULL,
    password_hash  VARCHAR(128) NOT NULL,
    email          VARCHAR(128) NOT NULL
    )
""")


cursor.execute("""
CREATE TABLE term (
    term_id        INT PRIMARY KEY,                
    name           VARCHAR(40) NOT NULL,
    start_date     DATE NOT NULL,
    end_date       DATE NOT NULL,
    UNIQUE KEY uq_term_name (name)
    )ENGINE=InnoDB;
""")
cursor.execute("""
    CREATE TABLE department (
    dept_id        INT AUTO_INCREMENT PRIMARY KEY,
    code           VARCHAR(16) NOT NULL,          
    name           VARCHAR(128) NOT NULL,
    UNIQUE KEY uq_dept_code (code)
    )ENGINE=InnoDB;
""")

               
cursor.execute("""
CREATE TABLE instructor (
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

#mass storage for all the schedule data we have

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
        UNIQUE KEY uq_term_section (year, semester, section_code))ENGINE=InnoDB;
""")


cursor.execute("""
  CREATE TABLE visitors (
  visitor_id CHAR(36) PRIMARY KEY,
  first_seen DATETIME NOT NULL,
  last_seen DATETIME NOT NULL,
  user_agent_hash CHAR(64),
  ip_prefix VARBINARY(8), -- store truncated IPv4/6
  country CHAR(2)
) ENGINE=InnoDB;

""")


cursor.execute("""
               CREATE TABLE generation_jobs (
  job_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  input_hash CHAR(64) NOT NULL,
  status ENUM('queued','running','succeeded','failed') NOT NULL,
  error_text TEXT,
  started_at DATETIME NULL,
  finished_at DATETIME NULL,
  cost_cents INT NULL
) ENGINE=InnoDB;
""")

mydb.commit()