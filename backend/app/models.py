"""
SQLAlchemy declarative models for Re:Learn.
Tables: learners, problems, submissions, diagnoses, probe_events,
        reassessments, learner_misconceptions
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, JSON, Boolean, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Learner(Base):
    __tablename__ = "learners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, default="anonymous")
    session_token = Column(String(64), unique=True, nullable=False)
    code = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="learner")
    diagnoses = relationship("Diagnosis", back_populates="learner")
    probe_events = relationship("ProbeEvent", back_populates="learner")
    reassessments = relationship("Reassessment", back_populates="learner")
    misconceptions = relationship("LearnerMisconception", back_populates="learner")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(64), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    reference_solution = Column(Text, nullable=False)
    test_cases = Column(JSON, nullable=False)   # list of {input, expected_output}
    misconception_tags = Column(JSON)            # list of M-codes e.g. ["M1","M2"]
    difficulty = Column(String(20), default="intro")
    created_at = Column(DateTime, default=datetime.utcnow)

    submissions = relationship("Submission", back_populates="problem")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    code = Column(Text, nullable=False)
    passed_tests = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    execution_signature = Column(JSON)      # output vector across fixed inputs
    ast_features = Column(JSON)             # extracted AST feature dict
    trace_frames = Column(JSON)             # list of frame snapshots from tracer
    submitted_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    diagnosis = relationship("Diagnosis", back_populates="submission", uselist=False)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    probabilities = Column(JSON, nullable=False)   # {"M0": 0.1, "M1": 0.7, ...}
    top_misconception = Column(String(10))
    confidence = Column(Float, default=0.0)
    probe_required = Column(Boolean, default=False)
    probe_question_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="diagnoses")
    submission = relationship("Submission", back_populates="diagnosis")
    probe_events = relationship("ProbeEvent", back_populates="diagnosis")


class ProbeEvent(Base):
    __tablename__ = "probe_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.id"), nullable=False)
    question_id = Column(String(64), nullable=False)
    selected_option = Column(String(10), nullable=False)    # "A", "B", or "C"
    correct_option = Column(String(10), nullable=False)
    updated_probabilities = Column(JSON)
    is_correct = Column(Boolean)
    answered_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="probe_events")
    diagnosis = relationship("Diagnosis", back_populates="probe_events")


class Reassessment(Base):
    __tablename__ = "reassessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    original_diagnosis_id = Column(Integer, ForeignKey("diagnoses.id"))
    transfer_problem_id = Column(Integer, ForeignKey("problems.id"))
    counter_probe_problem_id = Column(Integer, ForeignKey("problems.id"))
    transfer_code = Column(Text)
    counter_probe_code = Column(Text)
    transfer_passed = Column(Boolean)
    counter_probe_passed = Column(Boolean)
    verdict = Column(String(20))    # "RESOLVED", "SUPPRESSED", "UNRESOLVED"
    assessed_at = Column(DateTime, default=datetime.utcnow)

    learner = relationship("Learner", back_populates="reassessments")


class LearnerMisconception(Base):
    __tablename__ = "learner_misconceptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    misconception_code = Column(String(10), nullable=False)   # e.g. "M1"
    misconception_label = Column(String(200))
    status = Column(String(20), default="active")   # active, resolved, suppressed
    first_detected_at = Column(DateTime, default=datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    learner = relationship("Learner", back_populates="misconceptions")
