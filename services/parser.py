import re

# Master skill list — covers SRE / DevOps / Cloud / Backend
KNOWN_SKILLS = [
    # Cloud
    "aws", "gcp", "azure", "cloud run", "ec2", "s3", "ecs", "eks", "fargate",
    "lambda", "cloudwatch", "rds", "iam", "route53", "cloudfront",
    # Containers & Orchestration
    "docker", "kubernetes", "k8s", "helm", "ecs", "containerd",
    # IaC & Config
    "terraform", "ansible", "pulumi", "cloudformation", "chef", "puppet",
    # CI/CD
    "github actions", "jenkins", "gitlab ci", "circleci", "argocd", "spinnaker",
    # Observability
    "prometheus", "grafana", "datadog", "splunk", "elk", "elasticsearch",
    "cloudwatch", "jaeger", "opentelemetry", "pagerduty",
    # Languages & Scripting
    "python", "go", "golang", "bash", "shell", "ruby", "java", "typescript",
    # Databases
    "postgresql", "postgres", "mysql", "redis", "mongodb", "cassandra",
    "dynamodb", "elasticsearch",
    # Networking
    "dns", "tcp/ip", "nginx", "load balancing", "vpn", "vpc",
    # Practices
    "sre", "devops", "gitops", "on-call", "incident response",
    "slo", "sli", "sla", "chaos engineering",
    # Version Control
    "git", "github", "gitlab",
]

# Regex to extract years of experience — matches patterns like:
# "3+ years", "2-4 years", "5 years of experience"
YOE_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:to|-)\s*\d*\s*years?|(\d+)\+?\s*years?\s*(?:of\s+)?experience",
    re.IGNORECASE,
)


def extract_skills(text: str) -> list[str]:
    """Return a deduplicated list of known skills found in the text."""
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        if skill in text_lower and skill not in found:
            found.append(skill)
    return found


def extract_years(text: str) -> int:
    """Return the minimum years of experience required. 0 if not found."""
    matches = YOE_PATTERN.findall(text)
    years = []
    for m in matches:
        val = m[0] or m[1]
        if val:
            years.append(int(val))
    return min(years) if years else 0