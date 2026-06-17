-- ============================================================
-- MOCKMENTOR UPGRADE SQL
-- Smart Placement Preparation & Interview Intelligence Platform
-- Run this AFTER the original database.sql is already imported.
-- Safe to run: uses CREATE TABLE IF NOT EXISTS throughout.
-- ============================================================

USE mockmentor_db;

-- ============================================================
-- TABLE: companies
-- Master list of companies for targeted prep
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    company_id   INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL UNIQUE,
    logo_emoji   VARCHAR(10)  DEFAULT '🏢',
    description  TEXT,
    avg_package  VARCHAR(50),
    difficulty   ENUM('Easy','Medium','Hard') DEFAULT 'Medium',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: company_rounds
-- Interview round types per company
-- ============================================================
CREATE TABLE IF NOT EXISTS company_rounds (
    round_id    INT AUTO_INCREMENT PRIMARY KEY,
    company_id  INT NOT NULL,
    round_name  VARCHAR(100) NOT NULL,
    round_order INT DEFAULT 1,
    description TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: company_questions
-- Company-specific interview questions (linked to topics)
-- ============================================================
CREATE TABLE IF NOT EXISTS company_questions (
    cq_id         INT AUTO_INCREMENT PRIMARY KEY,
    company_id    INT NOT NULL,
    topic_id      INT,
    round_id      INT,
    difficulty_id INT,
    question_text TEXT NOT NULL,
    sample_answer TEXT,
    frequency     INT DEFAULT 1,   -- how often asked
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id)    REFERENCES companies(company_id)         ON DELETE CASCADE,
    FOREIGN KEY (topic_id)      REFERENCES topics(topic_id)              ON DELETE SET NULL,
    FOREIGN KEY (round_id)      REFERENCES company_rounds(round_id)      ON DELETE SET NULL,
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id) ON DELETE SET NULL,
    INDEX idx_company (company_id),
    INDEX idx_topic   (topic_id)
);

-- ============================================================
-- TABLE: company_experiences
-- Student-submitted interview experiences
-- ============================================================
CREATE TABLE IF NOT EXISTS company_experiences (
    exp_id        INT AUTO_INCREMENT PRIMARY KEY,
    company_id    INT NOT NULL,
    candidate_id  INT NOT NULL,
    title         VARCHAR(200),
    experience    TEXT,
    result        ENUM('Selected','Rejected','Pending') DEFAULT 'Pending',
    difficulty    ENUM('Easy','Medium','Hard') DEFAULT 'Medium',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id)   REFERENCES companies(company_id)    ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: coding_questions
-- Coding problems with test cases
-- ============================================================
CREATE TABLE IF NOT EXISTS coding_questions (
    cq_id         INT AUTO_INCREMENT PRIMARY KEY,
    company_id    INT,
    difficulty_id INT,
    title         VARCHAR(200) NOT NULL,
    description   TEXT NOT NULL,
    input_format  TEXT,
    output_format TEXT,
    constraints   TEXT,
    sample_input  TEXT,
    sample_output TEXT,
    explanation   TEXT,
    topic_tags    VARCHAR(200),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id)    REFERENCES companies(company_id)            ON DELETE SET NULL,
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id) ON DELETE SET NULL,
    INDEX idx_difficulty (difficulty_id),
    INDEX idx_company    (company_id)
);

-- ============================================================
-- TABLE: coding_testcases
-- Test cases for each coding question
-- ============================================================
CREATE TABLE IF NOT EXISTS coding_testcases (
    tc_id       INT AUTO_INCREMENT PRIMARY KEY,
    cq_id       INT NOT NULL,
    input_data  TEXT,
    expected    TEXT NOT NULL,
    is_sample   TINYINT(1) DEFAULT 0,
    FOREIGN KEY (cq_id) REFERENCES coding_questions(cq_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: coding_submissions
-- Every code submission by a candidate
-- ============================================================
CREATE TABLE IF NOT EXISTS coding_submissions (
    sub_id        INT AUTO_INCREMENT PRIMARY KEY,
    cq_id         INT NOT NULL,
    candidate_id  INT NOT NULL,
    language      VARCHAR(30) DEFAULT 'python',
    code          TEXT,
    status        ENUM('Accepted','Wrong Answer','Error','Partial') DEFAULT 'Wrong Answer',
    score         DECIMAL(5,2) DEFAULT 0,
    runtime_ms    INT DEFAULT 0,
    test_passed   INT DEFAULT 0,
    test_total    INT DEFAULT 0,
    submitted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cq_id)         REFERENCES coding_questions(cq_id)      ON DELETE CASCADE,
    FOREIGN KEY (candidate_id)  REFERENCES candidates(candidate_id)     ON DELETE CASCADE,
    INDEX idx_candidate (candidate_id),
    INDEX idx_question  (cq_id)
);

-- ============================================================
-- TABLE: resumes
-- Uploaded resumes per candidate
-- ============================================================
CREATE TABLE IF NOT EXISTS resumes (
    resume_id    INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL UNIQUE,
    filename     VARCHAR(255),
    raw_text     LONGTEXT,
    uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: extracted_skills
-- Skills parsed from resumes
-- ============================================================
CREATE TABLE IF NOT EXISTS extracted_skills (
    skill_id     INT AUTO_INCREMENT PRIMARY KEY,
    resume_id    INT NOT NULL,
    skill_name   VARCHAR(100) NOT NULL,
    category     VARCHAR(50),
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE,
    INDEX idx_resume (resume_id)
);

-- ============================================================
-- TABLE: resume_analysis
-- Analysis results for each resume
-- ============================================================
CREATE TABLE IF NOT EXISTS resume_analysis (
    analysis_id     INT AUTO_INCREMENT PRIMARY KEY,
    resume_id       INT NOT NULL UNIQUE,
    match_score     DECIMAL(5,2) DEFAULT 0,
    recommended_topics TEXT,
    recommended_companies TEXT,
    analysis_text   TEXT,
    analyzed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
);

-- ============================================================
-- EXTEND existing recommendations table (safe if column missing)
-- ============================================================
ALTER TABLE recommendations
    ADD COLUMN IF NOT EXISTS source     VARCHAR(50)  DEFAULT 'system',
    ADD COLUMN IF NOT EXISTS priority   TINYINT      DEFAULT 2,
    ADD COLUMN IF NOT EXISTS is_read    TINYINT(1)   DEFAULT 0;

-- ============================================================
-- SEED DATA: companies
-- ============================================================
INSERT IGNORE INTO companies (company_name, logo_emoji, description, avg_package, difficulty) VALUES
('TCS',       '🔵', 'Tata Consultancy Services – largest IT company in India', '3.5–7 LPA',   'Easy'),
('Infosys',   '🟣', 'Global leader in next-generation digital services',        '3.6–8 LPA',   'Easy'),
('Wipro',     '🟡', 'Leading global IT, consulting and BPO company',            '3.5–7 LPA',   'Easy'),
('Amazon',    '🟠', 'World leader in e-commerce and cloud computing (AWS)',      '25–45 LPA',   'Hard'),
('Google',    '🔴', 'Global technology leader – Search, Cloud, AI',             '30–60 LPA',   'Hard'),
('Microsoft', '🔷', 'Global software and cloud technology company (Azure)',      '25–50 LPA',   'Hard'),
('Accenture', '🟢', 'Global consulting and technology services firm',           '4.5–9 LPA',   'Medium'),
('Cognizant', '⚪', 'IT services and consulting corporation',                   '4–8 LPA',     'Medium');

-- ============================================================
-- SEED DATA: company_rounds
-- ============================================================
INSERT IGNORE INTO company_rounds (company_id, round_name, round_order, description)
SELECT c.company_id, r.round_name, r.round_order, r.description
FROM companies c
JOIN (
    SELECT 'Online Assessment'    AS round_name, 1 AS round_order, 'Aptitude + Coding round'           AS description
    UNION ALL SELECT 'Technical Interview',  2, 'Core CS + DSA questions'
    UNION ALL SELECT 'HR Interview',         3, 'Behavioral and fitment round'
) r ON 1=1
WHERE c.company_name IN ('TCS','Infosys','Wipro','Accenture','Cognizant')
ON DUPLICATE KEY UPDATE round_name = round_name;

INSERT IGNORE INTO company_rounds (company_id, round_name, round_order, description)
SELECT c.company_id, r.round_name, r.round_order, r.description
FROM companies c
JOIN (
    SELECT 'Online Assessment'   AS round_name, 1 AS round_order, 'Coding problems (LeetCode style)'  AS description
    UNION ALL SELECT 'Phone Screen',        2, 'Data structures and algorithms'
    UNION ALL SELECT 'Technical Rounds',    3, '3-4 rounds of system design + DSA'
    UNION ALL SELECT 'Bar Raiser',          4, 'Leadership principles round'
    UNION ALL SELECT 'HR/Offer',            5, 'Compensation negotiation'
) r ON 1=1
WHERE c.company_name IN ('Amazon','Google','Microsoft')
ON DUPLICATE KEY UPDATE round_name = round_name;

-- ============================================================
-- SEED DATA: company_questions
-- ============================================================
INSERT IGNORE INTO company_questions (company_id, topic_id, difficulty_id, question_text, sample_answer, frequency)
SELECT c.company_id, t.topic_id, d.difficulty_id, q.question_text, q.sample_answer, q.frequency
FROM (
    SELECT 'TCS' AS co, 'DBMS' AS tp, 'Easy' AS diff,
           'What is a primary key? Give an example.' AS question_text,
           'A primary key uniquely identifies each row in a table. Example: student_id in a Students table.' AS sample_answer, 5
    UNION ALL SELECT 'TCS','DBMS','Easy','What is normalization?',
           'Normalization reduces data redundancy and ensures data integrity by dividing large tables into smaller related ones.',4
    UNION ALL SELECT 'TCS','Python','Easy','What are Python data types?',
           'Python data types include int, float, str, list, tuple, dict, set, bool, and NoneType.',5
    UNION ALL SELECT 'Infosys','Data Structures','Medium','Explain Binary Search Tree.',
           'BST is a binary tree where left child < parent < right child. Supports O(log n) search, insert, delete on average.',4
    UNION ALL SELECT 'Infosys','Algorithms','Medium','What is the time complexity of Quick Sort?',
           'Average case O(n log n), worst case O(n²) when pivot is always smallest/largest. Space O(log n).',4
    UNION ALL SELECT 'Amazon','System Design','Hard','Design a URL shortener like bit.ly.',
           'Use a hash function to generate 6-char code, store long→short mapping in DB, use Redis cache for hot URLs, load balancer for scale.',5
    UNION ALL SELECT 'Amazon','Data Structures','Hard','Find the LRU Cache implementation.',
           'Use HashMap + Doubly Linked List. HashMap for O(1) get, LinkedList for O(1) eviction of least recently used.',5
    UNION ALL SELECT 'Google','Algorithms','Hard','Given a sorted array, find two numbers that sum to target.',
           'Two-pointer approach: left=0, right=n-1. If sum==target return. If sum<target move left++, else right--. O(n) time.',5
    UNION ALL SELECT 'Microsoft','Operating Systems','Medium','What is a deadlock? How to prevent it?',
           'Deadlock: processes wait indefinitely for resources held by each other. Prevention: resource ordering, banker''s algorithm, timeouts.',4
    UNION ALL SELECT 'Wipro','Computer Networks','Easy','What is the OSI model?',
           '7 layers: Physical, Data Link, Network, Transport, Session, Presentation, Application. Each layer serves the one above it.',4
    UNION ALL SELECT 'Accenture','SQL','Easy','Write a query to find duplicate records.',
           'SELECT col, COUNT(*) FROM table GROUP BY col HAVING COUNT(*) > 1;',4
    UNION ALL SELECT 'Cognizant','Web Development','Medium','What is REST API?',
           'REST (Representational State Transfer) is an architectural style using HTTP methods (GET, POST, PUT, DELETE) for stateless communication.',4
) q
JOIN companies c ON c.company_name = q.co
JOIN topics t ON t.topic_name = q.tp
JOIN difficulty_levels d ON d.difficulty_name = q.diff
ON DUPLICATE KEY UPDATE frequency = frequency;

-- ============================================================
-- SEED DATA: coding_questions
-- ============================================================
INSERT IGNORE INTO coding_questions (difficulty_id, title, description, input_format, output_format,
    sample_input, sample_output, explanation, topic_tags, constraints)
SELECT d.difficulty_id, q.title, q.description, q.input_format, q.output_format,
       q.sample_input, q.sample_output, q.explanation, q.topic_tags, q.constraints
FROM difficulty_levels d
JOIN (
    SELECT 'Easy' AS diff, 'Two Sum' AS title,
        'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.' AS description,
        'First line: n (array size)\nSecond line: n space-separated integers\nThird line: target' AS input_format,
        'Two space-separated indices' AS output_format,
        '4\n2 7 11 15\n9' AS sample_input, '0 1' AS sample_output,
        'nums[0] + nums[1] = 2 + 7 = 9' AS explanation,
        'Array,Hash Map' AS topic_tags, '2 <= n <= 10^4, values -10^9 to 10^9' AS constraints
    UNION ALL
    SELECT 'Easy','Reverse a String',
        'Write a function that reverses a string. Input is a single word without spaces.',
        'A single string on one line.','The reversed string.',
        'hello','olleh','Simply reverse the characters of the string.','String,Two Pointer',
        '1 <= s.length <= 10^5'
    UNION ALL
    SELECT 'Easy','FizzBuzz',
        'Print numbers 1 to N. For multiples of 3 print Fizz, for multiples of 5 print Buzz, for multiples of both print FizzBuzz.',
        'A single integer N.','N lines of output.',
        '15',
        '1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz',
        'Replace multiples of 3 and 5 appropriately.','Math,String','1 <= N <= 10^4'
    UNION ALL
    SELECT 'Medium','Longest Substring Without Repeating Characters',
        'Given a string s, find the length of the longest substring without repeating characters.',
        'A single string s.','A single integer – the length.',
        'abcabcbb','3',
        'The answer is "abc" with length 3.','String,Sliding Window,Hash Map',
        '0 <= s.length <= 5 * 10^4'
    UNION ALL
    SELECT 'Medium','Valid Parentheses',
        'Given a string s containing just the characters (, ), {, }, [ and ], determine if the input string is valid.',
        'A single string s.','true or false',
        '()[]{]','true','Each bracket must be closed in correct order.','Stack,String',
        '1 <= s.length <= 10^4'
    UNION ALL
    SELECT 'Hard','Merge K Sorted Lists',
        'You are given an array of k linked-lists lists, each linked-list is sorted in ascending order. Merge all the linked-lists into one sorted linked-list and return it.',
        'First line: k (number of lists)\nNext k lines: space-separated integers representing each list (-1 means empty)',
        'Space-separated merged sorted values.','3\n1 4 5\n1 3 4\n2 6','1 1 2 3 4 4 5 6',
        'Use a min-heap / priority queue for efficient merging.','Linked List,Heap,Divide and Conquer',
        '0 <= k <= 10^4, 0 <= total nodes <= 5*10^4'
) q ON d.difficulty_name = q.diff;

-- ============================================================
-- SEED DATA: coding_testcases
-- ============================================================
-- Two Sum testcases
INSERT IGNORE INTO coding_testcases (cq_id, input_data, expected, is_sample)
SELECT cq_id, '4\n2 7 11 15\n9', '0 1', 1 FROM coding_questions WHERE title='Two Sum';
INSERT IGNORE INTO coding_testcases (cq_id, input_data, expected, is_sample)
SELECT cq_id, '3\n3 2 4\n6', '1 2', 0 FROM coding_questions WHERE title='Two Sum';

-- Reverse String testcases
INSERT IGNORE INTO coding_testcases (cq_id, input_data, expected, is_sample)
SELECT cq_id, 'hello', 'olleh', 1 FROM coding_questions WHERE title='Reverse a String';
INSERT IGNORE INTO coding_testcases (cq_id, input_data, expected, is_sample)
SELECT cq_id, 'python', 'nohtyp', 0 FROM coding_questions WHERE title='Reverse a String';

-- FizzBuzz testcases
INSERT IGNORE INTO coding_testcases (cq_id, input_data, expected, is_sample)
SELECT cq_id, '5', '1\n2\nFizz\n4\nBuzz', 1 FROM coding_questions WHERE title='FizzBuzz';

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_coding_sub_candidate ON coding_submissions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_coding_sub_question  ON coding_submissions(cq_id);
CREATE INDEX IF NOT EXISTS idx_exp_company          ON company_experiences(company_id);
CREATE INDEX IF NOT EXISTS idx_resume_candidate     ON resumes(candidate_id);
