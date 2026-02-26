from dataclasses import dataclass


@dataclass
class ResumeProfile:
    name: str
    skills: list[str]                # e.g. ["Docker", "Terraform", "AWS", "Python"]
    experience_years: int            # total years of experience
    domains: list[str]               # e.g. ["SRE", "DevOps", "Cloud"]
    certifications: list[str]        # e.g. ["AWS Certified Cloud Practitioner"]