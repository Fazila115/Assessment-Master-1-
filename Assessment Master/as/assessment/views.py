from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from student import models as SMODEL
from student import forms as SFORM
from django.contrib.auth.models import User
from django.shortcuts import render



from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from statistics import mean
from sklearn.model_selection import train_test_split

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'assessment/index.html')


def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')

    else:
        return redirect('admin-dashboard')



def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    'total_course':models.Course.objects.all().count(),
    'total_question':models.Question.objects.all().count(),
    }
    return render(request,'assessment/admin_dashboard.html',context=dict)


@login_required(login_url='adminlogin')
def admin_student_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    }
    return render(request,'assessment/admin_student.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'assessment/admin_view_student.html',{'students':students})




@login_required(login_url='adminlogin')
def admin_view_anylsis(request):
    # Fetch all courses
    courses = models.Course.objects.all()

    analysis_data = []

    for course in courses:
        # Get all results for the current course
        results = models.Result.objects.filter(exam=course)

        # Total available marks for the course
        total_marks = course.total_marks

        # Initialize counters for difficulty and discrimination calculations
        total_gained_marks = 0
        total_students = results.count()

        # Data for difficulty and discrimination index calculations
        correct_answers = 0
        top_27_percent_scores = []
        bottom_27_percent_scores = []
        student_scores = []

        # Categorize students' scores and calculate correct answers
        for result in results:
            percentage = (result.marks / total_marks) * 100
            total_gained_marks += result.marks
            student_scores.append(result.marks)

            # Count correct answers for difficulty index (e.g., assuming 1 mark per question)
            if result.marks == total_marks:
                correct_answers += 1

            # Classify scores for discrimination index (Top and Bottom 27%)
            if result.marks >= 0.7 * total_marks:
                top_27_percent_scores.append(result.marks)
            elif result.marks <= 0.3 * total_marks:
                bottom_27_percent_scores.append(result.marks)

        # Calculate Difficulty Index
        difficulty_index = (correct_answers / total_students) * 100 if total_students > 0 else 0

        # Calculate Discrimination Index
        if top_27_percent_scores and bottom_27_percent_scores:
            top_27_avg = mean(top_27_percent_scores)
            bottom_27_avg = mean(bottom_27_percent_scores)
            discrimination_index = (top_27_avg - bottom_27_avg) / total_marks * 100
        else:
            discrimination_index = 0

        # Calculate average percentage for the course
        average_percentage = (total_gained_marks / (total_marks * total_students)) * 100 if total_students > 0 else 0

        # --- Machine Learning (ML) Part ---

        # Classification for Difficulty Index (using Random Forest)
        # Feature: Average percentage, total students, and other features
        X = []
        y = []
        
        # Define labels for difficulty classification (e.g., easy, medium, hard)
        # Note: You need to define these labels based on your dataset, here using dummy example.
        difficulty_labels = ["easy", "medium", "hard"]

        # Example: Add a feature for each course based on the student performance
        for result in results:
            percentage = (result.marks / total_marks) * 100
            X.append([percentage, total_students])
            # For simplicity, assume we label courses manually, in real life you should label based on some criteria
            if percentage < 30:
                y.append("hard")
            elif percentage < 70:
                y.append("medium")
            else:
                y.append("easy")

        if len(X) >= 2:  # Need at least two samples for classification
            # Train classification model
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            clf = RandomForestClassifier(n_estimators=100)
            clf.fit(X_train, y_train)

            # Predict difficulty class for the course
            predicted_difficulty = clf.predict([[average_percentage, total_students]])[0]

        else:
            predicted_difficulty = "unknown"  # Not enough data for classification

        # Clustering for Discrimination Index (using KMeans)
        # We cluster student scores into two groups (high and low performers)
        if len(student_scores) > 1:  # Need at least two students to cluster
            # Standardize student scores (important for KMeans)
            scaler = StandardScaler()
            student_scores_scaled = scaler.fit_transform(np.array(student_scores).reshape(-1, 1))

            # KMeans clustering (2 clusters: high and low performers)
            kmeans = KMeans(n_clusters=2, random_state=42)
            kmeans.fit(student_scores_scaled)

            # Get cluster labels
            cluster_labels = kmeans.labels_

            # Divide scores into two groups: top performers and bottom performers
            top_cluster = [student_scores[i] for i in range(len(cluster_labels)) if cluster_labels[i] == 0]
            bottom_cluster = [student_scores[i] for i in range(len(cluster_labels)) if cluster_labels[i] == 1]

            # Calculate the Discrimination Index
            if top_cluster and bottom_cluster:
                top_avg = np.mean(top_cluster)
                bottom_avg = np.mean(bottom_cluster)
                discrimination_index = (top_avg - bottom_avg) / total_marks * 100
            else:
                discrimination_index = 0
        else:
            discrimination_index = 0

        # Add the data to the analysis list
        analysis_data.append({
            'course_name': course.course_name,
            'total_attempts': total_students,
            'less_than_50': len([r for r in results if (r.marks / total_marks) * 100 < 50]),
            'fifty_plus': len([r for r in results if 50 <= (r.marks / total_marks) * 100 < 60]),
            'sixty_plus': len([r for r in results if 60 <= (r.marks / total_marks) * 100 < 70]),
            'seventy_plus': len([r for r in results if 70 <= (r.marks / total_marks) * 100 < 80]),
            'eighty_plus': len([r for r in results if 80 <= (r.marks / total_marks) * 100 < 90]),
            'ninety_plus': len([r for r in results if (r.marks / total_marks) * 100 >= 90]),
            'average': round(average_percentage, 2),
            'course_difficulty_index': round(difficulty_index, 2),
            'course_discrimination_index': round(discrimination_index, 2),
            'predicted_difficulty': predicted_difficulty,  # ML predicted difficulty level
        })

    # Return the data to the template
    return render(request, 'assessment/admin_anylsis.html', {'analysis_data': analysis_data})



@login_required(login_url='adminlogin')
def update_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=SMODEL.User.objects.get(id=student.user_id)
    userForm=SFORM.StudentUserForm(instance=user)
    studentForm=SFORM.StudentForm(request.FILES,instance=student)
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=SFORM.StudentUserForm(request.POST,instance=user)
        studentForm=SFORM.StudentForm(request.POST,request.FILES,instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            studentForm.save()
            return redirect('admin-view-student')
    return render(request,'assessment/update_student.html',context=mydict)

@login_required(login_url='adminlogin')
def delete_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return HttpResponseRedirect('/admin-view-student')


@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request,'assessment/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm=forms.CourseForm()
    if request.method=='POST':
        courseForm=forms.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request,'assessment/admin_add_course.html',{'courseForm':courseForm})


@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.all()
    return render(request,'assessment/admin_view_course.html',{'courses':courses})

@login_required(login_url='adminlogin')
def delete_course_view(request,pk):
    course=models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')



@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request,'assessment/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm=forms.QuestionForm()
    if request.method=='POST':
        questionForm=forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            question=questionForm.save(commit=False)
            course=models.Course.objects.get(id=request.POST.get('courseID'))
            question.course=course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-question')
    return render(request,'assessment/admin_add_question.html',{'questionForm':questionForm})


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses= models.Course.objects.all()
    return render(request,'assessment/admin_view_question.html',{'courses':courses})

@login_required(login_url='adminlogin')
def view_question_view(request,pk):
    questions=models.Question.objects.all().filter(course_id=pk)
    return render(request,'assessment/view_question.html',{'questions':questions})

@login_required(login_url='adminlogin')
def delete_question_view(request,pk):
    question=models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'assessment/admin_view_student_marks.html',{'students':students})

@login_required(login_url='adminlogin')
def admin_view_marks_view(request,pk):
    courses = models.Course.objects.all()
    response =  render(request,'assessment/admin_view_marks.html',{'courses':courses})
    response.set_cookie('student_id',str(pk))
    return response

@login_required(login_url='adminlogin')
def admin_check_marks_view(request,pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student= SMODEL.Student.objects.get(id=student_id)

    results= models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'assessment/admin_check_marks.html',{'results':results})
