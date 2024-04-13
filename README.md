# OSINT Web Application

This is an Open Source Intelligence (OSINT) web application that combines the results from two tools, theHarvester and Amass, for scanning domains and gathering information about them. The server component is built with Flask, while the client component is built with React.

## Features

- Scan domains using theHarvester and Amass tools.
- View scan results and export them to an Excel file.
- Containerized with Docker for easy deployment and scalability.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/osint-web-app.git
   ```

2. Navigate to the project directory:

   ```bash
   cd osint-web-app
   ```

3. Build and run the Docker containers:

   ```bash
   docker-compose up --build
   ```

4. Access the application:

   - Open your web browser and go to http://localhost:3000 to access the client application.
   - Use the client to scan domains and view results.
   - The server is accessible at http://localhost:5000 for API requests.

## Usage

1. Enter a domain in the input field.
2. Select the tools you want to use for scanning (theHarvester, Amass, or both).
3. Click the "Scan" button to initiate the scan.
4. Wait for the scan to complete, and the results will be displayed.
5. Click on "Display Results" to view detailed results.
6. Click on "Export to Excel" to export the results to an Excel file.

