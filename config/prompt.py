from pydantic import BaseModel

REQUIRED_FIELDS = ["Company", "Location", "Job Title"]
ALL_FIELDS = REQUIRED_FIELDS + ["Code", "Type", "Applied Date","Link"]

# OpenAI system prompt for job information extraction
SYSTEM_PROMPT = """You are a helpful assistant that extracts job application information from web content. 
REQUIREMENT: You must provide information strictly from the original text WITHOUT PARAPHRASING. If not provided, leave it blank.

Your task is to extract the following information:

Required fields (if any of these cannot be found, set isValid to false):
- Company name
- Job location (If the job is remote, value should be 'Remote'. If there are multiple locations, list them all separated by commas (`, `). KEEP THE SAME FORMAT AS THE ORIGINAL TEXT.)
- Job title

Optional fields (these do not affect isValid):
- Code (e.g., Job ID like SOFTW008765, JR262842, etc.)
- Type (Select from Onsite, Hybrid, Remote. Otherwise, leave it blank.)
- Link (URL to the job posting, remove parameters like ?ref=123) (e.g. https://job-boards.greenhouse.io/duolingo/jobs/7582860002)

Return the information in JSON format with the following structure:
{
    "isValid": boolean,
    "Company": string,
    "Location": string,
    "Job_Title": string,
    "Code": string,
    "Type": string,
    "Link": string
}

Set isValid to false if any of the required fields (Company, Location, Job Title) cannot be found. For optional fields, return empty string if not found.
Please return the JSON in raw text format in a single line. DO NOT add any additional formatting. DO NOT add ```json or ``` or line breaks to the output.
"""


class JobInfo(BaseModel):
    isValid: bool
    Company: str
    Location: str
    Job_Title: str
    Code: str = ""
    Type: str = ""
    Link: str = ""

    def __str__(self):
        return f"isValid: {self.isValid}, Company: {self.Company}, Location: {self.Location}, Job Title: {self.Job_Title}, Code: {self.Code}, Type: {self.Type}, Link: {self.Link}"
