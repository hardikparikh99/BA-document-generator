# BA Document Generator

A web-based document generation system that leverages AI to create professional Business Analysis documents.

## Project Structure

```
BA-document-generator/
├── agents/           # AI agents and language models
├── app.py            # Main Flask application
├── data/             # Data files and templates
├── logs/             # Application logs
├── main.py           # Main entry point
├── models/           # AI models and configurations
├── requirements.txt  # Python dependencies
├── services/         # Business logic and services
├── static/           # Static assets (CSS, JS, images)
├── temp_files/       # Temporary files
├── templates/        # HTML templates
└── utils/           # Utility functions and helpers
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hardikparikh99/BA-document-generator.git
cd BA-document-generator
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy the `.env.example` file to `.env` and configure your environment variables:
```bash
cp .env.example .env
```

4. Run the application:
```bash
# For Flask application (default)
python app.py

# For FastAPI application
uvicorn main:app --reload

# For Streamlit application
streamlit run main.py
```

## Usage

1. Access the application at the appropriate URL based on the server you're running:
   - Flask: `http://localhost:5000`
   - FastAPI: `http://localhost:8000`
   - Streamlit: `http://localhost:8501`
2. Upload your requirements or input text
3. Generate professional BA documents using AI
4. Download the generated documents

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details

## Support

For support, please open an issue in the GitHub repository or contact the maintainers directly.

## Project Status

This project is actively maintained and under development. Contributions and feedback are welcome!
