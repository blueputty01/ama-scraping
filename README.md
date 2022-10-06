# 👩‍⚕️FREIDA Residency Program Database Scraping

Downloads data from FREIDA Residency Program Database to .csv file to help medical students decide on their programs.

### ⚙️ Technologies and Dependencies
- Selenium
- [uBlock Origin](https://github.com/gorhill/uBlock) to keep automation requests lean

### ❓ How it works
Queries FREIDA API for list of programs and their URLs, then opens those links in a browser to download the information for that program.
