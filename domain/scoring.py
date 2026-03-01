from dataclasses import dataclass
from domain.job import Job
from domain.resume import ResumeProfile


@dataclass
class ScoreResult:
    final_score: float               # 0.0 – 100.0
    keyword_coverage: float          # % of required skills matched
    missing_skills: list[str]        # skills in job not in resume
    matched_skills: list[str]        # skills in both job and resume
    experience_gap: int              # years short of requirement (0 = met)
    hard_mismatch: bool              # true if YOE gap > 3 years


class ScoringEngine:
    def __init__(self, yoe_weight: float = 0.25, skill_weight: float = 0.75):
        self.yoe_weight = yoe_weight
        self.skill_weight = skill_weight

    def score(self, job: Job, resume: ResumeProfile) -> ScoreResult:
        resume_skills = {s.lower() for s in resume.skills}
        job_skills = {s.lower() for s in job.required_skills}

        # Skill matching
        matched = list(job_skills & resume_skills)
        missing = list(job_skills - resume_skills)

        coverage = len(matched) / len(job_skills) if job_skills else 1.0

        # Experience alignment
        gap = max(0, job.required_years - resume.experience_years)
        hard_mismatch = gap > 3

        # YOE score: full marks if gap == 0, zero if gap >= 5
        yoe_score = max(0.0, 1.0 - (gap / 5))

        # Final weighted score
        final = (coverage * self.skill_weight + yoe_score * self.yoe_weight) * 100

        return ScoreResult(
            final_score=round(final, 1),
            keyword_coverage=round(coverage * 100, 1),
            missing_skills=sorted(missing),
            matched_skills=sorted(matched),
            experience_gap=gap,
            hard_mismatch=hard_mismatch,
        )