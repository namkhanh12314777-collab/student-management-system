import sqlite3
import getpass
import os
import sys
from datetime import datetime

class StudentManagementSystem:
    def __init__(self):
        self.db_name = "management_system.db"
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.current_user = None
        self.setup_database()

    def setup_database(self):
        """Initialize DB structure if not exists (Based on Design_Database)"""
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS User (
                AccountID TEXT PRIMARY KEY,
                UserName TEXT UNIQUE,
                PassWord TEXT,
                FullName TEXT,
                Sex TEXT CHECK(Sex IN ('Male', 'Female', 'Other')),
                YearOfBirth INTEGER CHECK(YearOfBirth BETWEEN 1900 AND 2100),
                Email TEXT UNIQUE,
                Role TEXT
            );
            CREATE TABLE IF NOT EXISTS Student (
                StudentID TEXT PRIMARY KEY,
                AccountID TEXT,
                Major TEXT,
                FOREIGN KEY(AccountID) REFERENCES User(AccountID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Teacher (
                TeacherID TEXT PRIMARY KEY,
                AccountID TEXT,
                InstituteName TEXT,
                FOREIGN KEY(AccountID) REFERENCES User(AccountID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Admin (
                AdminID TEXT PRIMARY KEY,
                AccountID TEXT,
                FOREIGN KEY(AccountID) REFERENCES User(AccountID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Subject (
                SubjectID TEXT PRIMARY KEY,
                SubjectName TEXT,
                Credits INTEGER CHECK(Credits > 0)
            );
            CREATE TABLE IF NOT EXISTS Course (
                CourseID TEXT PRIMARY KEY,
                SubjectID TEXT,
                TeacherID TEXT,
                ClassName TEXT,
                Year INTEGER,
                Semester INTEGER CHECK(Semester IN (1, 2)),
                ClassSize INTEGER DEFAULT 50,
                Description TEXT,
                FOREIGN KEY(SubjectID) REFERENCES Subject(SubjectID) ON DELETE CASCADE,
                FOREIGN KEY(TeacherID) REFERENCES Teacher(TeacherID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Schedule (
                ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
                CourseID TEXT,
                DayOfWeek INTEGER CHECK(DayOfWeek BETWEEN 1 AND 7),
                Start_Time TEXT,
                End_Time TEXT,
                Room TEXT,
                FOREIGN KEY(CourseID) REFERENCES Course(CourseID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Enrollment (
                EnrollID INTEGER PRIMARY KEY AUTOINCREMENT,
                CourseID TEXT,
                StudentID TEXT,
                Status TEXT,
                RegisterDate TEXT,
                Grade REAL,
                FOREIGN KEY(CourseID) REFERENCES Course(CourseID) ON DELETE CASCADE,
                FOREIGN KEY(StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE
            );
        ''')
        self.cursor.executescript('''
            CREATE INDEX IF NOT EXISTS idx_enrollment_course ON Enrollment(CourseID);
            CREATE INDEX IF NOT EXISTS idx_enrollment_student ON Enrollment(StudentID);
        ''')
        # Create default admin account if DB is empty
        self.cursor.execute("SELECT COUNT(*) FROM User")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO User VALUES ('ACC001','admin','admin123','System Admin','Male','1990','admin@uth.edu.vn','admin')")
            self.cursor.execute("INSERT INTO Admin VALUES ('ADM001','ACC001')")
            self.conn.commit()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _is_valid_time_format(self, time_str: str) -> bool:
        """Check valid HH:MM format (24h)"""
        if not time_str or ':' not in time_str:
            return False
        try:
            hh, mm = map(int, time_str.split(':'))
            return 0 <= hh <= 23 and 0 <= mm <= 59
        except:
            return False

    def _is_end_after_start(self, start: str, end: str) -> bool:
        """Compare end time > start time"""
        try:
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
            start_min = sh * 60 + sm
            end_min = eh * 60 + em
            return end_min > start_min
        except:
            return False

    # ==========================================
    # 2. USE-CASE: LOGIN
    # ==========================================
    def login(self):
        while True:
            self.clear_screen()
            print("====================================")
            print("   STUDENT MANAGEMENT SYSTEM - UTH")
            print("====================================")
            print("1. Login")
            print("2. Exit")
            choice = input("\nChoose: ")
            
            if choice == '2': sys.exit()
            if choice == '1':
                username = input("Username: ")
                password = getpass.getpass("Password: ") # Requirement 2.3: Hide password
                
                query = "SELECT * FROM User WHERE UserName = ? AND PassWord = ?"
                user = self.cursor.execute(query, (username, password)).fetchone()
                
                if user:
                    self.current_user = dict(user)
                    print(f"\n[OK]: Welcome {self.current_user['FullName']}!")
                    input("Press Enter to enter the system..."); return True
                else:
                    print("\n[Error]: Incorrect username or password!")
                    # Skip choice 2, always try again
                    input("Press Enter to try again...")

    # ==========================================
    # 3. USE-CASE: LOGOUT
    # ==========================================
    def logout(self):
        confirm = input("\nAre you sure you want to log out? (Y/N): ").upper()
        if confirm == 'Y':
            self.current_user = None
            print("[Notification]: Logged out."); input()
            return True
        return False

    # ==========================================
    # 4. USE-CASE: CHANGE PASSWORD
    # ==========================================
    def change_password(self):
        old_pw = getpass.getpass("Current password: ")
        if old_pw != self.current_user['PassWord']:
            print("[Error]: Incorrect old password!"); input(); return
        
        new_pw = getpass.getpass("New password (min 6 characters): ")
        if len(new_pw) < 6:
            print("[Error]: Password too short!"); input(); return
            
        confirm = getpass.getpass("Confirm new password: ")
        if new_pw == confirm:
            self.cursor.execute("UPDATE User SET PassWord=? WHERE AccountID=?", (new_pw, self.current_user['AccountID']))
            self.conn.commit()
            self.current_user['PassWord'] = new_pw
            print("[Success]: Password changed."); input()
        else:
            print("[Error]: Passwords do not match!"); input()

    # ==========================================
    # 5. USE-CASE: VIEW PROFILE
    # ==========================================
    def view_profile(self):
        self.clear_screen()
        u = self.current_user
        print(f"--- PERSONAL INFORMATION ---")
        print(f"Username: {u['UserName']}\nFull Name: {u['FullName']}\nEmail: {u['Email']}\nRole: {u['Role']}")
        input("\nPress Enter to return...")

    # ==========================================
    # ADMIN USE-CASES (11, 12, 13, 14, 15)
    # ==========================================
    def manage_users(self):
        """Manage users (Admin): View, Add, Edit, Delete Student/Teacher/Admin accounts"""
        while True:
            self.clear_screen()
            print("====================================")
            print("   USER MANAGEMENT")
            print("====================================")
            print("1. View user list")
            print("2. Add new user")
            print("3. Update user information")
            print("4. Delete user")
            print("5. Return to Admin menu")
            choice = input("\nChoose function: ").strip()

            if choice == '5':
                break

            # Select user type
            print("\nAccount type:")
            print("  1. Student")
            print("  2. Teacher")
            print("  3. Admin")
            role_choice = input("Choose type (1-3): ").strip()
            role_map = {'1': 'student', '2': 'teacher', '3': 'admin'}
            if role_choice not in role_map:
                print("[Error]: Invalid choice!")
                input("Press Enter to continue...")
                continue
            selected_role = role_map[role_choice]

            if choice == '1':
                # View list
                users = self.cursor.execute("""
                    SELECT u.AccountID, u.UserName, u.FullName, u.Email, u.Sex, u.YearOfBirth
                    FROM User u
                    WHERE u.Role = ?
                    ORDER BY u.AccountID
                """, (selected_role,)).fetchall()

                print(f"\n--- {selected_role.upper()} LIST ---")
                if not users:
                    print(f"No {selected_role} in the system yet.")
                else:
                    for u in users:
                        print(f"  • {u['AccountID']} | {u['UserName']} | {u['FullName']} | {u['Email']}")
                input("\nPress Enter to continue...")

            elif choice == '2':
                # Add new user
                print(f"\n--- ADD NEW {selected_role.upper()} ---")
                while True:
                    account_id = input("AccountID (e.g., ACCxxx): ").strip()
                    if not account_id:
                        print("[Error]: AccountID cannot be empty!")
                        continue
                    if self.cursor.execute("SELECT 1 FROM User WHERE AccountID = ?", (account_id,)).fetchone():
                        print("[Error]: AccountID already exists!")
                        continue
                    break

                username = input("Username: ").strip()
                if self.cursor.execute("SELECT 1 FROM User WHERE UserName = ?", (username,)).fetchone():
                    print("[Error]: Username already exists!")
                    input("Press Enter...")
                    continue

                full_name = input("Full name: ").strip()
                password = input("Default password (will be encrypted later): ") or "123456"
                sex = input("Gender (Male/Female/Other): ").strip() or "Male"
                yob = input("Year of birth (YYYY): ").strip() or "2000"
                email = input("Email: ").strip() or f"{username}@uth.edu.vn"

                confirm = input("\nConfirm adding user? (Y/N): ").upper()
                if confirm != 'Y':
                    print("Operation canceled.")
                    input("Press Enter...")
                    continue

                try:
                    self.cursor.execute("""
                        INSERT INTO User (AccountID, UserName, PassWord, FullName, Sex, YearOfBirth, Email, Role)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (account_id, username, password, full_name, sex, yob, email, selected_role))

                    if selected_role == 'student':
                        student_id = input("StudentID (e.g., 221xxxx): ").strip()
                        major = input("Major (default IT): ").strip() or "IT"
                        self.cursor.execute("INSERT INTO Student (StudentID, AccountID, Major) VALUES (?, ?, ?)",
                                            (student_id, account_id, major))
                    elif selected_role == 'teacher':
                        teacher_id = input("TeacherID (e.g., GVxxx): ").strip()
                        institute = input("Institute/Department: ").strip() or "Information Technology"
                        self.cursor.execute("INSERT INTO Teacher (TeacherID, AccountID, InstituteName) VALUES (?, ?, ?)",
                                            (teacher_id, account_id, institute))
                    elif selected_role == 'admin':
                        admin_id = input("AdminID (e.g., ADMxxx): ").strip()
                        self.cursor.execute("INSERT INTO Admin (AdminID, AccountID) VALUES (?, ?)",
                                            (admin_id, account_id))

                    self.conn.commit()
                    print("[Success]: New user added.")
                except sqlite3.Error as e:
                    print(f"[Database error]: {e}")
                input("Press Enter to continue...")

            elif choice == '3':
                # Update information
                print(f"\n--- UPDATE {selected_role.upper()} ---")
                account_id = input("Enter AccountID to edit: ").strip()
                user = self.cursor.execute("SELECT * FROM User WHERE AccountID = ? AND Role = ?",
                                           (account_id, selected_role)).fetchone()

                if not user:
                    print("[Error]: User with this AccountID not found!")
                    input("Press Enter...")
                    continue

                print("\nCurrent information:")
                print(f"  Username    : {user['UserName']}")
                print(f"  Full Name   : {user['FullName']}")
                print(f"  Email       : {user['Email']}")
                print(f"  Gender      : {user['Sex']}")
                print(f"  Year of birth: {user['YearOfBirth']}")

                new_username = input(f"New Username (Enter to keep): ").strip() or user['UserName']
                new_fullname = input(f"New full name (Enter to keep): ").strip() or user['FullName']
                new_email = input(f"New Email (Enter to keep): ").strip() or user['Email']
                new_sex = input(f"New Gender (Enter to keep): ").strip() or user['Sex']
                new_yob = input(f"New year of birth (Enter to keep): ").strip() or user['YearOfBirth']

                confirm = input("\nConfirm update? (Y/N): ").upper()
                if confirm == 'Y':
                    self.cursor.execute("""
                        UPDATE User SET 
                            UserName = ?, FullName = ?, Email = ?, Sex = ?, YearOfBirth = ?
                        WHERE AccountID = ?
                    """, (new_username, new_fullname, new_email, new_sex, new_yob, account_id))
                    self.conn.commit()
                    print("[Success]: Information updated.")
                else:
                    print("Operation canceled.")
                input("Press Enter...")

            elif choice == '4':
                # Delete user
                print(f"\n--- DELETE {selected_role.upper()} ---")
                account_id = input("Enter AccountID to delete: ").strip()
                user = self.cursor.execute("SELECT FullName FROM User WHERE AccountID = ? AND Role = ?",
                                           (account_id, selected_role)).fetchone()

                if not user:
                    print("[Error]: User not found!")
                    input("Press Enter...")
                    continue

                # Check constraints (e.g., teacher teaching classes, student with grades...)
                if selected_role == 'teacher':
                    count = self.cursor.execute("SELECT COUNT(*) FROM Course WHERE TeacherID IN (SELECT TeacherID FROM Teacher WHERE AccountID=?)",
                                                (account_id,)).fetchone()[0]
                    if count > 0:
                        print(f"[Error]: Cannot delete! This teacher is teaching {count} course sections.")
                        input("Press Enter...")
                        continue
                elif selected_role == 'student':
                    count = self.cursor.execute("SELECT COUNT(*) FROM Enrollment WHERE StudentID IN (SELECT StudentID FROM Student WHERE AccountID=?)",
                                                (account_id,)).fetchone()[0]
                    if count > 0:
                        print(f"[Error]: Cannot delete! This student has registered for {count} courses.")
                        input("Press Enter...")
                        continue

                confirm = input(f"Confirm DELETE user '{user['FullName']}' (AccountID: {account_id})? (Y/N): ").upper()
                if confirm == 'Y':
                    # ON DELETE CASCADE will automatically delete related records in Student/Teacher/Admin
                    self.cursor.execute("DELETE FROM User WHERE AccountID = ?", (account_id,))
                    self.conn.commit()
                    print("[Success]: User deleted.")
                else:
                    print("Delete operation canceled.")
                input("Press Enter...")

            else:
                print("[Error]: Invalid function!")
                input("Press Enter...")

    def manage_subjects(self):
        """Use-case 12: Manage Subjects - Admin view, add, edit, delete subjects in the system"""
        while True:
            self.clear_screen()
            print("====================================")
            print("   SUBJECT MANAGEMENT")
            print("====================================")
            print("1. View subject list")
            print("2. Add new subject")
            print("3. Update subject information")
            print("4. Delete subject")
            print("5. Return to Admin menu")
            choice = input("\nChoose function: ").strip()

            if choice == '5':
                break

            if choice == '1':
                # View subject list
                subjects = self.cursor.execute("""
                    SELECT SubjectID, SubjectName, Credits 
                    FROM Subject 
                    ORDER BY SubjectID
                """).fetchall()

                print("\n--- SUBJECT LIST ---")
                if not subjects:
                    print("No subjects in the system yet.")
                else:
                    print(" SubjectID  Subject Name                         Credits")
                    print("-" * 60)
                    for s in subjects:
                        print(f" {s['SubjectID']:<10} {s['SubjectName']:<35} {s['Credits']}")
                input("\nPress Enter to continue...")

            elif choice == '2':
                # Add new subject
                print("\n--- ADD NEW SUBJECT ---")
                while True:
                    sid = input("Enter subject code (SubjectID): ").strip()
                    if not sid:
                        print("[Error]: Subject code cannot be empty!")
                        continue
                    if self.cursor.execute("SELECT 1 FROM Subject WHERE SubjectID = ?", (sid,)).fetchone():
                        print("[Error]: Subject code already exists! Please enter a different code.")
                        continue
                    break

                name = input("Enter subject name: ").strip()
                if not name:
                    print("[Error]: Subject name cannot be empty!")
                    input("Press Enter...")
                    continue

                while True:
                    cr_input = input("Enter credits: ").strip()
                    try:
                        credits = int(cr_input)
                        if credits <= 0 or credits > 10:  # reasonable limit
                            print("[Error]: Credits must be from 1 to 10!")
                            continue
                        break
                    except ValueError:
                        print("[Error]: Please enter a valid integer!")

                confirm = input(f"\nConfirm adding subject: {sid} - {name} ({credits} credits)? (Y/N): ").upper()
                if confirm == 'Y':
                    try:
                        self.cursor.execute(
                            "INSERT INTO Subject (SubjectID, SubjectName, Credits) VALUES (?, ?, ?)",
                            (sid, name, credits)
                        )
                        self.conn.commit()
                        print("[Success]: New subject added.")
                    except sqlite3.Error as e:
                        print(f"[Database error]: {e}")
                else:
                    print("Add operation canceled.")
                input("Press Enter to continue...")

            elif choice == '3':
                # Update subject
                print("\n--- UPDATE SUBJECT ---")
                sid = input("Enter subject code to edit: ").strip()
                subject = self.cursor.execute(
                    "SELECT SubjectName, Credits FROM Subject WHERE SubjectID = ?",
                    (sid,)
                ).fetchone()

                if not subject:
                    print("[Error]: Subject with this code not found!")
                    input("Press Enter...")
                    continue

                print("\nCurrent information:")
                print(f"  Subject code: {sid}")
                print(f"  Subject name: {subject['SubjectName']}")
                print(f"  Credits     : {subject['Credits']}")

                new_name = input(f"New subject name (Enter to keep '{subject['SubjectName']}'): ").strip()
                new_name = new_name if new_name else subject['SubjectName']

                while True:
                    cr_input = input(f"New credits (Enter to keep {subject['Credits']}): ").strip()
                    if cr_input == "":
                        new_credits = subject['Credits']
                        break
                    try:
                        new_credits = int(cr_input)
                        if new_credits <= 0 or new_credits > 10:
                            print("[Error]: Credits must be from 1 to 10!")
                            continue
                        break
                    except ValueError:
                        print("[Error]: Please enter a valid integer.")

                confirm = input("\nConfirm updating subject? (Y/N): ").upper()
                if confirm == 'Y':
                    try:
                        self.cursor.execute(
                            "UPDATE Subject SET SubjectName = ?, Credits = ? WHERE SubjectID = ?",
                            (new_name, new_credits, sid)
                        )
                        self.conn.commit()
                        print("[Success]: Subject information updated.")
                    except sqlite3.Error as e:
                        print(f"[Database error]: {e}")
                else:
                    print("Update operation canceled.")
                input("Press Enter to continue...")

            elif choice == '4':
                # Delete subject
                print("\n--- DELETE SUBJECT ---")
                sid = input("Enter subject code to delete: ").strip()
                subject = self.cursor.execute(
                    "SELECT SubjectName FROM Subject WHERE SubjectID = ?",
                    (sid,)
                ).fetchone()

                if not subject:
                    print("[Error]: Subject with this code not found!")
                    input("Press Enter...")
                    continue

                # Check constraint: cannot delete if there are course sections
                course_count = self.cursor.execute(
                    "SELECT COUNT(*) FROM Course WHERE SubjectID = ?",
                    (sid,)
                ).fetchone()[0]

                if course_count > 0:
                    print(f"[Error]: Cannot delete! This subject has {course_count} course sections.")
                    input("Press Enter...")
                    continue

                confirm = input(f"Confirm DELETE subject '{subject['SubjectName']}' (code {sid})? (Y/N): ").upper()
                if confirm == 'Y':
                    try:
                        self.cursor.execute("DELETE FROM Subject WHERE SubjectID = ?", (sid,))
                        self.conn.commit()
                        print("[Success]: Subject deleted.")
                    except sqlite3.Error as e:
                        print(f"[Database error]: {e}")
                else:
                    print("Delete operation canceled.")
                input("Press Enter to continue...")

            else:
                print("[Error]: Invalid function!")
                input("Press Enter...")

    def manage_course_sections(self):
        """Use-case 13: Manage Course Sections - Admin organizes open classes for subjects"""
        while True:
            self.clear_screen()
            print("====================================")
            print("   COURSE SECTION MANAGEMENT")
            print("====================================")
            print("1. View course section list")
            print("2. Add new course section")
            print("3. Update course section information")
            print("4. Delete course section")
            print("5. Add student to class")
            print("6. Return to Admin menu")
            choice = input("\nChoose function: ").strip()

            if choice == '6':
                break

            if choice == '1':
                # View course section list
                courses = self.cursor.execute("""
                    SELECT c.CourseID, c.ClassName, c.Year, c.Semester, c.ClassSize, c.Description,
                           s.SubjectID, s.SubjectName, t.TeacherID, u.FullName AS TeacherName
                    FROM Course c
                    JOIN Subject s ON c.SubjectID = s.SubjectID
                    LEFT JOIN Teacher t ON c.TeacherID = t.TeacherID
                    LEFT JOIN User u ON t.AccountID = u.AccountID
                    ORDER BY c.Year DESC, c.Semester DESC, c.CourseID
                """).fetchall()

                print("\n--- COURSE SECTION LIST ---")
                if not courses:
                    print("No course sections in the system yet.")
                else:
                    print(" CourseID    Class     Subject                  Year  Sem  ClassSize  Teacher      Description")
                    print("-" * 80)
                    for c in courses:
                        teacher = f"{c['TeacherName'] or 'Not assigned'}"[:25]
                        print(f" {c['CourseID']:<11} {c['ClassName']:<9} {c['SubjectName'][:20]:<20} {c['Year']}  {c['Semester']} {c['ClassSize']}  {teacher} {c['Description']}")
                input("\nPress Enter to continue...")

            elif choice in ('2', '3', '4'):
                # Operations require selecting subject first (per sub-event flow)
                print("\n--- Select subject first ---")
                subjects = self.cursor.execute("SELECT SubjectID, SubjectName FROM Subject ORDER BY SubjectID").fetchall()
                if not subjects:
                    print("[Error]: No subjects in the system yet. Please add subjects first!")
                    input("Press Enter...")
                    continue

                print("Subject list:")
                for i, sub in enumerate(subjects, 1):
                    print(f" {i}. {sub['SubjectID']} - {sub['SubjectName']}")
                try:
                    idx = int(input("\nChoose subject sequence number: ")) - 1
                    if idx < 0 or idx >= len(subjects):
                        raise ValueError
                    selected_subject_id = subjects[idx]['SubjectID']
                except:
                    print("[Error]: Invalid choice!")
                    input("Press Enter...")
                    continue

                if choice == '2':
                    # Add new course section
                    print(f"\n--- ADD NEW COURSE SECTION for subject {selected_subject_id} ---")
                    while True:
                        course_id = input("Course section code (CourseID): ").strip()
                        if not course_id:
                            print("[Error]: Class code cannot be empty!")
                            continue
                        if self.cursor.execute("SELECT 1 FROM Course WHERE CourseID = ?", (course_id,)).fetchone():
                            print("[Error]: Course section code already exists!")
                            continue
                        break

                    class_name = input("Class name (e.g., CNTT K20A): ").strip()
                    if not class_name:
                        print("[Error]: Class name cannot be empty!")
                        continue

                    while True:
                        try:
                            year = int(input("Academic year (e.g., 2025): ").strip())
                            if year < 2000 or year > 2100:
                                print("[Error]: Invalid academic year!")
                                continue
                            break
                        except ValueError:
                            print("[Error]: Please enter an integer!")

                    while True:
                        try:
                            semester = int(input("Semester (1 or 2): ").strip())
                            if semester not in (1, 2):
                                print("[Error]: Semester can only be 1 or 2!")
                                continue
                            break
                        except ValueError:
                            print("[Error]: Please enter 1 or 2!")

                    # Add ClassSize
                    while True:
                        class_size_input = input("Class capacity (ClassSize, default 50): ").strip()
                        if not class_size_input:
                            class_size = 50
                            break
                        try:
                            class_size = int(class_size_input)
                            if class_size <= 0:
                                print("[Error]: Capacity must be greater than 0!")
                                continue
                            break
                        except ValueError:
                            print("[Error]: Please enter an integer!")

                    # Add Description
                    description = input("Class description (Description, Enter to skip): ").strip() or None

                    # Select teacher (optional)
                    teachers = self.cursor.execute("""
                        SELECT t.TeacherID, u.FullName 
                        FROM Teacher t JOIN User u ON t.AccountID = u.AccountID 
                        ORDER BY u.FullName
                    """).fetchall()
                    if not teachers:
                        print("[Notification]: No teachers in the system yet. Cannot assign teacher.")
                        teacher_id = None
                    else:
                        print("\nTeacher list:")
                        for i, t in enumerate(teachers, 1):
                            print(f" {i}. {t['TeacherID']} - {t['FullName']}")
                        teacher_choice = input("\nEnter teacher sequence number (Enter to skip): ").strip()
                        if teacher_choice:
                            try:
                                idx = int(teacher_choice) - 1
                                if 0 <= idx < len(teachers):
                                    teacher_id = teachers[idx]['TeacherID']
                                else:
                                    print("[Error]: Invalid choice! Teacher not assigned.")
                                    teacher_id = None
                            except ValueError:
                                print("[Error]: Invalid input! Teacher not assigned.")
                                teacher_id = None
                        else:
                            teacher_id = None

                    confirm = input(f"\nConfirm adding course section {course_id} - {class_name} for subject {selected_subject_id}? (Y/N): ").upper()
                    if confirm == 'Y':
                        try:
                            self.cursor.execute("""
                                INSERT INTO Course (CourseID, SubjectID, TeacherID, ClassName, Year, Semester, ClassSize, Description)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (course_id, selected_subject_id, teacher_id, class_name, year, semester, class_size, description))
                            self.conn.commit()
                            print("[Success]: New course section added.")
                        except sqlite3.Error as e:
                            print(f"[Database error]: {e}")
                    else:
                        print("Operation canceled.")
                    input("Press Enter to continue...")

                elif choice == '3':
                    # Update course section information
                    print("\n--- Select course section to update ---")
                    courses = self.cursor.execute("""
                        SELECT c.CourseID, c.ClassName, c.Year, c.Semester, t.TeacherID, u.FullName AS TeacherName, c.ClassSize, c.Description
                        FROM Course c
                        LEFT JOIN Teacher t ON c.TeacherID = t.TeacherID
                        LEFT JOIN User u ON t.AccountID = u.AccountID
                        WHERE c.SubjectID = ?
                        ORDER BY c.Year DESC, c.Semester DESC
                    """, (selected_subject_id,)).fetchall()

                    if not courses:
                        print("[Error]: No course sections for this subject yet.")
                        input("Press Enter...")
                        continue

                    print("\nCourse section list:")
                    for i, c in enumerate(courses, 1):
                        teacher = c['TeacherName'] or 'Not assigned'
                        print(f" {i}. {c['CourseID']} - {c['ClassName']} ({c['Year']} Sem{c['Semester']}) - Teacher: {teacher}")

                    try:
                        idx = int(input("\nChoose course sequence number: ")) - 1
                        if idx < 0 or idx >= len(courses):
                            raise ValueError
                        selected_course = courses[idx]
                        course_id = selected_course['CourseID']
                    except:
                        print("[Error]: Invalid choice!")
                        input("Press Enter...")
                        continue

                    print(f"\n--- UPDATE COURSE SECTION {course_id} ---")
                    print(f"Current class name: {selected_course['ClassName']}")
                    new_class_name = input("New class name (Enter to keep): ").strip() or selected_course['ClassName']

                    print(f"Current year: {selected_course['Year']}")
                    new_year_input = input("New year (Enter to keep): ").strip()
                    new_year = int(new_year_input) if new_year_input else selected_course['Year']

                    print(f"Current semester: {selected_course['Semester']}")
                    new_sem_input = input("New semester (1/2, Enter to keep): ").strip()
                    new_sem = int(new_sem_input) if new_sem_input else selected_course['Semester']

                    print(f"Current class size: {selected_course['ClassSize']}")
                    new_class_size_input = input("New class size (Enter to keep): ").strip()
                    new_class_size = int(new_class_size_input) if new_class_size_input else selected_course['ClassSize']

                    print(f"Current description: {selected_course['Description'] or 'None'}")
                    new_description = input("New description (Enter to keep): ").strip() or selected_course['Description']

                    # Update teacher
                    current_teacher = selected_course['TeacherName'] or 'None'
                    print(f"Current teacher: {current_teacher}")
                    teachers = self.cursor.execute("""
                        SELECT t.TeacherID, u.FullName 
                        FROM Teacher t JOIN User u ON t.AccountID = u.AccountID 
                        ORDER BY u.FullName
                    """).fetchall()

                    if teachers:
                        print("\nAvailable teachers:")
                        for i, t in enumerate(teachers, 1):
                            print(f" {i}. {t['TeacherID']} - {t['FullName']}")
                        teacher_choice = input("\nEnter new teacher sequence number (Enter to keep): ").strip()
                        if teacher_choice:
                            try:
                                idx = int(teacher_choice) - 1
                                if 0 <= idx < len(teachers):
                                    new_teacher_id = teachers[idx]['TeacherID']
                                else:
                                    print("[Error]: Invalid choice! Teacher unchanged.")
                                    new_teacher_id = selected_course['TeacherID']
                            except ValueError:
                                print("[Error]: Invalid input! Teacher unchanged.")
                                new_teacher_id = selected_course['TeacherID']
                        else:
                            new_teacher_id = selected_course['TeacherID']
                    else:
                        new_teacher_id = None

                    confirm = input("\nConfirm update? (Y/N): ").upper()
                    if confirm == 'Y':
                        try:
                            self.cursor.execute("""
                                UPDATE Course SET ClassName = ?, Year = ?, Semester = ?, TeacherID = ?, ClassSize = ?, Description = ?
                                WHERE CourseID = ?
                            """, (new_class_name, new_year, new_sem, new_teacher_id, new_class_size, new_description, course_id))
                            self.conn.commit()
                            print("[Success]: Course section updated.")
                        except sqlite3.Error as e:
                            print(f"[Database error]: {e}")
                    else:
                        print("Operation canceled.")
                    input("Press Enter to continue...")

                elif choice == '4':
                    # Delete course section
                    print("\n--- Select course section to delete ---")
                    courses = self.cursor.execute("""
                        SELECT c.CourseID, c.ClassName, c.Year, c.Semester
                        FROM Course c
                        WHERE c.SubjectID = ?
                        ORDER BY c.Year DESC, c.Semester DESC
                    """, (selected_subject_id,)).fetchall()

                    if not courses:
                        print("[Error]: No course sections for this subject yet.")
                        input("Press Enter...")
                        continue

                    print("\nCourse section list:")
                    for i, c in enumerate(courses, 1):
                        print(f" {i}. {c['CourseID']} - {c['ClassName']} ({c['Year']} Sem{c['Semester']})")

                    try:
                        idx = int(input("\nChoose course sequence number: ")) - 1
                        if idx < 0 or idx >= len(courses):
                            raise ValueError
                        selected_course = courses[idx]
                        course_id = selected_course['CourseID']
                        class_name = selected_course['ClassName']
                    except:
                        print("[Error]: Invalid choice!")
                        input("Press Enter...")
                        continue

                    # Check constraints: cannot delete if there are enrollments or schedules
                    enroll_count = self.cursor.execute("SELECT COUNT(*) FROM Enrollment WHERE CourseID = ?", (course_id,)).fetchone()[0]
                    sched_count = self.cursor.execute("SELECT COUNT(*) FROM Schedule WHERE CourseID = ?", (course_id,)).fetchone()[0]

                    if enroll_count > 0 or sched_count > 0:
                        print(f"[Error]: Cannot delete! This course has {enroll_count} enrollments and {sched_count} schedules.")
                        input("Press Enter...")
                        continue

                    confirm = input(f"Confirm DELETE course section {course_id} - {class_name}? (Y/N): ").upper()
                    if confirm == 'Y':
                        try:
                            self.cursor.execute("DELETE FROM Course WHERE CourseID = ?", (course_id,))
                            self.conn.commit()
                            print("[Success]: Course section deleted.")
                        except sqlite3.Error as e:
                            print(f"[Database error]: {e}")
                    else:
                        print("Operation canceled.")
                    input("Press Enter to continue...")

            elif choice == '5':
                # Add student to class
                print("\n--- ADD STUDENT TO CLASS ---")
                # Step 1: Select subject first
                subjects = self.cursor.execute("SELECT SubjectID, SubjectName FROM Subject ORDER BY SubjectID").fetchall()
                if not subjects:
                    print("[Error]: No subjects in the system yet. Please add subjects first!")
                    input("Press Enter...")
                    continue

                print("Subject list:")
                for i, sub in enumerate(subjects, 1):
                    print(f" {i}. {sub['SubjectID']} - {sub['SubjectName']}")
                try:
                    idx = int(input("\nChoose subject sequence number: ")) - 1
                    if idx < 0 or idx >= len(subjects):
                        raise ValueError
                    selected_subject_id = subjects[idx]['SubjectID']
                    selected_subject_name = subjects[idx]['SubjectName']
                except:
                    print("[Error]: Invalid choice!")
                    input("Press Enter...")
                    continue

                # Step 2: Select course section
                courses = self.cursor.execute("""
                    SELECT c.CourseID, c.ClassName, c.Year, c.Semester
                    FROM Course c
                    WHERE c.SubjectID = ?
                    ORDER BY c.Year DESC, c.Semester DESC
                """, (selected_subject_id,)).fetchall()

                if not courses:
                    print(f"[Error]: No course sections for subject {selected_subject_name} yet.")
                    input("Press Enter...")
                    continue

                print("\nCourse section list:")
                for i, c in enumerate(courses, 1):
                    print(f" {i}. {c['CourseID']} - {c['ClassName']} ({c['Year']} Sem{c['Semester']})")

                idx_input = input("\nEnter class sequence number (Enter to return): ").strip()
                if not idx_input:
                    print("Returned to menu.")
                    continue
                try:
                    idx = int(idx_input) - 1
                    if idx < 0 or idx >= len(courses):
                        raise ValueError
                    selected_course = courses[idx]
                    course_id = selected_course['CourseID']
                    class_name = selected_course['ClassName']
                except:
                    print("[Error]: Invalid choice!")
                    input("Press Enter...")
                    continue

                # Step 3: Display current students
                current = self.cursor.execute("""
                    SELECT s.StudentID, u.FullName
                    FROM Enrollment e
                    JOIN Student s ON e.StudentID = s.StudentID
                    JOIN User u ON s.AccountID = u.AccountID
                    WHERE e.CourseID = ?
                    ORDER BY s.StudentID
                """, (course_id,)).fetchall()

                print(f"\nCurrent students in class {course_id} - {class_name}:")
                if not current:
                    print("  No students yet.")
                else:
                    for st in current:
                        print(f"  • {st['StudentID']} - {st['FullName']}")

                # Step 4: Enter StudentID
                while True:
                    student_id = input("\nEnter StudentID to add (Enter to return): ").strip()
                    if not student_id:
                        print("Returned to menu.")
                        break

                    # Check if student exists
                    exists = self.cursor.execute("SELECT 1 FROM Student WHERE StudentID = ?", (student_id,)).fetchone()
                    if not exists:
                        print("[Error]: Student code does not exist! Enter again or Enter to return.")
                        continue

                    # Check if already registered for this class (define enrolled here)
                    enrolled = self.cursor.execute(
                        "SELECT 1 FROM Enrollment WHERE CourseID = ? AND StudentID = ?",
                        (course_id, student_id)
                    ).fetchone()

                    if enrolled:
                        print("[Error]: This student is already registered for this class! Enter again or Enter to return.")
                        continue

                    # Get student name
                    student_info = self.cursor.execute("""
                        SELECT u.FullName FROM Student s
                        JOIN User u ON s.AccountID = u.AccountID
                        WHERE s.StudentID = ?
                    """, (student_id,)).fetchone()

                    if not student_info:
                        print("[Error]: Unable to retrieve student information!")
                        continue

                    student_name = student_info['FullName']

                    confirm = input(f"\nConfirm ADD {student_id} - {student_name} to class {course_id} ({class_name})? (Y/N): ").upper()
                    if confirm == 'Y':
                        try:
                            self.cursor.execute(
                                "INSERT INTO Enrollment (CourseID, StudentID, Status, RegisterDate) VALUES (?, ?, ?, ?)",
                                (course_id, student_id, 'registered', datetime.now().strftime('%Y-%m-%d'))
                            )
                            self.conn.commit()
                            print(f"[Success]: Added student {student_id} to class {course_id}!")
                        except sqlite3.Error as e:
                            print(f"[Database error]: {e}")
                    else:
                        print("Operation canceled.")

                    break  # Exit after processing one student

                input("Press Enter to continue...")

            else:
                print("[Error]: Invalid function!")
                input("Press Enter...")

    def manage_schedules(self):
        """Use-case 14: Manage Class Schedules (Classroom Schedule Management) - Per exact specification"""
        while True:
            self.clear_screen()
            print("====================================")
            print("   SCHEDULE MANAGEMENT")
            print("====================================")
            print("1. View the class schedule")
            print("2. Add a new class schedule")
            print("3. Update the class schedule")
            print("4. Return to Admin menu")
            choice = input("\nChoose function: ").strip()

            if choice == '4':
                break

            # 3. The system displays the class list of sections
            print("\n--- COURSE SECTION LIST ---")
            courses = self.cursor.execute("""
                SELECT c.CourseID, c.ClassName, s.SubjectName, c.Year, c.Semester
                FROM Course c
                JOIN Subject s ON c.SubjectID = s.SubjectID
                ORDER BY c.Year DESC, c.Semester DESC, c.CourseID
            """).fetchall()

            if not courses:
                print("No course sections in the system yet.")
                input("Press Enter to continue...")
                continue

            print(" CourseID    Class     Subject                  Year  Sem")
            print("-" * 70)
            for c in courses:
                print(f" {c['CourseID']:<10} {c['ClassName']:<9} {c['SubjectName'][:25]:<25} {c['Year']}  {c['Semester']}")

            if choice not in ('1', '2', '3'):
                print("[Error]: Invalid function!")
                input("Press Enter...")
                continue

            if choice == '1':
                # View the class schedule - display all schedules
                schedules = self.cursor.execute("""
                    SELECT sch.ScheduleID, c.CourseID, c.ClassName, s.SubjectName,
                           sch.DayOfWeek, sch.Start_Time, sch.End_Time, sch.Room
                    FROM Schedule sch
                    JOIN Course c ON sch.CourseID = c.CourseID
                    JOIN Subject s ON c.SubjectID = s.SubjectID
                    ORDER BY c.CourseID, sch.DayOfWeek, sch.Start_Time
                """).fetchall()

                print("\n--- SCHEDULE LIST ---")
                if not schedules:
                    print("No schedules set yet.")
                else:
                    print(" SchID  CourseID   Class     Subject              Day  Start     End        Room")
                    print("-" * 90)
                    for sch in schedules:
                        print(f" {sch['ScheduleID']:<6} {sch['CourseID']:<10} {sch['ClassName']:<9} "
                              f"{sch['SubjectName'][:18]:<18} {sch['DayOfWeek']}    "
                              f"{sch['Start_Time']:<8} {sch['End_Time']:<9} {sch['Room'] or 'None'}")
                input("\nPress Enter to continue...")
                continue

            # 4-6. Admin selects add or update → enter section class code (CourseID) from keyboard
            action = "add" if choice == '2' else "update"
            while True:
                course_id = input(f"\nEnter course section code (CourseID) to {action} schedule: ").strip()
                if not course_id:
                    print("[Error]: Class code cannot be empty!")
                    continue
                course = self.cursor.execute("SELECT ClassName FROM Course WHERE CourseID = ?", (course_id,)).fetchone()
                if not course:
                    print("[Error]: Course not found")
                    retry = input("1. Try again | 2. Return to previous menu: ").strip()
                    if retry == '2':
                        break
                    continue
                selected_course_name = course['ClassName']
                break
            if not course:
                continue  # back to outer loop if broke out due to retry '2'

            if choice == '3':
                scheds = self.cursor.execute("""
                    SELECT ScheduleID, DayOfWeek, Start_Time, End_Time, Room
                    FROM Schedule WHERE CourseID = ? ORDER BY DayOfWeek, Start_Time
                """, (course_id,)).fetchall()

                if not scheds:
                    print("This class has no schedules yet.")
                    input("Press Enter...")
                    continue

                print("\nCurrent schedules for this class:")
                for i, s in enumerate(scheds, 1):
                    print(f" {i}. Day {s['DayOfWeek']} | {s['Start_Time']} - {s['End_Time']} | {s['Room'] or 'None'} (ID: {s['ScheduleID']})")

                try:
                    idx = int(input("\nChoose schedule sequence number to update: ")) - 1
                    if idx < 0 or idx >= len(scheds):
                        raise ValueError
                    sched_id = scheds[idx]['ScheduleID']
                except:
                    print("[Error]: Invalid choice!")
                    input("Press Enter...")
                    continue

            # 7. Enter class schedule information - COMMON LOOP
            while True:
                # Enter DayOfWeek
                try:
                    day_str = input("Day of the Week (1=Monday ... 7=Sunday): ").strip()
                    day = int(day_str)
                    if day < 1 or day > 7:
                        print("[Error]: Day must be from 1 to 7!")
                        continue
                except ValueError:
                    print("[Error]: Please enter a number from 1-7!")
                    continue

                # Enter Start Time
                start_time = input("Start Time (HH:MM): ").strip()
                if not self._is_valid_time_format(start_time):
                    print("[Error]: Invalid time format! (HH:MM)")
                    continue

                # Enter End Time
                end_time = input("End Time (HH:MM): ").strip()
                if not self._is_valid_time_format(end_time):
                    print("[Error]: Invalid time format!")
                    continue
                if not self._is_end_after_start(start_time, end_time):
                    print("[Error]: End time must be after start time!")
                    continue

                # Enter Room
                room = input("Classroom or Study Location: ").strip() or None

                # Confirm
                confirm = input(f"\nConfirm {action} schedule for class {course_id}?\n"
                                f"  Day: {day}\n  Time: {start_time} - {end_time}\n  Room: {room or 'None'}\n(Y/N): ").upper()
                if confirm != 'Y':
                    print("Operation canceled.")
                    input("Press Enter...")
                    break  # Exit input loop if canceled

                # Perform INSERT or UPDATE
                try:
                    if choice == '2':
                        self.cursor.execute("""
                            INSERT INTO Schedule (CourseID, DayOfWeek, Start_Time, End_Time, Room)
                            VALUES (?, ?, ?, ?, ?)
                        """, (course_id, day, start_time, end_time, room))
                        self.conn.commit()
                        print("[Success]: New schedule added.")
                    else:  # choice == '3' - Update
                        self.cursor.execute("""
                            UPDATE Schedule
                            SET DayOfWeek = ?, Start_Time = ?, End_Time = ?, Room = ?
                            WHERE ScheduleID = ?
                        """, (day, start_time, end_time, room, sched_id))
                        self.conn.commit()
                        print("[Success]: Schedule updated.")
                    break  # Exit loop on success

                except sqlite3.Error as e:
                    print(f"[Database error]: {e}")
                    continue  # back to ask again if DB error

            input("Press Enter to continue...")

    def view_reports(self):
            while True:
                self.clear_screen()
                print("====================================")
                print("   STATISTICAL REPORTS")
                print("====================================")
                print("1. User Statistics")
                print("2. Subject Statistics")
                print("3. Course Section Statistics")
                print("4. Registration & Grade Statistics")
                print("5. Schedule Statistics")
                print("6. Return to Admin menu")
                choice = input("\nChoose report type: ").strip()

                if choice == '6':
                    break

                report_lines = []
                report_lines.append("UTH STUDENT MANAGEMENT SYSTEM STATISTICAL REPORT")
                report_lines.append("=" * 60)
                report_lines.append(f"Report creation date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                report_lines.append("")

                if choice == '1':
                    # 1. User statistics by Role
                    users_by_role = self.cursor.execute("""
                        SELECT Role, COUNT(*) as count 
                        FROM User 
                        GROUP BY Role
                        ORDER BY count DESC
                    """).fetchall()

                    report_lines.append("1. USER STATISTICS")
                    report_lines.append("-" * 40)
                    total_users = 0
                    if not users_by_role:
                        report_lines.append("  No users in the system yet.")
                    else:
                        for row in users_by_role:
                            report_lines.append(f"  {row['Role'].upper():<10}: {row['count']:,} people")
                            total_users += row['count']
                        report_lines.append(f"  Total: {total_users:,} users")
                    report_lines.append("")

                elif choice == '2':
                    # 2. Subject statistics
                    subject_count = self.cursor.execute("SELECT COUNT(*) FROM Subject").fetchone()[0]
                    report_lines.append("2. SUBJECT STATISTICS")
                    report_lines.append("-" * 40)
                    if subject_count == 0:
                        report_lines.append("  No subjects in the system yet.")
                    else:
                        report_lines.append(f"  Total subjects: {subject_count:,} subjects")
                    report_lines.append("")

                elif choice == '3':
                    # 3. Course section statistics (Course)
                    total_courses = self.cursor.execute("SELECT COUNT(*) FROM Course").fetchone()[0]
                    courses_per_subject = self.cursor.execute("SELECT COUNT(DISTINCT CourseID) FROM Course GROUP BY SubjectID").fetchall()
                    avg_courses_per_subject = total_courses / len(courses_per_subject) if courses_per_subject else 0

                    report_lines.append("3. COURSE SECTION STATISTICS")
                    report_lines.append("-" * 40)
                    if total_courses == 0:
                        report_lines.append("  No course sections in the system yet.")
                    else:
                        report_lines.append(f"  Total course sections: {total_courses:,} classes")
                        report_lines.append(f"  Subjects with open classes: {len(courses_per_subject):,} subjects")
                        report_lines.append(f"  Average classes/subject: {avg_courses_per_subject:.1f} classes")
                    report_lines.append("")

                elif choice == '4':
                    # 4. Registration & grade statistics (ADDED PASS / FAIL SUBJECTS)
                    enroll_stats = self.cursor.execute("""
                        SELECT 
                            COUNT(*) as total_enroll,
                            COUNT(DISTINCT StudentID) as unique_students,
                            COUNT(DISTINCT CourseID) as courses_with_enroll,
                            COUNT(Grade) as graded_count,
                            AVG(Grade) as avg_grade,
                            SUM(CASE WHEN Grade >= 4.0 THEN 1 ELSE 0 END) as passed,
                            SUM(CASE WHEN Grade < 4.0 AND Grade IS NOT NULL THEN 1 ELSE 0 END) as failed
                        FROM Enrollment
                    """).fetchone()

                    report_lines.append("4. REGISTRATION & GRADE STATISTICS (10-point scale, pass >= 4.0)")
                    report_lines.append("-" * 60)
                    if enroll_stats['total_enroll'] == 0:
                        report_lines.append("  No registrations in the system yet.")
                    else:
                        report_lines.append(f"  Total course registrations: {enroll_stats['total_enroll']:,}")
                        report_lines.append(f"  Students registered for at least 1 course: {enroll_stats['unique_students']:,}")
                        report_lines.append(f"  Classes with registrations: {enroll_stats['courses_with_enroll']:,}")
                        report_lines.append(f"  Graded courses: {enroll_stats['graded_count']:,}")
                        if enroll_stats['graded_count'] > 0:
                            report_lines.append(f"  System-wide average grade: {enroll_stats['avg_grade']:.2f}")
                        report_lines.append("")
                        report_lines.append("  LEARNING OUTCOMES:")
                        report_lines.append(f"    - Passed (>= 4.0): {enroll_stats['passed']:,} instances")
                        report_lines.append(f"    - Failed (< 4.0): {enroll_stats['failed']:,} instances")
                        report_lines.append(f"    - No grade yet: {enroll_stats['total_enroll'] - enroll_stats['graded_count']:,} instances")
                    report_lines.append("")

                elif choice == '5':
                    # 5. Schedule statistics
                    schedule_count = self.cursor.execute("SELECT COUNT(*) FROM Schedule").fetchone()[0]
                    report_lines.append("5. SCHEDULE STATISTICS")
                    report_lines.append("-" * 40)
                    if schedule_count == 0:
                        report_lines.append("  No schedules in the system yet.")
                    else:
                        report_lines.append(f"  Total scheduled sessions: {schedule_count:,}")
                    report_lines.append("")

                else:
                    print("[Error]: Invalid choice!")
                    input("Press Enter to continue...")
                    continue

                # Display report in console
                print("\n".join(report_lines))

                # Export to txt file
                export = input("\nDo you want to export the report to txt file? (Y/N): ").upper()
                if export == 'Y':
                    filename = f"report_{choice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    try:
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write("\n".join(report_lines))
                        print(f"[Success]: Report saved to file: {filename}")
                    except Exception as e:
                        print(f"[Error saving file]: {e}")

                input("\nPress Enter to continue...")

    # ==========================================
    # STUDENT USE-CASES (6, 7)
    # ==========================================
    def student_view_schedule(self):
        res = self.cursor.execute("SELECT StudentID FROM Student WHERE AccountID=?", (self.current_user['AccountID'],)).fetchone()
        query = """SELECT sub.SubjectName, s.DayOfWeek, s.Start_Time, s.Room 
                   FROM Enrollment e JOIN Course c ON e.CourseID=c.CourseID 
                   JOIN Subject sub ON c.SubjectID=sub.SubjectID
                   JOIN Schedule s ON c.CourseID=s.CourseID WHERE e.StudentID=?"""
        data = self.cursor.execute(query, (res[0],)).fetchall()
        if not data: print("No timetable yet.")
        for r in data: print(f"{r[0]} | Day {r[1]} | {r[2]} | {r[3]}")
        input()

    def student_view_courses(self):
        """Use-case 7 & 8: View Course information / View Course's information - For students to view registered course information"""
        self.clear_screen()
        print("====================================")
        print("   COURSE INFORMATION")
        print("====================================")
        student_id_res = self.cursor.execute("SELECT StudentID FROM Student WHERE AccountID=?", (self.current_user['AccountID'],)).fetchone()
        if not student_id_res:
            print("[Error]: Student information not found!")
            input("Press Enter...")
            return

        student_id = student_id_res['StudentID']
        courses = self.cursor.execute("""
            SELECT c.CourseID, sub.SubjectName, c.ClassName, c.Year, c.Semester, u.FullName AS TeacherName, sub.Credits, e.Grade
            FROM Enrollment e
            JOIN Course c ON e.CourseID = c.CourseID
            JOIN Subject sub ON c.SubjectID = sub.SubjectID
            LEFT JOIN Teacher t ON c.TeacherID = t.TeacherID
            LEFT JOIN User u ON t.AccountID = u.AccountID
            WHERE e.StudentID = ?
            ORDER BY c.Year DESC, c.Semester DESC
        """, (student_id,)).fetchall()

        print("\n--- LIST OF REGISTERED COURSES ---")
        if not courses:
            print("You have not registered for any courses.")
        else:
            print(" CourseID    Subject                      Class     Year  Sem  Teacher                 Credits   Grade")
            print("-" * 100)
            for course in courses:
                teacher = course['TeacherName'] or 'Not assigned'
                grade = course['Grade'] if course['Grade'] is not None else 'No grade'
                print(f" {course['CourseID']:<10} {course['SubjectName'][:25]:<25} {course['ClassName']:<9} {course['Year']}  {course['Semester']}  {teacher[:20]:<20} {course['Credits']}        {grade}")
        input("\nPress Enter to return...")

    # ==========================================
    # LECTURER USE-CASES (8, 9, 10)
    # ==========================================
    def teacher_enter_grades(self):
        """Use-case 9: Enter Grades - Enter grades for students, support Enter to skip"""
        self.clear_screen()
        print("====================================")
        print("   ENTER STUDENT GRADES")
        print("====================================")

        # Get list of classes teaching
        teacher_res = self.cursor.execute("SELECT TeacherID FROM Teacher WHERE AccountID=?", (self.current_user['AccountID'],)).fetchone()
        if not teacher_res:
            print("[Error]: Teacher information not found!")
            input("Press Enter to return...")
            return

        teacher_id = teacher_res['TeacherID']
        courses = self.cursor.execute("""
            SELECT CourseID, ClassName, Year, Semester
            FROM Course 
            WHERE TeacherID = ?
            ORDER BY Year DESC, Semester DESC
        """, (teacher_id,)).fetchall()

        if not courses:
            print("[Notification]: You have not been assigned any classes to enter grades.")
            input("Press Enter to return...")
            return

        print("\nList of classes you are teaching:")
        for i, c in enumerate(courses, 1):
            print(f" {i}. {c['CourseID']} - {c['ClassName']} ({c['Year']} Sem{c['Semester']})")

        try:
            idx = int(input("\nChoose class sequence number to enter grades: ").strip()) - 1
            if idx < 0 or idx >= len(courses):
                raise ValueError
            selected_course = courses[idx]
            course_id = selected_course['CourseID']
            class_name = selected_course['ClassName']
        except:
            print("[Error]: Invalid choice!")
            input("Press Enter to return...")
            return

        # Get list of students in class
        students = self.cursor.execute("""
            SELECT e.EnrollID, s.StudentID, u.FullName, e.Grade
            FROM Enrollment e
            JOIN Student s ON e.StudentID = s.StudentID
            JOIN User u ON s.AccountID = u.AccountID
            WHERE e.CourseID = ?
            ORDER BY s.StudentID
        """, (course_id,)).fetchall()

        if not students:
            print(f"[Notification]: Class {course_id} - {class_name} has no registered students yet.")
            input("Press Enter to return...")
            return

        print(f"\nEnter grades for class {course_id} - {class_name}")
        print(" (Press Enter to skip - keep old grade or blank if no grade)")
        print("-" * 60)

        updated_count = 0
        for student in students:
            current_grade = student['Grade'] if student['Grade'] is not None else "No grade"
            print(f"\nStudent: {student['StudentID']} - {student['FullName']}")
            print(f"  Current grade: {current_grade}")

            while True:
                grade_input = input("  Enter new grade (0-10, Enter to skip): ").strip()
                
                # Press Enter → skip
                if not grade_input:
                    print("  → Skipped (kept old grade)")
                    break

                try:
                    grade = float(grade_input)
                    if 0 <= grade <= 10:
                        # Update grade
                        self.cursor.execute("UPDATE Enrollment SET Grade = ? WHERE EnrollID = ?",
                                            (grade, student['EnrollID']))
                        updated_count += 1
                        print(f"  → Grade updated: {grade}")
                        break
                    else:
                        print("[Error]: Grade must be from 0 to 10! Enter again or Enter to skip.")
                except ValueError:
                    print("[Error]: Please enter a valid number (0-10)! Enter again or Enter to skip.")

        self.conn.commit()
        print("\n" + "=" * 60)
        print(f"[Completed]: Updated grades for {updated_count} students in class.")
        print(f"  Total students in class: {len(students)}")
        input("\nPress Enter to return to menu...")

    def teacher_view_schedule(self):
        """Use-case 10: View teaching Schedule - For teachers to view their teaching schedule"""
        self.clear_screen()
        print("====================================")
        print("   TEACHING SCHEDULE")
        print("====================================")
        teacher_id_res = self.cursor.execute("SELECT TeacherID FROM Teacher WHERE AccountID=?", (self.current_user['AccountID'],)).fetchone()
        if not teacher_id_res:
            print("[Error]: Teacher information not found!")
            input("Press Enter...")
            return

        teacher_id = teacher_id_res['TeacherID']
        schedules = self.cursor.execute("""
            SELECT c.CourseID, c.ClassName, sub.SubjectName,
                   s.DayOfWeek, s.Start_Time, s.End_Time, s.Room
            FROM Course c
            JOIN Subject sub ON c.SubjectID = sub.SubjectID
            JOIN Schedule s ON c.CourseID = s.CourseID
            WHERE c.TeacherID = ?
            ORDER BY c.Year DESC, c.Semester DESC, s.DayOfWeek, s.Start_Time
        """, (teacher_id,)).fetchall()

        print("\n--- YOUR TEACHING SCHEDULE ---")
        if not schedules:
            print("You have not been assigned any classes or no teaching schedule yet.")
        else:
            print(" CourseID   Class     Subject              Day  Start     End        Room")
            print("-" * 80)
            for sch in schedules:
                print(f" {sch['CourseID']:<10} {sch['ClassName']:<9} {sch['SubjectName'][:18]:<18} {sch['DayOfWeek']}    {sch['Start_Time']:<8} {sch['End_Time']:<9} {sch['Room'] or 'None'}")
        input("\nPress Enter to return...")

    def teacher_view_courses(self):
        """View Course information - For teachers to view information of courses they are teaching"""
        self.clear_screen()
        print("====================================")
        print("   COURSE INFORMATION (Teacher)")
        print("====================================")
        
        teacher_id_res = self.cursor.execute("SELECT TeacherID FROM Teacher WHERE AccountID=?", (self.current_user['AccountID'],)).fetchone()
        if not teacher_id_res:
            print("[Error]: Teacher information not found!")
            input("Press Enter...")
            return

        teacher_id = teacher_id_res['TeacherID']
        courses = self.cursor.execute("""
            SELECT c.CourseID, sub.SubjectName, c.ClassName, c.Year, c.Semester, sub.Credits, c.ClassSize, COUNT(e.StudentID) as Enrolled
            FROM Course c
            JOIN Subject sub ON c.SubjectID = sub.SubjectID
            LEFT JOIN Enrollment e ON c.CourseID = e.CourseID AND e.Status = 'registered'
            WHERE c.TeacherID = ?
            GROUP BY c.CourseID
            ORDER BY c.Year DESC, c.Semester DESC
        """, (teacher_id,)).fetchall()

        print("\n--- LIST OF COURSES TEACHING ---")
        if not courses:
            print("You have not been assigned to teach any courses.")
        else:
            print(" CourseID    Subject                      Class     Year  Sem  Credits   Enrollment")
            print("-" * 90)
            for course in courses:
                enrolled = course['Enrolled'] or 0
                print(f" {course['CourseID']:<10} {course['SubjectName'][:25]:<25} {course['ClassName']:<9} {course['Year']}  {course['Semester']}  {course['Credits']:<9} {enrolled}/{course['ClassSize']}")
        input("\nPress Enter to return...")

    # ==========================================
    # MAIN MENUS
    # ==========================================
    def admin_menu(self):
        while True:
            self.clear_screen()
            print(f"--- ADMIN DASHBOARD ---")
            print("1. Profile | 2. Users | 3. Subjects | 4. Course Sections | 5. Schedules | 6. Reports | 7. PW | 8. Logout")
            c = input("Choose: ")
            if c == '1': self.view_profile()
            elif c == '2': self.manage_users()
            elif c == '3': self.manage_subjects()
            elif c == '4': self.manage_course_sections()
            elif c == '5': self.manage_schedules()
            elif c == '6': self.view_reports()
            elif c == '7': self.change_password()
            elif c == '8': 
                if self.logout(): break

    def student_menu(self):
        while True:
            self.clear_screen()
            print(f"--- STUDENT MENU ---")
            print("1. Profile | 2. Schedule | 3. Courses | 4. PW | 5. Logout")
            c = input("Choose: ")
            if c == '1': self.view_profile()
            elif c == '2': self.student_view_schedule()
            elif c == '3': self.student_view_courses()
            elif c == '4': self.change_password()
            elif c == '5':
                if self.logout(): break

    def teacher_menu(self):
        while True:
            self.clear_screen()
            print(f"--- TEACHER MENU ---")
            print("1. Profile | 2. Teaching Course | 3. Teaching Schedule | 4. Enter Grades | 5. PW | 6. Logout")
            c = input("Choose: ")
            if c == '1': self.view_profile()
            elif c == '2': self.teacher_view_courses()
            elif c == '3': self.teacher_view_schedule()
            elif c == '4': self.teacher_enter_grades()
            elif c == '5': self.change_password()
            elif c == '6':
                if self.logout(): break

    def run(self):
        while True:
            if self.login():
                role = self.current_user['Role'].lower()
                if role == 'admin': self.admin_menu()
                elif role == 'student': self.student_menu()
                elif role == 'teacher': self.teacher_menu()

if __name__ == "__main__":
    app = StudentManagementSystem()
    app.run()