# 👩‍⚕️FREIDA Residency Program Database Scraping

Downloads data from FREIDA Residency Program Database to .csv file to help medical students decide on their programs.

### ⚙️ Technologies and Dependencies
- Selenium
- [uBlock Origin](https://github.com/gorhill/uBlock) to keep automation requests lean

### ❓ How it works
Queries FREIDA API for list of programs and their URLs, then opens those links in a browser to download the information for that program.

1. Create `.env` file containing USERNAME and PASSWORD for the AMA site. 
2. Set the specialty interests as a constant in `main.py`, at the top of the file (values found through network inspection)