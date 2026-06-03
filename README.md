# Mutual Fund FAQ Assistant

A facts-only Q&A assistant for HDFC mutual fund schemes using RAG (Retrieval-Augmented Generation) approach.

## Project Structure

```
Milestone2/
├── backend/                    # FastAPI backend with RAG pipeline
│   ├── config/               # Configuration files
│   ├── database/             # ChromaDB setup and management
│   ├── llm/                 # Groq LLM integration
│   ├── processing/           # Data processing and embeddings
│   ├── scraping/             # Groww web scraper
│   ├── tests/                # Backend tests
│   ├── main.py               # FastAPI application entry point
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend containerization
│   └── .env.example         # Environment variables template
├── frontend/                  # Next.js frontend
│   ├── app/                 # Next.js app directory
│   ├── components/           # React components
│   ├── public/              # Static assets
│   ├── package.json          # Node.js dependencies
│   ├── next.config.js        # Next.js configuration
│   └── tailwind.config.js    # TailwindCSS configuration
├── docs/                     # Documentation
│   ├── architecture.md       # Detailed architecture document
│   ├── edge-cases.md        # Edge cases analysis
│   └── problemStatement.md  # Project requirements
├── .github/                  # GitHub Actions workflows
│   └── workflows/
│       └── data-scraping.yml # Daily data scraping automation
└── README.md                # This file
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Vector Database**: ChromaDB
- **LLM Integration**: Groq (Llama2-70b)
- **Document Processing**: LangChain
- **Web Scraping**: BeautifulSoup + Selenium
- **Deployment**: Railway

### Frontend
- **Framework**: Next.js 14 with TypeScript
- **Styling**: TailwindCSS
- **State Management**: React hooks
- **HTTP Client**: Axios
- **Deployment**: Vercel

### Infrastructure
- **CI/CD**: GitHub Actions
- **Scheduling**: Daily cron jobs
- **Monitoring**: Built-in health checks
- **Data Sources**: 5 Groww mutual fund URLs

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized deployment)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env.local file
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```

### Docker Setup (Optional)

1. **Build and run backend container**:
   ```bash
   cd backend
   docker build -t mutual-fund-api .
   docker run -p 8000:8000 --env-file .env mutual-fund-api
   ```

## Environment Variables

### Backend (.env)
```env
# Required
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8000
CHROMA_DB_PATH=./chroma_db
PORT=8000
ENVIRONMENT=development
GROWW_BASE_URL=https://groww.in
SCRAPING_DELAY=2
MAX_RETRIES=3
NOTIFICATION_WEBHOOK=your_webhook_url_here
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Data Sources

The system scrapes data from 5 specific Groww mutual fund URLs:
1. HDFC Large Cap Fund Direct Growth
2. HDFC Equity Fund Direct Growth  
3. HDFC Focused Fund Direct Growth
4. HDFC ELSS Tax Saver Fund Direct Plan Growth
5. HDFC Mid Cap Fund Direct Growth

## API Endpoints

### Health Check
- `GET /api/health` - System health status

### Chat
- `POST /api/chat` - Submit user query for factual response
  ```json
  {
    "query": "What is the expense ratio of HDFC Large Cap Fund?"
  }
  ```

### Sources
- `GET /api/sources` - List of official data sources

## Automated Data Collection

The system automatically updates data daily at 2:00 AM UTC using GitHub Actions:
- Scrapes all 5 Groww URLs
- Processes and chunks the data
- Generates embeddings using sentence transformers
- Updates ChromaDB with new information
- Creates backups and monitors data quality

## Deployment

### Backend (Railway)
1. Push to GitHub main branch
2. Configure Railway secrets in GitHub repository settings
3. Automatic deployment via GitHub Actions

### Frontend (Vercel)
1. Push to GitHub main branch
2. Configure Vercel project and secrets
3. Automatic deployment via GitHub Actions

## Development Workflow

1. **Local Development**: Run both backend and frontend locally
2. **Data Updates**: Manual trigger of GitHub Actions workflow
3. **Testing**: Run tests before deployment
4. **Monitoring**: Check health endpoints and logs

## Compliance Features

- **Facts-only responses**: No investment advice provided
- **Source citations**: Every response includes source link
- **Query classification**: Filters out advisory questions
- **Data privacy**: No personal data collection
- **Rate limiting**: Respectful scraping of Groww platform

## Monitoring

### Health Checks
- Backend: `/api/health`
- Frontend: Automatic deployment health checks

### Metrics Tracked
- Scraping success rates
- API response times
- Data freshness
- Error rates and types

## Troubleshooting

### Common Issues

1. **TypeScript Errors**: Run `npm install` in frontend directory
2. **Import Errors**: Ensure all dependencies are installed
3. **API Connection**: Check environment variables and network
4. **Scraping Failures**: Verify Groww website accessibility

### Logs
- Backend: Check console output for detailed logs
- GitHub Actions: Check Actions tab for workflow status
- Railway: View logs in Railway dashboard

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request with description

## License

This project is developed as part of Milestone 2 for educational purposes.

## Support

For issues and questions:
- Check the documentation in `/docs` folder
- Review the edge cases analysis
- Monitor GitHub Actions for deployment status
