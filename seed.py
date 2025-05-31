# testquest/seed.py
from sqlmodel import Session
from database import engine
from models import User, TeacherStudent, Test, Question, StudentTestAssignment

print("Seeding database...")

with Session(engine) as session:
    # Users
    admin = User(username="admin", password="password", role="admin")
    teacher = User(username="teacher", password="password", role="teacher")
    student = User(username="student1", password="password", role="student")
    student2 = User(username="student2", password="password", role="student")
    session.add_all([admin, teacher, student, student2])
    session.commit()

    # Link teacher to students
    session.add_all([
        TeacherStudent(teacher_id=teacher.id, student_id=student.id),
        TeacherStudent(teacher_id=teacher.id, student_id=student2.id),
    ])
    session.commit()

    # Test 1
    test1 = Test(name="Practice SHSAT 1", created_by=teacher.id)
    session.add(test1)
    session.commit()

    session.add_all([
        StudentTestAssignment(student_id=student.id, test_id=test1.id),
        StudentTestAssignment(student_id=student2.id, test_id=test1.id),
    ])
    session.commit()

    questions1 = [
        Question(
            test_id=test1.id,
            order=1,
            question_text="\\text{What is }2 + 2\\text{?}",
            choices='{ "A": "3", "B": "4", "C": "5", "D": "6" }',
            correct_choice="B",
            explanation="Algebra"
        ),
        Question(
            test_id=test1.id,
            order=2,
            question_text="\\text{Which is a prime number?}",
            choices='{ "A": "4", "B": "6", "C": "7", "D": "9" }',
            correct_choice="C",
            explanation="Number Theory"
        ),
    ]
    session.add_all(questions1)
    session.commit()

    # Test 2
    test2 = Test(name="Practice SHSAT 2", created_by=teacher.id)
    session.add(test2)
    session.commit()

    session.add_all([
        StudentTestAssignment(student_id=student.id, test_id=test2.id),
        StudentTestAssignment(student_id=student2.id, test_id=test2.id),
    ])
    session.commit()

    questions2 = [
        Question(
            test_id=test2.id,
            order=2,
            question_text=r'\text{How many positive even factors of } 48 \text{ are greater than } 24 \text{ and less than } 48\text{?}',
            choices='{"A": "0", "B": "1", "C": "2", "D": "12"}',
            correct_choice="A",
            explanation=r'\text{The even factors of } 48 \text{ are: } 2, 4, 6, 8, 12, 16, 24, 48. \\ \text{None of these are between } 24 \text{ and } 48. \\ \text{Therefore, there are } 0 \text{ positive even factors of } 48 \text{ in that range.}'
        ),

        Question(
            test_id=test2.id,
            order=3,
            question_text=r'\text{Read this paragraph.} \\ (1) \text{When coal was used to heat homes, it frequently left a soot stain on the walls.} \\ (2) \text{Brothers Cleo and Noah McVicker, who owned a cleaning product company, created a doughy substance to help people remove this soot.} \\ (3) \text{Over time, as natural gas becomes more common, people had little need for soot cleansers, and the McVickers’ family company struggled to stay in business.} \\ (4) \text{Then one day, Joe McVicker, Cleo’s son, learned that his sister-in-law had been using the substance for art projects in her classroom, so he remarketed the product as the toy known today as Play-Doh.} \\ \text{Which sentence should be revised to correct an inappropriate shift in verb tense?}',
            choices='{"A": "\\\\text{sentence 1}", "B": "\\\\text{sentence 2}", "C": "\\\\text{sentence 3}", "D": "\\\\text{sentence 4}"}',
            correct_choice="C",
            explanation=r'\text{Sentence 3 contains a verb tense shift: the clause } \textit{as natural gas becomes more common} \text{ is in the present tense, while the surrounding context uses past tense. It should be revised to } \textit{as natural gas became more common}\text{.}'
        ),

        Question(
            test_id=test2.id,
            order=87,
            question_text=r'\text{Today, Tien’s age is } \frac{1}{4} \text{ of Jordan’s age. In 2 years, Tien’s age will be } \frac{1}{3} \text{ of Jordan’s age.} \\ \text{How old is Jordan today?}',
            choices='{"A": "\\\\text{4 years old}", "B": "\\\\text{6 years old}", "C": "\\\\text{12 years old}", "D": "\\\\text{16 years old}"}',
            correct_choice="D",
            explanation=r'\text{Let } T = \frac{1}{4}J. \\ \text{In 2 years, } T + 2 = \frac{1}{3}(J + 2). \\ \text{Substitute and solve:} \\ \frac{1}{4}J + 2 = \frac{1}{3}(J + 2) \\ \frac{1}{4}J = \frac{1}{3}J - \frac{4}{3} \\ -\frac{1}{12}J = -\frac{4}{3} \\ J = 16'
        )

    ]
    session.add_all(questions2)
    session.commit()

    test3 = Test(name="Practice SHSAT 3", created_by=teacher.id)
    session.add(test3)
    session.commit()

    session.add_all([
        StudentTestAssignment(student_id=student.id, test_id=test3.id),
        StudentTestAssignment(student_id=student2.id, test_id=test3.id),
    ])
    session.commit()

    questions3 = [
        Question(
            test_id=test3.id,
            order=13,
            question_text=r'\text{Which sentence is irrelevant to the ideas in the third paragraph (sentences 11--16) and should be deleted?}',
            choices='{"A": "\\\\text{sentence 12}","B": "\\\\text{sentence 13}","C": "\\\\text{sentence 15}","D": "\\\\text{sentence 16}"}',
            correct_choice = "B",
            explanation = r'\text{The third paragraph focuses on the bike sharing program in New York City. Sentence 13 discusses a program in China, which is unrelated to this focus. Therefore, sentence 13 is irrelevant and should be deleted.}'
        ),

        Question(
            test_id=test3.id,
            order=17,
            question_text=r'\text{Read this sentence.} \\ \boxed{\text{Active hobbies, such as jogging or yoga, can also provide relief from some of the effects of stress, because they prompt the body to release chemicals called endorphins, which can promote positive feelings.}} \\ \text{Where should this sentence be added to best support the ideas in the second paragraph (sentences 4--9)?}',
            choices='{"A": "\\\\text{between sentences 6 and 7}", "B": "\\\\text{between sentences 7 and 8}","C": "\\\\text{between sentences 8 and 9}","D": "\\\\text{at the end of the paragraph (after sentence 9)}"}',
            correct_choice = "C",
            explanation = r'\text{The sentence discusses hobbies and their effects on stress, making it most relevant after sentence 8, which lists specific hobbies. Sentence 9 ends the discussion, so placing the sentence after 9 would be too late. Only Option C correctly places the sentence where its ideas logically support the paragraph.}'
        ),

        Question(
            test_id=test3.id,
            order=18,
            question_text=r'\text{Which revision of sentence 16 uses the most precise language?}',
            choices='{"A": "\\\\textbf{A.} \\\\text{A hobbyist might try to learn more about a hobby or go to events with other people who also like the same hobby.}","B": "\\\\textbf{B.} \\\\text{A hobbyist might enroll in a course related to the hobby or attend a convention with other people who enjoy the hobby.}","C": "\\\\textbf{C.} \\\\text{A hobbyist might try to find new information about a hobby or go to places where other people are involved with the hobby.}","D": "\\\\textbf{D.} \\\\text{A hobbyist might want to expand his or her knowledge of a hobby or do an activity with other people who pursue the same hobby.}"}',
            correct_choice = "B",
            explanation = r'\text{Sentence 16 needs more precise language than vague phrases like “do something” or “go to places.” Option B gives specific examples such as “enroll in a course” and “attend a convention,” which clarify the types of social activities. The other options remain too general or repeat vague ideas from the original sentence.}'
        ),

        Question(
            test_id=test3.id,
            order=23,
            question_text=r'\text{In the winter that followed the summer of 1816, New Englanders most likely experienced}',
            choices='{"A": "\\\\textbf{A.} \\\\text{new weather events that they had not encountered before.}","B": "\\\\textbf{B.} \\\\text{temperatures that were warmer than usual for that time of year.}","C": "\\\\textbf{C.} \\\\text{shortages of fruits, vegetables, and other essential crops.}","D": "\\\\textbf{D.} \\\\text{difficulty adjusting to a different time line for planting crops.}"}',
            correct_choice = "C",
            explanation = r'\text{The summer of 1816 had poor crop yields, with many crops “stunted or destroyed.” As a result, food shortages during the winter of 1816–1817 were likely. There is no textual evidence for new weather events, warmer temperatures, or difficulty adjusting to planting timelines.}'
        ),

        Question(
            test_id=test3.id,
            order=37,
            question_text=r'\text{Why does the author mention orange soda in the fourth paragraph?}',
            choices='{"A": "\\\\textbf{A.} \\\\text{to suggest that consumer preferences for natural or artificial flavors vary}","B": "\\\\textbf{B.} \\\\text{to explain why natural flavors are more expensive than artificial substitutes}", "C": "\\\\textbf{C.} \\\\text{to demonstrate that consumers sometimes prefer artificial flavors to natural flavors}","D": "\\\\textbf{D.} \\\\text{to give an example of a natural flavor that may become difficult to find in the future}" }',
            correct_choice = "C",
            explanation = r'\text{The author mentions orange soda to illustrate that some consumers prefer synthetic flavors over their natural counterparts. The passage does not use orange soda to discuss varying preferences broadly (A), cost differences (B), or scarcity of natural flavors (D), which rules those options out.}'
        ),

        Question(
            test_id=test3.id,
            order=70,
            question_text=r'\text{The perimeter of a rectangle is } 510 \text{ centimeters. The ratio of the length to the width is } 3\!:\!2\text{. What are the dimensions of this rectangle?}',
            choices='{"A": "\\\\textbf{A.} \\\\text{150 cm by 105 cm}","B": "\\\\textbf{B.} \\\\text{153 cm by 102 cm}","C": "\\\\textbf{C.} \\\\text{158 cm by 97 cm}","D": "\\\\textbf{D.} \\\\text{165 cm by 90 cm}"}',
    correct_choice = "B",
    explanation = r'\text{Let the width be } 2x \text{ and the length be } 3x. \\ \text{Perimeter } = 2(2x) + 2(3x) = 4x + 6x = 10x. \\ 10x = 510 \\ x = 51 \\ \text{So width } = 2x = 102 \text{ cm and length } = 3x = 153 \text{ cm.}'
    ),

Question(
    test_id=test3.id,
    order=1,
    question_text=r'\text{1 dollar = 7 lorgs} \\ \text{1 dollar = 0.5 dalt} \\ \\ \text{Kevin has 140 lorgs and 16 dalts. If he exchanges the lorgs and dalts for dollars according to the rates above, how many dollars will he receive?}',
    choices='{"A": "\\\\text{\\\\$28}", "B": "\\\\text{\\\\$52}", "C": "\\\\text{\\\\$182}", "D": "\\\\text{\\\\$282}"}',
    correct_choice="B",
    explanation=r'\text{Use proportions to convert lorgs and dalts to dollars.} \\ \text{Lorgs: } \frac{140}{x} = \frac{7}{1} \Rightarrow 7x = 140 \Rightarrow x = 20 \\ \text{Dalts: } \frac{16}{x} = \frac{0.5}{1} \Rightarrow 0.5x = 16 \Rightarrow x = 32 \\ \text{Total: } 20 + 32 = 52 \text{ dollars.}'
),

Question(
    test_id=test3.id,
    order=104,
    question_text=r'\text{If } 3n \text{ is a positive even number, how many \textbf{odd} numbers are in the range from } 3n \text{ up to and including } 3n + 5\text{?}',
    choices='{"A": "\\\\textbf{A.} \\\\text{2}","B": "\\\\textbf{B.} \\\\text{3}","C": "\\\\textbf{C.} \\\\text{4}","D": "\\\\textbf{D.} \\\\text{5}"}',
    correct_choice="B",
    explanation=r'\text{Since } 3n \text{ is even, } 3n + 1 \text{ is odd. } \\ \text{Adding 2 to an odd number gives another odd number, so } 3n + 3 \text{ and } 3n + 5 \text{ are also odd.} \\ \text{Thus, the odd numbers in the range from } 3n \text{ to } 3n + 5 \text{ are: } 3n + 1, 3n + 3, 3n + 5. \\ \text{There are 3 odd numbers in this range.}'
),

Question(
    test_id=test3.id,
    order=114,
    question_text=r'\text{A paste is made by mixing the following ingredients by weight: 4 parts powder, 3 parts water, 2 parts resin, and 1 part hardener. One billboard requires 30 pounds of this paste. How many total pounds of resin are required for 4 billboards?}',
    choices='{"A": "\\\\textbf{A.} \\\\text{6 lb}","B": "\\\\textbf{B.} \\\\text{8 lb}","C": "\\\\textbf{C.} \\\\text{24 lb}","D": "\\\\textbf{D.} \\\\text{48 lb}"}',
    correct_choice="C",
    explanation=r'\text{The ratio is } 4\!:\!3\!:\!2\!:\!1, \text{ totaling } 10 \text{ parts. Resin makes up } \frac{2}{10} = \frac{1}{5} \text{ of the paste.} \\ \text{For 1 billboard: } \frac{1}{5} \times 30 = 6 \text{ lb of resin. For 4 billboards: } 6 \times 4 = 24 \text{ lb of resin.}'
)

        ]
    session.add_all(questions3)
    session.commit()

print("✅ Done seeding!")
