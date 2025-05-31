from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs
import mysql.connector
import argparse
import time
import re
from selenium.common.exceptions import NoSuchElementException

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="hasannet123@",
    database="scholars_data"
)
cursor = db.cursor()

options = Options()
options.add_argument('--lang=en-US')
options.add_argument('--start-maximized')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

parser = argparse.ArgumentParser()
parser.add_argument('--query', type=str, default="Lebanese University", help="Search query")
parser.add_argument('--mode', type=str, choices=["profiles", "full"], default="profiles", help="Scraping mode")
parser.add_argument('--limit', type=int, default=0, help="Number of profiles to scrape (0 = all)")
args = parser.parse_args()

query = args.query
mode = args.mode
limit = args.limit
scraped_profiles = 0

def process_citations(driver, cursor, paper_id):
    try:
        while True:
            time.sleep(2)
            citations = driver.find_elements(By.CSS_SELECTOR, 'div.gs_r.gs_or.gs_scl')
            for cite in citations:
                try:
                    title = cite.find_element(By.CSS_SELECTOR, 'h3.gs_rt').text.strip()
                    authors_year = cite.find_element(By.CSS_SELECTOR, 'div.gs_a').text.strip()
                    year_match = re.search(r'(19|20)\d{2}', authors_year)
                    year = year_match.group() if year_match else None
                    publisher = authors_year.split("-")[-1].strip() if "-" in authors_year else "N/A"
                    cursor.execute(
                        "INSERT INTO CITATIONS (PID, CTitle, CAuthors, CYear, CPublisher) VALUES (%s, %s, %s, %s, %s)",
                        (paper_id, title, authors_year, year, publisher)
                    )
                except Exception as e:
                    print("[!] Error inserting citation:", e)
                    continue
            try:
                next_buttoncite = driver.find_element(By.CSS_SELECTOR, 'button.gs_btnPR.gs_in_ib.gs_btn_lrge.gs_btn_half.gs_btn_lsu')
                if next_buttoncite.is_enabled():
                    driver.execute_script("arguments[0].click();", next_buttoncite)
                else:
                    break
            except NoSuchElementException:
                break
    except Exception as e:
        print("[!] Error in process_citations():", e)


url = f"https://scholar.google.com/scholar?hl=en&q={query.replace(' ', '+')}"
driver.get(url)
time.sleep(3)

if "not a robot" in driver.page_source.lower():
    input("[!] CAPTCHA detected. Solve it manually and press Enter...")

try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, f'//a[contains(@href,"view_op=view_org") and contains(text(),"{query}")]'))
    )
    profile_link = driver.find_element(By.XPATH, f'//a[contains(@href,"view_op=view_org") and contains(text(),"{query}")]')
    driver.execute_script("arguments[0].click();", profile_link)
    print(f"[✓] Clicked '{query}' profile link.")
    time.sleep(2)
except Exception as e:
    print("[!] Could not click profile link:", e)

while True:
    profile_links = driver.find_elements(By.CSS_SELECTOR, 'h3.gs_ai_name a')
    if not profile_links:
        break
    for i in range(len(profile_links)):
        if limit > 0 and scraped_profiles >= limit:
            break
        try:
            profile_links = driver.find_elements(By.CSS_SELECTOR, 'h3.gs_ai_name a')
            profile_links[i].click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "gsc_rsb_st")))

            parsed_url = urlparse(driver.current_url)
            rid = parse_qs(parsed_url.query).get("user", ["N/A"])[0]
            name = driver.find_element(By.ID, "gsc_prf_in").text
            affiliation = driver.find_element(By.CLASS_NAME, "gsc_prf_il").text
            try:
                email = driver.find_element(By.ID, "gsc_prf_ivh").text
            except:
                email = "N/A"
            homepage = driver.find_elements(By.CSS_SELECTOR, "a.gsc_prf_ila")[-1].get_attribute("href") if driver.find_elements(By.CSS_SELECTOR, "a.gsc_prf_ila") else "N/A"
            interests = ", ".join([i.text for i in driver.find_elements(By.CSS_SELECTOR, "#gsc_prf_int .gsc_prf_inta")])
            try:
                citation_rows = driver.find_elements(By.CSS_SELECTOR, "table#gsc_rsb_st tbody tr")
                article_stats = {}
                for row in citation_rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                         metric = cols[0].text.strip().lower()
                         value = cols[1].text.strip()
                         if "citations" in metric:
                             article_stats["Total_Citations"] = int(value)
                         elif "h-index" in metric:
                              article_stats["H_Index"] = int(value)
                         elif "i10-index" in metric:
                             article_stats["i10_index"] = int(value)
                total_citations = article_stats.get("Total_Citations", 0)
                h_index = article_stats.get("H_Index", 0)
                i10_index = article_stats.get("i10_index", 0)
            except:
                total_citations = 0
                h_index = 0
                i10_index = 0
            

            try:
                citation_rows = driver.find_elements(By.CSS_SELECTOR, "table#gsc_rsb_st tbody tr")
                article_stats = {}
                for row in citation_rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        metric = cols[0].text.strip().lower()
                        value = cols[1].text.strip()
                        if "citations" in metric:
                            article_stats["Total_Citations"] = int(value)
                        elif "h-index" in metric:
                            article_stats["H_Index"] = int(value)
                        elif "i10-index" in metric:
                            article_stats["i10_index"] = int(value)
                total_citations = article_stats.get("Total_Citations", 0)
                h_index = article_stats.get("H_Index", 0)
                i10_index = article_stats.get("i10_index", 0)
            except:
                total_citations = 0
                h_index = 0
                i10_index = 0

            try:
                prev_count, same_count = 0, 0
                while True:
                    articles_now = driver.find_elements(By.CLASS_NAME, 'gsc_a_tr')
                    if len(articles_now) == prev_count:
                        same_count += 1
                        if same_count >= 5:
                            break
                    else:
                        same_count = 0
                    prev_count = len(articles_now)
                    try:
                        more_btn = driver.find_element(By.ID, "gsc_bpf_more")
                        if more_btn.is_displayed():
                            driver.execute_script("arguments[0].click();", more_btn)
                            time.sleep(2)
                    except:
                        break
                total_publications = len(driver.find_elements(By.CLASS_NAME, "gsc_a_tr"))
            except:
                total_publications = 0

            cursor.execute("""
                INSERT INTO RESEARCHERS (RID, RName, Affiliation, Interests, Email, URL, Total_Citations, Total_Publications, H_Index, i10_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                Total_Citations=VALUES(Total_Citations),
                Total_Publications=VALUES(Total_Publications),
                H_Index=VALUES(H_Index),
                i10_index=VALUES(i10_index)
            """, (rid, name, affiliation, interests, email, homepage, total_citations, total_publications, h_index, i10_index))
            db.commit()
            scraped_profiles += 1

            if mode == "full":
                from bs4 import BeautifulSoup
                rows_html = driver.page_source
                soup = BeautifulSoup(rows_html, "html.parser")
                article_rows = soup.select("tr.gsc_a_tr")

                for index in range(len(article_rows)):
                    try:
                        rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
                        row = rows[index]
                        title_el = row.find_element(By.CLASS_NAME, "gsc_a_at")
                        title = title_el.text
                        link = title_el.get_attribute("href")
                        if not link:
                            continue
                        driver.execute_script("window.open(arguments[0]);", link)
                        driver.switch_to.window(driver.window_handles[1])
                        time.sleep(2)

                        article = {"RID": rid, "Title": title, "Link": link}
                        fields = driver.find_elements(By.CLASS_NAME, "gsc_oci_field")
                        values = driver.find_elements(By.CLASS_NAME, "gsc_oci_value")

                        for f, v in zip(fields, values):
                            label = f.text.strip()
                            val = v.text.strip()
                            if label == "Authors":
                                article["Authors"] = val
                            elif label == "Publication date":
                                year_match = re.search(r"(19|20)\d{2}", val)
                                article["Year"] = year_match.group(0) if year_match else None
                            elif label in ["Journal", "Conference", "Book"]:
                                article["Source"] = val
                            elif label == "Type":
                                article["Type"] = val
                            elif label == "Total citations":
                                try:
                                    cited_by_text = driver.find_element(By.CSS_SELECTOR, ".gsc_oci_value a").text
                                    match = re.search(r"\d+", cited_by_text)
                                    article["Citations"] = int(match.group()) if match else 0
                                except:
                                    article["Citations"] = 0

                        article.setdefault("Year", None)
                        article.setdefault("Source", None)
                        article.setdefault("Type", None)
                        article.setdefault("Citations", 0)
                        article.setdefault("Authors", None)

                        cursor.execute("""
                            INSERT INTO PAPERS (RID, PYear, PTitle, PAuthors, PLink, PType, PSource, PCitations)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (article["RID"], article["Year"], article["Title"], article["Authors"], article["Link"], article["Type"], article["Source"], article["Citations"]))
                        db.commit()
                        paper_id = cursor.lastrowid

                        try:
                            cited_by_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Cited by")
                            if cited_by_link:
                                cited_by_link.click()
                                WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gs_r.gs_or.gs_scl'))
                                )
                                if "not a robot" in driver.page_source.lower() or "unusual traffic" in driver.page_source.lower() or "automated queries" in driver.page_source.lower():
                                    print("[!] CAPTCHA detected. Solve it manually in browser.")
                                    input("Press Enter once the CAPTCHA is solved...")
                                    try:
                                        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gs_r.gs_or.gs_scl'))
        )
                                    except:
                                        print("[!] CAPTCHA passed, but citation results didn’t load.")
                                    
                                process_citations(driver, cursor, paper_id)
                                driver.back()
                                
                        except Exception as e:
                            print("[!] Error processing citations for paper:", e)
                        finally:
                            if len(driver.window_handles) > 0:
                                driver.switch_to.window(driver.window_handles[0])
                            time.sleep(1)

                    except Exception as e:
                        print("[!] Article error:", e)
                        try:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                        except:
                            pass
                        continue

            driver.back()
            time.sleep(2)

        except Exception as e:
            print(f"[!] Profile error ({i+1}):", e)
            try:
                driver.back()
                time.sleep(2)
            except:
                pass
            continue

    if limit > 0 and scraped_profiles >= limit:
        break

    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, 'button.gs_btnPR.gs_in_ib.gs_btn_half.gs_btn_lsb.gs_btn_srt.gsc_pgn_pnx')
        if next_btn.is_enabled():
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(3)
        else:
            break
    except:
        break

print("Scraped Successfully")
cursor.close()
db.close()
driver.quit()