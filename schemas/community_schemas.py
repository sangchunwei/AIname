from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PollOptionIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    moral: str | None = Field(default=None, max_length=1000)


class CommunityPostCreate(BaseModel):
    post_type: Literal["discussion", "name_poll"] = "discussion"
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    options: list[PollOptionIn] = Field(default_factory=list, max_length=8)


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: int | None = None


class VoteIn(BaseModel):
    option_id: int


class PollOptionOut(BaseModel):
    id: int
    name: str
    moral: str | None
    vote_count: int


class CommentOut(BaseModel):
    id: int
    user_id: int
    author_name: str
    content: str
    parent_comment_id: int | None = None
    reply_to_author: str | None = None
    like_count: int = 0
    liked_by_me: bool = False
    created_at: datetime


class CommunityPostOut(BaseModel):
    id: int
    user_id: int
    author_name: str
    post_type: str
    title: str
    content: str
    like_count: int
    comment_count: int
    vote_count: int
    liked_by_me: bool
    my_vote_option_id: int | None
    created_at: datetime
    options: list[PollOptionOut] = Field(default_factory=list)
    comments: list[CommentOut] = Field(default_factory=list)


class CommunityPostListOut(BaseModel):
    total: int
    page: int
    page_size: int
    posts: list[CommunityPostOut]
