# Radact - Document Redaction Tool

A simple C# console application that reads DOCX files and redacts sensitive information such as names, emails, phone numbers, and other personally identifiable information (PII).

## Features

- Reads Microsoft Word (.docx) documents
- Redacts multiple types of sensitive information:
  - Personal names
  - Email addresses
  - Phone numbers
  - Social Security Numbers (SSN)
  - Credit card numbers
  - IP addresses
  - Passwords and API keys
  - Dates
- Saves redacted content as text files with "redact_" prefix

## Prerequisites

- .NET 10.0 or later
- DocumentFormat.OpenXml package (already included)

## Project Structure

```
Radact/
├── Program.cs          # Main application code
├── Radact.csproj      # Project configuration
├── docs/              # Input and output directory
│   ├── 1.docx        # Sample input document
│   └── redact_1.txt  # Generated redacted output
└── README.md         # This file
```

## How to Run

1. **Clone or navigate to the project directory:**
   ```bash
   cd /path/to/Radact
   ```

2. **Place your DOCX file in the docs folder:**
   - The application currently processes `docs/1.docx`
   - Replace this file with your document or modify the path in Program.cs

3. **Run the application:**
   ```bash
   dotnet run
   ```

4. **View the results:**
   - Original content will be displayed in the console
   - Redacted content will be displayed in the console
   - Redacted content will be saved to `docs/redact_1.txt`

## Example Output

```
Document content loaded successfully!
Content length: 1450 characters

--- Original Document Content ---
From: Jonathan Miller – Senior Security Analyst
Email: j.miller@company.com
...

--- Redacted Document Content ---
From: [NAME_REDACTED] – [NAME_REDACTED] Analyst
Email: [EMAIL_REDACTED]
...

Redacted content saved to: docs/redact_1.txt
```

## Customization

To process different files or modify redaction rules:

1. **Change input file:** Edit the `docxFilePath` variable in Program.cs
2. **Add redaction rules:** Modify the `InitializeRedactionRules()` method in the `DocumentRedactor` class
3. **Change output format:** Modify the `GenerateOutputPath()` method in the `DocumentWriter` class

## Architecture

The application follows Object-Oriented Programming principles with the following classes:

- **DocumentProcessor:** Main workflow orchestrator
- **DocumentReader:** Handles DOCX file reading
- **DocumentRedactor:** Applies redaction rules to content
- **DocumentWriter:** Saves redacted content to files
- **RedactionRule:** Represents individual redaction patterns

## Build

To build the project without running:

```bash
dotnet build
```

To create a release build:

```bash
dotnet build --configuration Release
```
