from datetime import datetime, timedelta

from sqlmodel import Session
from database import engine
from models import (
    User,
    Classroom,
    ClassroomStudentLink,
    ClassroomTeacherLink,
    ClassroomTestAssignment,
    Test,
    Question,
)

print("Seeding database...")

with Session(engine) as session:
    # Create Users
    admin = User(username="admin", password="password", role="admin")
    teacher = User(username="teacher", password="password", role="teacher")
    student1 = User(username="student1", password="password", role="student")
    student2 = User(username="student2", password="password", role="student")
    session.add_all([admin, teacher, student1, student2])
    session.commit()

    # Create a classroom
    classroom = Classroom(name="SHSAT Prep Class")
    session.add(classroom)
    session.commit()

    # Link teacher and students to the classroom
    session.add(ClassroomTeacherLink(classroom_id=classroom.id, teacher_id=teacher.id))
    session.add_all([
        ClassroomStudentLink(classroom_id=classroom.id, student_id=student1.id),
        ClassroomStudentLink(classroom_id=classroom.id, student_id=student2.id),
    ])
    session.commit()

    # Create tests
    now = datetime.utcnow()
    next_month = now + timedelta(days=30)

    test1 = Test(
        name="Practice SHSAT 1",
        description="This is the first SHSAT practice test.",
        created_by=teacher.id,
        is_timed=True,
        duration_minutes=60,
        max_attempts=3,
        available_from=now,
        available_until=next_month,
        is_published=True,
        show_results_immediately=True,
        allow_back_navigation=True,
        shuffle_questions=False,
        pass_score=70.0,
        graded_by="auto"
    )

    test2 = Test(
        name="Practice SHSAT 2",
        description="Second in the SHSAT practice series.",
        created_by=teacher.id,
        is_timed=True,
        duration_minutes=75,
        max_attempts=2,
        available_from=now,
        available_until=next_month,
        is_published=False,
        show_results_immediately=False,
        allow_back_navigation=False,
        shuffle_questions=True,
        pass_score=75.0,
        graded_by="manual"
    )

    test3 = Test(
        name="Practice SHSAT 3",
        description="Final SHSAT practice test for review.",
        created_by=teacher.id,
        is_timed=False,
        duration_minutes=None,
        max_attempts=5,
        available_from=None,
        available_until=None,
        is_published=True,
        show_results_immediately=True,
        allow_back_navigation=True,
        shuffle_questions=False,
        pass_score=65.0,
        graded_by="auto"
    )
    session.add_all([test1, test2, test3])
    session.commit()

    # Assign tests to the classroom
    session.add_all([
        ClassroomTestAssignment(classroom_id=classroom.id, test_id=test1.id),
        ClassroomTestAssignment(classroom_id=classroom.id, test_id=test2.id),
        ClassroomTestAssignment(classroom_id=classroom.id, test_id=test3.id),
    ])
    session.commit()

    # Add questions for all tests (you can reuse the `questions1`, `questions2`, `questions3` lists from your original script)
    # Example for test1 only:
    session.add_all([
        Question(
            test_id=test1.id,
            order=1,
            question_text='What is $2 + 2$?',
            choices='{ "A": "3", "B": "4", "C": "5", "D": "6" }',
            correct_choice="B",
            explanation='$2 + 2 = 4$.\\So the correct answer is B.'
        ),
        Question(
            test_id=test1.id,
            order=2,
            question_text='Which is a prime number?',
            choices='{ "A": "4", "B": "6", "C": "7", "D": "9" }',
            correct_choice="C",
            explanation='A prime number has exactly two distinct positive divisors: $1$ and itself.\\$7$ is only divisible by $1$ and $7$.\\So the correct answer is C.'
        ),
    ])
    session.commit()

    questions2 = [
        Question(
            test_id=test2.id,
            order=2,
            question_text='How many positive even factors of $48$ are greater than $24$ and less than $48$?',
            choices='{"A": "0", "B": "1", "C": "2", "D": "12"}',
            correct_choice="A",
            explanation='The even factors of $48$ are: $2, 4, 6, 8, 12, 16, 24, 48$.\\None of these are between $24$ and $48$.\\Therefore, there are $0$ positive even factors of $48$ in that range.'
        ),

        Question(
            test_id=test2.id,
            order=3,
            question_text='Read this paragraph.\\(1) When coal was used to heat homes, it frequently left a soot stain on the walls.\\(2) Brothers Cleo and Noah McVicker, who owned a cleaning product company, created a doughy substance to help people remove this soot.\\(3) Over time, as natural gas becomes more common, people had little need for soot cleansers, and the McVickers’ family company struggled to stay in business.\\(4) Then one day, Joe McVicker, Cleo’s son, learned that his sister-in-law had been using the substance for art projects in her classroom, so he remarketed the product as the toy known today as Play-Doh.\\Which sentence should be revised to correct an inappropriate shift in verb tense?',
            choices='{"A": "sentence 1", "B": "sentence 2", "C": "sentence 3", "D": "sentence 4"}',
            correct_choice="C",
            explanation='Sentence 3 contains a verb tense shift: the clause "as natural gas becomes more common" is in the present tense, while the surrounding context uses past tense.\\It should be revised to "as natural gas became more common".'
        ),

        Question(
            test_id=test2.id,
            order=87,
            question_text='Today, Tien’s age is $\\frac{1}{4}$ of Jordan’s age. In 2 years, Tien’s age will be $\\frac{1}{3}$ of Jordan’s age.\\How old is Jordan today?',
            choices='{"A": "4 years old", "B": "6 years old", "C": "12 years old", "D": "16 years old"}',
            correct_choice="D",
            explanation='Let $T = \\frac{1}{4}J$.\\In 2 years: $T + 2 = \\frac{1}{3}(J + 2)$.\\Substitute: $\\frac{1}{4}J + 2 = \\frac{1}{3}(J + 2)$.\\Solve: $\\frac{1}{4}J = \\frac{1}{3}J - \\frac{4}{3}$.\\$-\\frac{1}{12}J = -\\frac{4}{3}$, so $J = 16$.'
        )
    ]

    session.add_all(questions2)
    session.commit()

    questions3 = [
        Question(
            test_id=test3.id,
            order=13,
            question_text='Which sentence is irrelevant to the ideas in the third paragraph (sentences 11--16) and should be deleted?',
            choices='{"A": "sentence 12","B": "sentence 13","C": "sentence 15","D": "sentence 16"}',
            correct_choice="B",
            explanation='The third paragraph focuses on the bike sharing program in New York City. Sentence 13 discusses a program in China, which is unrelated to this focus. Therefore, sentence 13 is irrelevant and should be deleted.'
        ),

        Question(
            test_id=test3.id,
            order=17,
            question_text='Read this sentence.  "Active hobbies, such as jogging or yoga, can also provide relief from some of the effects of stress, because they prompt the body to release chemicals called endorphins, which can promote positive feelings."  Where should this sentence be added to best support the ideas in the second paragraph (sentences 4--9)?',
            choices='{"A": "between sentences 6 and 7", "B": "between sentences 7 and 8","C": "between sentences 8 and 9","D": "at the end of the paragraph (after sentence 9)"}',
            correct_choice="C",
            explanation='The sentence discusses hobbies and their effects on stress, making it most relevant after sentence 8, which lists specific hobbies. Sentence 9 ends the discussion, so placing the sentence after 9 would be too late. Only Option C correctly places the sentence where its ideas logically support the paragraph.'
        ),

        Question(
            test_id=test3.id,
            order=18,
            question_text='Which revision of sentence 16 uses the most precise language?',
            choices='{"A": "A. A hobbyist might try to learn more about a hobby or go to events with other people who also like the same hobby.","B": "B. A hobbyist might enroll in a course related to the hobby or attend a convention with other people who enjoy the hobby.","C": "C. A hobbyist might try to find new information about a hobby or go to places where other people are involved with the hobby.","D": "D. A hobbyist might want to expand his or her knowledge of a hobby or do an activity with other people who pursue the same hobby."}',
            correct_choice="B",
            explanation='Sentence 16 needs more precise language than vague phrases like “do something” or “go to places.” Option B gives specific examples such as “enroll in a course” and “attend a convention,” which clarify the types of social activities. The other options remain too general or repeat vague ideas from the original sentence.'
        ),

        Question(
            test_id=test3.id,
            order=23,
            question_text='In the winter that followed the summer of 1816, New Englanders most likely experienced',
            choices='{"A": "A. new weather events that they had not encountered before.","B": "B. temperatures that were warmer than usual for that time of year.","C": "C. shortages of fruits, vegetables, and other essential crops.","D": "D. difficulty adjusting to a different time line for planting crops."}',
            correct_choice="C",
            explanation='The summer of 1816 had poor crop yields, with many crops “stunted or destroyed.” As a result, food shortages during the winter of 1816–1817 were likely. There is no textual evidence for new weather events, warmer temperatures, or difficulty adjusting to planting timelines.'
        ),

        Question(
            test_id=test3.id,
            order=37,
            question_text='Why does the author mention orange soda in the fourth paragraph?',
            choices='{"A": "A. to suggest that consumer preferences for natural or artificial flavors vary","B": "B. to explain why natural flavors are more expensive than artificial substitutes", "C": "C. to demonstrate that consumers sometimes prefer artificial flavors to natural flavors","D": "D. to give an example of a natural flavor that may become difficult to find in the future"}',
            correct_choice="C",
            explanation='The author mentions orange soda to illustrate that some consumers prefer synthetic flavors over their natural counterparts. The passage does not use orange soda to discuss varying preferences broadly (A), cost differences (B), or scarcity of natural flavors (D), which rules those options out.'
        ),

        Question(
            test_id=test3.id,
            order=70,
            question_text='The perimeter of a rectangle is $510$ centimeters. The ratio of the length to the width is $3:2$. What are the dimensions of this rectangle?',
            choices='{"A": "A. 150 cm by 105 cm","B": "B. 153 cm by 102 cm","C": "C. 158 cm by 97 cm","D": "D. 165 cm by 90 cm"}',
            correct_choice="B",
            explanation='Let the width be $2x$ and the length be $3x$. Perimeter $= 2(2x) + 2(3x) = 4x + 6x = 10x$. $10x = 510$, so $x = 51$. Width $= 2x = 102$ cm and length $= 3x = 153$ cm.'
        ),

        Question(
            test_id=test3.id,
            order=1,
            question_text='1 dollar = 7 lorgs; 1 dollar = 0.5 dalt. Kevin has 140 lorgs and 16 dalts. If he exchanges the lorgs and dalts for dollars according to the rates above, how many dollars will he receive?',
            choices='{"A": "$28", "B": "$52", "C": "$182", "D": "$282"}',
            correct_choice="B",
            explanation='Use proportions to convert lorgs and dalts to dollars. Lorgs: $\\frac{140}{x} = \\frac{7}{1} \\Rightarrow 7x = 140 \\Rightarrow x = 20$. Dalts: $\\frac{16}{x} = \\frac{0.5}{1} \\Rightarrow 0.5x = 16 \\Rightarrow x = 32$. Total: $20 + 32 = 52$ dollars.'
        ),

        Question(
            test_id=test3.id,
            order=104,
            question_text='If $3n$ is a positive even number, how many **odd** numbers are in the range from $3n$ up to and including $3n + 5$?',
            choices='{"A": "A. 2","B": "B. 3","C": "C. 4","D": "D. 5"}',
            correct_choice="B",
            explanation='Since $3n$ is even, $3n + 1$ is odd. Adding 2 to an odd number gives another odd number, so $3n + 3$ and $3n + 5$ are also odd. Thus, the odd numbers in the range from $3n$ to $3n + 5$ are: $3n + 1$, $3n + 3$, $3n + 5$. There are 3 odd numbers in this range.'
        ),

        Question(
            test_id=test3.id,
            order=114,
            question_text='A paste is made by mixing the following ingredients by weight: 4 parts powder, 3 parts water, 2 parts resin, and 1 part hardener. One billboard requires 30 pounds of this paste. How many total pounds of resin are required for 4 billboards?',
            choices='{"A": "A. 6 lb","B": "B. 8 lb","C": "C. 24 lb","D": "D. 48 lb"}',
            correct_choice="C",
            explanation='The ratio is $4:3:2:1$, totaling 10 parts. Resin makes up $\\frac{2}{10} = \\frac{1}{5}$ of the paste. For 1 billboard: $\\frac{1}{5} \\times 30 = 6$ lb of resin. For 4 billboards: $6 \\times 4 = 24$ lb of resin.'
        )
    ]

    session.add_all(questions3)
    session.commit()

print("✅ Done seeding!")
