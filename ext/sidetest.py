from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import datetime

driver = webdriver.PhantomJS()
driver.get("http://www.flashscore.com/team/newcastle-utd/"
	   "p6ahwuwJ/fixtures/")
driver.implicitly_wait(2)
url = "http://www.livesoccertv.com/teams/england/newcastle-united/"

xp = ".//div[@id='fs-fixtures']/table"
tables = driver.find_elements_by_xpath(xp)
for table in tables:
	comp = './/span[@class="tournament_part"]'
	comp = table.find_element_by_xpath(comp).text
	comp = "PL" if comp == "Premier League" else comp
	comp = "FRDLY" if comp == "Club Friendly" else comp
	comp = "CHSP" if comp == "Championship" else comp
	matches = './/tbody/tr'
	matches = table.find_elements_by_xpath(matches)
	for match in matches:
		matchid = match.get_attribute("id").split("_")[2]
		lnk = f"http://www.flashscore.com/match/{matchid}/#h2h;overall"
		dt = match.find_element_by_class_name("time").text
		d,t = dt.split(" ")
		d = datetime.datetime.strptime(d,"%d.%m.").replace(year=datetime.datetime.now().year)
		d = d + datetime.timedelta(years=1) if d < datetime.datetime.now() else d
		d = datetime.datetime.strftime(d,"%a %d %b")
		ht = match.find_element_by_class_name("padr").text
		at = match.find_element_by_class_name("padl").text
		ic = "[](#icon-home)" if "Newcastle" in ht else "[](#icon-away)"
		op = ht if "Newcastle" in at else at
		print(f"{d} | {t} | {ic} | {op} | {lnk} | {comp}")
		break