from django.db import models
from student.models import Student

class Course(models.Model):
    course_name = models.CharField(max_length=50)
    question_number = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()

    # Aggregated statistics for the course
    average_difficulty = models.FloatField(default=0)
    average_discrimination = models.FloatField(default=0)
    average_distractor_index = models.FloatField(default=0)

    def __str__(self):
        return self.course_name


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    question = models.CharField(max_length=600)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    cat = (('Option1', 'Option1'), ('Option2', 'Option2'), ('Option3', 'Option3'), ('Option4', 'Option4'))
    answer = models.CharField(max_length=200, choices=cat)

    # Add new fields for difficulty, discrimination, and distractor indices
    difficulty_index = models.FloatField(default=0)  # Difficulty index
    discrimination_index = models.FloatField(default=0)  # Discrimination index
    distractor_option1 = models.FloatField(default=0)  # Distractor index for option 1
    distractor_option2 = models.FloatField(default=0)  # Distractor index for option 2
    distractor_option3 = models.FloatField(default=0)  # Distractor index for option 3
    distractor_option4 = models.FloatField(default=0)  # Distractor index for option 4

    def __str__(self):
        return self.question


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Result of {self.student} in {self.exam.course_name}"
class StudentAnswer(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE)  # Reference to the result (exam)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)  # Reference to the question
    answer = models.CharField(max_length=200)  # Student's answer
    correct = models.BooleanField(default=False)  # Whether the student's answer is correct

    def __str__(self):
        return f"Answer for {self.question.question} by {self.result.student}"
