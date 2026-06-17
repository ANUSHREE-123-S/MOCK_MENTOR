-- ============================================================
-- MOCKMENTOR DATABASE SCHEMA
-- Smart Interview Preparation & Performance Analytics System
-- ============================================================

CREATE DATABASE IF NOT EXISTS mockmentor_db;
USE mockmentor_db;

-- ============================================================
-- TABLE 1: candidates
-- Stores registered student/candidate information
-- ============================================================
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    college VARCHAR(200),
    skills TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

-- ============================================================
-- TABLE 2: admins
-- Stores admin login credentials
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- ============================================================
-- TABLE 3: topics
-- Stores interview topic categories (normalized)
-- ============================================================
CREATE TABLE IF NOT EXISTS topics (
    topic_id INT AUTO_INCREMENT PRIMARY KEY,
    topic_name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================
-- TABLE 4: difficulty_levels
-- Normalized table for difficulty levels
-- ============================================================
CREATE TABLE IF NOT EXISTS difficulty_levels (
    difficulty_id INT AUTO_INCREMENT PRIMARY KEY,
    difficulty_name VARCHAR(50) NOT NULL UNIQUE
);

-- ============================================================
-- TABLE 5: questions
-- Stores interview questions (FK to topics, difficulty_levels)
-- ============================================================
CREATE TABLE IF NOT EXISTS questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    difficulty_id INT NOT NULL,
    question_text TEXT NOT NULL,
    sample_answer TEXT,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE,
    FOREIGN KEY (difficulty_id) REFERENCES difficulty_levels(difficulty_id) ON DELETE CASCADE,
    INDEX idx_topic (topic_id),
    INDEX idx_difficulty (difficulty_id)
);

-- ============================================================
-- TABLE 6: interviews
-- Records each mock interview session
-- ============================================================
CREATE TABLE IF NOT EXISTS interviews (
    interview_id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    topic_id INT NOT NULL,
    interview_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_score DECIMAL(5,2) DEFAULT 0,
    feedback TEXT,
    interview_duration INT DEFAULT 0,  -- duration in seconds
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE,
    INDEX idx_candidate (candidate_id)
);

-- ============================================================
-- TABLE 7: responses
-- Stores each answer given during an interview
-- ============================================================
CREATE TABLE IF NOT EXISTS responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL,
    question_id INT NOT NULL,
    user_answer TEXT,
    score DECIMAL(4,2) DEFAULT 0,
    time_taken INT DEFAULT 0,  -- time in seconds
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 8: interview_feedback
-- Stores detailed feedback for each interview
-- ============================================================
CREATE TABLE IF NOT EXISTS interview_feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL UNIQUE,
    technical_score DECIMAL(4,2) DEFAULT 0,
    communication_score DECIMAL(4,2) DEFAULT 0,
    confidence_score DECIMAL(4,2) DEFAULT 0,
    suggestions TEXT,
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 9: leaderboard
-- Stores rankings for all candidates
-- ============================================================
CREATE TABLE IF NOT EXISTS leaderboard (
    leaderboard_id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL UNIQUE,
    average_score DECIMAL(5,2) DEFAULT 0,
    rank_position INT DEFAULT 0,
    total_interviews INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 10: recommendations
-- Stores weak topic recommendations per candidate
-- ============================================================
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    topic_id INT NOT NULL,
    recommendation_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
);

-- ============================================================
-- SEED DATA: difficulty_levels
-- ============================================================
INSERT INTO difficulty_levels (difficulty_name) VALUES
('Easy'), ('Medium'), ('Hard');

-- ============================================================
-- SEED DATA: topics
-- ============================================================
INSERT INTO topics (topic_name) VALUES
('DBMS'), ('Data Structures'), ('Algorithms'), ('Operating Systems'),
('Computer Networks'), ('Python'), ('Java'), ('Web Development'),
('System Design'), ('SQL');

-- ============================================================
-- SEED DATA: admins (password = "admin123" hashed)
-- ============================================================
INSERT INTO admins (username, password) VALUES
('admin', 'pbkdf2:sha256:600000$rF8K2mNpQwXvYzLd$a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2');

-- ============================================================
-- SEED DATA: questions (sample questions per topic)
-- ============================================================
INSERT INTO questions (topic_id, difficulty_id, question_text, sample_answer) VALUES
-- DBMS Easy
(1, 1, 'What is a Primary Key?', 'A Primary Key is a column (or set of columns) in a table that uniquely identifies each row. It cannot be NULL and must be unique.'),
(1, 1, 'What is a Foreign Key?', 'A Foreign Key is a column that creates a link between two tables. It references the Primary Key of another table, ensuring referential integrity.'),
(1, 1, 'What is normalization?', 'Normalization is the process of organizing a database to reduce redundancy and improve data integrity by dividing large tables into smaller related ones.'),
-- DBMS Medium
(1, 2, 'Explain the difference between INNER JOIN and LEFT JOIN.', 'INNER JOIN returns only matching rows from both tables. LEFT JOIN returns all rows from the left table plus matching rows from the right table; unmatched rows show NULL.'),
(1, 2, 'What are ACID properties?', 'ACID stands for Atomicity (all or nothing), Consistency (data remains valid), Isolation (concurrent transactions do not interfere), Durability (committed data is permanent).'),
-- DBMS Hard
(1, 3, 'Explain 3NF with an example.', '3NF (Third Normal Form) requires that a table is in 2NF and no non-key attribute is transitively dependent on the primary key. Example: Separating Student, Course, and Instructor tables.'),

-- Data Structures Easy
(2, 1, 'What is a Stack?', 'A Stack is a linear data structure that follows LIFO (Last In, First Out) principle. Elements are added and removed from the same end called the top.'),
(2, 1, 'What is a Queue?', 'A Queue is a linear data structure that follows FIFO (First In, First Out) principle. Elements are added at the rear and removed from the front.'),
-- Data Structures Medium
(2, 2, 'Explain Binary Search Tree (BST).', 'A BST is a binary tree where left child < parent < right child. Search, insert, delete operations take O(log n) on average.'),
(2, 2, 'What is a Hash Table?', 'A Hash Table stores key-value pairs using a hash function to compute the index. Average O(1) for insert, delete, and search operations.'),
-- Data Structures Hard
(2, 3, 'Explain AVL Tree and its rotations.', 'AVL Tree is a self-balancing BST where height difference of left and right subtrees is at most 1. Rotations (LL, RR, LR, RL) maintain balance after insertion/deletion.'),

-- Algorithms Easy
(3, 1, 'What is Bubble Sort?', 'Bubble Sort repeatedly swaps adjacent elements if they are in the wrong order. Time complexity is O(n²). It is simple but inefficient for large datasets.'),
(3, 1, 'What is Binary Search?', 'Binary Search finds an element in a sorted array by repeatedly dividing the search interval in half. Time complexity is O(log n).'),
-- Algorithms Medium
(3, 2, 'Explain Quick Sort algorithm.', 'Quick Sort selects a pivot and partitions the array so that elements smaller than pivot go left and larger go right, then recursively sorts both halves. Average O(n log n).'),
(3, 2, 'What is Dynamic Programming?', 'Dynamic Programming solves problems by breaking them into overlapping subproblems, solving each once, and storing results (memoization or tabulation) to avoid redundant computation.'),
-- Algorithms Hard
(3, 3, 'Explain Dijkstra algorithm with complexity.', "Dijkstra's algorithm finds the shortest path from source to all vertices in a weighted graph. Uses a priority queue. Time complexity is O((V+E) log V) with min-heap."),

-- OS Easy
(4, 1, 'What is a Process?', 'A process is a program in execution. It includes the program code, current activity, stack, data section, and heap. Each process has its own address space.'),
(4, 2, 'What is Deadlock?', 'Deadlock is a situation where two or more processes are waiting for each other to release resources, causing all of them to be stuck indefinitely.'),

-- Python Easy
(6, 1, 'What is a list comprehension in Python?', 'List comprehension is a concise way to create lists. Example: [x*2 for x in range(5)] creates [0,2,4,6,8]. It is faster than a traditional for loop.'),
(6, 1, 'What is the difference between list and tuple?', 'Lists are mutable (can be changed) and use square brackets. Tuples are immutable (cannot be changed) and use parentheses. Tuples are faster and safer for fixed data.'),
(6, 2, 'Explain decorators in Python.', 'Decorators are functions that modify the behavior of another function. They use the @decorator syntax. Common examples are @staticmethod, @classmethod, and custom logging decorators.'),

-- SQL Medium
(10, 2, 'Write a SQL query to find the second highest salary.', 'SELECT MAX(salary) FROM employees WHERE salary < (SELECT MAX(salary) FROM employees); OR using DENSE_RANK().'),
(10, 2, 'What is the difference between WHERE and HAVING?', 'WHERE filters rows before grouping; it cannot use aggregate functions. HAVING filters groups after GROUP BY; it can use aggregate functions like COUNT, SUM, AVG.'),
(10, 3, 'Explain indexing and when to use it.', 'An index is a data structure that improves query speed. Use it on frequently searched columns. It speeds up SELECT but slows down INSERT/UPDATE/DELETE due to index maintenance.');

-- ============================================================
-- SEED DATA: sample candidates
-- ============================================================
INSERT INTO candidates (name, email, password, college, skills) VALUES
('Arjun Sharma', 'arjun@example.com', 'pbkdf2:sha256:600000$demo$hashvalue1', 'IIT Delhi', 'Python, DBMS, DSA'),
('Priya Patel', 'priya@example.com', 'pbkdf2:sha256:600000$demo$hashvalue2', 'NIT Trichy', 'Java, Algorithms, SQL'),
('Rahul Verma', 'rahul@example.com', 'pbkdf2:sha256:600000$demo$hashvalue3', 'BITS Pilani', 'C++, OS, Networks'),
('Sneha Reddy', 'sneha@example.com', 'pbkdf2:sha256:600000$demo$hashvalue4', 'VIT Vellore', 'Python, Web Dev, SQL'),
('Karan Mehta', 'karan@example.com', 'pbkdf2:sha256:600000$demo$hashvalue5', 'DTU Delhi', 'Java, DSA, System Design');

-- ============================================================
-- IMPORTANT SQL QUERIES (for reference - used in backend)
-- ============================================================

-- Top 5 students by average score:
-- SELECT c.name, l.average_score, l.rank_position
-- FROM leaderboard l JOIN candidates c ON l.candidate_id = c.candidate_id
-- ORDER BY l.rank_position LIMIT 5;

-- Weakest topic for a candidate:
-- SELECT t.topic_name, AVG(r.score) as avg_score
-- FROM responses r
-- JOIN interviews i ON r.interview_id = i.interview_id
-- JOIN questions q ON r.question_id = q.question_id
-- JOIN topics t ON q.topic_id = t.topic_id
-- WHERE i.candidate_id = ?
-- GROUP BY t.topic_name ORDER BY avg_score ASC LIMIT 1;

-- Topic-wise performance:
-- SELECT t.topic_name, AVG(i.total_score) as avg_score, COUNT(i.interview_id) as total
-- FROM interviews i JOIN topics t ON i.topic_id = t.topic_id
-- WHERE i.candidate_id = ?
-- GROUP BY t.topic_name;

-- Leaderboard ranking:
-- SELECT c.name, c.college, AVG(i.total_score) as avg_score, COUNT(i.interview_id) as interviews
-- FROM candidates c LEFT JOIN interviews i ON c.candidate_id = i.candidate_id
-- GROUP BY c.candidate_id ORDER BY avg_score DESC;
