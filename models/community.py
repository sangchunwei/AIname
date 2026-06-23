from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class CommunityPost(Base):
    __tablename__ = "community_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    post_type: Mapped[str] = mapped_column(String(30), default="discussion", index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="published", index=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    comment_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class CommunityComment(Base):
    __tablename__ = "community_comment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_post.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CommunityLike(Base):
    __tablename__ = "community_like"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_community_like_post_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_post.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class NamePollOption(Base):
    __tablename__ = "name_poll_option"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_post.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class NamePollVote(Base):
    __tablename__ = "name_poll_vote"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_name_poll_vote_post_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_post.id"), index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("name_poll_option.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
