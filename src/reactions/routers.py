from fastapi import Depends, APIRouter, Form, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.utils import FORADMIN, get_current_user, get_current_user_cookies
from src.models.models import User, Reaction
from src.reactions.repos import ReactionRepository
from src.reactions.schemas import ReactionResponse, ReactionRequest
from src.utils.front_end_utils import get_response_format

reaction_router = APIRouter()

@reaction_router.post(
    "/create/",
    summary="Create a new tag",
    description="""
    Creates a new tag with the specified name. 
    The tag name must be unique and should not exceed 50 characters.
    """,
    status_code=status.HTTP_201_CREATED,
    dependencies=FORADMIN
)
async def create_tag(
    reaction_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    response_format: str = Depends(get_response_format)
):
    """
    Endpoint to create a new tag.

    This endpoint allows the creation of a new tag in the database. If a tag with the same name already exists,
    it will be returned instead of creating a duplicate.

    :param reaction_name: The name of the reaction to create (required).
    :param db: Database session dependency.
    :param response_format: Swagger or HTML?
    :return: The newly created or existing tag as a `TagResponse` model.
    """
    reaction_repo = ReactionRepository(db)
    reaction = await reaction_repo.create_reaction(reaction_name=reaction_name)
    if response_format == 'json':
        return reaction


@reaction_router.post(
    "/add_reaction/",
    status_code=status.HTTP_201_CREATED,
)
async def add_reaction_to_photo(
        request: Request,
        reaction_data: ReactionRequest,
        db: AsyncSession = Depends(get_db),) -> dict:
    user = await get_current_user_cookies(request, db)
    reaction_repo = ReactionRepository(db)

    result = await reaction_repo.add_reaction(
        reaction_data.photo_id,
        user.id,
        reaction_data.reaction_id
    )

    reaction_counts = await reaction_repo.get_reaction_counts(reaction_data.photo_id)

    return {
        "reaction_counts": reaction_counts,
        "current_reaction": result.reaction_id if result else None
    }


@reaction_router.post(
    "/get_reaction/",
    status_code=status.HTTP_200_OK,
    response_model=ReactionResponse
)
async def get_reaction_by_user_and_photo(
        photo_id: int,
        user_id: int,
        db: AsyncSession = Depends(get_db),):
    reaction_repo = ReactionRepository(db)
    reaction = await reaction_repo.get_reaction_by_user_and_photo(photo_id, user_id)

    if reaction:
        return reaction
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found"
        )


@reaction_router.post(
    "/get_all_reactions_by_photo/",
    status_code=status.HTTP_200_OK,
)
async def get_reaction_by_user_and_photo(
        photo_id: int,
        db: AsyncSession = Depends(get_db),):
    reaction_repo = ReactionRepository(db)
    reactions = await reaction_repo.get_all_reactions_by_photo(photo_id)

    if reactions:
        return reactions
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reactions not found"
        )


@reaction_router.post(
    "/change_reaction/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReactionResponse
)
async def change_reaction(
        photo_id: int,
        new_reaction_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),):

    reaction_repo = ReactionRepository(db)
    reaction = await reaction_repo.change_reaction(photo_id, user.id, new_reaction_id)

    if reaction:
        return reaction
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found"
        )

@reaction_router.post(       
    "/delete_reaction/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=str
)
async def delete_reaction(
        photo_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db), ):

    reaction_repo = ReactionRepository(db)
    reaction = await reaction_repo.delete_reaction(photo_id, user.id)

    if reaction:
        return reaction
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found"
        )

