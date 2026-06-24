from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.community import CommunityComment, CommunityCommentLike, CommunityLike, CommunityPost, NamePollOption, NamePollVote
from models.user import User
from schemas.community_schemas import (
    CommentCreate, CommunityPostCreate, CommunityPostListOut, CommunityPostOut, VoteIn,
)


router = APIRouter(prefix="/community", tags=["社区与灵感投票"])
auth_handler = AuthHandler()


async def get_post_or_404(post_id: int, session: AsyncSession) -> CommunityPost:
    post = await session.scalar(
        select(CommunityPost).where(CommunityPost.id == post_id, CommunityPost.status == "published")
    )
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post


async def serialize_post(post: CommunityPost, user_id: int, session: AsyncSession, include_comments: bool = False):
    author = await session.scalar(select(User).where(User.id == post.user_id))
    liked = await session.scalar(
        select(CommunityLike.id).where(CommunityLike.post_id == post.id, CommunityLike.user_id == user_id)
    )
    vote = await session.scalar(
        select(NamePollVote).where(NamePollVote.post_id == post.id, NamePollVote.user_id == user_id)
    )
    options = list(
        (await session.scalars(select(NamePollOption).where(NamePollOption.post_id == post.id).order_by(NamePollOption.id))).all()
    )
    comments_out = []
    if include_comments:
        rows = (
            await session.execute(
                select(CommunityComment, User.username)
                .join(User, User.id == CommunityComment.user_id)
                .where(CommunityComment.post_id == post.id, CommunityComment.status == "published")
                .order_by(CommunityComment.id)
            )
        ).all()
        comment_author_by_id = {comment.id: username for comment, username in rows}
        comments_out = []
        for comment, username in rows:
            liked_comment = await session.scalar(
                select(CommunityCommentLike.id).where(
                    CommunityCommentLike.comment_id == comment.id,
                    CommunityCommentLike.user_id == user_id,
                )
            )
            comments_out.append({
                "id": comment.id,
                "user_id": comment.user_id,
                "author_name": username,
                "content": comment.content,
                "parent_comment_id": comment.parent_comment_id,
                "reply_to_author": comment_author_by_id.get(comment.parent_comment_id),
                "like_count": comment.like_count,
                "liked_by_me": bool(liked_comment),
                "created_at": comment.created_at,
            })
    return {
        "id": post.id, "user_id": post.user_id,
        "author_name": author.username if author else "已注销用户",
        "post_type": post.post_type, "title": post.title, "content": post.content,
        "like_count": post.like_count, "comment_count": post.comment_count,
        "vote_count": post.vote_count, "liked_by_me": bool(liked),
        "my_vote_option_id": vote.option_id if vote else None,
        "created_at": post.created_at,
        "options": [{"id": item.id, "name": item.name, "moral": item.moral, "vote_count": item.vote_count} for item in options],
        "comments": comments_out,
    }


@router.post("/posts", response_model=CommunityPostOut)
async def create_post(
    data: CommunityPostCreate,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    if data.post_type == "name_poll" and not 2 <= len(data.options) <= 8:
        raise HTTPException(status_code=400, detail="名字投票需要 2 到 8 个候选项")
    post = CommunityPost(user_id=user_id, post_type=data.post_type, title=data.title, content=data.content)
    session.add(post)
    await session.flush()
    if data.post_type == "name_poll":
        session.add_all([NamePollOption(post_id=post.id, name=item.name, moral=item.moral) for item in data.options])
    await session.commit()
    await session.refresh(post)
    return await serialize_post(post, user_id, session, True)


@router.get("/posts", response_model=CommunityPostListOut)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    post_type: str | None = Query(default=None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    filters = [CommunityPost.status == "published"]
    if post_type in {"discussion", "name_poll"}:
        filters.append(CommunityPost.post_type == post_type)
    total = await session.scalar(select(func.count(CommunityPost.id)).where(*filters))
    posts = list((await session.scalars(
        select(CommunityPost).where(*filters).order_by(CommunityPost.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all())
    return {"total": total or 0, "page": page, "page_size": page_size,
            "posts": [await serialize_post(post, user_id, session, True) for post in posts]}


@router.get("/posts/{post_id}", response_model=CommunityPostOut)
async def get_post(
    post_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await serialize_post(await get_post_or_404(post_id, session), user_id, session, True)


@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    post = await get_post_or_404(post_id, session)
    liked = await session.scalar(select(CommunityLike).where(CommunityLike.post_id == post_id, CommunityLike.user_id == user_id))
    if liked:
        await session.delete(liked)
        post.like_count = max(0, post.like_count - 1)
        active = False
    else:
        session.add(CommunityLike(post_id=post_id, user_id=user_id))
        post.like_count += 1
        active = True
    await session.commit()
    return {"liked": active, "like_count": post.like_count}


@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    data: CommentCreate,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    post = await get_post_or_404(post_id, session)
    if data.parent_comment_id is not None:
        parent = await session.scalar(
            select(CommunityComment).where(
                CommunityComment.id == data.parent_comment_id,
                CommunityComment.post_id == post_id,
                CommunityComment.status == "published",
            )
        )
        if not parent:
            raise HTTPException(status_code=404, detail="回复的评论不存在")
    comment = CommunityComment(
        post_id=post_id,
        parent_comment_id=data.parent_comment_id,
        user_id=user_id,
        content=data.content,
    )
    session.add(comment)
    post.comment_count += 1
    await session.commit()
    return {"message": "评论成功"}


@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    comment = await session.scalar(
        select(CommunityComment).where(CommunityComment.id == comment_id, CommunityComment.status == "published")
    )
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    liked = await session.scalar(
        select(CommunityCommentLike).where(
            CommunityCommentLike.comment_id == comment_id,
            CommunityCommentLike.user_id == user_id,
        )
    )
    if liked:
        await session.delete(liked)
        comment.like_count = max(0, comment.like_count - 1)
        active = False
    else:
        session.add(CommunityCommentLike(comment_id=comment_id, user_id=user_id))
        comment.like_count += 1
        active = True
    await session.commit()
    return {"liked": active, "like_count": comment.like_count}


@router.post("/posts/{post_id}/vote")
async def vote_poll(
    post_id: int,
    data: VoteIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    post = await get_post_or_404(post_id, session)
    if post.post_type != "name_poll":
        raise HTTPException(status_code=400, detail="该帖子不是名字投票")
    option = await session.scalar(select(NamePollOption).where(NamePollOption.id == data.option_id, NamePollOption.post_id == post_id))
    if not option:
        raise HTTPException(status_code=400, detail="候选名字不存在")
    vote = await session.scalar(select(NamePollVote).where(NamePollVote.post_id == post_id, NamePollVote.user_id == user_id))
    if vote and vote.option_id == option.id:
        return {"message": "你已经投过该选项", "option_id": option.id}
    if vote:
        old_option = await session.scalar(select(NamePollOption).where(NamePollOption.id == vote.option_id))
        if old_option:
            old_option.vote_count = max(0, old_option.vote_count - 1)
        vote.option_id = option.id
    else:
        session.add(NamePollVote(post_id=post_id, option_id=option.id, user_id=user_id))
        post.vote_count += 1
    option.vote_count += 1
    await session.commit()
    return {"message": "投票成功", "option_id": option.id}


@router.delete("/posts/{post_id}/vote")
async def cancel_vote_poll(
    post_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    post = await get_post_or_404(post_id, session)
    if post.post_type != "name_poll":
        raise HTTPException(status_code=400, detail="该帖子不是名字投票")
    vote = await session.scalar(
        select(NamePollVote).where(NamePollVote.post_id == post_id, NamePollVote.user_id == user_id)
    )
    if not vote:
        return {"message": "当前没有投票记录", "option_id": None}
    option = await session.scalar(select(NamePollOption).where(NamePollOption.id == vote.option_id))
    if option:
        option.vote_count = max(0, option.vote_count - 1)
    post.vote_count = max(0, post.vote_count - 1)
    await session.delete(vote)
    await session.commit()
    return {"message": "已取消投票", "option_id": None}


@router.delete("/posts/{post_id}")
async def delete_own_post(
    post_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    post = await session.scalar(select(CommunityPost).where(CommunityPost.id == post_id, CommunityPost.user_id == user_id))
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.status = "deleted"
    await session.commit()
    return {"message": "帖子已删除"}
