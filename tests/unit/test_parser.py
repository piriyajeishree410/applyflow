from services.parser import extract_skills, extract_years


def test_extract_known_skills():
    text = "We need Terraform, Docker, and AWS experience."
    skills = extract_skills(text)
    assert "terraform" in skills
    assert "docker" in skills
    assert "aws" in skills


def test_extract_skills_case_insensitive():
    text = "Experience with KUBERNETES and Python required."
    skills = extract_skills(text)
    assert "kubernetes" in skills
    assert "python" in skills


def test_extract_skills_no_false_positives():
    text = "We are a great company with amazing culture."
    skills = extract_skills(text)
    assert skills == []


def test_extract_years_plus_format():
    assert extract_years("Requires 3+ years of experience") == 3


def test_extract_years_range_format():
    assert extract_years("5-7 years experience required") == 5


def test_extract_years_plain_format():
    assert extract_years("You have 4 years of experience") == 4


def test_extract_years_not_found():
    assert extract_years("No experience required") == 0


def test_extract_years_multiple_takes_minimum():
    text = "2+ years required, ideally 5 years of experience"
    assert extract_years(text) == 2