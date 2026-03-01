import pytest
from domain.job import Job
from domain.resume import ResumeProfile
from domain.scoring import ScoringEngine


@pytest.fixture
def engine():
    return ScoringEngine()


@pytest.fixture
def resume():
    return ResumeProfile(
        name="Test",
        skills=["docker", "terraform", "aws", "python", "github actions"],
        experience_years=2,
        domains=["DevOps"],
        certifications=[],
    )


def make_job(**kwargs):
    defaults = dict(
        id="test-1",
        title="SRE Engineer",
        company="testco",
        location="Remote",
        description="",
        required_skills=["docker", "terraform", "aws"],
        required_years=2,
        source="greenhouse",
        source_url="https://example.com",
    )
    defaults.update(kwargs)
    return Job(**defaults)


def test_perfect_match(engine, resume):
    job = make_job(required_skills=["docker", "terraform", "aws"], required_years=2)
    result = engine.score(job, resume)
    assert result.final_score == 100.0
    assert result.missing_skills == []
    assert result.experience_gap == 0
    assert result.hard_mismatch is False


def test_partial_skill_match(engine, resume):
    job = make_job(required_skills=["docker", "kubernetes", "terraform"], required_years=2)
    result = engine.score(job, resume)
    assert result.keyword_coverage < 100.0
    assert "kubernetes" in result.missing_skills
    assert "docker" in result.matched_skills
    assert "terraform" in result.matched_skills


def test_yoe_gap(engine, resume):
    job = make_job(required_skills=["docker"], required_years=4)
    result = engine.score(job, resume)
    assert result.experience_gap == 2
    assert result.hard_mismatch is False  # gap <= 3


def test_hard_mismatch(engine, resume):
    job = make_job(required_skills=["docker"], required_years=6)
    result = engine.score(job, resume)
    assert result.experience_gap == 4
    assert result.hard_mismatch is True


def test_no_required_skills(engine, resume):
    job = make_job(required_skills=[], required_years=0)
    result = engine.score(job, resume)
    assert result.final_score == 100.0


def test_score_range(engine, resume):
    job = make_job(required_skills=["docker", "kubernetes", "helm"], required_years=5)
    result = engine.score(job, resume)
    assert 0.0 <= result.final_score <= 100.0