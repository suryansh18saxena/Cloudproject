import json
import re
import google.generativeai as genai

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings

from .models import InterviewSession, InterviewMessage


# ─── Configure Gemini ────────────────────────────────────────────────
def _get_gemini_model():
    """Get a configured Gemini model instance."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-2.5-flash')


# ─── Role descriptions for better AI prompts ─────────────────────────
ROLE_DESCRIPTIONS = {
    'cloud_engineer': 'Cloud Engineer (AWS/Azure/GCP infrastructure, IaC, cloud services)',
    'devops_engineer': 'DevOps Engineer (CI/CD, Docker, Kubernetes, automation, monitoring)',
    'solutions_architect': 'Solutions Architect (system design, cloud architecture, scalability)',
    'sre': 'Site Reliability Engineer (reliability, monitoring, incident management, SLOs)',
    'cloud_security': 'Cloud Security Engineer (IAM, security best practices, compliance)',
    'data_engineer': 'Data Engineer (ETL pipelines, data warehousing, big data, streaming)',
    'backend_developer': 'Backend Developer (APIs, databases, server-side logic, microservices)',
    'fullstack_developer': 'Full Stack Developer (frontend + backend, React/Django, databases)',
    'ml_engineer': 'ML Engineer (machine learning, model deployment, MLOps, data science)',
    'platform_engineer': 'Platform Engineer (internal developer platforms, infrastructure, tooling)',
}


@login_required
def interview_home(request):
    """Render the interview chatbot page."""
    # Get active session if any
    active_session = InterviewSession.objects.filter(
        user=request.user,
        status='active'
    ).first()

    # Stats
    total_interviews = InterviewSession.objects.filter(
        user=request.user, status='completed'
    ).count()

    completed = InterviewSession.objects.filter(user=request.user, status='completed')
    avg_score = 0
    if completed.exists():
        scores = [s.overall_score for s in completed]
        avg_score = round(sum(scores) / len(scores), 1)

    context = {
        'active_session': active_session,
        'total_interviews': total_interviews,
        'avg_score': avg_score,
        'role_choices': InterviewSession.ROLE_CHOICES,
        'difficulty_choices': InterviewSession.DIFFICULTY_CHOICES,
    }
    return render(request, 'interview/interview.html', context)


@login_required
def recent_sessions(request):
    """Render a dedicated page for browsing recent interview sessions."""
    sessions = InterviewSession.objects.filter(user=request.user).order_by('-started_at')[:20]
    active_session = InterviewSession.objects.filter(user=request.user, status='active').first()

    completed = InterviewSession.objects.filter(user=request.user, status='completed')
    avg_score = 0
    if completed.exists():
        scores = [s.overall_score for s in completed]
        avg_score = round(sum(scores) / len(scores), 1)

    context = {
        'sessions': sessions,
        'active_session': active_session,
        'active_sessions': InterviewSession.objects.filter(user=request.user, status='active').count(),
        'total_sessions': InterviewSession.objects.filter(user=request.user).count(),
        'completed_sessions': completed.count(),
        'avg_score': avg_score,
    }
    return render(request, 'interview/recent_sessions.html', context)


@login_required
@require_POST
def start_interview(request):
    """Start a new interview session."""
    try:
        role = request.POST.get('role', 'cloud_engineer')
        difficulty = request.POST.get('difficulty', 'junior')

        # End any existing active session
        InterviewSession.objects.filter(
            user=request.user, status='active'
        ).update(status='abandoned', ended_at=timezone.now())

        # Create new session
        session = InterviewSession.objects.create(
            user=request.user,
            role=role,
            difficulty=difficulty,
            status='active',
        )

        # Generate welcome message + first question using Gemini
        role_desc = ROLE_DESCRIPTIONS.get(role, role)
        diff_label = dict(InterviewSession.DIFFICULTY_CHOICES).get(difficulty, difficulty)

        prompt = f"""You are an expert technical interviewer for the role of {role_desc}.
The candidate is at {diff_label} experience level.

Start the interview with:
1. A brief, friendly greeting (1-2 lines max)
2. Then ask the FIRST technical interview question appropriate for this role and level.

IMPORTANT RULES:
- Ask exactly ONE question at a time.
- Make the question specific and practical, not generic.
- For cloud roles, focus on real-world scenarios.
- Format your response as JSON with this exact structure:
{{
    "greeting": "Your brief greeting message",
    "question": "Your first technical question"
}}
Return ONLY the JSON, nothing else."""

        model = _get_gemini_model()
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {
                "greeting": f"Welcome! Let's begin your {role_desc} interview.",
                "question": "Tell me about your experience with cloud services and infrastructure."
            }

        greeting = data.get('greeting', '')
        question = data.get('question', '')

        # Save welcome message
        InterviewMessage.objects.create(
            session=session,
            sender='bot',
            content=greeting,
            is_question=False,
        )

        # Save first question
        InterviewMessage.objects.create(
            session=session,
            sender='bot',
            content=question,
            is_question=True,
        )

        session.total_questions = 1
        session.save()

        return JsonResponse({
            'status': 'success',
            'session_id': session.id,
            'greeting': greeting,
            'question': question,
            'role': session.get_role_display(),
            'difficulty': session.get_difficulty_display(),
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def send_answer(request):
    """Process user's answer and get AI feedback + next question."""
    try:
        session_id = request.POST.get('session_id')
        user_answer = request.POST.get('answer', '').strip()

        if not user_answer:
            return JsonResponse({'status': 'error', 'message': 'Please provide an answer.'})

        session = get_object_or_404(InterviewSession, id=session_id, user=request.user, status='active')

        # Get the last question asked
        last_question = InterviewMessage.objects.filter(
            session=session, sender='bot', is_question=True
        ).last()

        if not last_question:
            return JsonResponse({'status': 'error', 'message': 'No question found to answer.'})

        # Save user's answer
        InterviewMessage.objects.create(
            session=session,
            sender='user',
            content=user_answer,
        )

        # Get conversation history for context
        messages = InterviewMessage.objects.filter(session=session).order_by('created_at')
        history = ""
        for msg in messages:
            role = "Interviewer" if msg.sender == 'bot' else "Candidate"
            history += f"{role}: {msg.content}\n"

        role_desc = ROLE_DESCRIPTIONS.get(session.role, session.role)
        diff_label = session.get_difficulty_display()

        prompt = f"""You are an expert technical interviewer for {role_desc} at {diff_label} level.

Here is the conversation so far:
{history}

The candidate just answered the question: "{last_question.content}"
Their answer was: "{user_answer}"

ANALYZE their answer and provide:
1. A rating (excellent/good/average/poor/incorrect)
2. A score from 0 to 10
3. Brief feedback explaining what was good and what could be improved (2-4 lines)
4. The ideal/expected answer for this question (2-3 lines)
5. A follow-up or next technical interview question

RESPOND ONLY IN THIS JSON FORMAT:
{{
    "rating": "good",
    "score": 7,
    "feedback": "Your feedback here...",
    "ideal_answer": "The ideal answer here...",
    "next_question": "Your next interview question here...",
    "encouragement": "A brief encouraging or constructive one-liner"
}}
Return ONLY the JSON, nothing else."""

        model = _get_gemini_model()
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Parse JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = {
                "rating": "average",
                "score": 5,
                "feedback": "Your answer covers the basics. Try to be more specific with examples.",
                "ideal_answer": "A comprehensive answer would include specific technical details and real-world examples.",
                "next_question": "Can you explain how you would design a scalable system?",
                "encouragement": "Keep going, you're doing well!"
            }

        rating = data.get('rating', 'average')
        score = min(10, max(0, int(data.get('score', 5))))
        feedback = data.get('feedback', '')
        ideal_answer = data.get('ideal_answer', '')
        next_question = data.get('next_question', '')
        encouragement = data.get('encouragement', '')

        # Save feedback message
        InterviewMessage.objects.create(
            session=session,
            sender='bot',
            content=f"{encouragement}\n\n**Feedback:** {feedback}",
            is_feedback=True,
            answer_rating=rating,
            ideal_answer=ideal_answer,
            score=score,
        )

        # Save next question
        InterviewMessage.objects.create(
            session=session,
            sender='bot',
            content=next_question,
            is_question=True,
        )

        # Update session stats
        session.total_questions += 1
        if score >= 7:
            session.correct_answers += 1
        # Running average score
        all_feedback = InterviewMessage.objects.filter(
            session=session, is_feedback=True
        )
        if all_feedback.exists():
            total_score = sum(m.score for m in all_feedback)
            session.overall_score = round((total_score / all_feedback.count()) * 10, 1)
        session.save()

        return JsonResponse({
            'status': 'success',
            'rating': rating,
            'score': score,
            'feedback': feedback,
            'ideal_answer': ideal_answer,
            'next_question': next_question,
            'encouragement': encouragement,
            'session_stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'overall_score': session.overall_score,
            }
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def end_interview(request):
    """End the interview session and generate final report."""
    try:
        session_id = request.POST.get('session_id')
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user, status='active')

        # Get all feedback messages for summary
        feedbacks = InterviewMessage.objects.filter(session=session, is_feedback=True)
        questions_asked = InterviewMessage.objects.filter(session=session, is_question=True)

        # Build summary using Gemini
        feedback_summary = ""
        for i, fb in enumerate(feedbacks, 1):
            q = questions_asked[i - 1] if i - 1 < len(questions_asked) else None
            feedback_summary += f"Q{i}: {q.content if q else 'N/A'}\n"
            feedback_summary += f"Rating: {fb.answer_rating}, Score: {fb.score}/10\n"
            feedback_summary += f"Feedback: {fb.content}\n\n"

        role_desc = ROLE_DESCRIPTIONS.get(session.role, session.role)

        prompt = f"""You are an expert technical interviewer. The interview for {role_desc} role is now complete.

Here's the summary of all questions and feedback:
{feedback_summary}

Total Questions: {session.total_questions}
Good Answers (score >= 7): {session.correct_answers}

Generate a SHORT final interview report with:
1. Overall performance summary (2-3 lines)
2. Top 3 strengths
3. Top 3 areas for improvement
4. Final verdict (Hire/Maybe/Not Ready) with brief justification
5. One study tip

RESPOND ONLY IN THIS JSON FORMAT:
{{
    "summary": "Overall performance summary...",
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["area1", "area2", "area3"],
    "verdict": "Maybe",
    "verdict_reason": "Brief justification...",
    "study_tip": "One actionable study tip..."
}}
Return ONLY the JSON, nothing else."""

        model = _get_gemini_model()
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            report = json.loads(json_match.group())
        else:
            report = {
                "summary": "Interview session completed.",
                "strengths": ["Participated actively"],
                "improvements": ["Practice more technical concepts"],
                "verdict": "Keep Practicing",
                "verdict_reason": "More preparation needed.",
                "study_tip": "Review core concepts for your target role."
            }

        # End session
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()

        return JsonResponse({
            'status': 'success',
            'report': report,
            'stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'overall_score': session.overall_score,
                'duration_minutes': session.duration_minutes,
            }
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def session_history(request, session_id):
    """Get full chat history for a session."""
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    messages = InterviewMessage.objects.filter(session=session).order_by('created_at')

    msg_list = []
    for msg in messages:
        msg_list.append({
            'sender': msg.sender,
            'content': msg.content,
            'is_question': msg.is_question,
            'is_feedback': msg.is_feedback,
            'answer_rating': msg.answer_rating,
            'ideal_answer': msg.ideal_answer,
            'score': msg.score,
            'created_at': msg.created_at.strftime('%I:%M %p'),
        })

    return JsonResponse({
        'status': 'success',
        'session': {
            'id': session.id,
            'role': session.get_role_display(),
            'difficulty': session.get_difficulty_display(),
            'status': session.status,
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'overall_score': session.overall_score,
            'started_at': session.started_at.strftime('%b %d, %Y %I:%M %p'),
        },
        'messages': msg_list,
    })
