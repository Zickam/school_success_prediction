from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Integer, String, UUID, Enum, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship

from ..engine import Base
from ..schemas.user import Roles
from ..schemas.invitation import InvitationType, InvitationStatus
from . import user_class_table

class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(Integer, unique=True)
    role = Column(Enum(Roles))
    name = Column(String)
    teacher_subjects = Column(JSON, nullable=True)  # List of subject UUIDs for subject teachers
    parent_children = Column(JSON, nullable=True)  # List of child UUIDs for parents
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes = relationship("Class", secondary=user_class_table, back_populates="users")
    grades = relationship("Grade", back_populates="user")
    
    # For homeroom teachers - the class they manage
    managed_class = relationship("Class", back_populates="homeroom_teacher", uselist=False)
    
    # For parents - their children
    children = relationship("User", 
                          secondary="parent_child",
                          primaryjoin="User.uuid==parent_child.c.parent_uuid",
                          secondaryjoin="User.uuid==parent_child.c.child_uuid",
                          backref="parents")
    
    # Invitation relationships
    sent_invitations = relationship("Invitation", 
                                  back_populates="inviter",
                                  foreign_keys="[Invitation.inviter_uuid]")
    parent_invitations = relationship("Invitation",
                                    back_populates="child",
                                    foreign_keys="[Invitation.child_uuid]")


class School(Base):
    __tablename__ = "schools"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    facility_name = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    classes = relationship("Class", back_populates="school")


class Class(Base):
    __tablename__ = "classes"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    start_year = Column(Integer)
    class_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school_uuid = Column(UUID(as_uuid=True), ForeignKey('schools.uuid'))
    school = relationship("School", back_populates="classes")
    users = relationship("User", secondary=user_class_table, back_populates="classes")
    subjects = relationship("Subject", back_populates="class_")
    
    # Homeroom teacher relationship
    homeroom_teacher_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), nullable=True)
    homeroom_teacher = relationship("User", back_populates="managed_class", foreign_keys=[homeroom_teacher_uuid])
    
    # Invitations
    invitations = relationship("Invitation", back_populates="class_")


class Subject(Base):
    __tablename__ = "subjects"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class_uuid = Column(UUID(as_uuid=True), ForeignKey('classes.uuid'))
    class_ = relationship("Class", back_populates="subjects")
    grades = relationship("Grade", back_populates="subject")
    invitations = relationship("Invitation", back_populates="subject")

    def __repr__(self):
        return f"<Subject {self.name}>"


class Grade(Base):
    __tablename__ = "grades"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    value = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    subject_uuid = Column(UUID(as_uuid=True), ForeignKey('subjects.uuid'))
    
    user = relationship("User", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")


class Invitation(Base):
    __tablename__ = 'invitations'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(Enum(InvitationType))
    role = Column(Enum(Roles))
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    class_uuid = Column(UUID(as_uuid=True), ForeignKey('classes.uuid'), nullable=True)
    subject_uuid = Column(UUID(as_uuid=True), ForeignKey('subjects.uuid'), nullable=True)
    child_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), nullable=True)
    inviter_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))

    # Relationships
    class_ = relationship("Class", back_populates="invitations")
    subject = relationship("Subject", back_populates="invitations")
    child = relationship("User", 
                        back_populates="parent_invitations",
                        foreign_keys="[Invitation.child_uuid]")
    inviter = relationship("User", 
                          back_populates="sent_invitations",
                          foreign_keys="[Invitation.inviter_uuid]") 