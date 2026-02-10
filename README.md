# GraphQL Recon Tool 🛡️

A lightweight, modular Python suite designed for Vulnerability Assessment and Penetration Testing (VAPT) of GraphQL endpoints. This tool automates the discovery of hidden endpoints, checks for introspection vulnerabilities, and extracts sensitive mutations.

## 🚀 Features

* **Path Fuzzing**: Automatically discovers GraphQL endpoints using a customizable `payloads.txt` wordlist.
* **Introspection Check**: Probes the API to determine if the schema is publicly accessible.
* **Schema Dumping**: Extracts the full JSON schema for offline analysis.
* **Mutation Analysis**: Automatically parses the schema to identify "Write" operations (Mutations) and flags sensitive keywords (e.g., delete, update, password).
* **Colorized Output**: Uses `colorama` for clear, readable terminal results.

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/Sumit0x00/graphql-hunt
cd graphql-hunt
```

2. Set up a Virtual Environment (Recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install Dependencies:
```bash
pip install -r requirements.txt
```

## 📖 Usage

### Basic Scan
Provide a base URL. The tool will automatically fuzz for common GraphQL paths:
```bash
python3 main.py -u https://api.example.com
```

### Direct Endpoint Scan
If you already know the path, provide the full URL:
```bash
python3 main.py -u https://api.example.com/v1/graphql
```

### Save Output
Specify a custom filename for the schema dump:
```bash
python3 main.py -u https://api.example.com/graphql -o my_scan.json
```

## ⚠️ Disclaimer

This tool is for educational and ethical security testing purposes only. Always obtain proper authorization before scanning any system that you do not own.