from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from domain.profile import SearchProfile, ExperienceLevel, LocationPref
from infrastructure.repositories import ProfileRepository

router = APIRouter()


class ProfileCreate(BaseModel):
    user_id: str
    name: str
    role_keywords: list[str]
    required_stack: list[str]
    preferred_stack: list[str] = []
    experience_level: str = "entry"
    location_pref: str = "any"
    min_match_score: float = 0.0
    skills: list[str] = []
    experience_years: int = 0
    certifications: list[str] = []
    companies: list[str] = []


@router.post("")
def create_profile(body: ProfileCreate):
    try:
        profile = SearchProfile(
            user_id=body.user_id,
            name=body.name,
            role_keywords=body.role_keywords,
            required_stack=body.required_stack,
            preferred_stack=body.preferred_stack,
            experience_level=ExperienceLevel(body.experience_level),
            location_pref=LocationPref(body.location_pref),
            min_match_score=body.min_match_score,
            skills=body.skills,
            experience_years=body.experience_years,
            certifications=body.certifications,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ProfileRepository().save(profile)
    return {"user_id": body.user_id, "created": True}


@router.post("")
def create_profile(body: ProfileCreate):
    try:
        profile = SearchProfile(
            user_id=body.user_id,
            name=body.name,
            role_keywords=body.role_keywords,
            required_stack=body.required_stack,
            preferred_stack=body.preferred_stack,
            experience_level=ExperienceLevel(body.experience_level),
            location_pref=LocationPref(body.location_pref),
            min_match_score=body.min_match_score,
            skills=body.skills,
            experience_years=body.experience_years,
            certifications=body.certifications,
            companies=body.companies,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ProfileRepository().save(profile)
    return {"user_id": body.user_id, "created": True}


@router.get("/{user_id}")
def get_profile(user_id: str):
    profile = ProfileRepository().get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("")
def list_profiles():
    profiles = ProfileRepository().get_all_active()
    return {"profiles": profiles, "total": len(profiles)}