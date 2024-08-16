# Web Scraper and Security Analyzer

This project consists of two Python scripts: a web scraper (`scrape.py`) and a security analyzer (`scan.py`). The web scraper downloads content from a specified website, and the security analyzer examines the downloaded code for potential vulnerabilities.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/ehsan329/scraper.git
   cd scraper
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Google AI API key:
   - Obtain an API key from the Google AI Platform.
   - Replace `'API'` in the `genai.configure(api_key='API')` line of `scan.py` with your actual API key.

## Usage

1. Run the web scraper:
   ```
   python scrape.py
   ```
   This will download content from the specified website (default: https://ai.google.dev/competition) to the `downloaded_content` directory.

2. Run the security analyzer:
   ```
   python scan.py
   ```
   This will analyze the downloaded content for potential vulnerabilities and generate reports in the `ai_responses2` directory.

## Features

### Web Scraper (scrape.py)
- Crawls websites up to a specified depth
- Downloads HTML, JavaScript, and CSS content
- Beautifies JavaScript and CSS files
- Extracts and saves potential API endpoints
- Captures dynamic content using Playwright
- Attempts to deobfuscate JavaScript code

### Security Analyzer (scan.py)
- Analyzes code for various security vulnerabilities
- Generates detailed reports on found vulnerabilities
- Provides severity ratings and mitigation strategies
- Uses the Google Gemini 1.5 Pro/flash AI model for analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
