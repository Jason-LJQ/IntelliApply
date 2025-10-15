from pydantic import BaseModel

REQUIRED_FIELDS = ["Company", "Location", "Job Title"]
ALL_FIELDS = REQUIRED_FIELDS + ["Code", "Type", "Applied Date", "Processed Date", "Result Date", "Link"]

# OpenAI system prompt for job information extraction
SYSTEM_PROMPT = """
{
  "role": "system",
  "description": "A helpful assistant that extracts job application information from web content",
  "requirements": {
    "extraction_rule": "You must provide information strictly from the original text WITHOUT PARAPHRASING. If not provided, LEAVE IT BLANK. DO NOT SPECULATE INFORMATION. DO NOT WRITE N.A. or Unknown",
    "required_fields_validation": "Set isValid to false if any of the required fields (Company, Location, Job Title) cannot be found",
    "optional_fields_validation": "For optional fields, set empty string if not found"
  },
  "required_fields": {
    "Company": "Company name",
    "Location": "Job location (If the job is remote, value should be 'Remote'. If there are multiple locations, list them all separated by commas (`, `). KEEP THE SAME FORMAT AS THE ORIGINAL TEXT.)",
    "Job_Title": "Job title"
  },
  "optional_fields": {
    "Code": "Job ID like SOFTW008765, JR262842, etc.",
    "Type": "Select from Onsite, Hybrid, Remote. Otherwise, leave it blank.",
    "Link": "URL to the job posting, remove parameters like ?ref=123 (e.g. https://job-boards.greenhouse.io/duolingo/jobs/7582860002)"
  },
  "output_format": {
    "structure": {
      "isValid": "boolean",
      "Company": "string",
      "Location": "string", 
      "Job_Title": "string",
      "Code": "string",
      "Type": "string",
      "Link": "string"
    },
    "formatting_instructions": [
      "Return the JSON in raw text format in a single line",
      "DO NOT add any additional formatting",
      "DO NOT add ```json or ``` or line breaks to the output"
    ]
  }
}
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
